#!/usr/bin/env python3
"""Ledger validation tests: structure, ordering, chronology, exit codes.

All fixtures are SYNTHETIC validator inputs, not hardware evidence.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from _harness import (LEDGERS, S, cli, codes, ledger_findings, ledger_path,
                       validate_ledger)


class ValidLedger(unittest.TestCase):
    """A gate that rejects everything is not a gate."""

    def test_valid_ledger_has_no_errors(self):
        findings, summary = ledger_findings("synthetic_valid.jsonl")
        self.assertEqual(codes(findings, S.ERROR), set(),
                         msg="\n".join(f"{f.code} {f.where} {f.message}" for f in findings))

    def test_valid_ledger_exit_code_zero(self):
        proc = cli("validate-ledger.py", str(ledger_path("synthetic_valid.jsonl")))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_valid_ledger_is_labelled_synthetic(self):
        findings, _ = ledger_findings("synthetic_valid.jsonl")
        self.assertIn("L-SYN-1", codes(findings))

    def test_schema_backend_is_reported(self):
        _, summary = ledger_findings("synthetic_valid.jsonl")
        self.assertIn(summary["schema_backend"], ("jsonschema", "builtin-mini"))


class AdversarialLedgers(unittest.TestCase):
    """Each fixture must be caught by its specific code, not incidentally."""

    EXPECT = {
        "adv01_exit_zero_no_timing.jsonl": "L-EXE-3",
        "adv05_multiplied_speedups.jsonl": "L-SPD-1",
        "adv06_no_fresh_composition_run.jsonl": "L-CMP-3",
        "adv09_contradictory_rerun.jsonl": "L-CNT-1",
        "adv12_manual_raise.jsonl": "L-CLM-3",
        "adv13_negative_erased.jsonl": "L-ST-2",
        "adv14_hash_chain_broken.jsonl": "L-HASH-1",
        "adv15_illegal_transition.jsonl": "L-ST-1",
        "adv16_claim_exceeds_evidence.jsonl": "L-CLM-1",
        "adv17_gap_closed_without_evidence.jsonl": "L-GAP-2",
        "adv18_operator_not_implemented.jsonl": "L-OPR-1",
        "adv19_unresolved_dependency.jsonl": "L-DEP-1",
        "adv20_formal_without_proof.jsonl": "L-FRM-4",
        "adv21_all_vacuous_checks.jsonl": "L-VAC-1",
    }

    def test_expected_code_is_raised(self):
        for name, expected in self.EXPECT.items():
            with self.subTest(fixture=name):
                findings, _ = ledger_findings(name)
                self.assertIn(expected, codes(findings, S.ERROR))

    def test_every_adversarial_ledger_fails(self):
        for name in self.EXPECT:
            with self.subTest(fixture=name):
                proc = cli("validate-ledger.py", str(ledger_path(name)))
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_fixtures_cover_every_adversarial_case_id(self):
        # Cases 1-12 of the adversarial battery, plus the regression set.
        present = {p.name for p in LEDGERS.glob("*.jsonl")}
        for required in ("adv01", "adv05", "adv06", "adv09", "adv12"):
            self.assertTrue(any(n.startswith(required) for n in present), required)


class MultiplicationIsRefused(unittest.TestCase):
    def test_product_of_components_is_rejected(self):
        findings, _ = ledger_findings("adv05_multiplied_speedups.jsonl")
        hit = [f for f in findings if f.code == "L-SPD-1"]
        self.assertTrue(hit)
        self.assertIn("product_of_components", hit[0].message)

    def test_unmeasured_composed_value_is_rejected(self):
        findings, _ = ledger_findings("adv05_multiplied_speedups.jsonl")
        errors = {f.code for f in findings if f.severity == S.ERROR}
        self.assertIn("L-SPD-2", errors)
        msgs = " ".join(f.message for f in findings if f.code == "L-SPD-2")
        self.assertIn("S_composed", msgs)
        self.assertIn("S_cumulative", msgs)

    def test_individual_product_is_available_only_for_detection(self):
        # The helper exists so the validator can recognise it, and it refuses
        # degenerate domains rather than returning a plausible-looking number.
        self.assertEqual(S.individual_speedup([3.0, 2.0]), 6.0)
        with self.assertRaises(S.CompositionError):
            S.individual_speedup([0.0, 2.0])


class GapTaxonomy(unittest.TestCase):
    def test_every_mandatory_gap_class_is_present(self):
        mandatory = {
            "dependency", "equivalence_correctness", "measurement", "attribution",
            "scaling", "hardware_mechanism", "composition", "formal_proof",
            "vacuity", "provenance", "reproducibility",
        }
        self.assertTrue(mandatory.issubset(set(S.GAP_CLASSES)))

    def test_legacy_repository_vocabulary_maps_into_the_taxonomy(self):
        for legacy in ("DEPENDENCY_GAP", "FORMAL_GAP", "RECONSTRUCTION_GAP",
                       "OBSERVABLE_COMPLETENESS_GAP", "HARDWARE_MECHANISM_GAP"):
            self.assertIn(legacy, S.GAP_CLASS_ALIASES)
            self.assertIn(S.GAP_CLASS_ALIASES[legacy], S.GAP_CLASSES)


class ValidatorDoesNotFabricate(unittest.TestCase):
    """The validator must not write, repair, or upgrade anything it reads."""

    def test_ledger_bytes_are_unchanged_by_validation(self):
        path = ledger_path("synthetic_valid.jsonl")
        before = path.read_bytes()
        cli("validate-ledger.py", str(path))
        self.assertEqual(path.read_bytes(), before)

    def test_adversarial_ledger_is_not_repaired(self):
        path = ledger_path("adv14_hash_chain_broken.jsonl")
        before = path.read_bytes()
        findings, _ = ledger_findings(path.name)
        self.assertTrue(findings)
        self.assertEqual(path.read_bytes(), before)

    def test_no_new_files_are_created(self):
        path = ledger_path("synthetic_valid.jsonl")
        before = sorted(p.name for p in path.parent.iterdir())
        cli("validate-ledger.py", str(path))
        self.assertEqual(sorted(p.name for p in path.parent.iterdir()), before)

    def test_fixture_files_are_marked_synthetic(self):
        for path in LEDGERS.glob("*.jsonl"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                self.assertTrue(
                    (rec.get("provenance") or {}).get("synthetic") or rec.get("synthetic"),
                    msg=f"{path.name} carries a record that is not labelled synthetic",
                )


class MalformedInput(unittest.TestCase):
    def test_unparseable_line_is_an_error_not_a_crash(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "broken.jsonl"
            broken.write_text('{"not": "json"\n', encoding="utf-8")
            findings, summary = validate_ledger.validate_ledger(broken, None)
        self.assertEqual(summary["records"], 0)
        self.assertIn("L-SCHEMA", codes(findings, S.ERROR))

    def test_blank_and_comment_lines_are_tolerated(self):
        import tempfile
        body = ledger_path("synthetic_valid.jsonl").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            padded = Path(tmp) / "padded.jsonl"
            padded.write_text("# a comment\n\n" + body, encoding="utf-8")
            findings, summary = validate_ledger.validate_ledger(padded, None)
        self.assertEqual(summary["records"], 6)
        self.assertEqual(codes(findings, S.ERROR), set())

    def test_missing_file_is_usage_error(self):
        proc = cli("validate-ledger.py", str(ledger_path("does_not_exist.jsonl")))
        self.assertEqual(proc.returncode, 2)


class JsonOutput(unittest.TestCase):
    def test_json_mode_emits_machine_readable_verdict(self):
        proc = cli("validate-ledger.py", str(ledger_path("adv05_multiplied_speedups.jsonl")), "--json")
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["verdict"], "FAIL")
        self.assertGreater(payload["errors"], 0)
        self.assertEqual(payload["schema_version"], S.SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main(verbosity=2)
