import json, hashlib, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from agd_framework.utils import *
from agd_framework.canonical import Phase1Canonical, CanonicalState
from agd_framework.omega import OmegaObservable, OmegaSignature
from agd_framework.quotient import Phase3Quotient, QuotientClass
from agd_framework.decision import Phase4Decision, DecisionResult

@dataclass
class FalseMergeViolation:
    x: dict
    y: dict
    Q_x: str
    Q_y: str
    D_x: str
    D_y: str
    differing_observable: str
    suspected_missing_invariant: str
    omega_version: str

@dataclass
class FalseMergeReport:
    report_id: str
    timestamp: str
    total_pairs_tested: int
    violations: List[dict]
    omega_version: str
    conclusion: str
    iterations: int

class Phase5FalseMerge:
    def __init__(self, quotient: Phase3Quotient,
                 decision: Phase4Decision,
                 omega: OmegaObservable):
        self.quotient = quotient
        self.decision = decision
        self.omega = omega
        self.violations: List[dict] = []
        self.iterations = 0

    def test_all_classes(self, states: List[CanonicalState]) -> FalseMergeReport:
        violations = []
        total_pairs = 0
        max_iterations = 5

        for iteration in range(max_iterations):
            self.iterations = iteration + 1
            classes_with_members = {
                cid: cls for cid, cls in self.quotient.classes.items()
                if cls.member_count >= 2
            }

            iteration_violations = []
            for class_id, qc in classes_with_members.items():
                members = qc.member_state_ids
                for i in range(len(members)):
                    for j in range(i+1, len(members)):
                        total_pairs += 1
                        x_id, y_id = members[i], members[j]
                        q_x = self.quotient.get_class(x_id)
                        q_y = self.quotient.get_class(y_id)
                        D_x = self.decision.get_decision_hash(x_id)
                        D_y = self.decision.get_decision_hash(y_id)

                        if D_x and D_y and D_x != D_y:
                            diff_obs = self._find_difference(x_id, y_id)
                            missing = self._suspect_invariant(x_id, y_id)
                            viol = {
                                "x": {"state_id": x_id, "task_id": states[x_id].task_id if x_id in states else x_id},
                                "y": {"state_id": y_id, "task_id": states[y_id].task_id if y_id in states else y_id},
                                "Q(x)": q_x,
                                "Q(y)": q_y,
                                "D(x)": D_x,
                                "D(y)": D_y,
                                "differing_observable": diff_obs,
                                "suspected_missing_invariant": missing,
                                "omega_version": self.omega.version,
                            }
                            iteration_violations.append(viol)
                            self.violations.append(viol)

            if not iteration_violations:
                break

            if iteration + 1 < max_iterations:
                new_version = f"omega_v{iteration + 2}"
                self.omega.version = new_version

        conclusion = "SAFE" if not violations else "UNSAFE"
        if violations:
            conclusion = "UNSAFE_AFTER_REFINEMENT"

        report = FalseMergeReport(
            report_id=f"fmr_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}",
            timestamp=now_iso(),
            total_pairs_tested=total_pairs,
            violations=[v for v in violations],
            omega_version=self.omega.version,
            conclusion=conclusion,
            iterations=self.iterations,
        )
        return report

    def _find_difference(self, x_id: str, y_id: str) -> str:
        dx = self.decision.decisions.get(x_id)
        dy = self.decision.decisions.get(y_id)
        if dx and dy:
            for key in ["selected_apis", "arguments", "refusal", "no_call", "special_case"]:
                if getattr(dx, key, None) != getattr(dy, key, None):
                    return key
        return "unknown_decision_difference"

    def _suspect_invariant(self, x_id: str, y_id: str) -> str:
        dx = self.decision.decisions.get(x_id)
        dy = self.decision.decisions.get(y_id)
        if dx and dy:
            if dx.refusal != dy.refusal:
                return "refusal_disposition_invariant"
            if dx.special_case != dy.special_case:
                return "special_case_disposition_invariant"
            if dx.arguments != dy.arguments:
                return "parameter_value_invariant"
        return "unidentified_invariant"
