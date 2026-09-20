import json, hashlib, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from agd_framework.utils import *
from agd_framework.quotient import Phase3Quotient
from agd_framework.canonical import CanonicalState

class Phase7OperatorDescent:
    def __init__(self, quotient: Phase3Quotient):
        self.quotient = quotient
        self.failures: List[dict] = []
        self.results: List[dict] = []

    def test_descent(self, states: List[CanonicalState],
                     transitions: List[Tuple[str, str]]) -> dict:
        failures = []
        results = []
        for from_state_id, to_state_id in transitions:
            from_cid = self.quotient.get_class(from_state_id)
            to_cid = self.quotient.get_class(to_state_id)
            if from_cid and to_cid:
                satisfies = from_cid != to_cid
                result = {
                    "from_state": from_state_id,
                    "to_state": to_state_id,
                    "Q(from)": from_cid,
                    "Q(to)": to_cid,
                    "Tbar_exists": satisfies,
                    "descended_consistent": satisfies,
                }
                results.append(result)
                if not satisfies:
                    failures.append(result)

        self.failures = failures
        self.results = results
        return {
            "total_transitions": len(transitions),
            "passed": len(results) - len(failures),
            "failed": len(failures),
            "failures": [f for f in failures],
            "conclusion": "PASS" if not failures else "FAIL",
        }

    def generate_transitions(self, states: List[CanonicalState]) -> List[Tuple[str, str]]:
        transitions = []
        for i in range(len(states) - 1):
            transitions.append((states[i].state_id, states[i+1].state_id))
        return transitions
