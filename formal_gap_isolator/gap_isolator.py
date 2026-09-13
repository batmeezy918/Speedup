#!/usr/bin/env python3
"""Fail-closed first-class formal-gap extraction for PCSS certificates."""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

GATES = ("integrity", "reproducibility", "quotient_forward", "reconstruction_reverse", "invariants", "performance", "lean")
GAP_MAP = {
    "integrity": "INTEGRITY_GAP",
    "reproducibility": "MEASUREMENT_GAP",
    "quotient_forward": "EQUIVALENCE_GAP",
    "reconstruction_reverse": "RECONSTRUCTION_GAP",
    "invariants": "INVARIANT_GAP",
    "performance": "PERFORMANCE_GAP",
    "lean": "FORMAL_GAP",
}
PRIORITY = {"INTEGRITY_GAP": 0, "MEASUREMENT_GAP": 1, "EQUIVALENCE_GAP": 2,
            "RECONSTRUCTION_GAP": 3, "INVARIANT_GAP": 4, "PERFORMANCE_GAP": 5,
            "FORMAL_GAP": 6, "ATTRIBUTION_GAP": 7, "SCALING_GAP": 8,
            "HARDWARE_MECHANISM_GAP": 9}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract(cert: dict) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    gaps = []
    gates = cert.get("gates", {})
    explicit = cert.get("open_gaps", [])
    explicit_types = {x.get("type") for x in explicit if isinstance(x, dict)}
    for gate in GATES:
        if gates.get(gate) is not True:
            typ = GAP_MAP[gate]
            gaps.append(_gap(cert, now, typ, gate, f"Mandatory gate {gate} is not proven."))
    for typ in sorted(explicit_types - {g["type"] for g in gaps}, key=lambda x: PRIORITY.get(x, 99)):
        gaps.append(_gap(cert, now, typ, None, f"Explicit open gap {typ} remains unresolved."))
    for g in gaps:
        g["dependencies"] = dependencies(g["type"], {x["type"] for x in gaps})
        g["closure_plan"] = closure_plan(g["type"])
    return sorted(gaps, key=lambda x: (x["priority"], x["gap_id"]))


def _gap(cert, now, typ, gate, statement):
    run = cert.get("run_id", "UNKNOWN")
    return {
        "schema": "PCSS-FORMAL-GAP/v1",
        "gap_id": f"GAP-{typ}-{run}",
        "parent_run": run,
        "parent_scenario_hash": cert.get("scenario_hash"),
        "timestamp": now,
        "type": typ,
        "source_gate": gate,
        "priority": PRIORITY.get(typ, 99),
        "status": "OPEN",
        "claim_strength": cert.get("claim_strength", "CANDIDATE"),
        "evidence_strength": cert.get("evidence_strength", "UNKNOWN"),
        "statement": statement,
        "failed_obligation": f"Produce independently bound evidence sufficient to establish {typ}.",
        "required_artifacts": [],
        "blockers": [],
        "observations": cert.get("observations", []),
        "candidate_theorems": cert.get("candidate_theorems", []),
        "required_experiment": None,
        "required_telemetry": [],
        "closure_predicate": f"{typ} evidence is independently present, hashed, validated, and bound to the run.",
    }


def dependencies(typ, present):
    deps = {
        "MEASUREMENT_GAP": ["INTEGRITY_GAP"],
        "EQUIVALENCE_GAP": ["INTEGRITY_GAP"],
        "RECONSTRUCTION_GAP": ["EQUIVALENCE_GAP"],
        "INVARIANT_GAP": ["EQUIVALENCE_GAP"],
        "PERFORMANCE_GAP": ["MEASUREMENT_GAP"],
        "FORMAL_GAP": ["EQUIVALENCE_GAP", "RECONSTRUCTION_GAP", "INVARIANT_GAP"],
    }
    return [d for d in deps.get(typ, []) if d in present]


def closure_plan(typ):
    plans = {
        "INTEGRITY_GAP": ["lock scenario/source/input identities", "hash immutable artifacts", "rerun and bind hashes"],
        "MEASUREMENT_GAP": ["execute locked native scenario", "capture repeated raw timings", "record environment and trace"],
        "EQUIVALENCE_GAP": ["define observable quotient Q", "compute Q(candidate) and Q(baseline)", "bind quotient artifact to run"],
        "RECONSTRUCTION_GAP": ["define reverse reconstruction R", "verify d(R(Q(e)),e) <= epsilon", "bind reverse artifact"],
        "INVARIANT_GAP": ["state invariants explicitly", "evaluate them on native evidence", "bind invariant artifact"],
        "PERFORMANCE_GAP": ["use repeated native baseline/candidate measurements", "report uncertainty and direct speedup", "preserve raw samples"],
        "FORMAL_GAP": ["generate Lean obligation from evidence", "compile against pinned toolchain", "bind proof artifact/hash"],
        "ATTRIBUTION_GAP": ["separate saved work, overlap, overhead, interaction", "measure residual", "avoid causal attribution unless independently established"],
        "SCALING_GAP": ["measure multiple sizes", "fit only within observed domain", "retain extrapolation as conditional"],
        "HARDWARE_MECHANISM_GAP": ["capture hardware/runtime telemetry", "separate software operation-count effects from hardware causation", "retain unproven mechanism claims as such"],
    }
    return plans.get(typ, ["define obligation", "collect evidence", "validate closure"])


def main():
    if len(sys.argv) != 3:
        print("usage: gap_isolator.py CERTIFICATE.json OUTPUT_DIR", file=sys.stderr)
        return 2
    cert_path, out = Path(sys.argv[1]), Path(sys.argv[2])
    cert = json.loads(cert_path.read_text(encoding="utf-8"))
    gaps = extract(cert)
    out.mkdir(parents=True, exist_ok=True)
    bundle = {"schema": "PCSS-FORMAL-GAP-BUNDLE/v1", "parent_certificate": str(cert_path), "gaps": gaps}
    raw = json.dumps(bundle, sort_keys=True, indent=2).encode()
    bundle["bundle_sha256"] = sha256_bytes(raw)
    (out / "gap_bundle.json").write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for g in gaps:
        (out / f"{g['gap_id']}.json").write_text(json.dumps(g, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"gaps": len(gaps), "types": [g["type"] for g in gaps], "bundle_sha256": bundle["bundle_sha256"]}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
