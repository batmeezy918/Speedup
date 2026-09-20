import json, hashlib, re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from agd_framework.utils import *

@dataclass
class OmegaSignature:
    omega_id: str
    version: str
    requested_api_identity: str
    api_family_domain: str
    required_parameter_names: List[str]
    parameter_values_hash: str
    parameter_types: Dict[str, str]
    required_optional_status: Dict[str, str]
    dialogue_constraints: str
    tool_availability: List[str]
    infeasibility_constraints: str
    ordering_constraints: str
    multi_call_structure: str
    previous_tool_results_hash: str
    benchmark_category: str
    language: str
    evaluator_output_structure: str
    full_signature_hash: str

    def to_dict(self) -> dict:
        return asdict(self)

class OmegaObservable:
    def __init__(self, version: str = "omega_v1"):
        self.version = version
        self.signatures: Dict[str, OmegaSignature] = {}
        self.change_log: List[dict] = []

    def _extract_api_identity(self, task_data: dict) -> str:
        ac = task_data.get("automated_checks", "")
        tools = re.findall(r'(?:call|use|invoke|execute|run)\s+(\w+)', ac, re.IGNORECASE)
        if not tools:
            return "openclaw_general"
        return "|".join(sorted(set(tools)))

    def _extract_api_family(self, task_data: dict) -> str:
        cat = task_data.get("category", "")
        ac = task_data.get("automated_checks", "")
        families = []
        if "file" in ac.lower() or "read" in ac.lower() or "write" in ac.lower():
            families.append("filesystem")
        if "bash" in ac.lower() or "command" in ac.lower() or "exec" in ac.lower():
            families.append("shell")
        if "http" in ac.lower() or "fetch" in ac.lower() or "url" in ac.lower():
            families.append("network")
        if "db" in ac.lower() or "database" in ac.lower() or "sql" in ac.lower():
            families.append("database")
        if "email" in ac.lower():
            families.append("communication")
        if not families:
            if cat and "Safety" in cat:
                families.append("safety_enforcement")
            elif cat and "Information" in cat:
                families.append("information_retrieval")
            elif cat and "Office" in cat:
                families.append("productivity")
            elif cat and "Data" in cat:
                families.append("data_analysis")
            elif cat and "Development" in cat:
                families.append("devops")
            elif cat and "Automation" in cat:
                families.append("workflow")
            else:
                families.append("general_purpose")
        return "|".join(families)

    def _extract_parameters(self, task_data: dict) -> Tuple[List[str], Dict[str, str], Dict[str, str], str]:
        ac = task_data.get("automated_checks", "")
        prompts = task_data.get("prompt", "")
        combined = ac + "\n" + prompts
        param_names = sorted(set(re.findall(r'(\w+(?:_id|_path|_file|_name|_type|_value)?)\s*[=:]', combined)))
        if not param_names:
            param_names = ["task_id", "workspace_path", "prompt", "checks"]
        param_types = {}
        for p in param_names:
            if "path" in p or "file" in p or "dir" in p:
                param_types[p] = "path"
            elif "id" in p:
                param_types[p] = "identifier"
            elif "name" in p:
                param_types[p] = "string"
            elif "value" in p:
                param_types[p] = "any"
            else:
                param_types[p] = "string"
        required_optional = {}
        for p in param_names:
            if p in ["task_id", "workspace_path"]:
                required_optional[p] = "required"
            else:
                required_optional[p] = "optional"
        values_hash = hashlib.sha256(json.dumps(param_types, sort_keys=True).encode()).hexdigest()
        return param_names, param_types, required_optional, values_hash

    def compute(self, task_data: dict, task_path: Path,
                previous_results: List[str] = None) -> OmegaSignature:
        api_id = self._extract_api_identity(task_data)
        api_family = self._extract_api_family(task_data)
        param_names, param_types, req_opt, param_hash = self._extract_parameters(task_data)
        ac = task_data.get("automated_checks", "")
        prompts = task_data.get("prompt", "")

        dialogue_constraints = ""
        if "refuse" in ac.lower() or "decline" in ac.lower():
            dialogue_constraints += "must_refuse|prohibition;"
        if "must" in ac.lower() or "required" in ac.lower():
            dialogue_constraints += "mandatory_steps;"
        if "never" in ac.lower() or "do not" in ac.lower() or "dont" in ac.lower():
            dialogue_constraints += "negative_constraint;"
        if not dialogue_constraints:
            dialogue_constraints = "standard"

        tool_availability = []
        if "file" in ac.lower() or "file" in prompts.lower():
            tool_availability.append("filesystem")
        if "bash" in ac.lower() or "command" in ac.lower():
            tool_availability.append("shell")
        if "web" in ac.lower() or "internet" in ac.lower() or "url" in ac.lower():
            tool_availability.append("web")
        if "email" in ac.lower():
            tool_availability.append("email")
        if "database" in ac.lower() or "sql" in ac.lower():
            tool_availability.append("database")
        if not tool_availability:
            tool_availability = ["openclaw_general"]

        infeasibility = ""
        if "cannot" in ac.lower() or "impossible" in ac.lower() or "infeasible" in ac.lower():
            infeasibility = "marked_infeasible"

        ordering = ""
        if "before" in ac.lower() or "first" in ac.lower() or "then" in ac.lower():
            ordering = "sequential_dependent"
        elif "parallel" in ac.lower() or "simultaneously" in ac.lower():
            ordering = "parallel_independent"
        else:
            ordering = "unordered"

        multi_call = "single"
        if ac.count("def grade") > 0:
            multi_call = "multi_turn_grade"

        prev_hash = hashlib.sha256(json.dumps(previous_results or []).encode()).hexdigest()
        category = task_data.get("category", "")
        language = task_data.get("language", "en") if "language" in task_data else "en"

        eval_structure = json.dumps({
            "has_grade_fn": "def grade" in ac,
            "pass_threshold": True,
            "overall_score": True,
            "privacy_score": "privacy" in ac.lower(),
        }, sort_keys=True)

        sig_dict = {
            "requested_api_identity": api_id,
            "api_family_domain": api_family,
            "required_parameter_names": param_names,
            "parameter_values_hash": param_hash,
            "parameter_types": param_types,
            "required_optional_status": req_opt,
            "dialogue_constraints": dialogue_constraints,
            "tool_availability": sorted(tool_availability),
            "infeasibility_constraints": infeasibility,
            "ordering_constraints": ordering,
            "multi_call_structure": multi_call,
            "previous_tool_results_hash": prev_hash,
            "benchmark_category": category,
            "language": language,
            "evaluator_output_structure": eval_structure,
        }
        sig_json = json.dumps(sig_dict, sort_keys=True)
        sig_hash = hashlib.sha256(sig_json.encode()).hexdigest()

        sig = OmegaSignature(
            omega_id=f"omega_{sig_hash[:16]}",
            version=self.version,
            requested_api_identity=api_id,
            api_family_domain=api_family,
            required_parameter_names=param_names,
            parameter_values_hash=param_hash,
            parameter_types=param_types,
            required_optional_status=req_opt,
            dialogue_constraints=dialogue_constraints,
            tool_availability=sorted(tool_availability),
            infeasibility_constraints=infeasibility,
            ordering_constraints=ordering,
            multi_call_structure=multi_call,
            previous_tool_results_hash=prev_hash,
            benchmark_category=category,
            language=language,
            evaluator_output_structure=eval_structure,
            full_signature_hash=sig_hash,
        )
        self.signatures[sig_hash] = sig
        return sig

    def upgrade(self, new_version: str, reason: str,
                task_data: dict, task_path: Path) -> OmegaSignature:
        old_version = self.version
        self.version = new_version
        sig = self.compute(task_data, task_path)
        self.change_log.append({
            "from_version": old_version,
            "to_version": new_version,
            "reason": reason,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "task_id": task_data.get("task_id", ""),
        })
        return sig
