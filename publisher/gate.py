#!/usr/bin/env python3
"""PCSS gate predicate — READ-ONLY evaluator (legacy compatibility surface).

The repository has exactly ONE publication authority: publisher/strict_gate.py.
This module may evaluate gate predicates for analysis/CI, but its CLI must
never promote: it reports "GATE PREDICATE: all mandatory gates true/false" and
delegates any publication decision to publisher/strict_gate.py.

Both legacy fields (certificate["gates"] booleans) and the canonical
gate_results[gate].value representation are accepted here, purely for
backwards compatibility with pre-2.0 certificates.
"""
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


def value_of(certificate: dict, name: str):
    """Read a gate value from either representation. Returns None if unknown."""
    gr = certificate.get("gate_results")
    if isinstance(gr, dict) and name in gr:
        return gr[name].get("value") if isinstance(gr[name], dict) else gr[name]
    gates = certificate.get("gates")
    if isinstance(gates, dict):
        return gates.get(name)
    return None


def evaluate(certificate: dict) -> tuple[bool, list[str]]:
    """Return (all_required_passed, [failures]). Read-only; no promotion."""
    failures = [name for name in REQUIRED if value_of(certificate, name) is not True]
    return not failures, failures


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: gate.py CERTIFICATE.json", file=sys.stderr)
        print("NOTE: the single publication authority is publisher/strict_gate.py", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    cert = json.loads(path.read_text(encoding="utf-8"))
    ok, failures = evaluate(cert)
    if ok:
        print("GATE PREDICATE: all mandatory PCSS gates true (publication decision belongs to strict_gate.py)")
        return 0
    print("GATE PREDICATE: mandatory gates not proven (publication decision belongs to strict_gate.py)")
    for name in failures:
        print(f" - {name}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())