#!/usr/bin/env python3
"""Fail-closed specimen gate. Unknown is not true."""
import json
import sys
from pathlib import Path

REQUIRED = (
    "integrity",
    "reproducibility",
    "quotient_forward",
    "reconstruction_reverse",
    "invariants",
    "performance",
    "lean",
)

def main() -> int:
    if len(sys.argv) != 2:
        print("usage: strict_gate.py CERTIFICATE.json", file=sys.stderr)
        return 2
    cert = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    gates = cert.get("gates", {})
    missing = [name for name in REQUIRED if gates.get(name) is not True]
    if missing:
        print("QUARANTINED")
        for name in missing:
            print(f" - {name}")
        return 1
    print("VERIFIED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
