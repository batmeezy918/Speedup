#!/usr/bin/env python3
"""Claim-strength enforcement tests.

The constitutional invariant of this framework is

    CLAIM_STRENGTH <= EVIDENCE_STRENGTH

These tests assert that the invariant is actually enforced by code, that the
ladders are total and ordered, and that a label alone never passes.

All fixtures are SYNTHETIC validator inputs, not hardware evidence.
"""
from __future__ import annotations

import itertools
import unittest

from _harness import (S, codes, findings_for_record, ledger_findings,
                      load_json, run_findings, run_path)


class LadderIntegrity(unittest.TestCase):
    def test_evidence_ladder_is_ordered_and_unique(self):
        self.assertEqual(len(set(S.EVIDENCE_LADDER)), len(S.EVIDENCE_LADDER))
        ranks = [S.EVIDENCE_RANK[name] for name in S.EVIDENCE_LADDER]
        self.assertEqual(ranks, sorted(ranks))
        self.assertEqual(ranks[0], 0)

    def test_claim_ladder_matches_the_repository_lattice(self):
        # speedup/const.py CLAIM_LATTICE is the repository's promotion lattice.
        # The skill's ladder adds NONE at the bottom and must preserve the order.
        repo = ("CANDIDATE", "STRONG_LOCAL", "FORMAL_PARTIAL", "VERIFIED")
        idx = [S.CLAIM_RANK[name] for name in repo]
        self.assertEqual(idx, sorted(idx))
        self.assertTrue(set(repo).issubset(set(S.CLAIM_LADDER)))

    def test_every_claim_kind_has_a_floor_at_every_strength(self):
        for strength in S.CLAIM_LADDER:
            for kind in S.CLAIM_KINDS:
                self.assertIsNotNone(
                    S.minimum_evidence_for(strength, kind),
                    msg=f"no evidence floor declared for ({strength}, {kind})",
                )


class ClaimNeverExceedsEvidence(unittest.TestCase):
    def test_exact_floor_is_admissible(self):
        for (strength, kind), floor in S.MINIMUM_EVIDENCE.items():
            with self.subTest(claim=f"{strength}/{kind}"):
                self.assertIsNone(S.claim_exceeds_evidence(strength, floor, kind))

    def test_one_rung_below_the_floor_is_rejected(self):
        for (strength, kind), floor in S.MINIMUM_EVIDENCE.items():
            rank = S.EVIDENCE_RANK[floor]
            if rank == 0:
                continue
            weaker = S.EVIDENCE_LADDER[rank - 1]
            with self.subTest(claim=f"{strength}/{kind}", evidence=weaker):
                self.assertIsNotNone(S.claim_exceeds_evidence(strength, weaker, kind))

    def test_rank_inversion_is_always_rejected(self):
        for claim, evidence in itertools.product(S.CLAIM_LADDER, S.EVIDENCE_LADDER):
            if S.CLAIM_RANK[claim] > S.EVIDENCE_RANK[evidence]:
                with self.subTest(claim=claim, evidence=evidence):
                    self.assertIsNotNone(S.claim_exceeds_evidence(claim, evidence, "performance"))

    def test_unknown_strengths_are_rejected_not_ignored(self):
        self.assertIsNotNone(S.claim_exceeds_evidence("VERY_VERIFIED", "FORMAL", "formal"))
        self.assertIsNotNone(S.claim_exceeds_evidence("VERIFIED", "TOTALLY_SOUND", "formal"))


class DocumentedBehaviour(unittest.TestCase):
    """The specific behaviours the skill promises, one test each."""

    def test_missing_raw_timings_blocks_a_measured_speedup_claim(self):
        findings = run_findings("adv01_exit_zero_no_timing.json")
        found = codes(findings, S.ERROR)
        # Both arms present but empty: no positive sample anywhere, and fewer
        # than two arms with real timings, so no ratio may be formed.
        self.assertIn("R-TIME-2", found)
        self.assertIn("R-TIME-3", found)
        self.assertIn("R-CLM-1", found)

    def test_a_non_positive_sample_set_is_also_a_timing_absence(self):
        self.assertIn("R-TIME-2", codes(run_findings("adv16_zero_input_domain.json"), S.ERROR))

    def test_missing_correctness_blocks_a_verified_implementation_claim(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record["correctness"] = {}
        record["claim"]["kind"] = "implementation"
        record["claim"]["strength"] = "STRONG_LOCAL"
        record["evidence_strength"] = "REPRODUCED"
        found = codes(findings_for_record(record), S.ERROR)
        self.assertIn("R-CORR-3", found)
        self.assertIn("R-CLM-1", found)

    def test_failed_equivalence_rejects_correctness_promotion(self):
        findings = run_findings("adv14_equivalence_failed.json")
        found = codes(findings, S.ERROR)
        self.assertIn("R-CORR-1", found)
        self.assertIn("R-CORR-2", found)
        self.assertIn("R-CORR-7", found)

    def test_unsupported_causal_mechanism_restricts_the_claim(self):
        findings = run_findings("adv07_mechanism_without_evidence.json")
        self.assertIn("R-MECH-1", codes(findings, S.ERROR))

    def test_unresolved_dependencies_reject_the_claim_that_relies_on_them(self):
        run_codes = codes(run_findings("adv11_unresolved_dependency.json"), S.ERROR)
        self.assertIn("R-DEP-1", run_codes)
        ledger, _ = ledger_findings("adv19_unresolved_dependency.jsonl")
        self.assertIn("L-DEP-1", codes(ledger, S.ERROR))

    def test_contradictory_runs_are_preserved_not_smoothed(self):
        findings, _ = ledger_findings("adv09_contradictory_rerun.jsonl")
        self.assertIn("L-CNT-1", codes(findings, S.ERROR))
        hit = [f for f in findings if f.code == "L-CNT-1"][0]
        self.assertIn("contradiction", hit.message)

    def test_manual_raise_without_transitions_is_rejected(self):
        run_found = codes(run_findings("adv12_manual_claim_raise.json"), S.ERROR)
        ledger_found, _ = ledger_findings("adv12_manual_raise.jsonl")
        self.assertIn("R-CLM-2", run_found)
        self.assertIn("L-CLM-2", codes(ledger_found, S.ERROR))
        self.assertIn("L-CLM-3", codes(ledger_found, S.ERROR))


class CorrectnessIsNotPerformance(unittest.TestCase):
    """A correctness pass does not imply a speedup; a speedup does not imply correctness."""

    def test_performance_claim_does_not_satisfy_an_implementation_claim(self):
        # Same evidence level, different claim kind: the floor differs.
        self.assertIsNotNone(S.claim_exceeds_evidence("STRONG_LOCAL", "REPRODUCED", "implementation"))
        self.assertIsNone(S.claim_exceeds_evidence("STRONG_LOCAL", "REPRODUCED", "performance"))

    def test_mechanism_claim_needs_mechanism_evidence_not_a_timing_delta(self):
        self.assertIsNotNone(S.claim_exceeds_evidence("STRONG_LOCAL", "REPRODUCED", "hardware_mechanism"))
        self.assertIsNone(S.claim_exceeds_evidence("STRONG_LOCAL", "MECHANISM", "hardware_mechanism"))


class TransitionRecords(unittest.TestCase):
    def test_complete_chain_is_accepted(self):
        records = [
            {"from": "UNEVIDENCED", "to": "OBSERVED", "event_ref": "e1"},
            {"from": "OBSERVED", "to": "EXECUTED", "event_ref": "e2"},
            {"from": "EXECUTED", "to": "REPRODUCED", "event_ref": "e3"},
        ]
        self.assertTrue(S.transition_chain_is_complete("REPRODUCED", records))

    def test_missing_rung_is_rejected(self):
        records = [
            {"from": "UNEVIDENCED", "to": "OBSERVED", "event_ref": "e1"},
            {"from": "OBSERVED", "to": "REPRODUCED", "event_ref": "e3"},
        ]
        self.assertFalse(S.transition_chain_is_complete("REPRODUCED", records))

    def test_out_of_order_chain_is_rejected(self):
        records = [
            {"from": "EXECUTED", "to": "REPRODUCED", "event_ref": "e2"},
            {"from": "UNEVIDENCED", "to": "OBSERVED", "event_ref": "e1"},
        ]
        self.assertFalse(S.transition_chain_is_complete("REPRODUCED", records))

    def test_transition_without_event_reference_is_rejected(self):
        records = [{"from": "UNEVIDENCED", "to": "OBSERVED", "event_ref": ""}]
        self.assertFalse(S.transition_chain_is_complete("OBSERVED", records))

    def test_empty_transitions_reject_any_promotion(self):
        self.assertFalse(S.transition_chain_is_complete("OBSERVED", []))
        self.assertTrue(S.transition_chain_is_complete("UNEVIDENCED", []))


class CompositionDoesNotInheritStrength(unittest.TestCase):
    """VERIFIED(P_i) never implies VERIFIED(P_i composed with P_j)."""

    def test_component_verification_is_not_sufficient(self):
        # The composition rule is enforced structurally: a composition record
        # must present its own measured evidence, not borrow the component's.
        findings, _ = ledger_findings("adv06_no_fresh_composition_run.jsonl")
        self.assertIn("L-CMP-3", codes(findings, S.ERROR))

    def test_composition_claim_needs_correctness_evidence(self):
        self.assertIsNotNone(S.claim_exceeds_evidence("STRONG_LOCAL", "REPRODUCED", "composition"))
        self.assertIsNone(S.claim_exceeds_evidence("STRONG_LOCAL", "CORRECTNESS", "composition"))


class ScopeIsMandatory(unittest.TestCase):
    def test_valid_record_declares_a_scope(self):
        self.assertNotIn("R-CLM-4", codes(run_findings("synthetic_valid_run.json"), S.ERROR))

    def test_blank_scope_is_an_error(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record["claim"]["scope"] = "   "
        self.assertIn("R-CLM-4", codes(findings_for_record(record), S.ERROR))


if __name__ == "__main__":
    unittest.main(verbosity=2)
