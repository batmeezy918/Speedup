#!/usr/bin/env python3
"""Evidence-backed PCSS publication gate.

A VERIFIED result requires explicit gates plus immutable local artifact hashes.
This evaluator is deliberately unable to infer quotient, reconstruction,
invariants, attribution, or Lean proof from timing alone.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

GATES = ("integrity", "reproducibility", "quotient_forward", "reconstruction_reverse", "invariants", "performance", "lean")
BASE_ARTIFACTS = ("scenario.json", "environment.json", "trace.json", "performance.json")
PROOF_ARTIFACTS = {
    "quotient_forward": "quotient_hash",
    "reconstruction_reverse": "reverse_hash",
    "invariants": "invariants_hash",
    "lean": "proof_hash",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def evaluate(cert: dict, root: Path) -> tuple[bool, list[str]]:
    failures: list[str] = []
    gates = cert.get("gates")
    if not isinstance(gates, dict):
        return False, ["gates"]
    failures += [g for g in GATES if gates.get(g) is not True]

    for key in ("run_id", "scenario_hash", "source_hash", "input_hash", "environment_hash", "trace_hash", "performance_hash"):
        if not isinstance(cert.get(key), str) or not cert[key]:
            failures.append(key)

    artifacts = cert.get("artifacts")
    if not isinstance(artifacts, dict):
        failures.append("artifacts")
    else:
        for name in BASE_ARTIFACTS:
            expected = artifacts.get(name)
            path = root / name
            if not isinstance(expected, str) or not expected:
                failures.append(f"artifact:{name}")
            elif not path.is_file():
                failures.append(f"missing:{name}")
            elif digest(path) != expected:
                failures.append(f"hash:{name}")

    for gate, field in PROOF_ARTIFACTS.items():
        if gates.get(gate) is True and (not isinstance(cert.get(field), str) or not cert[field]):
            failures.append(field)

    if gates.get("performance") is True:
        perf = cert.get("performance")
        if not isinstance(perf, dict):
            failures.append("performance_artifact")
        else:
            for key in ("metric", "median_baseline", "median_candidate", "speedup_measured", "samples"):
                if key not in perf:
                    failures.append(f"performance:{key}")
    return not failures, sorted(set(failures))


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: strict_gate.py CERTIFICATE.json", file=sys.stderr)
        return 2
    cert_path = Path(sys.argv[1]).resolve()
    try:
        cert = json.loads(cert_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"QUARANTINED: invalid certificate: {exc}")
        return 1
    ok, failures = evaluate(cert, cert_path.parent)
    if ok:
        print("VERIFIED: all mandatory PCSS gates and artifact hashes passed")
        return 0
    print("QUARANTINED: mandatory PCSS evidence not proven")
    for failure in failures:
        print(f" - {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
