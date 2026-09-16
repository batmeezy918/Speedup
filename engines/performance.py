#!/usr/bin/env python3
"""Canonical performance engine (gate X).

Standardized timing statistics: baseline, candidate, direct speedup =
baseline_cost / candidate_cost; median, p95, p99, repetitions, warmups,
timing source, resource snapshot.

Never multiplies isolated speedups to claim a composed speedup.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
from typing import Any, Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from publisher import evidence_lib  # noqa: E402


def percentile(values: list[float], p: float) -> float:
    return evidence_lib.percentile(values, p)


def median(values: list[float]) -> float:
    return evidence_lib.median(values)


class PerformanceEngine:
    def __init__(self, *, repetitions: int = 30, warmups: int = 0,
                 timing_source: str = "clock_gettime_monotonic",
                 metric: str = "wall_clock_ns"):
        self.repetitions = repetitions
        self.warmups = warmups
        self.timing_source = timing_source
        self.metric = metric

    @staticmethod
    def now() -> float:
        try:
            return time.clock_gettime(time.CLOCK_MONOTONIC)
        except AttributeError:
            return time.perf_counter()

    def measure(self, fn: Callable) -> dict:
        timings = []
        for _ in range(self.repetitions + self.warmups):
            t0 = self.now()
            fn()
            t1 = self.now()
            if _ >= self.warmups:
                timings.append((t1 - t0) * 1e9)  # nanoseconds
        return {
            "timings_ns": timings,
            "median": median(timings),
            "mean": sum(timings) / len(timings) if timings else 0.0,
            "min": min(timings) if timings else 0.0,
            "max": max(timings) if timings else 0.0,
            "p95": percentile(timings, 0.95),
            "p99": percentile(timings, 0.99),
            "samples": len(timings),
            "unit": "ns",
        }

    def compare(self, baseline: dict, candidate: dict) -> dict:
        b = baseline["median"]
        c = candidate["median"]
        speedup = b / c if c > 0 else 0.0
        valid = baseline.get("samples", 0) > 0 and candidate.get("samples", 0) > 0 and c > 0
        passed = valid and speedup > 1.0
        return {
            "baseline_measurement": baseline,
            "candidate_measurement": candidate,
            "direct_speedup": speedup,
            "pass": passed,
            "reason": "" if passed else (
                ("no speedup measured" if valid else "invalid/incomplete timing measurements")
                if valid else "invalid timing (no samples or zero-cost candidate)"),
            "metric": self.metric,
            "repetitions": self.repetitions,
            "warmups": self.warmups,
            "timing_source": self.timing_source,
        }


def run_performance(baseline_fn, candidate_fn, *, repetitions=30, warmups=0,
                    timing_source="clock_gettime_monotonic",
                    metric="wall_clock_ns") -> dict:
    engine = PerformanceEngine(repetitions=repetitions, warmups=warmups,
                               timing_source=timing_source, metric=metric)
    bm = engine.measure(baseline_fn)
    cm = engine.measure(candidate_fn)
    return engine.compare(bm, cm)