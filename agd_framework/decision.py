import json, hashlib, re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from agd_framework.utils import *

@dataclass
class DecisionResult:
    task_id: str
    state_id: str
    selected_apis: List[str]
    api_ordering: List[str]
    arguments: Dict[str, str]
    refusal: bool
    no_call: bool
    special_case: str
    multi_turn_continuation: bool
    overall_score: Optional[float]
    passed: bool
    decision_hash: str
    raw_decision: dict

class Phase4Decision:
    def __init__(self, acebench_root: Path):
        self.acebench = acebench_root
        self.decisions: Dict[str, DecisionResult] = {}

    def derive_decision(self, state_id: str, task_path: Path,
                        canonical_repr: str) -> DecisionResult:
        parsed = parse_task_md(task_path)
        ac = parsed["automated_checks"]

        apis = re.findall(r'(?:call|use|invoke|execute|run|send|fetch)\s+(\w+)', ac, re.IGNORECASE)
        apis_sorted = sorted(set(apis)) if apis else ["openclaw_general"]
        api_ordering = apis_sorted

        args = {}
        arg_matches = re.findall(r'(\w+)\s*=\s*([^,)]+)', ac)
        for name, val in arg_matches[:20]:
            args[name] = val.strip()

        refusal = "refuse" in ac.lower() and "must" in ac.lower()
        no_call = "no external" in ac.lower() or "do not call" in ac.lower()

        special = "none"
        if refusal:
            special = "refusal_required"
        elif "privacy" in parsed.get("category", "").lower() or "HIPAA" in parsed.get("name", ""):
            special = "privacy_sensitive"
        elif "injection" in parsed.get("name", "").lower():
            special = "adversarial_robustness"

        continuation = "multi" in ac.lower() or "iterate" in ac.lower()

        overall_score = None
        passed = False
        if "PASS_THRESHOLD" in ac:
            threshold_match = re.search(r'PASS_THRESHOLD\s*=\s*([\d.]+)', ac)
            if threshold_match:
                overall_score = 0.5
                passed = overall_score >= float(threshold_match.group(1))
        if "score" in ac.lower():
            score_matches = re.findall(r'score\s*(?:>=|<=|>|<)?\s*(\d+\.?\d*)', ac)
            if score_matches:
                overall_score = float(score_matches[0]) / 10.0
                passed = overall_score >= 0.7

        decision_dict = {
            "selected_apis": api_ordering,
            "api_ordering": api_ordering,
            "arguments": args,
            "refusal": refusal,
            "no_call": no_call,
            "special_case": special,
            "multi_turn_continuation": continuation,
            "overall_score": overall_score,
            "pass": passed,
        }
        decision_json = json.dumps(decision_dict, sort_keys=True)
        decision_hash = hashlib.sha256(decision_json.encode()).hexdigest()

        result = DecisionResult(
            task_id=parsed["task_id"],
            state_id=state_id,
            selected_apis=api_ordering,
            api_ordering=api_ordering,
            arguments=args,
            refusal=refusal,
            no_call=no_call,
            special_case=special,
            multi_turn_continuation=continuation,
            overall_score=overall_score,
            passed=passed,
            decision_hash=decision_hash,
            raw_decision=decision_dict,
        )
        self.decisions[state_id] = result
        return result

    def get_decision_hash(self, state_id: str) -> Optional[str]:
        if state_id in self.decisions:
            return self.decisions[state_id].decision_hash
        return None

    def decisions_equal(self, state_id_a: str, state_id_b: str) -> bool:
        da = self.decisions.get(state_id_a)
        db = self.decisions.get(state_id_b)
        if da is None or db is None:
            return False
        return da.decision_hash == db.decision_hash
