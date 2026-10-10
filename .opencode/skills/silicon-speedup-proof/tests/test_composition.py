#!/usr/bin/env python3
"""Composition mathematics tests.

Three quantities stay distinct:

    S_i          = T_baseline,i / T_candidate,i
    S_composed   = T_baseline,composition / T_new_composed
    S_cumulative = T_original_baseline,end-to-end / T_final_composition,end-to-end

The last two require measured timings for their own comparison domains. They
are never obtained by multiplying isolated component ratios.

All fixtures are SYNTHETIC validator inputs, not hardware evidence.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _harness import (LEDGERS, S, codes, findings_for_record, ledger_findings,
                      load_json, run_findings, run_path, validate_ledger)


def read_records(name: str):
    text = (LEDGERS / name).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def rechain(records):
    """Recompute the hash chain so only the semantic rule under test fires."""
    prev = "GENESIS"
    for rec in records:
        if S.is_gap_record(rec):
            continue
        rec["prev_hash"] = prev
        rec["record_hash"] = S.compute_record_hash(rec)
        prev = rec["record_hash"]
    return records


def validate_records(records):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ledger.jsonl"
        path.write_text(
            "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n", encoding="utf-8")
        return validate_ledger.validate_ledger(path, None)


class SpeedupArithmetic(unittest.TestCase):
    def test_speedup_is_baseline_over_candidate(self):
        self.assertAlmostEqual(S.speedup(120.0, 40.0), 3.0)

    def test_speedup_refuses_a_non_positive_domain(self):
        for base, cand in ((0.0, 1.0), (1.0, 0.0), (-1.0, 1.0), (1.0, -1.0)):
            with self.subTest(base=base, cand=cand):
                with self.assertRaises(S.CompositionError):
                    S.speedup(base, cand)

    def test_speedup_refuses_missing_arms(self):
        with self.assertRaises(S.CompositionError):
            S.speedup(None, 1.0)

    def test_speedup_refuses_non_finite_arms(self):
        with self.assertRaises(S.CompositionError):
            S.speedup(float("nan"), 1.0)


class ThreeQuantitiesStayDistinct(unittest.TestCase):
    def test_declared_si_matches_the_recomputed_median_ratio(self):
        kernel = [r for r in read_records("synthetic_valid.jsonl")
                  if r.get("primitive_id") == "P-SYN-KERNEL" and r.get("status") == "reproduced"][0]
        arms = {m["arm"]: m for m in kernel["measurements"]}
        recomputed = S.speedup(S.median(arms["baseline"]["samples"]),
                               S.median(arms["candidate"]["samples"]))
        self.assertAlmostEqual(kernel["speedups"]["S_i"], recomputed, places=9)

    def test_a_tampered_ratio_is_caught(self):
        findings, _ = ledger_findings("adv14_hash_chain_broken.jsonl")
        self.assertIn("L-SPD-9", codes(findings, S.ERROR))

    def test_multiplying_components_is_refused(self):
        findings, _ = ledger_findings("adv05_multiplied_speedups.jsonl")
        errors = codes(findings, S.ERROR)
        self.assertIn("L-SPD-1", errors)   # declared computation is multiplication
        self.assertIn("L-SPD-2", errors)   # S_composed / S_cumulative not measured directly

    def test_unmeasured_composed_value_is_rejected_at_run_level(self):
        # A run record that declares a composed ratio with no composition arms.
        record = load_json(run_path("synthetic_valid_run.json"))
        record["claim"]["kind"] = "composition"
        record["timing"]["arms"] = [{"name": "baseline", "scope": "end-to-end", "samples": []}]
        found = codes(findings_for_record(record), S.ERROR)
        self.assertIn("R-TIME-3", found)

    def test_valid_ledger_passes(self):
        findings, _ = ledger_findings("synthetic_valid.jsonl")
        self.assertEqual(codes(findings, S.ERROR), set())


class IdealModel(unittest.TestCase):
    def test_sequential_model_is_ratio_of_sums(self):
        self.assertAlmostEqual(S.ideal_sequential([60.0, 60.0], [20.0, 20.0]), 3.0)

    def test_ideal_model_is_undefined_for_a_zero_total(self):
        with self.assertRaises(S.CompositionError):
            S.ideal_sequential([60.0, 60.0], [0.0, 0.0])

    def test_ideal_model_is_undefined_for_a_zero_baseline_total(self):
        with self.assertRaises(S.CompositionError):
            S.ideal_sequential([0.0, 0.0], [20.0, 20.0])

    def test_ideal_model_is_undefined_with_no_stages(self):
        with self.assertRaises(S.CompositionError):
            S.ideal_sequential([], [])

    def test_ideal_model_rejects_mismatched_stage_counts(self):
        with self.assertRaises(S.CompositionError):
            S.ideal_sequential([60.0, 60.0], [20.0])

    def test_eta_is_one_when_the_composition_matches_its_ideal(self):
        base = [60.0, 60.0]
        s_ideal = S.ideal_sequential(base, [20.0, 20.0])
        s_measured = S.speedup(sum(base), sum([20.0, 20.0]))
        self.assertAlmostEqual(S.interaction_factor(s_measured, s_ideal), 1.0)

    def test_eta_below_one_flags_interference(self):
        eta = S.interaction_factor(S.speedup(120.0, 200.0),
                                   S.ideal_sequential([60.0, 60.0], [20.0, 20.0]))
        self.assertAlmostEqual(eta, 0.2)
        self.assertLess(eta, 1.0)

    def test_eta_is_undefined_for_a_zero_or_absent_ideal(self):
        self.assertIsNone(S.interaction_factor(2.0, 0.0))
        self.assertIsNone(S.interaction_factor(2.0, None))

    def test_eta_requires_a_defined_ideal(self):
        findings, _ = ledger_findings("adv05_multiplied_speedups.jsonl")
        self.assertIn("L-SPD-5", codes(findings, S.ERROR))

    def test_interaction_factor_is_not_a_speedup_claim(self):
        # eta is a diagnostic ratio. The validator only accepts it alongside a
        # declared ideal model; it never promotes a performance claim by itself.
        findings, _ = ledger_findings("synthetic_valid.jsonl")
        self.assertNotIn("L-SPD-5", codes(findings))


class ScopeComparability(unittest.TestCase):
    def test_matching_scopes_are_compatible(self):
        self.assertTrue(S.scopes_compatible(["end-to-end", "end-to-end", None]))

    def test_mixed_scopes_are_incompatible(self):
        self.assertFalse(S.scopes_compatible(["stage-2 only", "end-to-end"]))

    def test_mixed_scope_record_is_rejected(self):
        self.assertIn("R-TIME-5", codes(run_findings("adv15_mixed_scopes.json"), S.ERROR))


class CompositionFreshness(unittest.TestCase):
    """A composition must be re-run as one implementation."""

    def test_reusing_a_component_run_id_is_rejected(self):
        findings, _ = ledger_findings("adv06_no_fresh_composition_run.jsonl")
        self.assertIn("L-CMP-3", codes(findings, S.ERROR))

    def test_legal_composition_in_the_valid_ledger_is_accepted(self):
        findings, _ = ledger_findings("synthetic_valid.jsonl")
        self.assertNotIn("L-CMP-3", codes(findings))

    def test_unknown_component_is_flagged_not_assumed_present(self):
        records = rechain(read_records("synthetic_valid.jsonl"))
        comp = [r for r in records if r.get("kind") == "composition"][0]
        comp["provenance"]["component_ids"] = ["P-DOES-NOT-EXIST"]
        findings, _ = validate_records(records)
        self.assertIn("L-CMP-2", codes(findings, S.WARN))

    def test_composition_with_fresh_run_id_is_accepted(self):
        records = rechain(read_records("synthetic_valid.jsonl"))
        findings, _ = validate_records(records)
        self.assertNotIn("L-CMP-3", codes(findings))


class MultiplicativeReferenceIsDiagnosticOnly(unittest.TestCase):
    def test_reference_is_computable_but_never_promoted(self):
        self.assertEqual(S.multiplicative_reference([3.0, 2.0]), 6.0)
        findings, _ = ledger_findings("adv05_multiplied_speedups.jsonl")
        self.assertIn("L-SPD-1", codes(findings, S.ERROR))

    def test_individual_product_refuses_degenerate_ratios(self):
        with self.assertRaises(S.CompositionError):
            S.individual_speedup([3.0, 0.0])
        with self.assertRaises(S.CompositionError):
            S.individual_speedup([3.0, None])


if __name__ == "__main__":
    unittest.main(verbosity=2)