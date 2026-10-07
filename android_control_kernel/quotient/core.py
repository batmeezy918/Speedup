"""Quotient/descent primitives. Runtime witnesses are separate from proofs."""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Tuple

@dataclass(frozen=True)
class Invariant:
    name: str
    predicate: Callable[[Any], bool]

@dataclass(frozen=True)
class SpeedupOperator:
    operator_id: str
    domain: str
    transform: Callable[[Any], Any]
    invariants: Tuple[Invariant, ...]
    evidence_class: str  # proven | measured | candidate

    def admissible(self, state: Any) -> bool:
        return all(inv.predicate(state) for inv in self.invariants)

def descend(op: SpeedupOperator, state: Any) -> Any:
    if not op.admissible(state):
        raise ValueError(f"operator {op.operator_id} is not admissible")
    return op.transform(state)
