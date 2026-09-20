from __future__ import annotations
import os, sys, json, hashlib, time, re, shutil, tempfile
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any, Optional, Dict, List, Tuple, Set, FrozenSet
from collections import defaultdict
def _simple_yaml_parse(text: str) -> dict:
    result = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^(\w+):\s*(?:[\"\']?)(.*?)(?:[\"\']?)\s*$", line)
        if m:
            key = m.group(1)
            val = m.group(2)
            if val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            elif val.isdigit():
                val = int(val)
            result[key] = val
    return result

ACEBENCH_ROOT = Path(os.environ.get("ACEBENCH_ROOT", Path(__file__).resolve().parent.parent / "acebench_official"))
WORKSPACE = Path(__file__).resolve().parent.parent
ARTIFACTS = WORKSPACE / "artifacts"

for d in [ARTIFACTS/"provenance", ARTIFACTS/"baseline", ARTIFACTS/"agd",
          ARTIFACTS/"adversarial", ARTIFACTS/"receipts"]:
    d.mkdir(parents=True, exist_ok=True)

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_str(s: str) -> str:
    return sha256_hex(s.encode("utf-8"))

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def load_task_files() -> List[Path]:
    tasks_dir = ACEBENCH_ROOT / "tasks" / "ACE_Bench"
    if not tasks_dir.exists():
        return []
    return sorted(tasks_dir.glob("*.md"))

def parse_task_md(task_file: Path) -> dict:
    content = task_file.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not fm_match:
        raise ValueError(f"YAML frontmatter not found: {task_file}")
    metadata = _simple_yaml_parse(fm_match.group(1))
    body = fm_match.group(2)
    sections: dict = {}
    current_section: Optional[str] = None
    lines: list = []
    in_code_block = False
    for line in body.split("\n"):
        if re.match(r"^```", line):
            in_code_block = not in_code_block
        header = re.match(r"^##\s+(.+)$", line)
        if header and not in_code_block:
            if current_section is not None:
                sections[current_section] = "\n".join(lines).strip()
            current_section = header.group(1)
            lines = []
        else:
            lines.append(line)
    if current_section is not None:
        sections[current_section] = "\n".join(lines).strip()

    def strip_codeblock(raw: str) -> str:
        s = re.sub(r"^```[^\n]*\n?", "", raw.strip())
        s = re.sub(r"\n?```$", "", s).strip()
        return s

    prompt = sections.get("Prompt", "").strip()
    raw_workspace = sections.get("Workspace Path", "").strip()
    workspace_path = strip_codeblock(raw_workspace)
    automated_checks = strip_codeblock(sections.get("Automated Checks", ""))
    env = strip_codeblock(sections.get("Env", ""))
    skills = strip_codeblock(sections.get("Skills", ""))
    warmup = strip_codeblock(sections.get("Warmup", ""))
    task_id = metadata.get("id", task_file.stem)
    timeout_seconds = int(metadata.get("timeout_seconds", 120))
    agent_category = metadata.get("agent_category", "")
    category = metadata.get("category") or task_file.parent.name
    name = metadata.get("name", "")
    source = metadata.get("source", "")
    original_id = metadata.get("original_id", "")
    privacy_note = metadata.get("privacy_note", "")

    return {
        "task_id": task_id, "prompt": prompt, "workspace_path": workspace_path,
        "automated_checks": automated_checks, "env": env, "skills": skills,
        "warmup": warmup, "timeout_seconds": timeout_seconds,
        "agent_category": agent_category, "category": category,
        "name": name, "source": source, "original_id": original_id,
        "privacy_note": privacy_note, "raw_content": content,
        "frontmatter": metadata,
    }
