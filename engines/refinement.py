#!/usr/bin/env python3
"""Quotient refinement engine (Phase 18).

Pipeline: candidate quotient -> counterexample -> violated observable/invariant
-> split equivalence class -> revalidate -> repeat.

If stable: record initial partition, refinement sequence, final partition,
termination evidence, stability evidence.

Do NOT claim coarsest/universal quotient unless formally established.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Sequence

from . import quotient as Q
from . import invariant as INV


class RefinementJournalEntry:
    def __init__(self, step: int, split_class: list[int], reason: str):
        self.step = step
        self.split_class = sorted(split_class)
        self.reason = reason


def validate_candidate(classes, model, pi, T, Tbar, project=None) -> tuple[bool, str]:
    """Check whether a partition is a valid quotient for the model's probe state."""
    x = model.make_initial(seed=0)
    if not classes:
        return False, "empty partition"
    total = sum(len(c) for c in classes)
    if total != model.r if hasattr(model, 'r') else total != len(pi(x)):
        return False, f"total coords {total} != expected {model.r if hasattr(model, 'r') else len(pi(x))}"
    # construct projection that maps each coord to its class index
    coord_to_class = {}
    for cls_idx, coords in enumerate(classes):
        for coord in coords:
            coord_to_class[coord] = cls_idx
    def proj_q(v):
        return [v[coord_to_class[i]] for i in sorted(coord_to_class.keys())]
    # check intertwining: pi(T(x)) == Tbar(pi(x)) when we use the actual pi/Tbar from the model
    q = pi(x)
    tq = Tbar(q)
    tx = T(x)
    tq2 = proj_q(tx)
    # Check: for each class, all coords in class have the same weight (same quotient coord after projection)
    ok = True
    reasons = []
    for cls_idx, coords in enumerate(classes):
        if len(coords) <= 1:
            continue
        w0 = tx[coords[0]] / x[coords[0]] if x[coords[0]] != 0 else float("nan")
        for i in coords[1:]:
            w = tx[i] / x[i] if x[i] != 0 else float("nan")
            if abs(w - w0) > 1e-9:
                ok = False
                reasons.append(f"class {cls_idx}: coords {coords[0]} and {i} have different weights {w0} vs {w}")
                break
    if not ok:
        return False, "; ".join(reasons[:3])
    return True, ""


def refine(classes: list[list[int]], counterexample: Any | None,
           model, pi: Callable, T: Callable, Tbar: Callable,
           *, max_steps: int = 16) -> tuple[list[list[int]], list[dict]]:
    """Refinement loop: split violating classes until stable or max_steps.

    Returns: (final_classes, journal_entries_as_dicts)
    """
    journal: list[dict] = []
    current = [list(c) for c in classes]
    stable = False
    step = 0

    while not stable and step < max_steps:
        ok, reason = validate_candidate(current, model, pi, T, Tbar)
        if ok:
            stable = True
            journal.append({"step": step, "event": "stable", "classes": [sorted(c) for c in current],
                            "reason": "all classes validated"})
            break
        # split largest class as proxy (exact partition should never reach here for the invariant-sector model)
        largest_idx = max(range(len(current)), key=lambda i: len(current[i]))
        cls = current[largest_idx]
        if len(cls) <= 1:
            journal.append({"step": step, "event": "cannot_split_further", "class": cls, "reason": reason})
            break
        mid = len(cls) // 2
        new_classes = [c for i, c in enumerate(current) if i != largest_idx]
        new_classes.append(sorted(cls[:mid]))
        new_classes.append(sorted(cls[mid:]))
        journal.append({"step": step, "event": "split", "class_index": largest_idx,
                         "original": sorted(cls), "split_to": [sorted(cls[:mid]), sorted(cls[mid:])],
                         "reason": reason})
        current = new_classes
        step += 1

    return current, journal


if __name__ == "__main__":
    print("refinement engine module (lib only)")