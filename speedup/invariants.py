"""PCSS Invariant Engine (Phase 7).

Omega(e)
Verify preservation:
    Omega(e_candidate) == Omega(e_baseline)
or the explicitly declared numerical relation.

The invariant definition is part of the scenario identity.  No
undocumented invariant may be silently substituted.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .jsonutil import sha256


def verify_invariants(
    *,
    baseline_invariants: Dict[str, float],
    candidate_invariants: Dict[str, float],
    relation: str = "equality",
    tolerance: float | None = None,
    declared_names: List[str] | None = None,
) -> Dict[str, Any]:
    """Compare invariant signatures between baseline and candidate.

    relation: 'equality' (default) or 'numerical_relation' with tolerance.
    """
    if declared_names is None:
        declared_names = list(baseline_invariants.keys())

    missing = [n for n in declared_names if n not in candidate_invariants]
    if missing:
        return {
            "pass": False,
            "detail": f"candidate missing declared invariants: {missing}",
        }

    tol = 1e-12 if tolerance is None else float(tolerance)
    violations: List[Dict[str, float]] = []
    for name in declared_names:
        b = float(baseline_invariants[name])
        c = float(candidate_invariants[name])
        if relation == "equality":
            err = abs(b - c)
        else:
            denom = max(abs(b), abs(c), 1e-15)
            err = abs(b - c) / denom
        if err > tol:
            violations.append({"invariant": name, "baseline": b, "candidate": c, "error": err})

    evidence = {
        "pass": not violations,
        "relation": relation,
        "tolerance": tol,
        "violations": violations,
        "declared": declared_names,
    }
    evidence["invariant_hash"] = sha256(evidence)
    return evidence