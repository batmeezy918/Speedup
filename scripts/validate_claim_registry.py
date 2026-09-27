#!/usr/bin/env python3
"""Fail-closed check: REGISTRY.json class must respect lean/gates."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "claims" / "REGISTRY.json"


def main() -> int:
    data = json.loads(REG.read_text())
    errors: list[str] = []
    verified = 0
    for claim in data.get("claims", []):
        cid = claim.get("id", "?")
        klass = claim.get("class")
        gates = claim.get("gates") or {}
        lean = gates.get("lean")
        if klass == "VERIFIED":
            verified += 1
            if lean is False:
                errors.append(f"{cid}: VERIFIED with lean=false")
            if gates and not all(gates.get(k) is True for k in (
                "integrity", "reproducibility", "quotient_forward",
                "reconstruction_reverse", "invariants", "performance", "lean"
            )):
                errors.append(f"{cid}: VERIFIED without all seven gates true")
        if cid.startswith("sim2xr") and klass == "VERIFIED":
            errors.append(f"{cid}: SIM2XR must not be VERIFIED while L is open")
    if data.get("verified_count", 0) != verified:
        errors.append(
            f"verified_count={data.get('verified_count')} but VERIFIED rows={verified}"
        )
    if errors:
        print("REGISTRY INVALID")
        for e in errors:
            print(" -", e)
        return 1
    print(f"REGISTRY OK  claims={len(data.get('claims', []))} verified={verified}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
