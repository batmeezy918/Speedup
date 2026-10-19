#!/usr/bin/env python3
"""
Explicit safe runner for S6 adaptation on official COCO/BBOB.

Contract:
  - suite = cocoex.Suite("bbob", "", f"dimensions: {D}")
  - for i in range(len(suite)):
        problem = suite.get_problem(i)   # never the Observer
        run_s6_adapt(problem, ...)

Observer has no .dimension. Passing it produces the AttributeError seen in
runs 62-65. This file makes the correct call site the only path.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable

try:
    import cocoex
except ImportError:
    cocoex = None  # type: ignore


def identity_check(dimensions: int = 10) -> dict[str, Any]:
    if cocoex is None:
        raise RuntimeError("cocoex not installed")
    suite = cocoex.Suite("bbob", "", f"dimensions: {dimensions}")
    n = len(suite)
    first = suite.get_problem(0)
    return {
        "suite": "bbob",
        "dimensions": dimensions,
        "problem_count": n,
        "expected": 360 if dimensions == 10 else None,
        "first_id": first.id,
        "first_dimension": first.dimension,
        "cocoex_version": getattr(cocoex, "__version__", "unknown"),
    }


def run_suite_safe(
    run_s6_adapt: Callable[[Any], Any],
    dimensions: int = 10,
    *,
    observer_folder: str | None = None,
) -> list[dict[str, Any]]:
    """
    Iterate by index and pass only Problem objects.

    This is the one-line fix made structural:
        problem = suite.get_problem(i)
        result = run_s6_adapt(problem)
    """
    if cocoex is None:
        raise RuntimeError("cocoex not installed")

    suite = cocoex.Suite("bbob", "", f"dimensions: {dimensions}")
    observer = None
    if observer_folder:
        observer = cocoex.Observer("bbob", f"result_folder: {observer_folder}")

    results: list[dict[str, Any]] = []
    for i in range(len(suite)):
        problem = suite.get_problem(i)          # <-- the fix
        if observer is not None:
            problem.observe_with(observer)

        # Guard: fail closed if anything other than a Problem is ever passed
        if not hasattr(problem, "dimension"):
            raise TypeError(
                f"index {i}: object has no dimension attribute "
                f"(type={type(problem).__name__}). Observer was not passed."
            )

        out = run_s6_adapt(problem)
        results.append({
            "index": i,
            "problem_id": getattr(problem, "id", f"unknown_{i}"),
            "dimension": problem.dimension,
            "result": out,
        })
    return results


def main() -> None:
    check = identity_check()
    print(json.dumps(check, indent=2))
    if check["problem_count"] != 360 and check["dimensions"] == 10:
        print("IDENTITY_FAIL", file=sys.stderr)
        sys.exit(1)
    print("IDENTITY_PASS")
    print("Safe runner ready. Call run_suite_safe(your_run_s6_adapt).")


if __name__ == "__main__":
    main()
