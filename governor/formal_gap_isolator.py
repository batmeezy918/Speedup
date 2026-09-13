#!/usr/bin/env python3
"""Compile PCSS evidence failures into first-class, executable proof gaps.

This module is deliberately fail-closed: it extracts obligations and closure
plans, but it never promotes evidence or changes a primitive's evidence class.

Pipeline:
    certificate -> gaps -> dependency order -> closure plans -> artifacts

A gap is an operational state object, not prose.  The emitted objects are
stable JSON so they can be hashed, reviewed, replayed, and appended to the
formal-gap ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

GATES = ("I", "R", "Q", "Q_inverse", "Omega", "X", "L")
GATE_NAMES = {
    "I": ("integrity", "INTEGRITY_GAP"),
    "R": ("reproducibility", "REPRODUCIBILITY_GAP"),
    "Q": ("quotient_forward", "EQUIVALENCE_GAP"),
    "Q_inverse": ("reconstruction_reverse", "RECONSTRUCTION_GAP"),
    "Omega": ("invariants", "INVARIANT_GAP"),
    "X": ("performance", "MEASUREMENT_GAP"),
    "L": ("lean", "FORMAL_GAP"),
}
PRIORITY = {
    "INTEGRITY_GAP": 10,
    "REPRODUCIBILITY_GAP": 20,
    "MEASUREMENT_GAP": 30,
    "EQUIVALENCE_GAP": 40,
    "RECONSTRUCTION_GAP": 50,
    "INVARIANT_GAP": 60,
    "FORMAL_GAP": 70,
    "ATTRIBUTION_GAP": 80,
    "SCALING_GAP": 90,
    "HARDWARE_MECHANISM_GAP": 100,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode())


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def base_statement(gap_type: str, gate: str) -> tuple[str, str, list[str]]:
    if gap_type == "INTEGRITY_GAP":
        return ("The evidence package is not cryptographically bound to all required run artifacts.",
                "I requires every declared base artifact to exist and hash exactly to its certificate binding.",
                ["scenario.json", "environment.json", "trace.json", "performance.json"])
    if gap_type == "REPRODUCIBILITY_GAP":
        return ("The native execution is not yet reproducibly established under the locked scenario.",
                "R requires deterministic/reproducible native outputs under the declared environment and run protocol.",
                ["scenario.json", "environment.json", "trace.json"])
    if gap_type == "EQUIVALENCE_GAP":
        return ("Forward quotient equivalence between baseline and candidate has not been established.",
                "Q requires Q(E_candidate) = Q(E_baseline), or an explicitly declared and justified tolerance.",
                ["quotient.json"])
    if gap_type == "RECONSTRUCTION_GAP":
        return ("Reverse reconstruction from the quotient has not been established.",
                "Q^-1 requires a reconstruction map R with d(R(Q(e)), e) <= epsilon and bidirectional consistency.",
                ["reconstruction.json"])
    if gap_type == "INVARIANT_GAP":
        return ("Required observable invariants have not been independently established.",
                "Omega requires the declared invariants to hold for the transformed/reconstructed observable state.",
                ["invariants.json"])
    if gap_type == "MEASUREMENT_GAP":
        return ("The performance claim lacks complete direct native measurement evidence.",
                "X requires declared metric, baseline/candidate samples, aggregation, uncertainty treatment, and successful runs.",
                ["performance.json", "trace.json"])
    if gap_type == "FORMAL_GAP":
        return ("The evidence obligations have not been discharged by the required formal proof artifact.",
                "L requires a proof artifact whose source, theorem obligations, and hash are bound to the run evidence.",
                ["proof artifact"])
    if gap_type == "ATTRIBUTION_GAP":
        return ("The observed effect is not yet causally attributed to the claimed implementation mechanism.",
                "Attribution must reconcile saved work, overlap, new overhead, interaction, and residual unexplained effect.",
                ["attribution.json"])
    if gap_type == "SCALING_GAP":
        return ("Scaling behavior outside the measured scenario has not been established.",
                "Scaling requires measurements across the declared dimension/parameter domain and an explicit extrapolation bound.",
                ["scaling.json"])
    if gap_type == "HARDWARE_MECHANISM_GAP":
        return ("The measured effect has not been causally tied to a hardware/runtime mechanism.",
                "Hardware attribution requires independent telemetry and residual accounting; operation-count savings alone are insufficient.",
                ["hardware_telemetry.json"])
    return (f"Unresolved proof gap: {gap_type}.", "The corresponding gate/obligation must be explicitly discharged.", [])


def dependency_ids(gap_type: str, gaps: list[dict[str, Any]]) -> list[str]:
    by_type = {g["type"]: g["gap_id"] for g in gaps}
    deps: list[str] = []
    if gap_type in {"REPRODUCIBILITY_GAP", "MEASUREMENT_GAP"} and "INTEGRITY_GAP" in by_type:
        deps.append(by_type["INTEGRITY_GAP"])
    if gap_type == "RECONSTRUCTION_GAP" and "EQUIVALENCE_GAP" in by_type:
        deps.append(by_type["EQUIVALENCE_GAP"])
    if gap_type == "FORMAL_GAP":
        for t in ("EQUIVALENCE_GAP", "RECONSTRUCTION_GAP", "INVARIANT_GAP"):
            if t in by_type:
                deps.append(by_type[t])
    return deps


def extract(cert: dict[str, Any], source_path: pathlib.Path) -> dict[str, Any]:
    gates = cert.get("gates") if isinstance(cert.get("gates"), dict) else {}
    run_id = str(cert.get("run_id") or source_path.stem)
    scenario_hash = cert.get("scenario_hash")
    timestamp = cert.get("timestamp") or now()
    gaps: list[dict[str, Any]] = []

    for gate in GATES:
        if gates.get(gate) is True:
            continue
        _, gap_type = GATE_NAMES[gate]
        statement, obligation, artifacts = base_statement(gap_type, gate)
        gap = {
            "schema": "PCSS-FORMAL-GAP/v1",
            "gap_id": f"G-{gap_type}-{run_id}",
            "parent_run": run_id,
            "parent_scenario_hash": scenario_hash,
            "timestamp": timestamp,
            "type": gap_type,
            "source_gate": gate,
            "priority": PRIORITY[gap_type],
            "status": "OPEN",
            "claim_strength": cert.get("claim_strength", "CANDIDATE"),
            "evidence_strength": cert.get("evidence_strength", "OBSERVATION"),
            "statement": statement,
            "failed_obligation": obligation,
            "required_artifacts": artifacts,
            "blockers": [],
            "observations": cert.get("open_gaps", {}).get(gap_type, []) if isinstance(cert.get("open_gaps"), dict) else [],
            "dependencies": [],
            "candidate_theorems": [],
            "required_experiment": [],
            "required_telemetry": [],
            "closure_predicate": f"gate {gate} == true with independently bound evidence",
        }
        gaps.append(gap)

    # Explicit non-gate gaps are preserved rather than inferred away.
    explicit = cert.get("open_gaps")
    if isinstance(explicit, dict):
        for gap_type in ("ATTRIBUTION_GAP", "SCALING_GAP", "HARDWARE_MECHANISM_GAP"):
            if gap_type not in explicit:
                continue
            statement, obligation, artifacts = base_statement(gap_type, "")
            gaps.append({
                "schema": "PCSS-FORMAL-GAP/v1",
                "gap_id": f"G-{gap_type}-{run_id}",
                "parent_run": run_id,
                "parent_scenario_hash": scenario_hash,
                "timestamp": timestamp,
                "type": gap_type,
                "source_gate": None,
                "priority": PRIORITY[gap_type],
                "status": "OPEN",
                "claim_strength": cert.get("claim_strength", "CANDIDATE"),
                "evidence_strength": cert.get("evidence_strength", "OBSERVATION"),
                "statement": statement,
                "failed_obligation": obligation,
                "required_artifacts": artifacts,
                "blockers": [],
                "observations": explicit[gap_type],
                "dependencies": [],
                "candidate_theorems": [],
                "required_experiment": [],
                "required_telemetry": [],
                "closure_predicate": "explicit gap evidence is independently captured, reconciled, and accepted",
            })

    gaps.sort(key=lambda g: (g["priority"], g["gap_id"]))
    for gap in gaps:
        gap["dependencies"] = dependency_ids(gap["type"], gaps)
        if gap["dependencies"]:
            gap["blockers"] = list(gap["dependencies"])
        gap["required_experiment"] = experiment_for(gap["type"])
        gap["required_telemetry"] = telemetry_for(gap["type"])

    plans = [compile_plan(g) for g in gaps]
    bundle = {
        "schema": "PCSS-FORMAL-GAP-BUNDLE/v1",
        "generated_at": now(),
        "parent_certificate": str(source_path),
        "parent_certificate_sha256": sha256_bytes(source_path.read_bytes()),
        "parent_run": run_id,
        "gaps": gaps,
        "closure_plans": plans,
        "promotion_policy": "NO_PROMOTION: gap extraction cannot promote evidence",
    }
    bundle["bundle_sha256"] = sha256_json(bundle)
    return bundle


def experiment_for(gap_type: str) -> list[str]:
    return {
        "INTEGRITY_GAP": ["rebuild certificate bindings from actual artifact bytes", "re-run strict hash validation"],
        "REPRODUCIBILITY_GAP": ["lock environment and scenario", "perform warmups plus repeated native runs", "compare output hashes and timing distributions"],
        "EQUIVALENCE_GAP": ["define observable quotient Q", "compute Q on baseline and candidate", "test equality/tolerance across all required cases"],
        "RECONSTRUCTION_GAP": ["construct reverse map R", "measure reconstruction distance", "verify forward/reverse certificate consistency"],
        "INVARIANT_GAP": ["instantiate declared invariants", "evaluate them on captured observables", "record tolerances and counterexamples"],
        "MEASUREMENT_GAP": ["rerun direct baseline/candidate timing", "capture raw samples", "compute median and dispersion without ratio multiplication"],
        "FORMAL_GAP": ["generate theorem obligations from the locked evidence", "compile the proof artifact", "bind proof hash to the certificate"],
        "ATTRIBUTION_GAP": ["measure saved work and all overhead terms", "reconcile residual", "separate accounting identity from causal hardware evidence"],
        "SCALING_GAP": ["measure declared parameter grid", "test fit/extrapolation assumptions", "retain out-of-domain claims as unverified"],
        "HARDWARE_MECHANISM_GAP": ["capture runtime/OS/hardware telemetry", "correlate mechanism with effect", "close unexplained residual"],
    }.get(gap_type, ["define and execute a gap-specific closure experiment"])


def telemetry_for(gap_type: str) -> list[str]:
    if gap_type in {"MEASUREMENT_GAP", "REPRODUCIBILITY_GAP"}:
        return ["wall_ns", "cpu_time", "exit_code", "stdout_hash", "stderr_hash", "environment_fingerprint"]
    if gap_type == "HARDWARE_MECHANISM_GAP":
        return ["cpu_frequency", "scheduler/jitter observations", "memory/bandwidth observations", "thermal/power data when available"]
    return []


def compile_plan(gap: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "PCSS-CLOSURE-PLAN/v1",
        "gap_id": gap["gap_id"],
        "objective": gap["failed_obligation"],
        "preconditions": gap["dependencies"],
        "actions": gap["required_experiment"],
        "telemetry": gap["required_telemetry"],
        "acceptance": gap["closure_predicate"],
        "terminal_states": ["CLOSED", "REFINED", "NEGATIVE"],
        "promotion": "never implied by closure-plan generation",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("certificate", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("gap_bundle.json"))
    args = ap.parse_args()
    try:
        cert = json.loads(args.certificate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: invalid certificate: {exc}")
        return 2
    bundle = extract(cert, args.certificate)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: extracted {len(bundle['gaps'])} first-class proof gaps")
    print(f"bundle_sha256={bundle['bundle_sha256']}")
    print("NO_PROMOTION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
