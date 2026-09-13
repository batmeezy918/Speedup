#!/usr/bin/env python3
"""Fail-closed validator for the append-only formal-gap ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

TERMINAL = {"CLOSED", "REFINED", "NEGATIVE"}
ACTIVE = {"OPEN", "READY", "EXECUTING", "EVIDENCE_CAPTURED", "REASSESSED"}
ALLOWED = ACTIVE | TERMINAL
REQUIRED = {
    "schema", "event_id", "gap_id", "timestamp", "parent_run",
    "type", "status", "obligation", "evidence_refs", "counterevidence_refs",
    "dependencies", "closure_predicate", "event_sha256",
}


def event_hash(row: dict) -> str:
    body = {k: v for k, v in row.items() if k != "event_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(path: pathlib.Path):
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        row["_line"] = n
        rows.append(row)
    return rows


def validate(rows):
    errors = []
    seen_events = set()
    seen_gaps = set()
    latest = {}
    for row in rows:
        line = row["_line"]
        missing = sorted(REQUIRED - row.keys())
        if missing:
            errors.append(f"line {line}: missing {', '.join(missing)}")
        eid = row.get("event_id")
        gid = row.get("gap_id")
        if eid in seen_events:
            errors.append(f"line {line}: duplicate event_id={eid}")
        seen_events.add(eid)
        status = row.get("status")
        if status not in ALLOWED:
            errors.append(f"line {line}: invalid status={status}")
        if row.get("event_sha256") != event_hash(row):
            errors.append(f"line {line}: event_sha256 mismatch")
        if status == "CLOSED" and not row.get("evidence_refs"):
            errors.append(f"line {line}: CLOSED requires evidence_refs")
        if status == "NEGATIVE" and not row.get("counterevidence_refs"):
            errors.append(f"line {line}: NEGATIVE requires counterevidence_refs")
        parents = row.get("parent_event_ids", [])
        if not isinstance(parents, list):
            errors.append(f"line {line}: parent_event_ids must be a list")
        elif any(p not in seen_events for p in parents):
            errors.append(f"line {line}: parent event must precede child")
        if gid in latest:
            prev = latest[gid]
            prev_status = prev.get("status")
            if prev_status in TERMINAL:
                errors.append(f"line {line}: terminal gap cannot receive another event")
        seen_gaps.add(gid)
        latest[gid] = row
    return errors, latest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ledger", nargs="?", default="evidence/ledger/FORMAL_GAP_LEDGER.jsonl")
    args = ap.parse_args()
    path = pathlib.Path(args.ledger)
    if not path.exists():
        print(f"FAIL: missing ledger: {path}")
        return 2
    try:
        rows = load(path)
        errors, latest = validate(rows)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 2
    if errors:
        print("FAIL: formal-gap ledger validation")
        for e in errors:
            print(" -", e)
        return 1
    print("PASS: formal-gap ledger validation")
    print(f"events={len(rows)} gaps={len(latest)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
