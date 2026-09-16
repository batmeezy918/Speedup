#!/usr/bin/env python3
"""Canonical invariant engine (gate Omega).

Contract (CONSTITUTION.md Article 5):
  Omega(e_candidate) == Omega(e_baseline)
or the explicitly declared numerical relation.

The invariant definition is part of the scenario identity: the engine reads the
invariant definition from the scenario that generated the traces. No
undocumented invariant may be silently substituted.
"""
from __future__ import annotations

import pathlib
import sys
from typing import Any, Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


class InvariantEngine:
    def __init__(self, *, invariant: Callable, relation: str = "exact",
                 tolerance: float = 0.0, name: str = "declared"):
        self.invariant = invariant
        self.relation = relation
        self.tolerance = tolerance
        self.name = name

    def check(self, sig_b: Any, sig_c: Any) -> bool:
        if self.relation == "exact":
            return sig_b == sig_c
        if isinstance(sig_b, (int, float)) and isinstance(sig_c, (int, float)):
            return abs(sig_b - sig_c) <= self.tolerance
        return False

    def run(self, baseline_states: list[Any], candidate_states: list[Any]) -> dict:
        b_sig = self.invariant(baseline_states[-1]) if baseline_states else None
        c_sig = self.invariant(candidate_states[-1]) if candidate_states else None
        b_sigs = [self.invariant(s) for s in baseline_states]
        c_sigs = [self.invariant(s) for s in candidate_states]
        ok = self.check(b_sig, c_sig) and all(self.check(x, y) for x, y in zip(b_sigs, c_sigs))
        return {
            "pass": bool(ok),
            "reason": "" if ok else "invariant signature disagreement",
            "invariant_name": self.name,
            "relation": self.relation,
            "tolerance": self.tolerance,
            "baseline_signature": b_sig,
            "candidate_signature": c_sig,
            "signature_steps_checked": min(len(b_sigs), len(c_sigs)),
        }


def run_invariant(baseline_states, candidate_states, invariant, *, name="declared",
                  relation="exact", tolerance=0.0) -> dict:
    return InvariantEngine(invariant=invariant, relation=relation, tolerance=tolerance,
                           name=name).run(baseline_states, candidate_states)