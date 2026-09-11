#!/usr/bin/env python3
"""COCI: Constitutional Citizen / Constitutional Witness Governor.

v0.1 is deliberately observational. It watches an explicitly authorized
filesystem root, classifies changed files, hashes them, and appends a
hash-linked JSONL witness ledger. It does not execute observed files or
promote observations to proof/claims.
"""
import argparse, hashlib, json, os, pathlib, time
from datetime import datetime, timezone

CATEGORIES = {
    "proof": ("lean4", ".lean", "proof", "theorem"),
    "implementation": ("src", "implementation", "governor", ".py", ".sh", ".cpp", ".rs", ".jl"),
    "benchmark": ("benchmark", "benchmarks", "evidence/optimizer", "benchmark"),
    "telemetry": ("telemetry", "telemetry.json", "telemetry/"),
    "evidence": ("evidence", "certificate", "artifact", "ledger"),
    "configuration": (".github", "config", ".json", ".yaml", ".yml", "lakefile"),
    "documentation": ("docs", ".md", ".txt"),
}


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(rel):
    s = rel.as_posix().lower()
    for category, needles in CATEGORIES.items():
        if any(n.lower() in s for n in needles):
            return category
    return "unknown"


def snapshot(root):
    out = {}
    for p in root.rglob("*"):
        if not p.is_file() or ".git" in p.parts or "governor/ledger" in p.as_posix():
            continue
        try:
            st = p.stat()
            rel = p.relative_to(root)
            out[rel.as_posix()] = {
                "size": st.st_size,
                "mtime_ns": st.st_mtime_ns,
                "sha256": sha256_file(p),
                "category": classify(rel),
            }
        except (OSError, PermissionError):
            continue
    return out


def event_id(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def append_event(ledger, previous, event):
    event["previous_event_hash"] = previous
    event["event_hash"] = event_id(event)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")
    return event["event_hash"]


def main():
    ap = argparse.ArgumentParser(description="COCI constitutional witness governor")
    ap.add_argument("--root", default=".", help="explicitly authorized root")
    ap.add_argument("--ledger", default="governor/ledger/coci.jsonl")
    ap.add_argument("--watch", type=float, default=0, help="poll interval seconds; 0 = one observation")
    args = ap.parse_args()
    root = pathlib.Path(args.root).resolve()
    ledger = pathlib.Path(args.ledger)
    previous = "GENESIS"
    if ledger.exists():
        try:
            last = ledger.read_text(encoding="utf-8").strip().splitlines()[-1]
            previous = json.loads(last).get("event_hash", previous)
        except Exception:
            pass
    prior = {}
    while True:
        current = snapshot(root)
        changed = []
        for path, record in current.items():
            if prior.get(path) != record:
                changed.append((path, record))
        for path in sorted(set(prior) - set(current)):
            changed.append((path, {"category": classify(pathlib.PurePosixPath(path)), "deleted": True}))
        for path, record in changed:
            now = datetime.now(timezone.utc).isoformat()
            category = record.get("category", "unknown")
            event = {
                "schema": "COCI-WITNESS-0.1",
                "timestamp_utc": now,
                "authorized_root": str(root),
                "path": path,
                "event_type": "deleted" if record.get("deleted") else "changed",
                "category": category,
                "operator_id": "COCI." + category.upper() + ".OBSERVE",
                "observation": record,
                "claim_strength": "OBSERVATION",
                "evidence_strength": "OBSERVATION",
                "promotion": "NONE",
            }
            previous = append_event(ledger, previous, event)
        prior = current
        if not args.watch:
            break
        time.sleep(args.watch)


if __name__ == "__main__":
    main()
