import json, hashlib, time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from agd_framework.utils import *
from agd_framework.canonical import Phase1Canonical, CanonicalState
from agd_framework.omega import OmegaObservable, OmegaSignature

@dataclass
class QuotientClass:
    class_id: str
    member_count: int
    representative: str
    member_state_ids: List[str]
    omega_signature_hash: str
    source_task_ids: List[str]
    omega_version: str

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class QuotientResult:
    states_count: int
    classes_count: int
    rho_Q: float
    classes: List[dict]
    execution_log: List[dict]

class Phase3Quotient:
    def __init__(self, omega: OmegaObservable):
        self.omega = omega
        self.classes: Dict[str, QuotientClass] = {}
        self.state_to_class: Dict[str, str] = {}
        self.log: List[dict] = []

    def construct(self, states: List[CanonicalState],
                  omega_sigs: Dict[str, OmegaSignature]) -> QuotientResult:
        groups: Dict[str, List[str]] = defaultdict(list)
        state_omegas: Dict[str, str] = {}

        for state in states:
            if state.state_id in omega_sigs:
                sig_hash = omega_sigs[state.state_id].full_signature_hash
            else:
                sig_hash = state.sha256
            state_omegas[state.state_id] = sig_hash
            groups[sig_hash].append(state.state_id)

        self.state_to_class = {}
        for sig_hash, member_ids in groups.items():
            class_id = f"cls_{sig_hash[:16]}"
            rep = member_ids[0]
            task_ids = [self._resolve_task_id(mid) for mid in member_ids]
            qc = QuotientClass(
                class_id=class_id,
                member_count=len(member_ids),
                representative=rep,
                member_state_ids=member_ids,
                omega_signature_hash=sig_hash,
                source_task_ids=task_ids,
                omega_version=self.omega.version,
            )
            self.classes[class_id] = qc
            for mid in member_ids:
                self.state_to_class[mid] = class_id
            self.log.append({
                "action": "class_created",
                "class_id": class_id,
                "members": len(member_ids),
                "omega_hash": sig_hash,
            })

        result = QuotientResult(
            states_count=len(states),
            classes_count=len(self.classes),
            rho_Q=len(states) / max(len(self.classes), 1),
            classes=[c.to_dict() for c in self.classes.values()],
            execution_log=self.log,
        )
        return result

    def _resolve_task_id(self, state_id: str) -> str:
        return state_id

    def get_class(self, state_id: str) -> Optional[str]:
        return self.state_to_class.get(state_id)

    def get_members(self, class_id: str) -> List[str]:
        if class_id in self.classes:
            return self.classes[class_id].member_state_ids
        return []
