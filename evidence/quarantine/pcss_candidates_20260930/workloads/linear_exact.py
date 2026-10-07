#!/usr/bin/env python3
"""Linear exact quotient — first fully closed reference primitive (Phase 10).

State model (exact invariant sector):
    full state   x = (u, v) with u in R^r (reduced coords), v in R^c (constraint coords)
    constraint   v = M u        (M : c x r, fixed, seeded)   -- exact invariant manifold
    full op      T(u, v) = (A u, M (A u))                   -- preserves the manifold
    reduced op   Tbar(q)   = A q                             (A : r x r, fixed, seeded)
    projection   pi(u, v)  = u
    section      sigma(q)  = (q, M q)                        (pi(sigma(q)) = q  exactly)
    observable   Obs(x)    = h(u)                            (depends on reduced coords only)

Exact relations (real arithmetic):
    pi(T(x))       = Tbar(pi(x))
    pi(sigma(q))   = q
    Obs(T^n(x))    = ObsBar(Tbar^n(pi(x)))   with ObsBar(q) = h(q)

The workload is deterministic: matrices A and M are derived from the seed by
a fixed PRNG, so two runs with the same seed produce identical observables.

Modes:
    --mode baseline   evaluate full operator T and emit observables per step
    --mode candidate  evaluate reduced operator Tbar and emit observables

Emitted observables are the same for both modes (by construction), letting
the quotient engine verify forward equivalence and the reconstruction engine
verify pi(sigma(q)) = q independently.
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np


def build_operators(d: int, r: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    c = d - r
    q = max(1, int(np.sqrt(r)))
    A = rng.standard_normal((r, r))
    M = rng.standard_normal((c, r))
    return A, M


def op_count(d: int, r: int) -> dict:
    c = d - r
    return {
        "full_multiplies": r * r + c * r,
        "reduced_multiplies": r * r,
        "ratio": (r * r + c * r) / max(r * r, 1),
    }


def run_baseline(d: int, r: int, seed: int, steps: int) -> list[dict]:
    A, M = build_operators(d, r, seed)
    rng = np.random.default_rng(seed ^ 0x5A5A5A5A)
    u = rng.standard_normal(r)
    v = M @ u
    obs = []
    for step in range(steps):
        t0 = time.perf_counter_ns()
        u_next = A @ u
        v_next = M @ u_next
        elapsed = time.perf_counter_ns() - t0
        u, v = u_next, v_next
        obs.append({
            "step": step,
            "f": float(np.sum(u * u)),
            "omega": float(np.abs(np.sum(u))),
            "elapsed_ns": elapsed,
        })
    return obs


def run_candidate(d: int, r: int, seed: int, steps: int) -> list[dict]:
    A, _M = build_operators(d, r, seed)
    rng = np.random.default_rng(seed ^ 0x5A5A5A5A)
    u = rng.standard_normal(r)
    obs = []
    for step in range(steps):
        t0 = time.perf_counter_ns()
        u = A @ u
        elapsed = time.perf_counter_ns() - t0
        obs.append({
            "step": step,
            "f": float(np.sum(u * u)),
            "omega": float(np.abs(np.sum(u))),
            "elapsed_ns": elapsed,
        })
    return obs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["baseline", "candidate"])
    ap.add_argument("--d", type=int, default=1_000_000)
    ap.add_argument("--r", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20260810)
    ap.add_argument("--steps", type=int, default=8)
    args = ap.parse_args()

    if args.r <= 0 or args.d <= args.r:
        raise SystemExit("need 0 < r < d")

    record = {
        "workload": "linear_exact_quotient",
        "mode": args.mode,
        "d": args.d,
        "r": args.r,
        "seed": args.seed,
        "steps": args.steps,
        "op_count": op_count(args.d, args.r),
        "observables": (
            run_baseline(args.d, args.r, args.seed, args.steps)
            if args.mode == "baseline"
            else run_candidate(args.d, args.r, args.seed, args.steps)
        ),
    }
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())