"""PCSS Reconstruction Engine (Phase 6).

R : O -> E
Verify  d(R(Q(e)), e) <= epsilon  over the declared domain.
Record max error, mean error, tolerance, metric, domain coverage and status.

The quotient implementation must NOT be allowed to certify its own
reconstruction: reconstruction evidence comes from an independent check
of states against the quotient representative.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .jsonutil import sha256


def verify_reconstruction(
    *,
    original_states: List[Any],
    reconstructed_states: List[Any],
    metric: str,
    tolerance: float,
    domain: str,
    independent: bool = True,
) -> Dict[str, Any]:
    """Compare original states with reconstructed states.

    independent=True records that the reconstruction check is executed by a
    separate harness rather than the quotient construction itself.
    """
    if not independent:
        return {
            "pass": False,
            "detail": "reconstruction evidence must be independently checked",
        }

    if len(original_states) != len(reconstructed_states):
        return {
            "pass": False,
            "detail": f"state count mismatch: {len(original_states)} vs {len(reconstructed_states)}",
        }

    errors: List[float] = []
    for o, r in zip(original_states, reconstructed_states):
        o = float(o)
        r = float(r)
        if metric in ("l1", "max_abs"):
            errors.append(abs(o - r))
        else:  # relative
            denom = max(abs(o), abs(r), 1e-15)
            errors.append(abs(o - r) / denom)

    max_err = max(errors) if errors else float("inf")
    mean_err = sum(errors) / len(errors) if errors else float("inf")
    r_pass = max_err <= tolerance

    evidence = {
        "pass": r_pass,
        "metric": metric,
        "tolerance": tolerance,
        "max_error": max_err,
        "mean_error": mean_err,
        "domain": domain,
        "sample_count": len(errors),
    }
    evidence["reconstruction_hash"] = sha256(evidence)
    return evidence