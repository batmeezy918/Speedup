#!/usr/bin/env python3
"""Evidence-backed PCSS publication gate.

A VERIFIED result requires explicit gates plus immutable local artifact hashes.
Proof-gate hashes are bound to actual files; a claimed hash string alone is
never accepted as proof evidence.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

GATES = ("integrity", "reproducibility", "quotient_forward", "reconstruction_reverse", "invariants", "performance", "lean")
BASE_ARTIFACTS = ("scenario.json", "environment.json", "trace.json", "performance.json")
PROOF_GATES = {
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

    # A proof gate is valid only when its certificate hash is bound to a
    # present local artifact whose bytes hash to the declared value.
    proof_files = cert.get("proof_artifacts")
    if not isinstance(proof_files, dict):
        proof_files = {}
    for gate, hash_field in PROOF_GATES.items():
        if gates.get(gate) is True:
            declared_hash = cert.get(hash_field)
            spec = proof_files.get(gate)
            if not isinstance(declared_hash, str) or not declared_hash:
                failures.append(hash_field)
                continue
            if not isinstance(spec, dict):
                failures.append(f"proof_binding:{gate}")
                continue
            rel = spec.get("path")
            expected = spec.get("sha256")
            if not isinstance(rel, str) or not rel or not isinstance(expected, str) or not expected:
                failures.append(f"proof_binding:{gate}")
                continue
            if expected != declared_hash:
                failures.append(f"proof_declared_hash:{gate}")
                continue
            path = (root / rel).resolve()
            try:
                path.relative_to(root.resolve())
            except ValueError:
                failures.append(f"proof_path_escape:{gate}")
                continue
            if not path.is_file():
                failures.append(f"proof_missing:{gate}")
            elif digest(path) != expected:
                failures.append(f"proof_hash:{gate}")

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
