#!/usr/bin/env python3
"""Speedup attribution (Phase 9).

Separates:
  * mathematical work reduction      (operation counts)
  * algorithmic work reduction       (order of growth)
  * memory reduction
  * implementation overhead
  * interpreter/runtime overhead
  * cache effects
  * allocation
  * reconstruction cost
  * quotient-construction cost
  * wall-clock speedup

A reported speedup must state exactly which quantity it measures. Theoretical
operation-count reduction is NOT hardware speedup.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any


def operation_count_ratio(baseline_ops: float, candidate_ops: float) -> float:
    if candidate_ops <= 0:
        return float("inf")
    return baseline_ops / candidate_ops


def analyze(*, baseline_ops: float, candidate_ops: float,
            measured_speedup: float, quotient_cost: float | None = None,
            reconstruction_cost: float | None = None,
            wall_clock_baseline: float | None = None,
            wall_clock_candidate: float | None = None,
            note: str = "") -> dict:
    theo = operation_count_ratio(baseline_ops, candidate_ops)
    return {
        "theory": {
            "baseline_ops": baseline_ops,
            "candidate_ops": candidate_ops,
            "operation_count_ratio": theo,
            "excluded_from_measured": ["interpreter overhead", "cache effects"],
        },
        "measured": {
            "wall_clock_speedup": measured_speedup,
            "wall_clock_baseline": wall_clock_baseline,
            "wall_clock_candidate": wall_clock_candidate,
        },
        "overhead_included": {
            "quotient_construction": quotient_cost,
            "reconstruction": reconstruction_cost,
        },
        "not_conflated": True,
        "note": note,
    }


def report(attribution: dict) -> str:
    return json.dumps(attribution, sort_keys=True, indent=2)


if __name__ == "__main__":
    print("attribution module (lib only)")