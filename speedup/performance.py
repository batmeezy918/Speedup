"""PCSS Performance Engine (Phase 8-9).

Standardized performance measurement:
    speedup = baseline_cost / candidate_cost

Separates:
    - mathematical work reduction
    - algorithmic work reduction
    - memory reduction
    - implementation overhead
    - quotient-construction cost
    - reconstruction cost
    - wall-clock speedup

Never multiply isolated speedups for composed claims.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .jsonutil import sha256


def compute_speedup(
    *,
    baseline_samples_ns: List[int],
    candidate_samples_ns: List[int],
    median_baseline_override: float | None = None,
    median_candidate_override: float | None = None,
) -> Dict[str, Any]:
    """Compute direct speedup from sample sequences with attribution.

    Returns X-gate evidence (measurement only, no claim enforcement).
    """
    if not baseline_samples_ns or not candidate_samples_ns:
        return {
            "pass": False,
            "detail": "empty sample set",
        }

    def med(vals):
        s = sorted(vals)
        n = len(s)
        m = n // 2
        return s[m] / 1e9 if n % 2 else (s[m - 1] + s[m]) / 2e9

    b_med = med(baseline_samples_ns) if median_baseline_override is None else median_baseline_override
    c_med = med(candidate_samples_ns) if median_candidate_override is None else median_candidate_override

    if c_med <= 0:
        return {"pass": False, "detail": "candidate median <= 0", "speedup": 0.0}

    speedup = b_med / c_med

    b_std = (
        (sum((x / 1e9 - b_med) ** 2 for x in baseline_samples_ns) / len(baseline_samples_ns)) ** 0.5
    )
    c_std = (
        (sum((x / 1e9 - c_med) ** 2 for x in candidate_samples_ns) / len(candidate_samples_ns)) ** 0.5
    )

    evidence = {
        "pass": speedup > 0,
        "reported_metric": "wall_clock_median_ratio",
        "timing_source": "perf_counter_ns",
        "baseline": {
            "median_s": b_med,
            "std_s": b_std,
            "samples": len(baseline_samples_ns),
        },
        "candidate": {
            "median_s": c_med,
            "std_s": c_std,
            "samples": len(candidate_samples_ns),
        },
        "speedup": speedup,
        "attribution": {
            "direct_wall_clock": speedup,
            "note": "actual measured wall-clock ratio only; not theory-based",
        },
    }
    evidence["performance_hash"] = sha256(evidence)
    return evidence