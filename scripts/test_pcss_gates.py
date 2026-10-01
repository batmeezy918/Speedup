#!/usr/bin/env python3
"""Regression tests for fail-closed PCSS gates."""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def write(path: Path, data: bytes) -> str:
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        artifacts = {}
        for name, data in {
            "scenario.json": b'{"scenario":"locked"}\n',
            "environment.json": b'{"environment":"test"}\n',
            "trace.json": b'{"runs":[]}\n',
            "performance.json": b'{"metric":"wall_ns","median_baseline":2,"median_candidate":1,"speedup_measured":2,"samples":1}\n',
        }.items():
            artifacts[name] = write(d / name, data)

        proof_artifacts = {}
        proof_hashes = {
            "quotient_forward": "6083243275ebe1808fe0217bbdccdfee12aad607b06107a7dcf4b7bddc2162ea",
            "reconstruction_reverse": "6432ec891a5ed3ee6b71c71e68392244f7b055564b136a31f729d2afdef274b5",
            "invariants": "d160aada2000e6a390f27c1b5847915bab64e46e33632e3997d08fa305bf110b",
            "lean": "4426b5d28ab223de134b3087061a26dadde7a583f8de2b58147443a5cbda7b8f",
        }
        for gate, content, declared_hash in [
            ("quotient_forward", b"quotient-proof-data\n", proof_hashes["quotient_forward"]),
            ("reconstruction_reverse", b"reverse-proof-data\n", proof_hashes["reconstruction_reverse"]),
            ("invariants", b"invariants-proof-data\n", proof_hashes["invariants"]),
            ("lean", b"lean-proof-data\n", proof_hashes["lean"]),
        ]:
            path = d / f"proof_{gate}.json"
            actual_hash = write(path, content)
            if actual_hash != declared_hash:
                print(f"Hash mismatch for {gate}: expected {declared_hash}, got {actual_hash}")
                return 1
            proof_artifacts[gate] = {"path": path.name, "sha256": declared_hash}

        cert = {
            "run_id": "gate-regression",
            "scenario_hash": artifacts["scenario.json"],
            "source_hash": "source",
            "input_hash": "input",
            "environment_hash": artifacts["environment.json"],
            "trace_hash": artifacts["trace.json"],
            "performance_hash": artifacts["performance.json"],
            "artifacts": artifacts,
            "proof_artifacts": proof_artifacts,
            "performance": {"metric":"wall_ns","median_baseline":2,"median_candidate":1,"speedup_measured":2,"samples":1},
            "gates": {g: True for g in ("integrity","reproducibility","quotient_forward","reconstruction_reverse","invariants","performance","lean")},
            "quotient_hash": proof_hashes["quotient_forward"],
            "reverse_hash": proof_hashes["reconstruction_reverse"],
            "invariants_hash": proof_hashes["invariants"],
            "proof_hash": proof_hashes["lean"],
        }
        cp = d / "certificate.json"
        cp.write_text(json.dumps(cert), encoding="utf-8")
        gate = ROOT / "publisher" / "strict_gate.py"
        good = subprocess.run([sys.executable, str(gate), str(cp)], capture_output=True, text=True)
        if good.returncode != 0:
            print(good.stdout + good.stderr)
            return 1
        # Tamper with an artifact: the same certificate must fail.
        (d / "trace.json").write_bytes(b'{"runs":["tampered"]}\n')
        bad = subprocess.run([sys.executable, str(gate), str(cp)], capture_output=True, text=True)
        if bad.returncode == 0 or "hash:trace.json" not in bad.stdout:
            print("tamper test failed")
            print(bad.stdout + bad.stderr)
            return 1
    print("PASS: strict PCSS gate accepts intact evidence and rejects tampering")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
