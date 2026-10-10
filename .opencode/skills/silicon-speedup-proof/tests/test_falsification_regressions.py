#!/usr/bin/env python3
"""Regression tests for defects found by adversarial falsification.

Every test here corresponds to a real defect that shipped once and was caught
by an external attacker. They exist so the same hole cannot be reopened by a
later refactor. Each pairs the attack with a control, because a gate that
rejects everything is not a gate.

All inputs are SYNTHETIC. Nothing here is a hardware measurement.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from _harness import (LEDGERS, PROJECT_ROOT, RUNS, S, codes,
                      findings_for_record, validate_ledger, validate_run)

LADDER = S.EVIDENCE_LADDER


def full_chain(target: str):
    chain, prev = [], "UNEVIDENCED"
    for lvl in LADDER[1:S.EVIDENCE_RANK[target] + 1]:
        chain.append({"from": prev, "to": lvl, "event_ref": f"artifact://{prev}_to_{lvl}"})
        prev = lvl
    return chain


def valid_record(**over):
    rec = json.loads((RUNS / "synthetic_valid_run.json").read_text(encoding="utf-8"))
    rec.update(over)
    return rec


def findings(rec, name="inline.json"):
    return findings_for_record(rec, where=name)


def ledger_findings_for(records, name="inline.jsonl"):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
                        encoding="utf-8")
        return validate_ledger.validate_ledger(path, PROJECT_ROOT)


def ledger_findings_text(text: str):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "l.jsonl"
        path.write_text(text, encoding="utf-8")
        return validate_ledger.validate_ledger(path, PROJECT_ROOT)


class Defect1_SelfDeclaredEvidenceStrength(unittest.TestCase):
    """A VERIFIED claim passed on a self-typed SCOPED_VERIFIED scalar, because
    validate-run.py never called transition_chain_is_complete and the schema
    made the honest fix illegal."""

    def _verified(self):
        return valid_record(
            claim={"strength": "VERIFIED", "kind": "performance",
                   "statement": "verified", "scope": "synthetic fixture only",
                   "assigned_manually": False},
            evidence_strength="SCOPED_VERIFIED",
            formal={"theorem_target": "speedup_bound", "file": "f.lean",
                    "command": "lean f.lean", "exit_status": 0, "kernel_checked": True},
        )

    def test_atomic_attack_no_transition_trail_is_rejected(self):
        found = codes(findings(self._verified()), S.ERROR)
        self.assertIn("R-CLM-3", found)

    def test_control_a_complete_trail_is_accepted(self):
        rec = self._verified()
        rec["transition_records"] = full_chain("SCOPED_VERIFIED")
        self.assertNotIn("R-CLM-3", codes(findings(rec), S.ERROR))

    def test_gate_discriminates_rather_than_always_rejecting(self):
        without = codes(findings(self._verified()), S.ERROR)
        partial = self._verified()
        partial["transition_records"] = full_chain("SCOPED_VERIFIED")[:-1]
        with_full = self._verified()
        with_full["transition_records"] = full_chain("SCOPED_VERIFIED")
        self.assertIn("R-CLM-3", without)
        self.assertIn("R-CLM-3", codes(findings(partial), S.ERROR))
        self.assertNotIn("R-CLM-3", codes(findings(with_full), S.ERROR))

    def test_a_skipped_rung_is_rejected(self):
        rec = self._verified()
        rec["transition_records"] = [
            {"from": "UNEVIDENCED", "to": "OBSERVED", "event_ref": "e1"},
            {"from": "OBSERVED", "to": "REPRODUCED", "event_ref": "e3"},
            {"from": "REPRODUCED", "to": "SCOPED_VERIFIED", "event_ref": "e7"},
        ]
        self.assertIn("R-CLM-3", codes(findings(rec), S.ERROR))

    def test_a_transition_without_an_event_reference_is_rejected(self):
        rec = self._verified()
        rec["transition_records"] = full_chain("SCOPED_VERIFIED")
        rec["transition_records"][2]["event_ref"] = ""
        self.assertIn("R-CLM-3", codes(findings(rec), S.ERROR))

    def test_the_schema_admits_the_honest_fix(self):
        # The attack succeeded partly because adding the trail was schema-illegal.
        rec = self._verified()
        rec["transition_records"] = full_chain("SCOPED_VERIFIED")
        errors = S.validate_against_schema(rec, "evidence-record.schema.json")
        self.assertEqual([e for e in errors if "transition_records" in e], [])

    def test_valid_fixture_carries_its_own_trail(self):
        rec = json.loads((RUNS / "synthetic_valid_run.json").read_text(encoding="utf-8"))
        self.assertTrue(S.transition_chain_is_complete(
            rec["evidence_strength"], rec.get("transition_records") or []))


class Defect2_OneBadLineVoidsTheAudit(unittest.TestCase):
    """A non-object ledger line raised AttributeError, killing the validator:
    the over-claimed records after it were never examined."""

    def test_int_line_is_reported_not_crashed_on(self):
        body = (LEDGERS / "synthetic_valid.jsonl").read_text()
        found, summary = ledger_findings_text("42\n" + body)
        self.assertIn("L-SCHEMA", codes(found, S.ERROR))
        self.assertEqual(summary["records"], 6)

    def test_list_line_is_reported_not_crashed_on(self):
        _, summary = ledger_findings_text("[1,2,3]\n{}\n")
        self.assertEqual(summary["records"], 1)

    def test_string_and_float_lines_are_reported(self):
        for line in ('"hello"', '4.2', 'null', 'true'):
            with self.subTest(line=line):
                found, _ = ledger_findings_text(line + "\n{}\n")
                self.assertIn("L-SCHEMA", codes(found, S.ERROR))

    def test_non_utf8_ledger_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "l.jsonl"
            path.write_bytes(b'{"schema_version": "\xff\xfe"}\n')
            found, _ = validate_ledger.validate_ledger(path, PROJECT_ROOT)
        self.assertIn("L-SCHEMA", codes(found, S.ERROR))

    def test_non_string_samples_do_not_crash_the_statistics(self):
        rec = valid_record()
        rec["timing"]["arms"][0]["samples"] = ["x", "y"]
        stats = S.arm_stats(rec["timing"]["arms"][0]["samples"])
        self.assertEqual(stats["n"], 0)
        self.assertEqual(stats["n_dropped"], 2)
        self.assertFalse(stats["has_timing"])
        # and the validator still reports rather than raising
        self.assertNotEqual(codes(findings(rec), S.ERROR), set())

    def test_non_numeric_speedup_is_reported(self):
        rec = json.loads((LEDGERS / "adv05_multiplied_speedups.jsonl")
                         .read_text().splitlines()[0])
        rec["speedups"]["S_i"] = "fast"
        self.assertIn("L-SPD-9", codes(ledger_findings_for([rec])[0], S.ERROR))

    def test_non_numeric_scaling_sizes_do_not_crash(self):
        rec = valid_record()
        rec["scaling"] = {"sizes": ["512", "1024"], "ratios": [1, 2]}
        rec["claim"]["statement"] = "scales linearly across sizes"
        self.assertNotEqual(codes(findings(rec), S.ERROR), set())

    def test_top_level_non_object_document_is_reported(self):
        for doc in ([1, 2, 3], 7, "x", None):
            with self.subTest(doc=type(doc).__name__):
                found = validate_run.validate_record(doc, where="d.json", repo_root=PROJECT_ROOT,
                                                     record_path=None)
                self.assertEqual(codes(found, S.ERROR), {"R-SCHEMA"})


class Defect3_FloorTableFailedOpen(unittest.TestCase):
    """minimum_evidence_for returned None for an unrecognised claim kind, so a
    typo silently removed the floor."""

    def test_unknown_kinds_fail_closed(self):
        for kind in ("perfomance", "PERFORMANCE", "", None, "hardware-mechanism", 42):
            with self.subTest(kind=kind):
                self.assertIsNotNone(
                    S.claim_exceeds_evidence("VERIFIED", "CORRECTNESS", kind))

    def test_known_kind_is_unaffected(self):
        self.assertIsNone(S.claim_exceeds_evidence("STRONG_LOCAL", "REPRODUCED", "performance"))

    def test_unknown_kind_requires_the_strictest_evidence(self):
        self.assertEqual(S.minimum_evidence_for("VERIFIED", "nonsense"), S.EVIDENCE_LADDER[-1])

    def test_every_declared_kind_has_a_non_default_floor(self):
        for kind in S.CLAIM_KINDS:
            with self.subTest(kind=kind):
                self.assertIn(S.minimum_evidence_for("VERIFIED", kind),
                              ("SCOPED_VERIFIED",))


class Defect4_EmptyLedgerPassed(unittest.TestCase):
    """An empty or comment-only ledger returned exit 0, so a truncated or
    mis-pathed ledger looked identical to a verified one."""

    def test_empty_ledger_is_an_error(self):
        found, summary = ledger_findings_text("")
        self.assertIn("L-EMPTY", codes(found, S.ERROR))
        self.assertEqual(summary["records"], 0)

    def test_comment_only_ledger_is_an_error(self):
        found, _ = ledger_findings_text("# a comment\n\n   \n")
        self.assertIn("L-EMPTY", codes(found, S.ERROR))

    def test_a_real_ledger_is_not_flagged_empty(self):
        body = (LEDGERS / "synthetic_valid.jsonl").read_text()
        found, _ = ledger_findings_text(body)
        self.assertNotIn("L-EMPTY", codes(found))


class Defect5_RepoRootSilentlyDisabledACheck(unittest.TestCase):
    """Without --repo-root the operator source_ref check vanished with no notice."""

    def _ledger_with_operator(self):
        body = (LEDGERS / "synthetic_valid.jsonl").read_text()
        records = [json.loads(l) for l in body.splitlines() if l.strip()]
        for rec in records:
            if rec.get("operator"):
                rec["operator"]["source_ref"] = "does/not/exist.py"
        prev = "GENESIS"
        for rec in records:
            if S.is_gap_record(rec):
                continue
            rec["prev_hash"] = prev
            rec["record_hash"] = S.compute_record_hash(rec)
            prev = rec["record_hash"]
        return records

    def test_missing_source_ref_is_an_error_with_repo_root(self):
        found, _ = ledger_findings_for(self._ledger_with_operator())
        self.assertIn("L-OPR-2", codes(found, S.ERROR))

    def test_absence_of_repo_root_is_reported_not_silent(self):
        records = self._ledger_with_operator()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "l.jsonl"
            path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
                            encoding="utf-8")
            found, _ = validate_ledger.validate_ledger(path, None)
        self.assertIn("L-OPR-2", codes(found, S.WARN))
        self.assertIn("--repo-root", " ".join(f.message for f in found if f.code == "L-OPR-2"))


class RefusedAttackIsStillRefused(unittest.TestCase):
    """The hardening must not have weakened any pre-existing gate."""

    def test_core_invariant_still_holds(self):
        # Note the ladder is a total order: CORRECTNESS evidence SATISFIES a
        # performance floor, because a record at CORRECTNESS has at least
        # REPRODUCED. These pairs are the genuinely inadmissible ones.
        for claim, evidence in (("VERIFIED", "OBSERVED"),
                                ("VERIFIED", "CORRECTNESS"),
                                ("VERIFIED", "FORMAL"),
                                ("VERIFIED", "MECHANISM"),
                                ("STRONG_LOCAL", "EXECUTED"),
                                ("STRONG_LOCAL", "OBSERVED"),
                                ("FORMAL_PARTIAL", "OBSERVED"),
                                ("FORMAL_PARTIAL", "EXECUTED")):
            with self.subTest(claim=claim, evidence=evidence):
                self.assertIsNotNone(S.claim_exceeds_evidence(claim, evidence, "performance"))

    def test_every_adversarial_fixture_still_fails(self):
        for path in sorted((LEDGERS).glob("adv*.jsonl")):
            with self.subTest(fixture=path.name):
                found, _ = ledger_findings_text(path.read_text())
                self.assertNotEqual(codes(found, S.ERROR), set())

    def test_valid_fixtures_still_pass(self):
        found, _ = ledger_findings_text(
            (LEDGERS / "synthetic_valid.jsonl").read_text())
        self.assertEqual(codes(found, S.ERROR), set())
        self.assertEqual(codes(findings(valid_record()), S.ERROR), set())


if __name__ == "__main__":
    unittest.main(verbosity=2)