#!/usr/bin/env python3
"""Fail-closed PCSS gate. Unknown is not true."""
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

def evaluate(certificate: dict):
    gates = certificate.get("gates", {})
    failures = [name for name in REQUIRED if gates.get(name) is not True]
    return not failures, failures

def main() -> int:
    if len(sys.argv) != 2:
        print("usage: strict_gate.py CERTIFICATE.json", file=sys.stderr)
        return 2
    cert = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    ok, failures = evaluate(cert)
    if ok:
        print("VERIFIED: all mandatory PCSS gates passed")
        return 0
    print("QUARANTINED: mandatory gates not proven")
    for name in failures:
        print(f" - {name}")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
