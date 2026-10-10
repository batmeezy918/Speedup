#!/usr/bin/env python3
"""Vacuity and adversarial-validation tests.

The question this module answers is not "did the tests pass?" but "could the
tests have failed?" A validation that cannot fail is not coverage, and a high
raw test count is not evidence.

Adversarial battery (SKILL.md section 9), cases 3, 4 and 5, plus the
regression guarantees: negative evidence survives updates, vacuous cases are
excluded from substantive coverage, and the validator never fabricates.

All fixtures are SYNTHETIC validator inputs, not hardware evidence.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _harness import (LEDGERS, RUNS, S, codes, findings_for_record,
                      ledger_findings, load_json, run_findings, run_path,
                      validate_ledger)


def substantive_check(**over):
    check = {
        "check_id": "real", "name": "real check",
        "parameters": {"n": 4096}, "parameter_roles": {"n": "dimension"},
        "assertion": "max_abs_error(candidate, baseline) <= 1e-12",
        "expected_source": "independent_oracle", "expected": 0.0, "observed": 3.2e-13,
        "passed": True,
    }
    check.update(over)
    return check


def vacuous_check(**over):
    base = dict(check_id="vac", name="vacuous check",
                parameters={"n": 1}, parameter_roles={"n": "dimension"},
                assertion="true", expected_source="self", expected=1, observed=1)
    base.update(over)
    return substantive_check(**base)


class VacuityModel(unittest.TestCase):
    def test_a_real_check_is_substantive(self):
        result = S.analyze_check(substantive_check())
        self.assertTrue(result.substantive, result.reasons)

    def test_trivial_dimension_is_vacuous(self):
        result = S.analyze_check(vacuous_check())
        self.assertFalse(result.substantive)
        self.assertTrue(any("trivial_parameter" in r for r in result.reasons), result.reasons)

    def test_zero_iteration_count_is_vacuous(self):
        check = substantive_check(parameters={"iters": 0},
                                  parameter_roles={"iters": "iteration_count"})
        self.assertFalse(S.analyze_check(check).substantive)

    def test_zero_tolerance_is_not_vacuous(self):
        # A zero tolerance is stricter, not weaker.
        check = substantive_check(parameters={"tol": 0},
                                  parameter_roles={"tol": "tolerance"})
        self.assertTrue(S.analyze_check(check).substantive)

    def test_missing_roles_are_vacuous_by_construction(self):
        check = substantive_check()
        del check["parameter_roles"]
        result = S.analyze_check(check)
        self.assertFalse(result.substantive)
        self.assertIn("no_declared_parameter_roles: discriminating power is not reconstructible",
                      result.reasons)

    def test_self_referential_expectation_is_vacuous(self):
        result = S.analyze_check(substantive_check(expected_source="self"))
        self.assertFalse(result.substantive)

    def test_trivial_assertion_is_vacuous(self):
        for text in ("true", "assert true", "x == x", "no-op"):
            with self.subTest(assertion=text):
                self.assertFalse(S.analyze_check(substantive_check(assertion=text)).substantive)

    def test_nothing_observed_is_vacuous(self):
        self.assertFalse(S.analyze_check(substantive_check(observed=None)).substantive)


class Case3_TrivialParameter(unittest.TestCase):
    """A test that is vacuous because the relevant parameter has a trivial value."""

    def test_fixture_is_detected(self):
        found = codes(run_findings("adv03_trivial_parameter.json"), S.ERROR)
        self.assertIn("R-VAC-1", found)
        self.assertIn("R-VAC-3", found)

    def test_dimension_one_passes_but_never_counts(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record["checks"] = [vacuous_check()]
        report = S.substantive_coverage(record["checks"])
        self.assertTrue(report.all_vacuous)
        self.assertEqual(report.substantive, 0)
        self.assertEqual(report.total, 1)

    def test_a_large_trivial_dimension_still_counts_for_nothing(self):
        # Passing, at scale, and still incapable of failing.
        record = load_json(run_path("synthetic_valid_run.json"))
        record["checks"] = [vacuous_check(parameters={"n": 4096}, parameter_roles={"n": "dimension"})]
        report = S.substantive_coverage(record["checks"])
        self.assertTrue(report.all_vacuous)


class Case4_AllVacuousBatch(unittest.TestCase):
    """A batch of validations that are all vacuous despite a high raw test count."""

    def test_run_level_detection(self):
        found = codes(run_findings("adv04_all_vacuous.json"), S.ERROR)
        self.assertIn("R-VAC-1", found)
        self.assertIn("R-VAC-3", found)

    def test_ledger_level_detection(self):
        findings, _ = ledger_findings("adv21_all_vacuous_checks.jsonl")
        found = codes(findings, S.ERROR)
        self.assertIn("L-VAC-1", found)

    def test_test_count_does_not_become_coverage(self):
        record = load_json(run_path("adv04_all_vacuous.json"))
        report = S.substantive_coverage(record["checks"])
        self.assertEqual(record["checks"].__len__(), 40)
        self.assertEqual(report.substantive, 0)
        self.assertTrue(report.all_vacuous)

    def test_one_substantive_check_rescues_the_batch(self):
        checks = [vacuous_check(check_id=f"v{i}") for i in range(39)] + [substantive_check()]
        report = S.substantive_coverage(checks)
        self.assertFalse(report.all_vacuous)
        self.assertEqual(report.substantive, 1)
        self.assertEqual(report.vacuous, 39)

    def test_empty_batch_is_not_all_vacuous(self):
        report = S.substantive_coverage([])
        self.assertFalse(report.all_vacuous)
        self.assertEqual(report.total, 0)


class Case5_MultipliedSpeedup(unittest.TestCase):
    """An individual speedup incorrectly multiplied by another to claim cumulative performance."""

    def test_multiplication_is_refused(self):
        found = codes(ledger_findings("adv05_multiplied_speedups.jsonl")[0], S.ERROR)
        self.assertIn("L-SPD-1", found)
        self.assertIn("L-SPD-2", found)

    def test_the_helper_exists_only_so_it_can_be_recognised(self):
        # The function computes the product; the validator refuses to accept it
        # as a composed or cumulative quantity.
        self.assertEqual(S.individual_speedup([3.0, 2.0]), 6.0)
        self.assertEqual(S.individual_speedup([2.0, 2.0, 2.0]), 8.0)


class CoverageAccounting(unittest.TestCase):
    """Vacuous validations are excluded from substantive coverage counts."""

    def test_mixed_batch_counts_only_substantive_entries(self):
        checks = [substantive_check(check_id="s1"),
                  vacuous_check(check_id="v1"),
                  substantive_check(check_id="s2")]
        report = S.substantive_coverage(checks)
        self.assertEqual((report.total, report.substantive, report.vacuous), (3, 2, 1))
        self.assertEqual(report.vacuous_ids, ["v1"])

    def test_synthetic_checks_are_counted_separately(self):
        checks = [substantive_check(check_id="s1", synthetic=True),
                  substantive_check(check_id="s2")]
        report = S.substantive_coverage(checks)
        self.assertEqual(report.substantive, 2)
        self.assertEqual(report.synthetic, 1)

    def test_valid_fixture_has_substantive_coverage(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        report = S.substantive_coverage(record["checks"])
        self.assertFalse(report.all_vacuous)
        self.assertGreaterEqual(report.substantive, 1)

    def test_each_vacuous_check_is_individually_explained(self):
        record = load_json(run_path("adv04_all_vacuous.json"))
        findings = findings_for_record(record)
        explanations = [f for f in findings if f.code == "R-VAC-4"]
        self.assertEqual(len(explanations), len(record["checks"]))
        for finding in explanations:
            self.assertTrue(finding.message)


class SyntheticIsolation(unittest.TestCase):
    """Synthetic fixtures never count as hardware evidence."""

    def test_synthetic_run_is_flagged(self):
        self.assertIn("R-SYN-1", codes(run_findings("synthetic_valid_run.json")))

    def test_synthetic_ledger_is_flagged(self):
        findings, summary = ledger_findings("synthetic_valid.jsonl")
        self.assertIn("L-SYN-1", codes(findings))
        self.assertTrue(summary["all_synthetic"])

    def test_every_fixture_is_labelled(self):
        for path in list(LEDGERS.glob("*.jsonl")) + list(RUNS.glob("*.json")):
            with self.subTest(fixture=path.name):
                if path.suffix == ".jsonl":
                    records = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
                    for rec in records:
                        self.assertTrue((rec.get("provenance") or {}).get("synthetic")
                                        or rec.get("synthetic"))
                else:
                    self.assertTrue(load_json(path).get("synthetic"))

    def test_raw_fixture_artifacts_say_they_are_synthetic(self):
        for path in (Path(__file__).resolve().parent / "fixtures" / "raw").glob("*.json"):
            with self.subTest(artifact=path.name):
                self.assertTrue(load_json(path).get("synthetic"))


class NegativeEvidenceSurvives(unittest.TestCase):
    """A later success appends; it never erases."""

    def test_erased_regression_is_detected(self):
        found = codes(ledger_findings("adv13_negative_erased.jsonl")[0], S.ERROR)
        self.assertIn("L-ST-2", found)

    def test_history_that_keeps_the_regression_is_accepted(self):
        # Same scenario, but the regression is preserved in status_history.
        records = [json.loads(l) for l in
                   (LEDGERS / "adv13_negative_erased.jsonl").read_text().splitlines() if l.strip()]
        records[1]["status_history"].append(
            {"status": "regressed", "timestamp": "2026-01-01T00:00:00Z", "seq": 1,
             "note": "preserved"})
        prev = "GENESIS"
        for rec in records:
            if S.is_gap_record(rec):
                continue
            rec["prev_hash"] = prev
            rec["record_hash"] = S.compute_record_hash(rec)
            prev = rec["record_hash"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "l.jsonl"
            path.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
                            encoding="utf-8")
            findings, _ = validate_ledger.validate_ledger(path, None)
        self.assertNotIn("L-ST-2", codes(findings))

    def test_contradiction_is_reported_not_smoothed(self):
        found = codes(ledger_findings("adv09_contradictory_rerun.jsonl")[0], S.ERROR)
        self.assertIn("L-CNT-1", found)

    def test_negative_statuses_are_declared_in_the_lattice(self):
        for status in ("regressed", "blocked", "quarantined"):
            self.assertIn(status, S.NEGATIVE_STATUSES)


class ValidatorDoesNotFabricateEvidence(unittest.TestCase):
    """The validator reports; it never authors."""

    def test_a_record_with_no_evidence_stays_at_unevidenced(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record["evidence_strength"] = "UNEVIDENCED"
        record["claim"]["strength"] = "NONE"
        record["claim"]["kind"] = "none"
        found = codes(findings_for_record(record), S.ERROR)
        self.assertEqual(found, set())

    def test_missing_artifact_is_reported_not_invented(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record["artifacts"] = []
        record["claim"]["strength"] = "STRONG_LOCAL"
        found = codes(findings_for_record(record))
        self.assertIn("R-PROV-2", found)
        self.assertEqual(record["artifacts"], [])  # the validator left it empty

    def test_unknown_verdict_is_reported_as_unknown(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record["exit_code"] = None
        found = codes(findings_for_record(record), S.WARN)
        self.assertIn("R-EXIT-1", found)

    def test_validation_does_not_mutate_the_record(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        before = json.dumps(record, sort_keys=True)
        findings_for_record(record)
        self.assertEqual(json.dumps(record, sort_keys=True), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)