#!/usr/bin/env python3
"""Exhaustively exercise all 2^7 PCSS gate combinations.

This proves the boolean decision surface of strict_gate.py is fail-closed:
exactly the all-true vector can pass when artifact hashes and required fields
are valid; every other gate vector must quarantine.
"""
from __future__ import annotations
import hashlib
import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATES = ("integrity", "reproducibility", "quotient_forward", "reconstruction_reverse", "invariants", "performance", "lean")
BASE = {
    "scenario.json": b'{"scenario":"matrix"}\n',
    "environment.json": b'{"environment":"matrix"}\n',
    "trace.json": b'{"runs":[]}\n',
    "performance.json": b'{"metric":"wall_ns","median_baseline":2,"median_candidate":1,"speedup_measured":2,"samples":1}\n',
}

def put(d: Path, name: str, data: bytes) -> str:
    (d / name).write_bytes(data)
    return hashlib.sha256(data).hexdigest()

def certificate(d: Path, values: tuple[bool, ...]) -> Path:
    hashes = {name: put(d, name, data) for name, data in BASE.items()}
    cert = {
        "run_id":"matrix",
        "scenario_hash":hashes["scenario.json"],
        "source_hash":"source",
        "input_hash":"input",
        "environment_hash":hashes["environment.json"],
        "trace_hash":hashes["trace.json"],
        "performance_hash":hashes["performance.json"],
        "artifacts":hashes,
        "performance":{"metric":"wall_ns","median_baseline":2,"median_candidate":1,"speedup_measured":2,"samples":1},
        "quotient_hash":"q", "reverse_hash":"r", "invariants_hash":"i", "proof_hash":"p",
        "gates":dict(zip(GATES, values)),
    }
    p = d / "certificate.json"
    p.write_text(json.dumps(cert), encoding="utf-8")
    return p

def main() -> int:
    gate = ROOT / "publisher" / "strict_gate.py"
    passed = 0
    rejected = 0
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        for values in itertools.product((False, True), repeat=len(GATES)):
            cp = certificate(d, values)
            result = subprocess.run([sys.executable, str(gate), str(cp)], capture_output=True, text=True)
            expected = all(values)
            actual = result.returncode == 0
            if actual != expected:
                print("FAIL: gate vector", values, "returned", result.returncode)
                print(result.stdout, result.stderr)
                return 1
            if actual: passed += 1
            else: rejected += 1
    print(f"PASS: exhaustive PCSS gate matrix; accepted={passed} rejected={rejected} total={passed+rejected}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
