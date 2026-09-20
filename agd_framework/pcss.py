import json
from typing import Dict
from agd_framework.utils import *

class Phase17PCSSGate:
    def __init__(self):
        self.gates: Dict[str, bool] = {}
        self.result: Dict = {}

    def evaluate_conditional(self,
                             quotient_correct: bool,
                             reconstruction_pass: bool,
                             invariant_preserved: bool,
                             provenance_complete: bool) -> Dict:
        gates = {
            "I": invariant_preserved and provenance_complete,
            "R": reconstruction_pass,
            "Q": quotient_correct,
            "Q-1": reconstruction_pass,
            "Omega": invariant_preserved,
            "X": True,
            "L": provenance_complete,
        }
        all_pass = all(gates.values())
        claim = "BLOCKED" if not all_pass else "PUBLISHABLE"

        self.result = {
            "gates": gates,
            "all_passed": all_pass,
            "publication_decision": claim,
            "failed_gates": [k for k, v in gates.items() if not v],
        }
        return self.result

    def classify_claim(self, proven: bool, validated: bool,
                         implemented: bool) -> Dict:
        classification = {
            "PROVEN": proven,
            "EMPIRICALLY_VALIDATED": validated,
            "IMPLEMENTED": implemented,
            "OPEN": not (proven or validated or implemented),
        }
        return classification
