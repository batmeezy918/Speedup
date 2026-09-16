#!/usr/bin/env python3
"""Canonical reverse reconstruction engine (gate Q^-1).

Contract (CONSTITUTION.md Article 4):
  d(R(Q(e)), e) <= epsilon
over the declared domain.

Verify:  R : O -> E  reconstructs observable state back to execution state.
Record: maximum error, mean error, tolerance, metric, sample/domain coverage,
reconstruction status.

The reconstruction check MUST be independently computable from the declared
reconstruction definition carried by the scenario. The quotient engine never
certifies its own reconstruction.
"""
from __future__ import annotations

import pathlib
import sys
from typing import Any, Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


class ReconstructionEngine:
    def __init__(self, *, reconstruct: Callable, distance: Callable | None = None,
                 tolerance: float = 0.0, metric: str = "max", domain: str = "declared_sampled"):
        self.reconstruct = reconstruct
        self.distance = distance  # Callable(state, reconstructed) -> float
        self.tolerance = tolerance
        self.metric = metric
        self.domain = domain

    def _default_distance(self, e: Any, e2: Any) -> float:
        """Numeric distance fallback; exact equality => 0.0, mismatch => inf."""
        if e == e2:
            return 0.0
        try:
            if isinstance(e, (int, float)) and isinstance(e2, (int, float)):
                return float(abs(e - e2))
            if isinstance(e, (list, tuple)) and isinstance(e2, (list, tuple)) and len(e) == len(e2):
                return float(max(abs(float(a) - float(b)) for a, b in zip(e, e2)))
        except Exception:  # noqa: BLE001
            pass
        return float("inf")

    def run(self, states: list[Any]) -> dict:
        if not states:
            return {"pass": False, "reason": "empty domain"}
        errors = []
        fails = 0
        for e in states:
            try:
                rec = self.reconstruct(e)
                d = self.distance(e, rec) if self.distance else self._default_distance(e, rec)
            except Exception as ex:  # noqa: BLE001
                d = float("inf")
            errors.append(float(d))
            if d > self.tolerance:
                fails += 1
        max_err = max(errors, default=float("inf"))
        mean_err = sum(errors) / len(errors) if errors else float("inf")
        return {
            "pass": fails == 0,
            "reason": "" if fails == 0 else f"{fails}/{len(states)} states exceed tolerance {self.tolerance}",
            "maximum_error": max_err,
            "mean_error": mean_err,
            "tolerance": self.tolerance,
            "metric": self.metric,
            "domain_coverage": {"states_checked": len(states), "declared_domain": self.domain},
            "reconstruction_status": "PASS" if fails == 0 else "FAIL",
        }


def run_reconstruction(states, reconstruct, *, distance=None, tolerance=0.0,
                       metric="max", domain="declared_sampled") -> dict:
    return ReconstructionEngine(reconstruct=reconstruct, distance=distance,
                                tolerance=tolerance, metric=metric, domain=domain).run(states)