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
        cert = {
            "run_id": "gate-regression",
            "scenario_hash": artifacts["scenario.json"],
            "source_hash": "source",
            "input_hash": "input",
            "environment_hash": artifacts["environment.json"],
            "trace_hash": artifacts["trace.json"],
            "performance_hash": artifacts["performance.json"],
            "artifacts": artifacts,
            "performance": {"metric":"wall_ns","median_baseline":2,"median_candidate":1,"speedup_measured":2,"samples":1},
            "gates": {g: True for g in ("integrity","reproducibility","quotient_forward","reconstruction_reverse","invariants","performance","lean")},
            "quotient_hash": "q", "reverse_hash": "r", "invariants_hash": "i", "proof_hash": "p",
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
