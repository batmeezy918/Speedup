import json, hashlib, time
from pathlib import Path
from typing import Dict, List, Optional
from agd_framework.utils import *
from agd_framework.quotient import Phase3Quotient
from agd_framework.canonical import CanonicalState
from agd_framework.decision import DecisionResult

class Phase8Reconstruction:
    def __init__(self, quotient: Phase3Quotient):
        self.quotient = quotient
        self.residuals: Dict[str, float] = {}
        self.omega_residuals: Dict[str, float] = {}

    def reconstruct(self, classes: List[dict],
                     representative_states: Dict[str, CanonicalState]) -> dict:
        reconstruction_results = []
        omega_residuals = []
        decision_residuals = []

        for cls in classes:
            rep_id = cls.get("representative", "")
            member_ids = cls.get("member_state_ids", [])
            if rep_id in representative_states:
                rep = representative_states[rep_id]
                for mid in member_ids:
                    if mid in representative_states:
                        member = representative_states[mid]
                        decision_sim = self._simulate_decision_residual(rep, member)
                        omega_sim = self._simulate_omega_residual(rep, member)
                        decision_residuals.append(decision_sim)
                        omega_residuals.append(omega_sim)

        total_decision_residual = sum(decision_residuals)
        total_omega_residual = sum(omega_residuals)

        return {
            "total_reconstructed": len(classes),
            "decision_residuals": decision_residuals,
            "omega_residuals": omega_residuals,
            "total_decision_residual": total_decision_residual,
            "total_omega_residual": total_omega_residual,
            "reconstruction_decision_pass": total_decision_residual == 0,
            "reconstruction_omega_pass": total_omega_residual == 0,
            "residual_details": {
                "decision": total_decision_residual / max(len(decision_residuals), 1),
                "omega": total_omega_residual / max(len(omega_residuals), 1),
            },
        }

    def _simulate_decision_residual(self, rep, member) -> float:
        return 0.0 if rep.sha256 == member.sha256 else 1.0

    def _simulate_omega_residual(self, rep, member) -> float:
        return 0.0 if rep.sha256 == member.sha256 else 1.0

    def record_residuals(self, state_id: str, value: float):
        self.residuals[state_id] = value
