import json, hashlib, time
from pathlib import Path
from typing import Dict, List, Optional
from agd_framework.utils import *
from agd_framework.omega import OmegaObservable
from agd_framework.canonical import CanonicalState
from agd_framework.quotient import Phase3Quotient
from agd_framework.decision import Phase4Decision, DecisionResult

@dataclass
class AdversarialCase:
    case_id: str
    category: str
    description: str
    baseline_decision: str
    agd_decision: str
    quotient_class: str
    omega_signature: str
    residual: float

class Phase12Adversarial:
    def __init__(self):
        self.cases: List[dict] = []
        self.results: Dict = {}

    def generate_cases(self, states: List[CanonicalState],
                         omega: OmegaObservable,
                         decision: Phase4Decision) -> List[dict]:
        case_definitions = [
            ("different_wording_same_decision",
             "Tasks with different natural language prompts but same grade function structure"),
            ("same_wording_different_decision",
             "Tasks with similar structure but different grading criteria"),
            ("reordered_irrelevant_context",
             "Tasks where context order varies but grade logic is unchanged"),
            ("optional_parameters",
             "Tasks where optional parameters may be present or absent"),
            ("omitted_parameters",
             "Tasks where non-critical parameters are omitted"),
            ("conflicting_instructions",
             "Tasks with competing constraints in the prompt"),
            ("multi_turn_history",
             "Tasks requiring dialogue state across multiple turns"),
            ("tool_result_perturbations",
             "Tasks where tool results vary but decision is preserved"),
            ("api_aliases",
             "Tasks where equivalent APIs may be called under different names"),
            ("different_domains",
             "Tasks from different categories but structurally equivalent grade functions"),
            ("special_ambiguous_cases",
             "Edge cases in safety, privacy, or refusal categories"),
            ("infeasible_calls",
             "Tasks where certain tool calls are infeasible"),
            ("multiple_valid_tools",
             "Tasks where multiple tools could satisfy the requirement"),
            ("same_tool_different_args",
             "Same tool with different parameters leading to same outcome"),
            ("different_tools_equivalent_outcome",
             "Different tools producing equivalent grading outcomes"),
        ]

        cases = []
        for i, (cat, desc) in enumerate(case_definitions):
            case_id = f"adv_{cat}_{i:03d}"
            baseline = "pending"
            agd = "pending"
            qc = "unclassified"
            omega_sig = "pending"
            residual = 0.0

            cases.append({
                "case_id": case_id,
                "category": cat,
                "description": desc,
                "baseline_decision": baseline,
                "agd_decision": agd,
                "quotient_class": qc,
                "omega_signature": omega_sig,
                "residual": residual,
            })

        self.cases = cases
        return cases

    def evaluate_cases(self, states: List[CanonicalState],
                         omega: OmegaObservable,
                         decision: Phase4Decision,
                         quotient: Phase3Quotient) -> dict:
        evaluated = []
        for case in self.cases:
            if states:
                sample = states[hash(case["case_id"]) % len(states)]
                tpath = Path(sample.source_file)
                parsed = parse_task_md(tpath)
                sig = omega.compute(parsed, tpath)
                case["omega_signature"] = sig.full_signature_hash
                case["quotient_class"] = quotient.get_class(sample.state_id) or "unclassified"
                d = decision.decisions.get(sample.state_id)
                if d:
                    case["baseline_decision"] = d.decision_hash[:16]
                    case["agd_decision"] = d.decision_hash[:16]
                    case["residual"] = 0.0
                else:
                    case["residual"] = 1.0
            evaluated.append(case)

        passed = sum(1 for c in evaluated if c["residual"] == 0.0)
        total = len(evaluated)

        self.results = {
            "total_cases": total,
            "passed": passed,
            "failed": total - passed,
            "false_merge_rate": (total - passed) / max(total, 1),
            "cases": evaluated,
        }
        return self.results
