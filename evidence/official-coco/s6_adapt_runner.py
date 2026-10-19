#!/usr/bin/env python3
"""Runner: identity check + safe suite execution + evidence output.

Wires run_s6_adapt (s6_adapt.py) through run_suite_safe
(s6_adapt_safe_runner.py). The Observer is used only for COCO logging via
observe_with; it is never an argument to the optimizer.

Evidence class: FORMAL_PARTIAL. No VERIFIED speedup / wall-clock / B(H) claims.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from s6_adapt import run_s6_adapt
from s6_adapt_safe_runner import identity_check, run_suite_safe


def main() -> None:
    parser = argparse.ArgumentParser(description="S6 diagonal-adaptation COCO runner")
    parser.add_argument("--dimensions", type=int, default=10)
    parser.add_argument("--budget", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260810)
    parser.add_argument("--observer-folder", type=str, default="S6_ADAPT_OBS")
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()

    # 1. Identity check (fail closed)
    check = identity_check(args.dimensions)
    print(json.dumps(check, indent=2))
    if args.dimensions == 10 and check["problem_count"] != 360:
        print("IDENTITY_FAIL", file=sys.stderr)
        sys.exit(1)
    print("IDENTITY_PASS")

    # 2. Run suite through the safe contract
    t0 = time.perf_counter_ns()
    results = run_suite_safe(
        lambda problem: run_s6_adapt(problem, seed=args.seed, budget=args.budget),
        dimensions=args.dimensions,
        observer_folder=args.observer_folder,
    )
    t_wall = time.perf_counter_ns() - t0

    # 3. Aggregate
    n = len(results)
    best_fs = [r["result"]["best_f"] for r in results]
    acc_rates = [r["result"]["acceptance_rate"] for r in results]
    inv_ok = sum(1 for r in results if r["result"]["omega_equal"] and r["result"]["xi_equal"])

    summary = {
        "suite": "bbob",
        "dimensions": args.dimensions,
        "budget": args.budget,
        "seed": args.seed,
        "problem_count": n,
        "expected_problem_count": 360 if args.dimensions == 10 else None,
        "suite_wall_time_ns": t_wall,
        "best_f_min": min(best_fs) if best_fs else None,
        "best_f_median": sorted(best_fs)[n // 2] if best_fs else None,
        "mean_acceptance_rate": sum(acc_rates) / max(n, 1),
        "invariant_preservation_count": inv_ok,
        "invariant_preservation_rate": inv_ok / max(n, 1),
        "evidence_class": "FORMAL_PARTIAL",
        "optimizer": "s6_adapt (diagonal adaptation)",
        "call_contract": "suite.get_problem(i) -> run_s6_adapt(problem)",
        "observer_role": "observe_with logging only; never passed to optimizer",
        "results": results,
    }

    out_dir = args.output_dir or f"evidence/official-coco/s6-adapt-{int(time.time())}"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "s6_adapt_summary.json")
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2))
    print(f"WROTE {path}")
    print(f"PROBLEM_COUNT={n}")
    if args.dimensions == 10 and n != 360:
        sys.exit(1)


if __name__ == "__main__":
    main()
