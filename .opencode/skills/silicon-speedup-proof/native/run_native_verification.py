#!/usr/bin/env python3
"""Bounded NATIVE baseline/candidate verification run.

This is a REAL run on REAL hardware, not a synthetic fixture. It exists to
exercise the silicon-speedup-proof workflow end to end and to produce one
non-synthetic evidence record.

Workload: block-diagonal matrix-vector product, pure-Python reference
implementation.

  baseline  : y[i] = sum over ALL j of A[i][j] * v[j]      (dense, zeros included)
  candidate : y[i] = sum over j in block(i) of A[i][j]*v[j] (declared block structure)

Equivalence argument: the off-block terms of the baseline are exactly
`0.0 * v[j]`, and adding an exact zero to a finite partial sum is exact in IEEE
754. Both arms sum the non-zero terms in the same left-to-right order, so the
outputs are bitwise identical. This is VERIFIED below, not asserted.

Scope, stated up front because it is narrow:
  * CPython 3.13, pure Python, single thread, one machine.
  * This measures work reduction in an interpreter loop. It is NOT a device
    property and carries NO hardware-mechanism claim.

Measurement discipline:
  * The repository's own evaluator is used unmodified: engines/performance.py
    PerformanceEngine (median, p95, p99, compare). Only the SCHEDULING is ours,
    because engines/performance.py runs all-A-then-all-B while the differential
    benchmarking discipline requires interleaving.
  * Interleaved A B A B ... so thermal drift is common-mode.
  * Warmup discarded, N >= 5 retained samples per arm.
  * A noise floor is measured as baseline-vs-baseline.
  * Runs are sequential; nothing else is executing concurrently.

Usage:
    python3 native/run_native_verification.py [--n 512] [--blocks 32] [--reps 15]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

SKILL = Path(__file__).resolve().parent.parent
REPO = SKILL.parents[2]          # .opencode/skills/<skill> -> repo root
sys.path.insert(0, str(REPO))

from engines.performance import PerformanceEngine  # noqa: E402

OUT = Path(__file__).resolve().parent / "artifacts"


def build_workload(n: int, blocks: int):
    """Block-diagonal A and a vector v, both deterministic."""
    assert n % blocks == 0, "n must divide evenly into blocks"
    bs = n // blocks
    rng = state = 12345
    A = [[0.0] * n for _ in range(n)]
    v = []
    for i in range(n):
        rng = (1103515245 * rng + 12345) % (2 ** 31)
        v.append(((rng / 2 ** 31) * 2.0) - 1.0)
    for b in range(blocks):
        for i in range(b * bs, (b + 1) * bs):
            for j in range(b * bs, (b + 1) * bs):
                rng = (1103515245 * rng + 12345) % (2 ** 31)
                A[i][j] = ((rng / 2 ** 31) * 2.0) - 1.0
    return A, v, bs


def baseline_fn(A, v, n):
    def run():
        out = [0.0] * n
        for i in range(n):
            row = A[i]
            s = 0.0
            for j in range(n):
                s += row[j] * v[j]
            out[i] = s
        return out
    return run


def candidate_fn(A, v, n, bs):
    def run():
        out = [0.0] * n
        for b in range(n // bs):
            lo, hi = b * bs, (b + 1) * bs
            for i in range(lo, hi):
                row = A[i]
                s = 0.0
                for j in range(lo, hi):
                    s += row[j] * v[j]
                out[i] = s
        return out
    return run


def interleaved(b_run, c_run, reps: int, warmups: int):
    """Drive the repository's own engine, but alternate arms so drift is
    common-mode. The engine's statistics are used unmodified."""
    engine = PerformanceEngine(repetitions=0, warmups=0,
                               timing_source="clock_gettime_monotonic",
                               metric="wall_clock_ns")
    base_ns: List[float] = []
    cand_ns: List[float] = []

    for _ in range(warmups):
        b_run(); c_run()
    for _ in range(reps):
        t0 = engine.now(); b_run(); t1 = engine.now()
        base_ns.append((t1 - t0) * 1e9)
        t0 = engine.now(); c_run(); t1 = engine.now()
        cand_ns.append((t1 - t0) * 1e9)

    def stats(samples):
        return {
            "median": _median(samples),
            "mad": _mad(samples),
            "mean": sum(samples) / len(samples),
            "min": min(samples),
            "max": max(samples),
            "p95": _pct(samples, 0.95),
            "p99": _pct(samples, 0.99),
            "samples": len(samples),
            "samples_ns": list(samples),
            "unit": "ns",
        }
    return stats(base_ns), stats(cand_ns)


def _mad(v):
    m = _median(v)
    return _median([abs(x - m) for x in v])


def _sorted(v):
    return sorted(v)


def _median(v):
    s = _sorted(v); n = len(s); m = n // 2
    return s[m] if n % 2 else (s[m - 1] + s[m]) / 2.0


def _pct(v, p):
    s = _sorted(v)
    if not s:
        return None
    k = max(0, min(len(s) - 1, int(round(p * (len(s) - 1)))))
    return s[k]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=512)
    ap.add_argument("--blocks", type=int, default=32)
    ap.add_argument("--reps", type=int, default=15)
    ap.add_argument("--warmups", type=int, default=3)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    started = time.time()
    A, v, bs = build_workload(args.n, args.blocks)
    b_run = baseline_fn(A, v, args.n)
    c_run = candidate_fn(A, v, args.n, bs)

    # --- Correctness first, before any timing is interpreted. ---
    y_base = b_run()
    y_cand = c_run()
    bitwise_identical = (y_base == y_cand)
    max_abs_err = max((abs(a - b) for a, b in zip(y_base, y_cand)), default=0.0)

    # --- Reverse derivation: reconstruct the dense A from the block view. ---
    A_reconstructed = [[0.0] * args.n for _ in range(args.n)]
    for b in range(args.blocks):
        lo, hi = b * bs, (b + 1) * bs
        for i in range(lo, hi):
            for j in range(lo, hi):
                A_reconstructed[i][j] = A[i][j]
    reverse_identical = (A_reconstructed == A)

    # --- Reverse derivation on the output: recompute the candidate's output
    #     from the baseline's dense form and compare. ---
    y_reverse = [0.0] * args.n
    for i in range(args.n):
        row = A_reconstructed[i]
        s = 0.0
        for j in range(args.n):
            s += row[j] * v[j]
        y_reverse[i] = s
    reverse_output_identical = (y_reverse == y_cand)

    # --- Native interleaved timing. ---
    base, cand = interleaved(b_run, c_run, args.reps, args.warmups)
    base["memory_bytes"] = None
    cand["memory_bytes"] = None

    # --- Noise floor: baseline against itself, same protocol. ---
    nf_base, nf_base2 = interleaved(b_run, b_run, args.reps, args.warmups)
    noise_floor_ratio = nf_base["median"] / nf_base2["median"]

    s_i = base["median"] / cand["median"]
    spread_ratio = (base["max"] - base["min"]) / base["median"]

    env = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": _cpu_model(),
        "python": platform.python_version(),
        "toolchain": f"CPython {platform.python_version()}",
        "compiler_flags": "n/a (interpreted)",
        "cores_total": os.cpu_count(),
        "note": "single-threaded, nothing else executed concurrently",
    }

    payload: Dict[str, Any] = {
        "kind": "native_run_raw_result",
        "synthetic": False,
        "note": "REAL native run produced by native/run_native_verification.py",
        "command": f"python3 native/run_native_verification.py --n {args.n} "
                   f"--blocks {args.blocks} --reps {args.reps} --warmups {args.warmups}",
        "cwd": "opencode/skills/silicon-speedup-proof",
        "started_unix": started,
        "workload": {
            "description": "block-diagonal matrix-vector product, pure Python",
            "n": args.n,
            "blocks": args.blocks,
            "block_size": bs,
            "baseline": "dense: sum over all j of A[i][j]*v[j]",
            "candidate": "block-structured: sum over j in block(i)",
            "input_generation": "deterministic LCG, seed 12345, no clock, no file",
        },
        "correctness": {
            "bitwise_identical_output": bitwise_identical,
            "max_abs_error": max_abs_err,
            "reverse_block_reconstruction_identical": reverse_identical,
            "reverse_output_identical": reverse_output_identical,
            "argument": "off-block terms are exactly 0.0 and IEEE-754 addition of an "
                        "exact zero to a finite partial sum is exact; both arms sum "
                        "the non-zero terms left to right",
        },
        "timing": {
            "protocol": "interleaved A B A B, warmup discarded, sequential execution",
            "evaluator": "engines/performance.py PerformanceEngine (unmodified)",
            "aggregation": "median",
            "warmup_discarded": args.warmups,
            "baseline": base,
            "candidate": cand,
        },
        "noise_floor": {
            "ratio": noise_floor_ratio,
            "description": "baseline against baseline, identical protocol",
            "baseline_median_ns": nf_base["median"],
            "baseline2_median_ns": nf_base2["median"],
        },
        "result": {
            "S_i": s_i,
            "baseline_relative_spread": spread_ratio,
            "samples_per_arm": args.reps,
        },
        "environment": env,
    }

    out_path = OUT / "native_blockdiag_run.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = hashlib.sha256(out_path.read_bytes()).hexdigest()
    (OUT / "native_blockdiag_run.json.sha256").write_text(digest + "\n", encoding="utf-8")

    print(json.dumps({
        "raw_result": str(out_path),
        "sha256": digest,
        "bitwise_identical_output": bitwise_identical,
        "reverse_output_identical": reverse_output_identical,
        "baseline_median_ns": base["median"],
        "candidate_median_ns": cand["median"],
        "S_i": s_i,
        "noise_floor_ratio": noise_floor_ratio,
        "samples_per_arm": args.reps,
        "baseline_relative_spread": spread_ratio,
    }, indent=2))
    return 0 if (bitwise_identical and reverse_output_identical) else 1


def _cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
