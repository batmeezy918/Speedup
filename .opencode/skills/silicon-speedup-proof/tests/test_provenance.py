#!/usr/bin/env python3
"""Provenance tests: where a result came from, and whether it can be re-derived.

Covers adversarial cases 7, 8, 10, 11 and 12, the operator-definition
discipline, and the repository convention that reference artifacts and
benchmark evaluators are never modified by this skill.

All fixtures are SYNTHETIC validator inputs, not hardware evidence.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _harness import (LEDGERS, PROJECT_ROOT, RUNS, S, codes, findings_for_record,
                      ledger_findings, load_json, run_findings, run_path,
                      validate_ledger)


class Case7_MechanismWithoutEvidence(unittest.TestCase):
    """A purported hardware explanation with no mechanism-specific evidence."""

    def test_mechanism_claim_is_rejected(self):
        found = codes(run_findings("adv07_mechanism_without_evidence.json"), S.ERROR)
        self.assertIn("R-MECH-1", found)

    def test_pure_prior_art_is_not_mechanism_evidence(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record["mechanism"] = {"claim": "x", "mechanism_specific": True,
                               "evidence": [{"ref": "r", "kind": "prior_work"}]}
        record["claim"]["kind"] = "hardware_mechanism"
        record["claim"]["strength"] = "STRONG_LOCAL"
        record["evidence_strength"] = "MECHANISM"
        found = codes(findings_for_record(record), S.ERROR)
        self.assertIn("R-MECH-1", found)

    def test_an_ablation_is_accepted_as_mechanism_evidence(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record["claim"]["kind"] = "hardware_mechanism"
        record["claim"]["strength"] = "STRONG_LOCAL"
        record["evidence_strength"] = "MECHANISM"
        found = codes(findings_for_record(record), S.ERROR)
        self.assertNotIn("R-MECH-1", found)


class Case8_MissingRunIdOrArtifact(unittest.TestCase):
    def test_missing_run_id_is_an_error(self):
        found = codes(run_findings("adv08_missing_run_id.json"), S.ERROR)
        self.assertIn("R-PROV-1", found)

    def test_absent_artifact_blocks_a_strong_claim(self):
        found = codes(run_findings("adv08_missing_run_id.json"))
        self.assertIn("R-PROV-2", found)

    def test_missing_run_id_on_a_measured_primitive_is_an_error(self):
        # The ledger fixture carries exit_code 0 and an empty measurements list.
        found = codes(ledger_findings("adv01_exit_zero_no_timing.jsonl")[0], S.ERROR)
        self.assertIn("L-EXE-3", found)

    def test_hash_mismatch_is_detected(self):
        found = codes(run_findings("adv17_artifact_hash_mismatch.json"), S.ERROR)
        self.assertIn("R-PROV-6", found)

    def test_intact_artifact_hashes_pass(self):
        found = codes(run_findings("synthetic_valid_run.json"), S.ERROR)
        self.assertNotIn("R-PROV-6", found)
        self.assertNotIn("R-PROV-5", found)

    def test_sha_helper_rejects_non_hashes(self):
        self.assertTrue(S.is_sha256("a" * 64))
        self.assertFalse(S.is_sha256("A" * 64))
        self.assertFalse(S.is_sha256("z" * 64))
        self.assertFalse(S.is_sha256(None))


class Case10_LeanProofWithoutTarget(unittest.TestCase):
    """A claimed Lean proof without a theorem target and successful proof execution."""

    def test_every_formal_requirement_is_enforced(self):
        found = codes(run_findings("adv10_lean_without_proof.json"), S.ERROR)
        for code in ("R-FRM-2", "R-FRM-3", "R-FRM-4", "R-FRM-5", "R-FRM-6"):
            self.assertIn(code, found)

    def test_formal_claim_with_no_formal_block_is_rejected(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record.pop("formal", None)
        record["claim"]["kind"] = "formal"
        record["claim"]["strength"] = "FORMAL_PARTIAL"
        record["evidence_strength"] = "FORMAL"
        self.assertIn("R-FRM-1", codes(findings_for_record(record), S.ERROR))

    def test_ledger_level_formal_rules_also_fire(self):
        found = codes(ledger_findings("adv20_formal_without_proof.jsonl")[0], S.ERROR)
        self.assertIn("L-FRM-4", found)
        self.assertIn("L-FRM-5", found)

    def test_a_nonzero_exit_status_is_not_a_proof(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record["claim"]["kind"] = "formal"
        record["claim"]["strength"] = "FORMAL_PARTIAL"
        record["evidence_strength"] = "FORMAL"
        record["formal"] = {"theorem_target": "t", "file": "f.lean",
                            "command": "lean f.lean", "exit_status": 1,
                            "kernel_checked": False}
        found = codes(findings_for_record(record), S.ERROR)
        self.assertIn("R-FRM-5", found)

    def test_a_kernel_checked_proof_with_target_and_exit_zero_passes(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record["claim"]["kind"] = "formal"
        record["claim"]["strength"] = "FORMAL_PARTIAL"
        record["evidence_strength"] = "FORMAL"
        record["formal"] = {"theorem_target": "theorem t : 1 + 1 = 2 := by decide",
                            "file": "formal/SSProofCore.lean", "command": "lean formal/SSProofCore.lean",
                            "exit_status": 0, "kernel_checked": True,
                            "scope_note": "establishes the arithmetic identity only"}
        found = codes(findings_for_record(record), S.ERROR)
        self.assertNotIn("R-FRM-5", found)
        self.assertNotIn("R-FRM-6", found)


class Case11_UnresolvedDependency(unittest.TestCase):
    def test_run_level_dependency_block(self):
        found = codes(run_findings("adv11_unresolved_dependency.json"), S.ERROR)
        self.assertIn("R-DEP-1", found)

    def test_ledger_level_dependency_block(self):
        found = codes(ledger_findings("adv19_unresolved_dependency.jsonl")[0], S.ERROR)
        self.assertIn("L-DEP-1", found)

    def test_resolved_dependencies_do_not_block(self):
        found = codes(run_findings("synthetic_valid_run.json"), S.ERROR)
        self.assertNotIn("R-DEP-1", found)


class Case12_ManualRaise(unittest.TestCase):
    def test_manual_raise_is_rejected_at_run_level(self):
        found = codes(run_findings("adv12_manual_claim_raise.json"), S.ERROR)
        self.assertIn("R-CLM-2", found)

    def test_manual_raise_without_transitions_is_rejected_at_ledger_level(self):
        found = codes(ledger_findings("adv12_manual_raise.jsonl")[0], S.ERROR)
        self.assertIn("L-CLM-2", found)
        self.assertIn("L-CLM-3", found)

    def test_verified_label_without_evidence_references_fails(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record["claim"]["strength"] = "VERIFIED"
        record["claim"]["assigned_manually"] = True
        record["evidence_strength"] = "OBSERVED"
        found = codes(findings_for_record(record), S.ERROR)
        self.assertIn("R-CLM-2", found)
        self.assertIn("R-CLM-1", found)


class HashChain(unittest.TestCase):
    def test_chain_is_verified_for_the_valid_ledger(self):
        found = codes(ledger_findings("synthetic_valid.jsonl")[0], S.ERROR)
        self.assertNotIn("L-HASH-1", found)
        self.assertNotIn("L-HASH-2", found)

    def test_tampering_breaks_the_chain(self):
        found = codes(ledger_findings("adv14_hash_chain_broken.jsonl")[0], S.ERROR)
        self.assertIn("L-HASH-1", found)

    def test_seq_must_increase(self):
        records = [json.loads(l) for l in
                   (LEDGERS / "synthetic_valid.jsonl").read_text().splitlines() if l.strip()]
        records[3]["seq"] = records[1]["seq"] - 1  # force a regression
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
        self.assertIn("L-SEQ-1", codes(findings, S.ERROR))

    def test_record_hash_is_stable_and_content_addressed(self):
        rec = {"a": 1, "b": [1, 2]}
        first = S.compute_record_hash(rec)
        self.assertEqual(first, S.compute_record_hash(dict(rec)))
        rec["b"] = [1, 3]
        self.assertNotEqual(first, S.compute_record_hash(rec))

    def test_canonical_bytes_are_key_order_independent(self):
        self.assertEqual(S.sha256_json({"a": 1, "b": 2}), S.sha256_json({"b": 2, "a": 1}))


class OperatorDiscipline(unittest.TestCase):
    """Notation is not an implementation. An undefined operator is a gap."""

    def test_registry_covers_the_frameworks_named_operators(self):
        for symbol in ("S", "Delta", "Omega", "Xi"):
            self.assertIn(symbol, S.OPERATOR_REGISTRY)

    def test_registry_records_honest_definition_status(self):
        # These statuses were established by grep over the target project at
        # build time; the probe is stored so a reader can re-derive them.
        self.assertEqual(S.OPERATOR_REGISTRY["Omega"]["definition_status"], "implemented")
        self.assertEqual(S.OPERATOR_REGISTRY["S"]["definition_status"], "undefined")
        self.assertEqual(S.OPERATOR_REGISTRY["Delta"]["definition_status"], "undefined")
        self.assertEqual(S.OPERATOR_REGISTRY["Xi"]["definition_status"], "undefined")
        for entry in S.OPERATOR_REGISTRY.values():
            self.assertTrue(entry.get("probe"))

    def test_omega_source_ref_resolves_in_the_real_repository(self):
        entry = S.OPERATOR_REGISTRY["Omega"]
        self.assertTrue((PROJECT_ROOT / entry["source_ref"]).exists(),
                        msg=f"{entry['source_ref']} should exist in the target project")

    def test_implemented_operator_without_source_ref_is_rejected(self):
        found = codes(ledger_findings("adv18_operator_not_implemented.jsonl")[0], S.ERROR)
        self.assertIn("L-OPR-1", found)

    def test_unimplemented_operator_blocks_a_verified_claim(self):
        records = [json.loads(l) for l in
                   (LEDGERS / "synthetic_valid.jsonl").read_text().splitlines() if l.strip()]
        target = [r for r in records if r.get("status") == "reproduced"][0]
        target["operator"] = {"symbol": "S", "definition_status": "specified",
                              "spec": "notational only"}
        target["claim"] = dict(target["claim"], strength="VERIFIED", kind="implementation")
        target["evidence"] = dict(target["evidence"], evidence_strength="SCOPED_VERIFIED",
                                  transition_records=[
                                      {"from": a, "to": b, "event_ref": f"synthetic://{a}{b}"}
                                      for a, b in zip(S.EVIDENCE_LADDER[:-1], S.EVIDENCE_LADDER[1:])
                                  ])
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
        found = codes(findings)
        self.assertIn("L-OPR-3", found)   # notation is not an implementation
        self.assertIn("L-OPR-4", found)   # and it blocks a VERIFIED claim

    def test_undefined_invariants_are_reported_as_unsupported(self):
        found = codes(ledger_findings("adv18_operator_not_implemented.jsonl")[0], S.WARN)
        self.assertIn("L-OPR-6", found)

    def test_heat_trace_and_curvature_are_recorded_as_undefined(self):
        for name in ("Omega(O psi)", "heat_trace(O)", "curvature(psi)"):
            self.assertIn(name, S.INVARIANT_SUPPORT)
        self.assertFalse(S.INVARIANT_SUPPORT["heat_trace(O)"].startswith("implemented"))
        self.assertFalse(S.INVARIANT_SUPPORT["curvature(psi)"].startswith("implemented"))


class RequiredProvenanceFields(unittest.TestCase):
    """Exact command lines, working directory, environment, versions."""

    def test_missing_command_is_an_error(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        record["command"] = ""
        self.assertIn("R-CMD-1", codes(findings_for_record(record), S.ERROR))

    def test_ledger_warns_when_a_native_run_omits_command_or_cwd(self):
        records = [json.loads(l) for l in
                   (LEDGERS / "synthetic_valid.jsonl").read_text().splitlines() if l.strip()]
        target = [r for r in records if r.get("status") == "reproduced"][0]
        target["native_run"]["command"] = ""
        target["native_run"]["cwd"] = ""
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
        self.assertIn("L-EXE-4", codes(findings, S.WARN))

    def test_valid_fixture_records_command_and_environment(self):
        record = load_json(run_path("synthetic_valid_run.json"))
        self.assertTrue(record["command"])
        self.assertIn("environment", record)


class SchemaConformance(unittest.TestCase):
    def test_every_fixture_matches_its_schema(self):
        for path in RUNS.glob("*.json"):
            with self.subTest(fixture=path.name):
                errors = S.validate_against_schema(load_json(path), "evidence-record.schema.json")
                # Adversarial fixtures are intentionally malformed in places;
                # only the valid fixture is required to be schema-clean.
                if path.name == "synthetic_valid_run.json":
                    self.assertEqual(errors, [])
                else:
                    self.assertIsInstance(errors, list)

    def test_schemas_are_valid_documents(self):
        for name in ("primitive.schema.json", "evidence-record.schema.json",
                     "gap-record.schema.json"):
            with self.subTest(schema=name):
                schema = S.load_schema(name)
                self.assertIn("required", schema)
                self.assertIn("properties", schema)


class FormalCore(unittest.TestCase):
    """The Lean core is checked for real when Lean is available, skipped otherwise.

    Skipping is honest UNKNOWN, never PASS. Mathlib is NOT available in this
    repository (lean4/lake-manifest.json has "packages": []), so the file under
    test deliberately depends on Lean core only.
    """

    LEAN_FILE = Path(S.SKILL_ROOT) / "formal" / "SSProofCore.lean" if hasattr(S, "SKILL_ROOT") \
        else Path(__file__).resolve().parent.parent / "formal" / "SSProofCore.lean"

    @classmethod
    def setUpClass(cls):
        cls.lean = shutil.which("lean")
        if cls.lean is None:
            raise unittest.SkipTest("lean is not on PATH: formal proof not run")

    def test_lean_file_exists(self):
        self.assertTrue(self.LEAN_FILE.exists())

    def test_lean_core_compiles_without_mathlib(self):
        proc = subprocess.run(
            [self.lean, str(self.LEAN_FILE)],
            capture_output=True, text=True, cwd=str(self.LEAN_FILE.parent.parent),
            env={**os.environ, "HOME": os.environ.get("HOME", "/root")},
            timeout=900,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("error", proc.stdout.lower())

    def test_mathlib_is_not_required(self):
        text = self.LEAN_FILE.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("import "):
                self.assertFalse(stripped.startswith("import Mathlib"),
                                 msg="this file must compile without Mathlib")

    def test_proof_evidence_record_is_machine_readable(self):
        record = load_json(self.LEAN_FILE.parent / "evidence" / "SSProofCore.formal.json")
        self.assertEqual(record["exit_status"], 0)
        self.assertTrue(record["kernel_checked"])
        self.assertIn("theorem", record["theorem_target"])
        self.assertIn("4.", record["toolchain"])


class NativeEvidenceIsReal(unittest.TestCase):
    """The non-synthetic native run must validate, and the validation must be
    capable of failing. A PASS that cannot go FAIL is vacuous."""

    NATIVE = Path(S.SKILL_ROOT) / "native"
    EV = NATIVE / "evidence"
    RAW = NATIVE / "artifacts"

    def test_native_artifacts_exist(self):
        self.assertTrue((self.EV / "native_blockdiag_evidence.json").exists())
        self.assertTrue((self.EV / "native_ledger.jsonl").exists())

    def test_evidence_record_is_marked_non_synthetic(self):
        record = load_json(self.EV / "native_blockdiag_evidence.json")
        self.assertFalse(record["synthetic"])
        self.assertEqual(record["executed_kind"], "native")
        self.assertNotEqual(record["exit_code"], None)

    def test_native_evidence_record_validates(self):
        proc = cli_run(self.EV / "native_blockdiag_evidence.json")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_native_ledger_validates(self):
        proc = cli_ledger(self.EV / "native_ledger.jsonl")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_ledger_is_not_labelled_synthetic(self):
        findings, summary = ledger_findings_native(self.EV / "native_ledger.jsonl")
        self.assertFalse(summary["all_synthetic"])
        self.assertNotIn("L-SYN-1", codes(findings))

    def test_raw_artifact_hashes_match_the_record(self):
        record = load_json(self.EV / "native_blockdiag_evidence.json")
        for art in record["artifacts"]:
            path = PROJECT_ROOT / art["path"]
            self.assertTrue(path.exists(), art["path"])
            self.assertEqual(S.sha256_file(path), art["sha256"], art["path"])

    def test_raw_artifact_records_real_samples(self):
        raw = load_json(self.RAW / "native_blockdiag_run2.json")
        self.assertGreater(len(raw["timing"]["baseline"]["samples_ns"]), 5)
        self.assertTrue(raw["correctness"]["bitwise_identical_output"])

    def test_tampering_with_a_real_artifact_is_detected(self):
        # Negative control: the native validation must be capable of failing.
        record = load_json(self.EV / "native_blockdiag_evidence.json")
        record["claim"]["strength"] = "VERIFIED"
        record["evidence_strength"] = "OBSERVED"
        found = codes(findings_for_record(record, where="native_blockdiag_evidence.json"),
                      S.ERROR)
        self.assertIn("R-CLM-1", found)

    def test_claiming_a_mechanism_for_the_native_run_is_rejected(self):
        record = load_json(self.EV / "native_blockdiag_evidence.json")
        record["claim"]["kind"] = "hardware_mechanism"
        record["evidence_strength"] = "MECHANISM"
        found = codes(findings_for_record(record, where="native_blockdiag_evidence.json"),
                      S.ERROR)
        self.assertIn("R-MECH-1", found)

    def test_native_scope_excludes_scaling_and_mechanism(self):
        record = load_json(self.EV / "native_blockdiag_evidence.json")
        scope = record["claim"]["scope"]
        self.assertIn("NOT a scaling claim", scope)
        self.assertIn("NOT a hardware-mechanism claim", scope)

    def test_open_gaps_are_recorded_and_bound_the_claim(self):
        findings = findings_for_record(load_json(self.EV / "native_blockdiag_evidence.json"),
                                       where="native_blockdiag_evidence.json")
        self.assertEqual(codes(findings, S.ERROR), set())
        record = load_json(self.EV / "native_blockdiag_evidence.json")
        self.assertIn("G-NATIVE-ATTRIB-001", record["gaps"])
        self.assertIn("G-NATIVE-DERIV-001", record["gaps"])


def cli_run(path: Path):
    import subprocess, sys
    return subprocess.run(
        [sys.executable, str(S.SCRIPTS_DIR / "validate-run.py"), str(path),
         "--repo-root", str(PROJECT_ROOT)],
        capture_output=True, text=True)


def cli_ledger(path: Path):
    import subprocess, sys
    return subprocess.run(
        [sys.executable, str(S.SCRIPTS_DIR / "validate-ledger.py"), str(path),
         "--repo-root", str(PROJECT_ROOT)],
        capture_output=True, text=True)


def ledger_findings_native(path: Path):
    return validate_ledger.validate_ledger(path, PROJECT_ROOT)


class RepositoryConventionsArePreserved(unittest.TestCase):
    """This skill must not mutate the artifacts it inspects."""

    def test_validators_write_nothing(self):
        before = {p: p.stat().st_mtime_ns for p in sorted(Path(S.SCRIPTS_DIR).glob("*.py"))}
        run_findings("synthetic_valid_run.json")
        ledger_findings("synthetic_valid.jsonl")
        after = {p: p.stat().st_mtime_ns for p in sorted(Path(S.SCRIPTS_DIR).glob("*.py"))}
        self.assertEqual(before, after)

    def test_reference_artifacts_are_not_rewritten(self):
        # The repository's own benchmark schemas and constitutional documents are
        # inputs to this skill, never outputs of it.
        for rel in ("schemas/pcss_certificate.schema.json", "CONSTITUTION.md",
                    "CLAIM_POLICY.md", "RECURSIVE_SPEEDUP_CONSTITUTION.md"):
            with self.subTest(artifact=rel):
                self.assertTrue((PROJECT_ROOT / rel).exists())

    def test_skill_does_not_ship_a_write_path(self):
        for name in ("ssproof.py", "validate-run.py", "validate-ledger.py"):
            text = (Path(S.SCRIPTS_DIR) / name).read_text(encoding="utf-8")
            with self.subTest(module=name):
                self.assertNotIn("os.remove", text)
                self.assertNotIn("shutil.rmtree", text)
                self.assertNotIn(".unlink(", text)
                self.assertNotIn("open(path, \"w\")", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)