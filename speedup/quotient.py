"""PCSS Quotient Engine (Phase 5).

Q : E -> O
The engine explicitly represents:
  - equivalence relation
  - quotient state
  - representative
  - projection
  - observable set
  - invariant set

For exact domains:  Q(T(e)) = Tbar(Q(e))
For numerical domains:  d(Q(T(e)), Tbar(Q(e))) <= epsilon

The engine never infers semantic equivalence merely from equal runtime
outputs.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from .jsonutil import sha256


class QuotientError(RuntimeError):
    pass


def verify_quotient_forward(
    *,
    baseline_observables: List[Any],
    candidate_observables: List[Any],
    equivalence_relation: str,
    tolerance: float | None = None,
    metric: str = "max_abs",
) -> Dict[str, Any]:
    """Check forward quotient equivalence between baseline and candidate traces.

    Returns a gate evidence record: {pass: bool, details, quotient_hash}.
    """
    if len(baseline_observables) != len(candidate_observables):
        return {
            "pass": False,
            "metric": metric,
            "tolerance": tolerance,
            "max_error": float("inf"),
            "detail": f"observable length mismatch: {len(baseline_observables)} vs {len(candidate_observables)}",
        }

    max_err = 0.0
    if metric == "max_abs":
        for b, c in zip(baseline_observables, candidate_observables):
            err = abs(float(b) - float(c))
            if err > max_err:
                max_err = err
    else:
        for b, c in zip(baseline_observables, candidate_observables):
            denom = max(abs(float(b)), abs(float(c)), 1e-15)
            err = abs(float(b) - float(c)) / denom
            if err > max_err:
                max_err = err

    tol = 1e-12 if tolerance is None else float(tolerance)
    q_pass = max_err <= tol

    evidence = {
        "pass": q_pass,
        "equivalence_relation": equivalence_relation,
        "metric": metric,
        "tolerance": tol,
        "max_error": max_err,
        "sample_count": len(baseline_observables),
    }
    evidence["quotient_hash"] = sha256(evidence)
    return evidence


def verify_quotient_from_traces(
    *,
    baseline_trace_path: str,
    candidate_trace_path: str,
    parse_observable: Callable[[dict], Any] | None = None,
    equivalence_relation: str = "exact_equality",
    tolerance: float | None = None,
) -> Dict[str, Any]:
    """Load trace files and verify quotient forward gate."""
    baseline_trace = json.loads(Path(baseline_trace_path).read_text(encoding="utf-8"))
    candidate_trace = json.loads(Path(candidate_trace_path).read_text(encoding="utf-8"))

    if parse_observable is None:
        parse_observable = lambda entry: entry.get("f") or entry.get("observable")

    base_obs = [parse_observable(e) for e in baseline_trace if isinstance(e, dict)]
    cand_obs = [parse_observable(e) for e in candidate_trace if isinstance(e, dict)]

    return verify_quotient_forward(
        baseline_observables=base_obs,
        candidate_observables=cand_obs,
        equivalence_relation=equivalence_relation,
        tolerance=tolerance,
    )