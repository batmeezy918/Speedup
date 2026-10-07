"""Compact registry for executable speedup operators."""
from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class OperatorRecord:
    operator_id: str
    domain: str
    multiplier: float | None
    evidence_class: str
    witness: str
    status: str = "registered"

class OperatorRegistry:
    def __init__(self) -> None:
        self._items: Dict[str, OperatorRecord] = {}

    def register(self, record: OperatorRecord) -> None:
        self._items[record.operator_id] = record

    def get(self, operator_id: str) -> OperatorRecord | None:
        return self._items.get(operator_id)

    def export(self) -> Dict[str, Any]:
        return {k: asdict(v) for k, v in self._items.items()}
