#!/usr/bin/env python3
"""Canonical forward quotient engine (gate Q).

Contract (CONSTITUTION.md Article 3):
  Q : E -> O  with  Q(E_candidate) = Q(E_baseline)
  or the explicitly declared tolerance relation for numerical domains.

The engine explicitly represents: equivalence relation, quotient state,
representative, projection, observable set, invariant set.

For exact domains it verifies Q(T(e)) = Tbar(Q(e)) over the executed steps
(intertwining) on the captured traces; for numerical domains it verifies the
declared metric/tolerance relation.

This engine NEVER infers semantic equivalence from equal runtime outputs, and
never manufactures Q, Q^-1, Omega, or L evidence for other gates.
"""
from __future__ import annotations

import pathlib
import sys
from typing import Any, Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from publisher import evidence_lib  # noqa: E402


class QuotientEngine:
    """Forward quotient preservation checker.

    run(project, baseline, candidate, relation, tolerance) -> quotient evidence
    """

    def __init__(self, *, Tbar: Callable | None = None,
                 projection: Callable | None = None,
                 T: Callable | None = None,
                 relation: str = "exact",
                 tolerance: float = 0.0,
                 metric: str = "l2",
                 observable_set: list[str] | None = None,
                 invariant_set: list[str] | None = None):
        self.Tbar = Tbar
        self.projection = projection
        self.T = T
        self.relation = relation
        self.tolerance = tolerance
        self.metric = metric
        self.observable_set = observable_set or []
        self.invariant_set = invariant_set or []

    def forward_equivalent(self, qb: Any, qc: Any) -> bool:
        if self.relation == "exact":
            return qb == qc
        # numerical relation: declared metric/tolerance
        if isinstance(qb, (int, float)) and isinstance(qc, (int, float)):
            return abs(qb - qc) <= self.tolerance
        if isinstance(qb, (list, tuple)) and isinstance(qc, (list, tuple)) and \
                len(qb) == len(qc):
            if self.metric == "max":
                return max((abs(float(a) - float(b)) for a, b in zip(qb, qc)), default=0.0) <= self.tolerance
            return sum((a - b) ** 2 for a, b in zip(qb, qc if False else qc)) ** 0.5 <= self.tolerance
        return False

    def run(self, baseline_states: list[Any], candidate_states: list[Any],
            candidate_projection: Callable | None = None) -> dict:
        if not baseline_states or not candidate_states:
            return {"pass": False, "reason": "empty traces", "forward_residual": None}
        if self.projection is None:
            raise ValueError("QuotientEngine.run requires a projection function")
        cproj = candidate_projection or self.projection
        qb = [self.projection(s) for s in baseline_states]
        qc = [cproj(s) for s in candidate_states]
        if len(qb) != len(qc):
            return {"pass": False, "reason": "trace length mismatch", "forward_residual": None}
        residuals = []
        fails = []
        for i, (a, c) in enumerate(zip(qb, qc)):
            ok = self.forward_equivalent(a, c)
            residuals.append(self._residual(a, c))
            if not ok:
                fails.append(i)
        if self.T is not None and self.Tbar is not None:
            intertwine_fails = []
            for i, s in enumerate(baseline_states[:-1]):
                try:
                    lhs = self.projection(self.T(s))
                    rhs = self.Tbar(self.projection(s))
                    if lhs != rhs:
                        intertwine_fails.append(i)
                except Exception as e:  # noqa: BLE001
                    intertwine_fails.append(f"{i}:{e}")
            if self.relation == "exact" and intertwine_fails:
                return {"pass": False, "reason": f"intertwining failed at steps {intertwine_fails[:5]}",
                        "forward_residual": self._max(residuals), "steps_checked": len(residuals)}
        return {
            "pass": not fails,
            "reason": "" if not fails else f"quotient disagreement at steps {fails[:10]}",
            "relation": self.relation,
            "metric": self.metric,
            "tolerance": self.tolerance,
            "forward_residual": self._max(residuals),
            "steps_checked": len(residuals),
            "observable_set": self.observable_set,
            "invariant_set": self.invariant_set,
            "quotient_states_baseline": qb,
            "quotient_states_candidate": qc,
        }

    def _residual(self, a: Any, c: Any) -> float:
        try:
            if isinstance(a, (int, float)):
                return float(abs(a - c))
            if isinstance(a, (list, tuple)):
                return float(sum(abs(float(x) - float(y)) for x, y in zip(a, c)))
        except Exception:  # noqa: BLE001
            return 0.0 if a == c else float("inf")
        return 0.0 if a == c else float("inf")

    def _max(self, residuals: list[float]) -> float:
        return max(residuals, default=0.0) if residuals else 0.0


def run_quotient(projection, baseline_states, candidate_states, *, Tbar=None, T=None,
                 relation="exact", tolerance=0.0, metric="l2",
                 observable_set=None, invariant_set=None,
                 candidate_projection=None) -> dict:
    """Convenience entry point. Returns a canonical quotient-evidence dict."""
    engine = QuotientEngine(Tbar=Tbar, projection=projection, T=T,
                            relation=relation, tolerance=tolerance, metric=metric,
                            observable_set=observable_set, invariant_set=invariant_set)
    return engine.run(baseline_states, candidate_states,
                      candidate_projection=candidate_projection)


if __name__ == "__main__":
    print("quotient engine module (lib only; use scripts/pcss_native_runner.py)")