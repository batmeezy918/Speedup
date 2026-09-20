import json, hashlib, time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from agd_framework.utils import *
from agd_framework.quotient import Phase3Quotient
from agd_framework.decision import Phase4Decision

@dataclass
class FactorizationReport:
    report_id: str
    timestamp: str
    total_states: int
    quotient_classes: int
    validated_states: int
    violations: int
    residual: float
    factorization: Dict[str, str]
    residual_indicator: Dict[str, int]

class Phase6Factorization:
    def __init__(self, quotient: Phase3Quotient,
                 decision: Phase4Decision):
        self.quotient = quotient
        self.decision = decision
        self.factorization: Dict[str, str] = {}

    def factorize(self, states: List) -> FactorizationReport:
        class_decisions: Dict[str, List[str]] = {}
        for state in states:
            cid = self.quotient.get_class(state.state_id)
            if cid is None:
                continue
            dhash = self.decision.get_decision_hash(state.state_id)
            if dhash is None:
                continue
            if cid not in class_decisions:
                class_decisions[cid] = []
            class_decisions[cid].append(dhash)

        violations = 0
        self.factorization = {}
        for cid, dhashes in class_decisions.items():
            unique = set(dhashes)
            if len(unique) == 1:
                self.factorization[cid] = dhashes[0]
            else:
                violations += len(unique) - 1
                self.factorization[cid] = list(unique)[0]

        validated = sum(1 for v in class_decisions.values() if len(set(v)) == 1)
        total = len(class_decisions)
        residual = 0.0 if violations == 0 else violations / max(total, 1)

        residual_indicator = {}
        for state in states:
            cid = self.quotient.get_class(state.state_id)
            if cid and cid in self.factorization:
                dhash = self.decision.get_decision_hash(state.state_id)
                predicted = self.factorization[cid]
                residual_indicator[state.state_id] = 1 if dhash != predicted else 0

        report = FactorizationReport(
            report_id=f"fac_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}",
            timestamp=now_iso(),
            total_states=len(states),
            quotient_classes=len(self.quotient.classes),
            validated_states=validated,
            violations=violations,
            residual=residual,
            factorization=self.factorization,
            residual_indicator=residual_indicator,
        )
        return report
