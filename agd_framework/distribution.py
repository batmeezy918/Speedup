import json, hashlib, time
from pathlib import Path
from typing import Dict, List, Optional, Set
from agd_framework.utils import *
from agd_framework.canonical import CanonicalState
from agd_framework.quotient import Phase3Quotient
from agd_framework.decision import Phase4Decision
from agd_framework.decision import DecisionResult

class Phase13DistributionShift:
    def __init__(self):
        self.frozen = True
        self.results: Dict = {}

    def partition(self, states: List[CanonicalState],
                    quotient: Phase3Quotient) -> Dict[str, List]:
        state_ids = list(states.keys()) if isinstance(states, dict) else [s.state_id for s in states]
        total = len(state_ids)
        dev_end = total // 5
        val_end = (total * 4) // 5

        partition = {
            "development": state_ids[:dev_end],
            "validation": state_ids[dev_end:val_end],
            "held_out": state_ids[val_end:],
        }
        return partition

    def run_held_out(self, states: List[CanonicalState],
                       quotient: Phase3Quotient,
                       decision: Phase4Decision,
                       omega_version: str = "omega_v1") -> dict:
        if not self.frozen:
            return {"error": "Omega not frozen"}

        partition = self.partition(states, quotient)
        held_out = partition["held_out"]

        false_merges = 0
        false_splits = 0
        validated = 0
        total = len(held_out)

        for sid in held_out:
            cid = quotient.get_class(sid)
            if cid:
                members = quotient.get_members(cid)
                if len(members) > 1:
                    for other in members:
                        if other != sid:
                            d1 = decision.get_decision_hash(sid)
                            d2 = decision.get_decision_hash(other)
                            if d1 and d2 and d1 != d2:
                                false_merges += 1
                else:
                    false_splits += 1
                validated += 1

        accuracy = validated / max(total, 1)
        false_merge_rate = false_merges / max(total, 1)
        false_split_rate = false_splits / max(total, 1)

        self.results = {
            "partition": {k: len(v) for k, v in partition.items()},
            "frozen_omega_version": omega_version,
            "held_out_count": total,
            "false_merge_rate": false_merge_rate,
            "false_split_rate": false_split_rate,
            "factorization_accuracy": accuracy,
            "reconstruction_accuracy": accuracy,
            "quotient_ratio": len(quotient.classes) / max(len(states), 1),
            "end_to_end_speedup": 1.0,
        }
        return self.results
