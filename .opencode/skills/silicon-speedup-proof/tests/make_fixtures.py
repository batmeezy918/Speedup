#!/usr/bin/env python3
"""Regenerate the SYNTHETIC validator fixtures.

Every fixture produced here is synthetic. None of it is a hardware
measurement, none of it is evidence about any real device, and none of it may
be cited as such. It exists so the validators have reproducible adversarial
inputs.

Run:
    python3 tests/make_fixtures.py

Deterministic: no timestamps or hashes are taken from the clock, so re-running
reproduces byte-identical files.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "scripts"))

import ssproof as S  # noqa: E402

FIX = HERE / "fixtures"
LEDGERS = FIX / "ledgers"
RUNS = FIX / "runs"
RAW = FIX / "raw"

TS = "2026-01-01T00:00:00Z"
COMMIT = "0" * 40  # synthetic commit marker, never a real revision
GENESIS = "GENESIS"

# --------------------------------------------------------------------------
# raw artifacts (real files, real hashes)
# --------------------------------------------------------------------------

RAW_FILES = {
    "synthetic_baseline_trace.json": {
        "synthetic": True,
        "note": "Synthetic baseline trace fixture. NOT a measurement.",
        "run_id": "synthetic-run-baseline",
        "samples_ms": [120.0, 121.0, 119.0, 120.5, 121.5],
    },
    "synthetic_candidate_trace.json": {
        "synthetic": True,
        "note": "Synthetic candidate trace fixture. NOT a measurement.",
        "run_id": "synthetic-run-candidate",
        "samples_ms": [40.0, 41.0, 39.5, 40.5, 41.5],
    },
    "synthetic_equivalence.json": {
        "synthetic": True,
        "note": "Synthetic equivalence artifact fixture. NOT a measurement.",
        "max_abs_error": 0.0,
        "tolerance": 1e-12,
        "pass": True,
    },
}


def write_raw() -> Dict[str, str]:
    RAW.mkdir(parents=True, exist_ok=True)
    hashes: Dict[str, str] = {}
    for name, body in RAW_FILES.items():
        path = RAW / name
        path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        hashes[name] = S.sha256_file(path)
    return hashes


# --------------------------------------------------------------------------
# record builders
# --------------------------------------------------------------------------

def baseline_arm(samples: List[float], scope: str = "end-to-end") -> Dict[str, Any]:
    return {"arm": "baseline", "metric": "wall_time", "unit": "ms", "samples": samples,
            "warmup_discarded": 2, "aggregation": "median", "interleaved": True, "scope": scope}


def candidate_arm(samples: List[float], scope: str = "end-to-end", memory: Optional[int] = None) -> Dict[str, Any]:
    arm = {"arm": "candidate", "metric": "wall_time", "unit": "ms", "samples": samples,
           "warmup_discarded": 2, "aggregation": "median", "interleaved": True, "scope": scope}
    if memory is not None:
        arm["memory_bytes"] = memory
    return arm


def transitions(*levels: str) -> List[Dict[str, str]]:
    chain: List[Dict[str, str]] = []
    prev = "UNEVIDENCED"
    for lvl in levels:
        chain.append({"from": prev, "to": lvl, "event_ref": f"synthetic://event/{prev}->{lvl}"})
        prev = lvl
    return chain


def primitive(
    *,
    seq: int,
    pid: str,
    version: int,
    status: str,
    kind: str = "primitive",
    run_id: str = "synthetic-run-0001",
    executed_kind: str = "native",
    exit_code: Optional[int] = 0,
    measurements: Optional[List[Dict[str, Any]]] = None,
    speedups: Optional[Dict[str, Any]] = None,
    claim_strength: str = "NONE",
    claim_kind: str = "none",
    evidence_strength: str = "UNEVIDENCED",
    component_ids: Optional[List[str]] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    operator: Optional[Dict[str, Any]] = None,
    implementation: Optional[Dict[str, Any]] = None,
    correctness: Optional[Dict[str, Any]] = None,
    formal: Optional[Dict[str, Any]] = None,
    mechanism: Optional[Dict[str, Any]] = None,
    contradictions: Optional[List[str]] = None,
    dependencies: Optional[List[Dict[str, str]]] = None,
    checks: Optional[List[Dict[str, Any]]] = None,
    open_gaps: Optional[List[str]] = None,
    known_regressions: Optional[List[str]] = None,
    timestamp: str = TS,
    claim_statement: str = "synthetic fixture claim",
    claim_scope: str = "synthetic fixture scope only",
    assigned_manually: bool = False,
    applicability: Optional[List[str]] = None,
    derivation_summary: str = "synthetic fixture derivation",
) -> Dict[str, Any]:
    prov: Dict[str, Any] = {
        "origin": "synthetic",
        "author": "make_fixtures.py",
        "synthetic": True,
        "parent_ids": [],
    }
    if component_ids:
        prov["component_ids"] = component_ids

    record: Dict[str, Any] = {
        "schema_version": S.SCHEMA_VERSION,
        "record_type": "primitive",
        "seq": seq,
        "primitive_id": pid,
        "version": version,
        "timestamp": timestamp,
        "kind": kind,
        "status": status,
        "source_commit": COMMIT,
        "provenance": prov,
        "requirement": {
            "statement": "synthetic fixture requirement",
            "applicability_conditions": applicability or ["synthetic fixture only"],
            "exclusions": ["not applicable to any real workload"],
        },
        "derivation": {"summary": derivation_summary, "steps": [], "refs": []},
        "native_run": {
            "run_id": run_id,
            "executed_kind": executed_kind,
            "command": "python3 tests/fixtures/run_synthetic_workload.py",
            "cwd": "synthetic",
            "exit_code": exit_code,
            "artifact_ref": "tests/fixtures/raw/synthetic_baseline_trace.json",
            "environment": {"platform": "synthetic", "cpu": "synthetic", "toolchain": "none"},
        },
        "measurements": measurements or [],
        "speedups": speedups or {},
        "claim": {
            "strength": claim_strength,
            "kind": claim_kind,
            "statement": claim_statement,
            "scope": claim_scope,
            "assigned_manually": assigned_manually,
        },
        "evidence": {
            "evidence_strength": evidence_strength,
            "refs": ["synthetic://fixture"],
            # Every rung from UNEVIDENCED up to the claimed level, each bound to
            # an event reference. The chain never contains a phantom
            # UNEVIDENCED -> UNEVIDENCED step.
            "transition_records": transitions(*S.EVIDENCE_LADDER[1:S.EVIDENCE_RANK[evidence_strength] + 1]),
        },
        "known_regressions": known_regressions or [],
        "open_gaps": open_gaps or [],
        "downstream_dependencies": [],
        "contradictions": contradictions or [],
        "prev_hash": GENESIS,
        "record_hash": "",
    }
    if operator:
        record["operator"] = operator
    if implementation:
        record["implementation"] = implementation
    if correctness:
        record["correctness"] = correctness
    if formal:
        record["formal"] = formal
    if mechanism:
        record["mechanism"] = mechanism
    if dependencies is not None:
        record["native_run"]["dependencies"] = dependencies
    if checks is not None:
        record["checks"] = checks
    if history is not None:
        record["status_history"] = history
    return record


def chain(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fill prev_hash / record_hash. The validator recomputes these.

    Gap records carry no chain fields by schema: they are side records that do
    not advance the primitive chain.
    """
    prev = GENESIS
    for rec in records:
        if S.is_gap_record(rec):
            continue
        rec["prev_hash"] = prev
        rec["record_hash"] = S.compute_record_hash(rec)
        prev = rec["record_hash"]
    return records


def gap(
    *,
    gap_id: str,
    gap_class: str,
    pid: str,
    status: str = "open",
    claim_impact: str = "blocks_promotion",
    evidence_desc: str = "synthetic fixture observation",
    closure: str = "produce the named artifact with a passing native run",
    closed_by: Optional[str] = None,
    legacy_alias: Optional[str] = None,
) -> Dict[str, Any]:
    rec: Dict[str, Any] = {
        "schema_version": S.SCHEMA_VERSION,
        "record_type": "gap",
        "gap_id": gap_id,
        "gap_class": gap_class,
        "primitive_id": pid,
        "status": status,
        "opened_at": TS,
        "closed_at": TS if status == "closed" else None,
        "closed_by_evidence": closed_by,
        "claim_impact": claim_impact,
        "observable_evidence": [{"description": evidence_desc, "observed_at": TS}],
        "closure_criterion": closure,
        "owner": "make_fixtures.py",
        "responsible_action": "close only with a real artifact",
        "synthetic": True,
    }
    if legacy_alias:
        rec["legacy_alias"] = legacy_alias
    return rec


def write_ledger(name: str, records: List[Dict[str, Any]]) -> Path:
    LEDGERS.mkdir(parents=True, exist_ok=True)
    path = LEDGERS / name
    lines = [json.dumps(r, sort_keys=True, separators=(",", ":")) for r in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# the VALID ledger
# --------------------------------------------------------------------------

#: Medians are exact: baseline 120.0 ms, candidate 40.0 ms, so the recomputed
#: median ratio is exactly 3.0 and the declared S_i can be cross-checked.
BASE_SAMPLES = [118.0, 119.0, 120.0, 121.0, 122.0]
CAND_SAMPLES = [38.0, 39.0, 40.0, 41.0, 42.0]
SYNTHETIC_S_I = 3.0
SYNTHETIC_MEM_BASE = 2048
SYNTHETIC_MEM_CAND = 1024
CORRECT = {
    "equivalence": {"pass": True, "metric": "max_abs_error", "tolerance": 1e-12,
                    "observed": 0.0, "expected": 0.0,
                    "artifact_ref": "tests/fixtures/raw/synthetic_equivalence.json"},
    "reverse_reconstruction": {"pass": True, "metric": "max_abs_error", "tolerance": 1e-12,
                               "observed": 0.0, "expected": 0.0,
                               "artifact_ref": "tests/fixtures/raw/synthetic_equivalence.json"},
    "invariant": {"pass": True, "metric": "declared_signature",
                  "artifact_ref": "tests/fixtures/raw/synthetic_equivalence.json"},
}


def valid_ledger() -> List[Dict[str, Any]]:
    pid = "P-SYN-KERNEL"
    recs = [
        primitive(seq=1, pid=pid, version=1, status="proposed",
                  run_id="", executed_kind="not_run", exit_code=None,
                  claim_strength="NONE", claim_kind="none", evidence_strength="UNEVIDENCED",
                  history=[{"status": "proposed", "timestamp": TS, "seq": 1}]),
        primitive(seq=2, pid=pid, version=2, status="implemented",
                  run_id="", executed_kind="not_run", exit_code=None,
                  claim_strength="NONE", claim_kind="none", evidence_strength="OBSERVED",
                  operator={"symbol": "Omega", "definition_status": "implemented",
                            "source_ref": "engines/invariant.py", "symbol_ref": "InvariantEngine.check",
                            "invariants": ["Omega(O psi)"]},
                  implementation={"path": "synthetic/kernel.py", "sha256": "a" * 64, "language": "python"},
                  history=[{"status": "proposed", "timestamp": TS, "seq": 1},
                           {"status": "implemented", "timestamp": TS, "seq": 2}]),
        primitive(seq=3, pid=pid, version=3, status="measured",
                  run_id="synthetic-run-0001", executed_kind="native", exit_code=0,
                  measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES, memory=1024)],
                  speedups={"S_i": 3.0, "computation": "measured_direct"},
                  claim_strength="CANDIDATE", claim_kind="performance", evidence_strength="EXECUTED",
                  correctness=CORRECT,
                  claim_statement="synthetic candidate is ~3x faster on the synthetic workload",
                  history=[{"status": "proposed", "timestamp": TS, "seq": 1},
                           {"status": "implemented", "timestamp": TS, "seq": 2},
                           {"status": "measured", "timestamp": TS, "seq": 3}]),
        primitive(seq=4, pid=pid, version=4, status="reproduced",
                  run_id="synthetic-run-0002", executed_kind="native", exit_code=0,
                  measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES, memory=1024)],
                  speedups={"S_i": 3.0, "computation": "measured_direct"},
                  claim_strength="STRONG_LOCAL", claim_kind="performance", evidence_strength="REPRODUCED",
                  correctness=CORRECT,
                  applicability=["synthetic fixture only", "identical input domain"],
                  claim_statement="synthetic candidate reproduces at ~3x on a second run",
                  history=[{"status": "proposed", "timestamp": TS, "seq": 1},
                           {"status": "implemented", "timestamp": TS, "seq": 2},
                           {"status": "measured", "timestamp": TS, "seq": 3},
                           {"status": "reproduced", "timestamp": TS, "seq": 4}]),
        primitive(seq=5, pid="P-SYN-COMPOSED", version=1, status="measured",
                  kind="composition", run_id="synthetic-run-composed-0003", executed_kind="native",
                  exit_code=0,
                  component_ids=[pid],
                  measurements=[
                      {"arm": "composition_baseline", "metric": "wall_time", "unit": "ms",
                       "samples": BASE_SAMPLES, "aggregation": "median", "scope": "end-to-end"},
                      {"arm": "composition", "metric": "wall_time", "unit": "ms",
                       "samples": [198.0, 199.0, 200.0, 201.0, 202.0], "aggregation": "median",
                       "scope": "end-to-end"},
                  ],
                  speedups={"S_composed": 120.0 / 200.0, "S_composed_measured_direct": True,
                            "S_ideal": 120.0 / 40.0, "S_ideal_model": "sequential_sum",
                            "S_ideal_assumptions": ["sequential stages",
                                                    "non-overlapping baseline timing domains",
                                                    "synthetic fixture only"],
                            "interaction_factor": (120.0 / 200.0) / (120.0 / 40.0),
                            "computation": "measured_direct"},
                  claim_strength="CANDIDATE", claim_kind="composition", evidence_strength="EXECUTED",
                  correctness=CORRECT,
                  claim_statement="synthetic composed implementation measured end to end at 0.6x",
                  history=[{"status": "measured", "timestamp": TS, "seq": 5}]),
        gap(gap_id="G-SYN-0001", gap_class="hardware_mechanism", pid=pid, status="open",
            claim_impact="qualifies_claim",
            evidence_desc="synthetic fixture has no counterfactual or ablation artifact",
            closure="record an ablation or counterfactual run under the synthetic protocol"),
    ]
    return chain(recs)


# --------------------------------------------------------------------------
# adversarial ledgers (one concern each)
# --------------------------------------------------------------------------

def adv01_exit_zero_no_timing() -> List[Dict[str, Any]]:
    """Exit code 0, no timing result."""
    return chain([
        primitive(seq=1, pid="P-SYN-NOTIME", version=1, status="measured",
                  run_id="synthetic-run-notime", exit_code=0,
                  measurements=[],
                  speedups={"S_i": 4.0, "computation": "measured_direct"},
                  claim_strength="STRONG_LOCAL", claim_kind="performance", evidence_strength="EXECUTED",
                  claim_statement="declared 4x despite there being no timing at all",
                  history=[{"status": "measured", "timestamp": TS, "seq": 1}]),
    ])


def adv05_multiplied_speedups() -> List[Dict[str, Any]]:
    """S_cumulative produced by multiplying isolated component ratios."""
    pid_a = "P-SYN-A"
    return chain([
        primitive(seq=1, pid=pid_a, version=1, status="reproduced",
                  run_id="synthetic-run-a", measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                  speedups={"S_i": 3.0, "computation": "measured_direct"},
                  claim_strength="STRONG_LOCAL", claim_kind="performance", evidence_strength="REPRODUCED",
                  history=[{"status": "reproduced", "timestamp": TS, "seq": 1}]),
        primitive(seq=2, pid="P-SYN-B", version=1, status="reproduced",
                  run_id="synthetic-run-b",
                  measurements=[baseline_arm(BASE_SAMPLES),
                                candidate_arm([58.0, 59.0, 60.0, 61.0, 62.0])],
                  speedups={"S_i": 2.0, "computation": "measured_direct"},
                  claim_strength="STRONG_LOCAL", claim_kind="performance", evidence_strength="REPRODUCED",
                  history=[{"status": "reproduced", "timestamp": TS, "seq": 1}]),
        primitive(seq=3, pid="P-SYN-AB", version=1, status="verified", kind="composition",
                  run_id="synthetic-run-ab", component_ids=[pid_a, "P-SYN-B"],
                  measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                  speedups={"S_i": 3.0, "S_composed": 6.0, "S_composed_measured_direct": False,
                            "S_cumulative": 6.0, "S_cumulative_measured_direct": False,
                            "interaction_factor": 6.0,
                            "computation": "product_of_components"},
                  claim_strength="VERIFIED", claim_kind="cumulative", evidence_strength="SCOPED_VERIFIED",
                  claim_statement="cumulative 6x obtained by multiplying 3x by 2x",
                  history=[{"status": "verified", "timestamp": TS, "seq": 3}]),
    ])


def adv06_no_fresh_composition_run() -> List[Dict[str, Any]]:
    """Composition of verified components with no fresh composed run."""
    pid_a = "P-SYN-C1"
    return chain([
        primitive(seq=1, pid=pid_a, version=1, status="verified",
                  run_id="synthetic-run-c1", measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                  speedups={"S_i": 3.0, "computation": "measured_direct"},
                  claim_strength="VERIFIED", claim_kind="implementation", evidence_strength="SCOPED_VERIFIED",
                  correctness=CORRECT,
                  history=[{"status": "verified", "timestamp": TS, "seq": 1}]),
        primitive(seq=2, pid=pid_a, version=2, status="verified",
                  run_id="synthetic-run-c2", measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                  speedups={"S_i": 3.0, "computation": "measured_direct"},
                  claim_strength="VERIFIED", claim_kind="implementation", evidence_strength="SCOPED_VERIFIED",
                  correctness=CORRECT,
                  history=[{"status": "verified", "timestamp": TS, "seq": 2}]),
        primitive(seq=3, pid="P-SYN-C1C2", version=1, status="verified", kind="composition",
                  run_id="synthetic-run-c2", component_ids=[pid_a],
                  measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                  speedups={"S_composed": 3.0, "S_composed_measured_direct": True,
                            "computation": "measured_direct"},
                  claim_strength="VERIFIED", claim_kind="composition", evidence_strength="SCOPED_VERIFIED",
                  claim_statement="composition inherits the component run id and its VERIFIED status",
                  history=[{"status": "verified", "timestamp": TS, "seq": 3}]),
    ])


def adv09_contradictory_rerun() -> List[Dict[str, Any]]:
    """A repeat run that conflicts with the earlier result."""
    pid = "P-SYN-CONTRA"
    return chain([
        primitive(seq=1, pid=pid, version=1, status="measured",
                  run_id="synthetic-run-ct-1", measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                  speedups={"S_i": 3.0, "computation": "measured_direct"},
                  claim_strength="CANDIDATE", claim_kind="performance", evidence_strength="EXECUTED",
                  history=[{"status": "measured", "timestamp": TS, "seq": 1}]),
        primitive(seq=2, pid=pid, version=2, status="verified",
                  run_id="synthetic-run-ct-2",
                  measurements=[baseline_arm(BASE_SAMPLES), candidate_arm([100.0, 101.0, 99.0, 100.5, 101.5])],
                  speedups={"S_i": 120.0 / 100.5, "computation": "measured_direct"},
                  claim_strength="VERIFIED", claim_kind="performance", evidence_strength="SCOPED_VERIFIED",
                  claim_statement="verified after a repeat run that contradicts the first result",
                  contradictions=[],
                  history=[{"status": "measured", "timestamp": TS, "seq": 1},
                           {"status": "verified", "timestamp": TS, "seq": 2}]),
    ])


def adv12_manual_raise() -> List[Dict[str, Any]]:
    """A manually raised evidence status with no transition records."""
    rec = primitive(seq=1, pid="P-SYN-MANUAL", version=1, status="verified",
                    run_id="synthetic-run-manual",
                    measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                    speedups={"S_i": 3.0, "computation": "measured_direct"},
                    claim_strength="VERIFIED", claim_kind="implementation", evidence_strength="SCOPED_VERIFIED",
                    correctness=CORRECT,
                    claim_statement="labelled verified by hand",
                    assigned_manually=True)
    rec["evidence"]["transition_records"] = []
    rec["evidence"]["refs"] = []
    return chain([rec])


def adv13_negative_erased() -> List[Dict[str, Any]]:
    """A regression observed once, then silently dropped from history."""
    pid = "P-SYN-ERASE"
    return chain([
        primitive(seq=1, pid=pid, version=1, status="regressed",
                  run_id="synthetic-run-er-1",
                  measurements=[baseline_arm(BASE_SAMPLES),
                                candidate_arm([198.0, 199.0, 200.0, 201.0, 202.0])],
                  speedups={"S_i": 0.6, "computation": "measured_direct"},
                  claim_strength="CANDIDATE", claim_kind="performance", evidence_strength="EXECUTED",
                  known_regressions=["synthetic candidate was 1.67x slower than baseline"],
                  history=[{"status": "regressed", "timestamp": TS, "seq": 1}]),
        primitive(seq=2, pid=pid, version=2, status="measured",
                  run_id="synthetic-run-er-2",
                  measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                  speedups={"S_i": 3.0, "computation": "measured_direct"},
                  claim_strength="CANDIDATE", claim_kind="performance", evidence_strength="EXECUTED",
                  history=[{"status": "measured", "timestamp": TS, "seq": 2}],
                  known_regressions=[]),
    ])


def adv14_hash_chain_broken() -> List[Dict[str, Any]]:
    """A record edited after it was written."""
    recs = valid_ledger()
    recs[2]["speedups"]["S_i"] = 99.0  # tamper, hash no longer matches
    return recs


def adv15_illegal_transition() -> List[Dict[str, Any]]:
    pid = "P-SYN-ILLEGAL"
    return chain([
        primitive(seq=1, pid=pid, version=1, status="measured",
                  run_id="synthetic-run-il-1",
                  measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                  speedups={"S_i": 3.0, "computation": "measured_direct"},
                  claim_strength="CANDIDATE", claim_kind="performance", evidence_strength="EXECUTED",
                  history=[{"status": "measured", "timestamp": TS, "seq": 1}]),
        primitive(seq=2, pid=pid, version=2, status="proposed",
                  run_id="synthetic-run-il-2",
                  history=[{"status": "measured", "timestamp": TS, "seq": 1},
                           {"status": "proposed", "timestamp": TS, "seq": 2}]),
    ])


def adv16_claim_exceeds_evidence() -> List[Dict[str, Any]]:
    return chain([
        primitive(seq=1, pid="P-SYN-OVER", version=1, status="verified",
                  run_id="synthetic-run-over",
                  measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                  speedups={"S_i": 3.0, "computation": "measured_direct"},
                  claim_strength="VERIFIED", claim_kind="implementation", evidence_strength="OBSERVED",
                  claim_statement="VERIFIED implementation on the strength of an observation",
                  history=[{"status": "verified", "timestamp": TS, "seq": 1}]),
    ])


def adv17_gap_closed_without_evidence() -> List[Dict[str, Any]]:
    pid = "P-SYN-GAP"
    recs = [
        primitive(seq=1, pid=pid, version=1, status="measured",
                  run_id="synthetic-run-gap",
                  measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                  speedups={"S_i": 3.0, "computation": "measured_direct"},
                  claim_strength="CANDIDATE", claim_kind="performance", evidence_strength="EXECUTED",
                  open_gaps=["G-SYN-0002"],
                  history=[{"status": "measured", "timestamp": TS, "seq": 1}]),
        gap(gap_id="G-SYN-0002", gap_class="measurement", pid=pid, status="closed",
            claim_impact="qualifies_claim", closed_by=None,
            evidence_desc="synthetic fixture declares the gap closed with nothing attached"),
    ]
    return chain(recs)


def adv18_operator_not_implemented() -> List[Dict[str, Any]]:
    """A named operator asserted as implemented when the project has no definition."""
    return chain([
        primitive(seq=1, pid="P-SYN-SOP", version=1, status="implemented",
                  run_id="", executed_kind="not_run", exit_code=None,
                  claim_strength="NONE", claim_kind="none", evidence_strength="OBSERVED",
                  operator={"symbol": "S", "definition_status": "implemented",
                            "invariants": ["heat_trace(O)", "curvature(psi)"]},
                  history=[{"status": "implemented", "timestamp": TS, "seq": 1}]),
    ])


def adv19_unresolved_dependency() -> List[Dict[str, Any]]:
    rec = primitive(seq=1, pid="P-SYN-DEP", version=1, status="reproduced",
                    run_id="synthetic-run-dep",
                    measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                    speedups={"S_i": 3.0, "computation": "measured_direct"},
                    claim_strength="STRONG_LOCAL", claim_kind="performance", evidence_strength="REPRODUCED",
                    dependencies=[{"id": "vendor-kernel", "status": "unresolved"},
                                  {"id": "local-only-lib", "status": "assumed"}],
                    history=[{"status": "reproduced", "timestamp": TS, "seq": 1}])
    return chain([rec])


def adv20_formal_without_proof() -> List[Dict[str, Any]]:
    rec = primitive(seq=1, pid="P-SYN-FORMAL", version=1, status="verified",
                    run_id="synthetic-run-formal",
                    measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                    speedups={"S_i": 3.0, "computation": "measured_direct"},
                    claim_strength="FORMAL_PARTIAL", claim_kind="formal", evidence_strength="FORMAL",
                    formal={"theorem_target": "theorem speedup_is_optimal", "file": "synthetic.lean",
                            "command": "lean synthetic.lean", "exit_status": None,
                            "output_ref": None, "kernel_checked": False},
                    history=[{"status": "verified", "timestamp": TS, "seq": 1}])
    return chain([rec])


def adv21_all_vacuous_checks() -> List[Dict[str, Any]]:
    checks = [
        {"check_id": f"vac-{i:02d}", "name": f"synthetic vacuous check {i}",
         "parameters": {"n": 1}, "parameter_roles": {"n": "dimension"},
         "assertion": "true", "expected_source": "self", "expected": 1, "observed": 1,
         "passed": True, "synthetic": True}
        for i in range(1, 26)
    ]
    return chain([
        primitive(seq=1, pid="P-SYN-VAC", version=1, status="verified",
                  run_id="synthetic-run-vac",
                  measurements=[baseline_arm(BASE_SAMPLES), candidate_arm(CAND_SAMPLES)],
                  speedups={"S_i": 3.0, "computation": "measured_direct"},
                  claim_strength="VERIFIED", claim_kind="implementation", evidence_strength="SCOPED_VERIFIED",
                  correctness=CORRECT, checks=checks,
                  claim_statement="25 passing validations, none of which could have failed",
                  history=[{"status": "verified", "timestamp": TS, "seq": 1}]),
    ])


# --------------------------------------------------------------------------
# run (evidence) record fixtures
# --------------------------------------------------------------------------

def run_record(**kw: Any) -> Dict[str, Any]:
    def _transitions(target: str):
        chain: List[Dict[str, str]] = []
        prev = "UNEVIDENCED"
        for lvl in S.EVIDENCE_LADDER[1:S.EVIDENCE_RANK[target] + 1]:
            chain.append({"from": prev, "to": lvl, "event_ref": f"synthetic://{prev}->{lvl}"})
            prev = lvl
        return chain

    rec: Dict[str, Any] = {
        "schema_version": S.SCHEMA_VERSION,
        "record_type": "evidence",
        "run_id": "synthetic-run-0001",
        "primitive_id": "P-SYN-KERNEL",
        "timestamp": TS,
        "executed_kind": "native",
        "command": "python3 tests/fixtures/run_synthetic_workload.py",
        "cwd": "synthetic",
        "exit_code": 0,
        "environment": {
            "platform": "synthetic",
            "machine": "synthetic",
            "cpu": "synthetic",
            "governor": "synthetic",
            "toolchain": "none",
            "compiler_flags": "none",
            "versions": {"python": "synthetic"},
        },
        "evidence_strength": "REPRODUCED",
        "transition_records": transitions(*S.EVIDENCE_LADDER[1:S.EVIDENCE_RANK["REPRODUCED"] + 1]),
        "timing": {
            "unit": "ms",
            "warmup_discarded": 2,
            "interleaved": True,
            "aggregation": "median",
            "arms": [
                {"name": "baseline", "scope": "end-to-end", "samples": BASE_SAMPLES, "memory_bytes": 2048},
                {"name": "candidate", "scope": "end-to-end", "samples": CAND_SAMPLES, "memory_bytes": 1024},
            ],
        },
        "correctness": CORRECT,
        "scaling": {"sizes": [256, 512, 1024], "ratios": [2.9, 3.0, 3.0], "unit": "elements"},
        "mechanism": {"claim": "synthetic mechanism", "mechanism_specific": True,
                      "evidence": [{"ref": "synthetic://ablation", "kind": "ablation",
                                    "description": "synthetic ablation fixture"}]},
        "checks": [{
            "check_id": "syn-c1", "name": "synthetic equivalence check",
            "parameters": {"n": 1024}, "parameter_roles": {"n": "dimension"},
            "assertion": "max_abs_error(candidate, baseline) <= 1e-12",
            "expected_source": "independent_oracle", "expected": 0.0, "observed": 0.0,
            "passed": True, "artifact_ref": "tests/fixtures/raw/synthetic_equivalence.json",
        }],
        "dependencies": [{"id": "synthetic-dep", "status": "resolved", "ref": "synthetic://dep"}],
        "artifacts": [
            {"role": "raw_result", "path": "tests/fixtures/raw/synthetic_candidate_trace.json", "sha256": HASHES["synthetic_candidate_trace.json"]},
            {"role": "raw_result", "path": "tests/fixtures/raw/synthetic_equivalence.json", "sha256": HASHES["synthetic_equivalence.json"]},
        ],
        "gaps": [],
        "synthetic": True,
        "claim": {"strength": "STRONG_LOCAL", "kind": "performance",
                  "statement": "synthetic candidate is ~3x faster on the synthetic workload",
                  "scope": "synthetic fixture only", "assigned_manually": False},
        "notes": "SYNTHETIC FIXTURE. Not a measurement.",
    }
    supplied = dict(kw)
    rec.update(supplied)
    target = rec.get("evidence_strength", "UNEVIDENCED")
    if "transition_records" not in supplied and target != "UNEVIDENCED":
        rec["transition_records"] = _transitions(target)
    return rec


def adv01_run() -> Dict[str, Any]:
    return run_record(
        run_id="synthetic-run-notime",
        timing={"unit": "ms", "arms": [{"name": "baseline", "scope": "end-to-end", "samples": []},
                                        {"name": "candidate", "scope": "end-to-end", "samples": []}]},
        evidence_strength="EXECUTED",
        claim={"strength": "STRONG_LOCAL", "kind": "performance",
               "statement": "claimed speedup from an exit code with no timing result",
               "scope": "synthetic fixture only", "assigned_manually": False},
    )


def adv02_run() -> Dict[str, Any]:
    return run_record(
        run_id="synthetic-run-regress",
        timing={"unit": "ms", "arms": [
            {"name": "baseline", "scope": "end-to-end", "samples": BASE_SAMPLES, "memory_bytes": 1024},
            {"name": "candidate", "scope": "end-to-end", "samples": [180.0, 181.0, 179.0, 180.5, 181.5],
             "memory_bytes": 8192},
        ]},
        evidence_strength="REPRODUCED",
        claim={"strength": "STRONG_LOCAL", "kind": "performance",
               "statement": "gate passed, so the candidate is reported as an improvement",
               "scope": "synthetic fixture only", "assigned_manually": False},
    )


def adv03_run() -> Dict[str, Any]:
    return run_record(
        run_id="synthetic-run-trivial",
        timing={"unit": "ms", "arms": [
            {"name": "baseline", "scope": "end-to-end", "samples": [1.0], "memory_bytes": 64},
            {"name": "candidate", "scope": "end-to-end", "samples": [0.5], "memory_bytes": 32},
        ]},
        evidence_strength="REPRODUCED",
        checks=[{"check_id": "vac-dim1", "name": "dimension-1 correctness check",
                 "parameters": {"n": 1}, "parameter_roles": {"n": "dimension"},
                 "assertion": "result == expected", "expected_source": "self",
                 "expected": 1.0, "observed": 1.0, "passed": True, "synthetic": True}],
        claim={"strength": "STRONG_LOCAL", "kind": "implementation",
               "statement": "correctness established at a trivial problem size",
               "scope": "synthetic fixture only", "assigned_manually": False},
    )


def adv04_run() -> Dict[str, Any]:
    checks = [
        {"check_id": f"vac-{i:03d}", "name": f"synthetic vacuous {i}",
         "parameters": {"iters": 0}, "parameter_roles": {"iters": "iteration_count"},
         "assertion": "true", "expected_source": "self", "expected": True, "observed": True,
         "passed": True, "synthetic": True}
        for i in range(1, 41)
    ]
    return run_record(
        run_id="synthetic-run-vacuous-batch",
        checks=checks,
        evidence_strength="SCOPED_VERIFIED",
        claim={"strength": "VERIFIED", "kind": "implementation",
               "statement": "40 validations passed, therefore verified",
               "scope": "synthetic fixture only", "assigned_manually": False},
    )


def adv07_run() -> Dict[str, Any]:
    return run_record(
        run_id="synthetic-run-mechanism",
        mechanism={"claim": "the speedup comes from the tensor cores' reduced instruction count",
                   "mechanism_specific": False, "evidence": []},
        evidence_strength="SCOPED_VERIFIED",
        claim={"strength": "STRONG_LOCAL", "kind": "hardware_mechanism",
               "statement": "hardware mechanism asserted from the timing delta alone",
               "scope": "synthetic fixture only", "assigned_manually": False},
    )


def adv08_run() -> Dict[str, Any]:
    rec = run_record(run_id="")
    rec["artifacts"] = []
    rec["evidence_strength"] = "OBSERVED"
    rec["claim"] = {"strength": "CANDIDATE", "kind": "performance",
                    "statement": "no run id, no artifact, still claimed",
                    "scope": "synthetic fixture only", "assigned_manually": False}
    return rec


def adv10_run() -> Dict[str, Any]:
    return run_record(
        run_id="synthetic-run-lean",
        formal={"theorem_target": "", "file": "", "command": "", "exit_status": None,
                "output_ref": None, "kernel_checked": False},
        evidence_strength="FORMAL",
        claim={"strength": "FORMAL_PARTIAL", "kind": "formal",
               "statement": "the speedup law is formally proven",
               "scope": "synthetic fixture only", "assigned_manually": False},
    )


def adv11_run() -> Dict[str, Any]:
    return run_record(
        run_id="synthetic-run-dep",
        dependencies=[{"id": "vendor-kernel", "status": "unresolved"},
                      {"id": "optional-accelerator", "status": "assumed"}],
        evidence_strength="REPRODUCED",
        claim={"strength": "STRONG_LOCAL", "kind": "implementation",
               "statement": "the partial passing test establishes the implementation",
               "scope": "synthetic fixture only", "assigned_manually": False},
    )


def adv12_run() -> Dict[str, Any]:
    return run_record(
        run_id="synthetic-run-manual",
        evidence_strength="OBSERVED",
        claim={"strength": "VERIFIED", "kind": "implementation",
               "statement": "raised to VERIFIED by hand with no supporting evidence",
               "scope": "synthetic fixture only", "assigned_manually": True},
    )


def adv13_run() -> Dict[str, Any]:
    rec = run_record(run_id="synthetic-run-scaling")
    rec["scaling"] = {"sizes": [4096], "ratios": [3.0], "unit": "elements"}
    rec["claim"] = {"strength": "STRONG_LOCAL", "kind": "performance",
                    "statement": "scales linearly, established at a single size",
                    "scope": "synthetic fixture only", "assigned_manually": False}
    return rec


def adv14_run() -> Dict[str, Any]:
    rec = run_record(run_id="synthetic-run-eqfail")
    rec["correctness"] = {
        "equivalence": {"pass": False, "metric": "max_abs_error", "tolerance": 1e-12,
                        "observed": 0.5, "expected": 0.0,
                        "artifact_ref": "tests/fixtures/raw/synthetic_equivalence.json",
                        "note": "candidate output diverges from baseline"},
        "reverse_reconstruction": {"pass": False, "metric": "max_abs_error", "observed": 0.4,
                                   "artifact_ref": "tests/fixtures/raw/synthetic_equivalence.json"},
        "invariant": {"pass": True, "metric": "declared_signature",
                      "artifact_ref": "tests/fixtures/raw/synthetic_equivalence.json"},
    }
    rec["claim"] = {"strength": "VERIFIED", "kind": "implementation",
                    "statement": "verified despite a failed equivalence gate",
                    "scope": "synthetic fixture only", "assigned_manually": False}
    return rec


def adv15_run() -> Dict[str, Any]:
    """Mixed timing scopes: a stage-level arm compared against an end-to-end arm."""
    rec = run_record(run_id="synthetic-run-scope")
    rec["timing"] = {"unit": "ms", "arms": [
        {"name": "baseline", "scope": "stage-2 only", "samples": BASE_SAMPLES},
        {"name": "candidate", "scope": "end-to-end", "samples": CAND_SAMPLES},
    ]}
    rec["claim"] = {"strength": "STRONG_LOCAL", "kind": "performance",
                    "statement": "ratio formed across incomparable timing domains",
                    "scope": "synthetic fixture only", "assigned_manually": False}
    return rec


def adv16_run() -> Dict[str, Any]:
    """Empty input domain: every sample is zero."""
    rec = run_record(run_id="synthetic-run-zero")
    rec["timing"] = {"unit": "ms", "arms": [
        {"name": "baseline", "scope": "end-to-end", "samples": [0.0, 0.0, 0.0, 0.0, 0.0]},
        {"name": "candidate", "scope": "end-to-end", "samples": [0.0, 0.0, 0.0, 0.0, 0.0]},
    ]}
    return rec


def adv17_run() -> Dict[str, Any]:
    """Artifact hash does not match the file on disk."""
    rec = run_record(run_id="synthetic-run-badhash")
    rec["artifacts"] = [{"role": "raw_result",
                         "path": "tests/fixtures/raw/synthetic_candidate_trace.json",
                         "sha256": "0" * 64}]
    return rec


def adv18_run() -> Dict[str, Any]:
    """N far below the minimum needed for a reproduced claim."""
    rec = run_record(run_id="synthetic-run-smalln")
    rec["timing"] = {"unit": "ms", "arms": [
        {"name": "baseline", "scope": "end-to-end", "samples": [120.0]},
        {"name": "candidate", "scope": "end-to-end", "samples": [40.0]},
    ]}
    return rec


HASHES: Dict[str, str] = {}

LEDGER_BUILDERS = {
    "synthetic_valid.jsonl": valid_ledger,
    "adv01_exit_zero_no_timing.jsonl": adv01_exit_zero_no_timing,
    "adv05_multiplied_speedups.jsonl": adv05_multiplied_speedups,
    "adv06_no_fresh_composition_run.jsonl": adv06_no_fresh_composition_run,
    "adv09_contradictory_rerun.jsonl": adv09_contradictory_rerun,
    "adv12_manual_raise.jsonl": adv12_manual_raise,
    "adv13_negative_erased.jsonl": adv13_negative_erased,
    "adv14_hash_chain_broken.jsonl": adv14_hash_chain_broken,
    "adv15_illegal_transition.jsonl": adv15_illegal_transition,
    "adv16_claim_exceeds_evidence.jsonl": adv16_claim_exceeds_evidence,
    "adv17_gap_closed_without_evidence.jsonl": adv17_gap_closed_without_evidence,
    "adv18_operator_not_implemented.jsonl": adv18_operator_not_implemented,
    "adv19_unresolved_dependency.jsonl": adv19_unresolved_dependency,
    "adv20_formal_without_proof.jsonl": adv20_formal_without_proof,
    "adv21_all_vacuous_checks.jsonl": adv21_all_vacuous_checks,
}

RUN_FILES = {
    "synthetic_valid_run.json": run_record,
    "adv01_exit_zero_no_timing.json": adv01_run,
    "adv02_slower_more_memory.json": adv02_run,
    "adv03_trivial_parameter.json": adv03_run,
    "adv04_all_vacuous.json": adv04_run,
    "adv07_mechanism_without_evidence.json": adv07_run,
    "adv08_missing_run_id.json": adv08_run,
    "adv10_lean_without_proof.json": adv10_run,
    "adv11_unresolved_dependency.json": adv11_run,
    "adv12_manual_claim_raise.json": adv12_run,
    "adv13_scaling_single_size.json": adv13_run,
    "adv14_equivalence_failed.json": adv14_run,
    "adv15_mixed_scopes.json": adv15_run,
    "adv16_zero_input_domain.json": adv16_run,
    "adv17_artifact_hash_mismatch.json": adv17_run,
    "adv18_sample_count_below_minimum.json": adv18_run,
}


def main() -> int:
    global HASHES
    HASHES = write_raw()

    for name, builder in LEDGER_BUILDERS.items():
        write_ledger(name, builder())

    RUNS.mkdir(parents=True, exist_ok=True)
    for name, builder in RUN_FILES.items():
        path = RUNS / name
        path.write_text(json.dumps(builder(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"wrote {len(RAW_FILES)} raw artifacts, {len(LEDGER_BUILDERS)} ledgers, {len(RUN_FILES)} run records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())