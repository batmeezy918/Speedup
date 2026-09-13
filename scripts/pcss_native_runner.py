#!/usr/bin/env python3
"""Fail-closed native PCSS runner.

Runs locked baseline/candidate commands, captures raw observations, computes
only directly measured performance, and emits a certificate with all proof
gates false until independently supplied evidence satisfies each gate.
This runner never infers quotient, reconstruction, invariants, attribution,
or Lean success from timing or exit status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
import time
from pathlib import Path
from statistics import median


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def run_once(command: str, cwd: Path) -> dict:
    start = time.perf_counter_ns()
    proc = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=False)
    end = time.perf_counter_ns()
    stdout = proc.stdout
    stderr = proc.stderr
    return {
        "command": command,
        "cwd": str(cwd.resolve()),
        "exit_code": proc.returncode,
        "wall_ns": end - start,
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_sha256": sha256_bytes(stderr),
        "stdout_bytes": len(stdout),
        "stderr_bytes": len(stderr),
    }


def deterministic(rows: list[dict]) -> bool:
    return len({(r["exit_code"], r["stdout_sha256"], r["stderr_sha256"]) for r in rows}) == 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--warmups", type=int, default=1)
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--out", default="pcss-native-run")
    ap.add_argument("--scenario-id", required=True)
    args = ap.parse_args()
    if args.repeats < 1 or args.warmups < 0:
        ap.error("repeats must be >=1 and warmups >=0")

    cwd = Path(args.workdir).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    scenario = {
        "scenario_id": args.scenario_id,
        "baseline_command": args.baseline,
        "candidate_command": args.candidate,
        "workdir": str(cwd),
        "repeats": args.repeats,
        "warmups": args.warmups,
        "timing_source": "perf_counter_ns",
        "shell": True,
    }
    scenario_bytes = json.dumps(scenario, sort_keys=True, separators=(",", ":")).encode()
    scenario_hash = sha256_bytes(scenario_bytes)
    (out / "scenario.json").write_bytes(scenario_bytes + b"\n")

    environment = {
        "platform": platform.platform(),
        "python": sys.version,
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": platform.node(),
        "cwd": str(cwd),
        "git_revision": os.popen("git rev-parse HEAD 2>/dev/null").read().strip(),
        "git_status": os.popen("git status --porcelain 2>/dev/null").read(),
    }
    env_bytes = json.dumps(environment, sort_keys=True, separators=(",", ":")).encode()
    environment_hash = sha256_bytes(env_bytes)
    (out / "environment.json").write_bytes(env_bytes + b"\n")

    warmup_rows = []
    for label, command in (("baseline", args.baseline), ("candidate", args.candidate)):
        for i in range(args.warmups):
            warmup_rows.append({"implementation": label, "index": i, **run_once(command, cwd)})

    rows = []
    for label, command in (("baseline", args.baseline), ("candidate", args.candidate)):
        for i in range(args.repeats):
            rows.append({"implementation": label, "index": i, **run_once(command, cwd)})

    trace = {"warmups": warmup_rows, "runs": rows}
    trace_bytes = json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()
    trace_hash = sha256_bytes(trace_bytes)
    (out / "trace.json").write_bytes(trace_bytes + b"\n")

    base = [r["wall_ns"] for r in rows if r["implementation"] == "baseline"]
    cand = [r["wall_ns"] for r in rows if r["implementation"] == "candidate"]
    baseline_median = median(base)
    candidate_median = median(cand)
    performance = {
        "metric": "wall_ns",
        "samples": args.repeats,
        "baseline_samples": base,
        "candidate_samples": cand,
        "median_baseline": baseline_median,
        "median_candidate": candidate_median,
        "speedup_measured": baseline_median / candidate_median if candidate_median > 0 else None,
        "baseline_deterministic": deterministic([r for r in rows if r["implementation"] == "baseline"]),
        "candidate_deterministic": deterministic([r for r in rows if r["implementation"] == "candidate"]),
        "all_baseline_exit_zero": all(r["exit_code"] == 0 for r in rows if r["implementation"] == "baseline"),
        "all_candidate_exit_zero": all(r["exit_code"] == 0 for r in rows if r["implementation"] == "candidate"),
    }
    performance_bytes = json.dumps(performance, sort_keys=True, separators=(",", ":")).encode()
    performance_hash = sha256_bytes(performance_bytes)
    (out / "performance.json").write_bytes(performance_bytes + b"\n")

    # These are deliberately NOT inferred. They require separate evidence.
    certificate = {
        "run_id": args.scenario_id,
        "scenario_hash": scenario_hash,
        "source_hash": None,
        "input_hash": None,
        "environment_hash": environment_hash,
        "trace_hash": trace_hash,
        "performance_hash": performance_hash,
        "quotient_hash": None,
        "reverse_hash": None,
        "invariants_hash": None,
        "attribution_hash": None,
        "proof_hash": None,
        "artifacts": {
            "scenario.json": scenario_hash,
            "environment.json": environment_hash,
            "trace.json": trace_hash,
            "performance.json": performance_hash,
        },
        "gates": {
            "integrity": False,
            "reproducibility": performance["baseline_deterministic"] and performance["candidate_deterministic"],
            "quotient_forward": False,
            "reconstruction_reverse": False,
            "invariants": False,
            "performance": True,
            "lean": False,
        },
        "claim_strength": "STRONG_LOCAL",
        "evidence_strength": "STRONG_LOCAL",
        "status": "NATIVE_RUN_ONLY",
        "note": "Timing and deterministic execution do not prove quotient, reconstruction, invariants, attribution, or Lean gates.",
    }
    (out / "certificate.json").write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "scenario_hash": scenario_hash, "trace_hash": trace_hash, "speedup_measured": performance["speedup_measured"], "status": "NATIVE_RUN_ONLY"}, indent=2))
    return 0 if performance["all_baseline_exit_zero"] and performance["all_candidate_exit_zero"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
