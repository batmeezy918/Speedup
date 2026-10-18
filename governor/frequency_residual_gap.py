#!/usr/bin/env python3
"""Compile msweep_v2 frequency-residual flags into first-class SCALING_GAP objects.

Consumes msweep_v2.json (schema muni.msweep-v2/v1) emitted by msweep_v2.c.
For every bin where |speedup/m - 1| > FREQUENCY_RESIDUAL_THRESHOLD, emits a
PCSS-FORMAL-GAP/v1 SCALING_GAP with a closure predicate, required experiment,
and dependency on MEASUREMENT_GAP (timing must be phase-split before the
residual can be attributed).

Fail-closed: this module extracts and compiles gaps. It never promotes
evidence or changes a primitive's evidence class. NO_PROMOTION.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

THRESHOLD = 0.05
PRIORITY_SCALING = 90


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode())


def compile_scaling_gap(bin_row: dict[str, Any], source_path: pathlib.Path) -> dict[str, Any]:
    m = bin_row["m"]
    ratio_m = bin_row["ratio_over_m"]
    residual = abs(ratio_m - 1.0)
    direction = "below" if ratio_m < 1.0 else "above"
    return {
        "schema": "PCSS-FORMAL-GAP/v1",
        "gap_id": f"G-SCALING_GAP-FREQRES-m{m}-{source_path.stem}",
        "parent_run": source_path.stem,
        "parent_scenario_hash": bin_row.get("scenario_hash"),
        "timestamp": now(),
        "type": "SCALING_GAP",
        "source_gate": "X",
        "priority": PRIORITY_SCALING,
        "status": "OPEN",
        "claim_strength": "CANDIDATE",
        "evidence_strength": "OBSERVATION",
        "statement": (
            f"At m={m} the measured speedup-to-m ratio is {ratio_m:.3f}, "
            f"{direction} the arithmetic prediction by {residual:.3f} "
            f"(threshold {THRESHOLD}). This is a frequency-domain residual: "
            f"the fixed DC overhead (plan_create + reconstruct) equals the "
            f"compressed arithmetic energy at this bin."
        ),
        "failed_obligation": (
            "Scaling requires measurements across the declared parameter domain "
            "with an explicit extrapolation bound; a bin deviating past threshold "
            "must be typed, attributed, and closed before any out-of-domain claim."
        ),
        "required_artifacts": ["msweep_v2.json", "scaling.json", "attribution.json"],
        "blockers": [],
        "observations": [bin_row],
        "dependencies": [],
        "candidate_theorems": [
            "AGD_GAP_DERIVATION.lean Gap1 (commutation decides exactness)",
            "fixed-cost model T(m) = a*m + C fitted per path",
        ],
        "required_experiment": [
            "re-run msweep_v2 with phase-split timing enabled",
            "fit C_base and C_quot by least squares; attribute residual to C_quot",
            "verify C_quot/quot_ms(m) predicts the observed dip location",
            "cross-environment witness on independent substrate to test if dip is arch-specific",
        ],
        "required_telemetry": [
            "plan_create_ms", "run_ms", "reconstruct_ms", "C_base", "C_quot",
            "cpu_frequency", "thermal_state",
        ],
        "closure_predicate": (
            f"|speedup/m - 1| <= {THRESHOLD} at m={m} with phase-split attribution "
            "reconciled, OR the deviation is typed as HARDWARE_MECHANISM_GAP "
            "with independent telemetry and accepted as a second-order effect "
            "with an explicit bound"
        ),
        "frequency_residual": residual,
        "direction": direction,
        "threshold": THRESHOLD,
    }


def extract(msweep: dict[str, Any], source_path: pathlib.Path) -> dict[str, Any]:
    gaps = []
    for row in msweep.get("bins", []):
        if abs(row.get("ratio_over_m", 1.0) - 1.0) > THRESHOLD:
            gaps.append(compile_scaling_gap(row, source_path))
    # dependency wiring: SCALING_GAP depends on MEASUREMENT_GAP if present
    by_type = {g["type"]: g["gap_id"] for g in gaps}
    for g in gaps:
        if "MEASUREMENT_GAP" in by_type:
            g["dependencies"].append(by_type["MEASUREMENT_GAP"])
            g["blockers"] = list(g["dependencies"])
    bundle = {
        "schema": "PCSS-FORMAL-GAP-BUNDLE/v1",
        "generated_at": now(),
        "parent_source": str(source_path),
        "parent_source_sha256": sha256_bytes(source_path.read_bytes()) if source_path.exists() else None,
        "source_schema": msweep.get("schema"),
        "frequency_residual_threshold": THRESHOLD,
        "gaps": gaps,
        "closure_plans": [
            {
                "schema": "PCSS-CLOSURE-PLAN/v1",
                "gap_id": g["gap_id"],
                "objective": g["failed_obligation"],
                "preconditions": g["dependencies"],
                "actions": g["required_experiment"],
                "telemetry": g["required_telemetry"],
                "acceptance": g["closure_predicate"],
                "terminal_states": ["CLOSED", "REFINED", "NEGATIVE"],
                "promotion": "never implied by closure-plan generation",
            }
            for g in gaps
        ],
        "promotion_policy": "NO_PROMOTION: gap extraction cannot promote evidence",
        "fixed_cost_model": msweep.get("fixed_cost_fit"),
    }
    bundle["bundle_sha256"] = sha256_json(bundle)
    return bundle


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("msweep_json", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("frequency_residual_bundle.json"))
    ap.add_argument("--threshold", type=float, default=THRESHOLD)
    args = ap.parse_args()
    global THRESHOLD
    THRESHOLD = args.threshold
    try:
        msweep = json.loads(args.msweep_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: invalid msweep json: {exc}")
        return 2
    if msweep.get("schema") != "muni.msweep-v2/v1":
        print(f"FAIL: schema mismatch: {msweep.get('schema')}")
        return 2
    bundle = extract(msweep, args.msweep_json)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: compiled {len(bundle['gaps'])} frequency-residual SCALING_GAP(s)")
    print(f"bundle_sha256={bundle['bundle_sha256']}")
    print("NO_PROMOTION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
