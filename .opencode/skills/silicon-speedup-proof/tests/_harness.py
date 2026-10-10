"""Shared test scaffolding for the silicon-speedup-proof validator tests.

Every fixture used here is SYNTHETIC. None of it is a hardware measurement.
The tests assert validator behaviour only; they never assert anything about a
real device.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
LEDGERS = FIXTURES / "ledgers"
RUNS = FIXTURES / "runs"
RAW = FIXTURES / "raw"

sys.path.insert(0, str(SCRIPTS))

import ssproof as S  # noqa: E402

validate_run = S.load_tool("validate-run")
validate_ledger = S.load_tool("validate-ledger")


def project_root() -> Path:
    """The repository this skill is installed into.

    Located by walking up from the skill directory, so the tests are independent
    of the working directory they are launched from.
    """
    for candidate in (SKILL, *SKILL.parents):
        if (candidate / "CONSTITUTION.md").exists() and (candidate / "speedup").is_dir():
            return candidate
    return SKILL


PROJECT_ROOT = project_root()


def ledger_path(name: str) -> Path:
    return LEDGERS / name


def run_path(name: str) -> Path:
    return RUNS / name


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def ledger_findings(name: str, repo_root: Path | None = PROJECT_ROOT, **kw):
    findings, summary = validate_ledger.validate_ledger(ledger_path(name), repo_root, **kw)
    return findings, summary


def run_findings(name: str, repo_root: Path | None = PROJECT_ROOT):
    path = run_path(name)
    record = load_json(path)
    findings = validate_run.validate_record(record, where=path.name, repo_root=repo_root, record_path=path)
    return findings


def findings_for_record(record, where: str = "inline.json", repo_root: Path | None = PROJECT_ROOT):
    """Validate an in-memory record without touching the filesystem fixtures."""
    record_path = RUNS / where
    return validate_run.validate_record(record, where=where, repo_root=repo_root,
                                       record_path=record_path)


def codes(findings, severity: str | None = None) -> set[str]:
    return {f.code for f in findings if severity is None or f.severity == severity}


def cli(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, cwd=str(SKILL),
    )