#!/usr/bin/env python3
"""Append-only PCSS formal-gap lifecycle governor.

Lifecycle: OPEN -> READY -> EXECUTING -> EVIDENCE_CAPTURED -> REASSESSED ->
CLOSED, with REFINED and NEGATIVE as terminal evidence outcomes. This module
records state transitions only; it never promotes a speedup primitive.
"""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TRANSITIONS = {
    "OPEN": {"READY", "REFINED"},
    "READY": {"EXECUTING", "REFINED"},
    "EXECUTING": {"EVIDENCE_CAPTURED", "NEGATIVE", "REFINED"},
    "EVIDENCE_CAPTURED": {"REASSESSED", "NEGATIVE", "REFINED"},
    "REASSESSED": {"CLOSED", "READY", "REFINED", "NEGATIVE"},
    "CLOSED": set(),
    "NEGATIVE": set(),
    "REFINED": set(),
}


def event_hash(event: dict) -> str:
    body = json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def append_event(path: Path, gap_id: str, old: str, new: str, evidence: list[str] | None = None) -> dict:
    if old not in TRANSITIONS or new not in TRANSITIONS.get(old, set()):
        raise ValueError(f"illegal transition: {old} -> {new}")
    event = {
        "schema": "PCSS-FORMAL-GAP-EVENT/v1",
        "gap_id": gap_id,
        "from": old,
        "to": new,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evidence": evidence or [],
    }
    event["event_sha256"] = event_hash(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def main() -> int:
    if len(sys.argv) < 5:
        print("usage: gap_lifecycle.py LEDGER.jsonl GAP_ID FROM TO [EVIDENCE ...]", file=sys.stderr)
        return 2
    path, gap_id, old, new = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    try:
        event = append_event(path, gap_id, old, new, sys.argv[5:])
    except ValueError as exc:
        print(f"REJECTED: {exc}")
        return 1
    print(json.dumps(event, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
