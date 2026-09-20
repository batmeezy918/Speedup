import json, os, time, hashlib
from pathlib import Path
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field, asdict
from collections import defaultdict

from agd_framework.utils import *

@dataclass
class CanonicalState:
    state_id: str
    task_id: str
    source_file: str
    category: str
    language: str
    turn: int
    canonical_representation: str
    sha256: str
    tool_schema: str = ""
    tool_arguments: str = ""
    tool_results: str = ""
    model_config: str = ""
    evaluator_relevant_state: str = ""
    dialogue_history_hash: str = ""
    agent_category: str = ""

class Phase1Canonical:
    def __init__(self):
        self.states: Dict[str, CanonicalState] = {}
        self._lock = defaultdict(int)

    def canonicalize(self, task_path: Path, turn: int = 0,
                     dialogue_history: str = "", tool_results: str = "",
                     model_config: str = "default") -> CanonicalState:
        parsed = parse_task_md(task_path)
        task_id = parsed["task_id"]
        source_file = str(task_path.resolve())
        category = parsed["category"]
        agent_category = parsed.get("agent_category", "")
        language = "en"

        components = {
            "task_id": task_id,
            "source_file": source_file,
            "category": category,
            "agent_category": agent_category,
            "language": language,
            "turn": turn,
            "prompt": parsed["prompt"],
            "automated_checks": parsed["automated_checks"],
            "frontmatter": json.dumps(parsed["frontmatter"], sort_keys=True),
            "dialogue_history_hash": hashlib.sha256(dialogue_history.encode()).hexdigest(),
            "tool_results_hash": hashlib.sha256(tool_results.encode()).hexdigest(),
            "model_config": model_config,
        }
        canonical_repr = json.dumps(components, sort_keys=True)
        sha = hashlib.sha256(canonical_repr.encode()).hexdigest()
        state_id = f"state_{sha[:16]}"

        state = CanonicalState(
            state_id=state_id, task_id=task_id, source_file=source_file,
            category=category, language=language, turn=turn,
            canonical_representation=canonical_repr, sha256=sha,
            tool_schema="openclaw_tool_schema_v1",
            tool_arguments=json.dumps(parsed.get("env", ""), sort_keys=True),
            tool_results=tool_results,
            model_config=model_config,
            evaluator_relevant_state=parsed["automated_checks"],
            dialogue_history_hash=components["dialogue_history_hash"],
            agent_category=agent_category,
        )
        self.states[state_id] = state
        return state

    def get_all_states(self) -> List[CanonicalState]:
        return list(self.states.values())
