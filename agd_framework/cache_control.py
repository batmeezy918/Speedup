import json, hashlib, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from agd_framework.utils import *
from agd_framework.quotient import Phase3Quotient
from agd_framework.canonical import CanonicalState
from agd_framework.decision import Phase4Decision, DecisionResult

class Phase11CacheControl:
    def __init__(self):
        self.exact_classes: Dict[str, List[str]] = {}
        self.structural_classes: Dict[str, List[str]] = {}
        self.agd_classes: Dict[str, List[str]] = {}
        self.results: dict = {}

    def compute_exact_cache(self, states: List[CanonicalState]) -> int:
        groups: Dict[str, List[str]] = {}
        for s in states:
            key = s.sha256
            if key not in groups:
                groups[key] = []
            groups[key].append(s.state_id)
        self.exact_classes = groups
        return len(groups)

    def compute_structural_dedup(self, states: List[CanonicalState]) -> int:
        groups: Dict[str, List[str]] = {}
        for s in states:
            key = s.task_id
            if key not in groups:
                groups[key] = []
            groups[key].append(s.state_id)
        self.structural_classes = groups
        return len(groups)

    def compute_agd_quotient(self, quotient: Phase3Quotient) -> int:
        groups: Dict[str, List[str]] = {}
        for cid, cls in quotient.classes.items():
            key = cid
            groups[key] = cls.member_state_ids
        self.agd_classes = groups
        return len(groups)

    def compare(self, states: List[CanonicalState],
                quotient: Phase3Quotient,
                decision: Phase4Decision) -> dict:
        exact_n = self.compute_exact_cache(states)
        struct_n = self.compute_structural_dedup(states)
        agd_n = self.compute_agd_quotient(quotient)

        def residual(class_groups, decision):
            total = 0
            for key, members in class_groups.items():
                if len(members) >= 2:
                    hashes = set()
                    for m in members:
                        d = decision.decisions.get(m)
                        if d:
                            hashes.add(d.decision_hash)
                    if len(hashes) > 1:
                        total += 1
            return total

        self.results = {
            "exact_cache_classes": exact_n,
            "conventional_classes": struct_n,
            "AGD_classes": agd_n,
            "exact_residual": residual(self.exact_classes, decision),
            "structural_residual": residual(self.structural_classes, decision),
            "AGD_residual": residual(self.agd_classes, decision),
        }
        return self.results
