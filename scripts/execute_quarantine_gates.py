#!/usr/bin/env python3
"""Execute every quarantined speedup claim against the PCSS publication gate.

This does not invent missing measurements. A claim meets publication only
when gate.py returns 0. Every recorded vector below is missing at least one
of I, R, Q, Qinv, Omega, X, L, so the expected result is QUARANTINED.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "publisher" / "gate.py"

CLAIMS = [
    {
        "id": "cocoex-bbob-dim10-budget1000-20260910",
        "class": "NEGATIVE",
        "gates": {
            "integrity": True,
            "reproducibility": True,
            "quotient_forward": False,
            "reconstruction_reverse": True,
            "invariants": True,
            "performance": False,
            "lean": False,
        },
    },
    {
        "id": "sim2xr-invariant-sector-20260908",
        "class": "STRONG_LOCAL",
        "gates": {
            "integrity": True,
            "reproducibility": True,
            "quotient_forward": True,
            "reconstruction_reverse": True,
            "invariants": True,
            "performance": True,
            "lean": False,
        },
    },
    {
        "id": "s6-s7-s8-coco-equivalent-20260515",
        "class": "QUARANTINED",
        "gates": {k: False for k in (
            "integrity", "reproducibility", "quotient_forward",
            "reconstruction_reverse", "invariants", "performance", "lean")},
    },
    {
        "id": "vault-canonical-decider-20260531T112101Z",
        "class": "CANDIDATE",
        "gates": {k: False for k in (
            "integrity", "reproducibility", "quotient_forward",
            "reconstruction_reverse", "invariants", "performance", "lean")},
    },
    {
        "id": "iqvf-coco",
        "class": "QUARANTINED",
        "gates": {k: False for k in (
            "integrity", "reproducibility", "quotient_forward",
            "reconstruction_reverse", "invariants", "performance", "lean")},
    },
    {
        "id": "snap-24-case-vs-cma",
        "class": "CANDIDATE",
        "gates": {k: False for k in (
            "integrity", "reproducibility", "quotient_forward",
            "reconstruction_reverse", "invariants", "performance", "lean")},
    },
    {
        "id": "ledger-reported-ratios",
        "class": "THEORETICAL_OR_SIMULATED",
        "gates": {k: False for k in (
            "integrity", "reproducibility", "quotient_forward",
            "reconstruction_reverse", "invariants", "performance", "lean")},
    },
    {
        "id": "graph500-reference",
        "class": "MEASURED_BASELINE",
        "gates": {
            "integrity": True,
            "reproducibility": False,
            "quotient_forward": False,
            "reconstruction_reverse": False,
            "invariants": False,
            "performance": False,
            "lean": False,
        },
    },
    {
        "id": "PCSS_NEON_GEMM_N512_20261001T052954Z",
        "class": "CERTIFICATE_BOUND",
        "gates": {
            "integrity": True,
            "reproducibility": True,
            "quotient_forward": False,
            "reconstruction_reverse": False,
            "invariants": False,
            "performance": True,
            "lean": True,
        },
    },
]


def main() -> int:
    results = []
    published = 0
    for claim in CLAIMS:
        cert = {
            "run_id": claim["id"],
            "class": claim["class"],
            "gates": claim["gates"],
        }
        path = Path("/tmp") / f"pcss-{claim['id']}.json"
        path.write_text(json.dumps(cert), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(GATE), str(path)],
            capture_output=True,
            text=True,
        )
        ok = proc.returncode == 0
        published += int(ok)
        missing = [
            name for name, value in claim["gates"].items() if value is not True
        ]
        results.append({
            "id": claim["id"],
            "class": claim["class"],
            "gate_exit": proc.returncode,
            "publishable": ok,
            "missing": missing,
            "stdout": proc.stdout.strip(),
        })
        print(f"{claim['id']}: exit={proc.returncode} publishable={ok} missing={missing}")
    out = ROOT / "evidence" / "quarantine" / "EXECUTION_20261001.json"
    out.write_text(json.dumps({
        "predicate": "PUBLISH <=> I and R and Q and Qinv and Omega and X and L",
        "published": published,
        "executed": len(results),
        "results": results,
    }, indent=2), encoding="utf-8")
    print(f"published={published} executed={len(results)}")
    return 0 if published == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
