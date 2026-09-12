#!/usr/bin/env python3
"""Fail-closed validator for the recursive proof-carrying speedup ledger.

This tool validates chronology, evidence strength, composition independence,
and the required derivation chain. It never promotes evidence. A VERIFIED
primitive must carry every mandatory gate explicitly; otherwise validation
fails or the record remains below VERIFIED.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

REQUIRED = {
    "primitive_id", "parent_ids", "timestamp", "scenario_hash",
    "implementation_hash", "run_hash", "proof_hash", "evidence_class",
    "S_ideal", "S_measured", "S_verified", "S_composed", "S_cumulative",
    "interaction_factor", "gap_status", "claim_strength",
    "evidence_strength", "stage_chain", "baseline_id", "composition_id",
}
STAGES = [
    "Requirement", "Derivation", "Operator", "Implementation", "Native Run",
    "Raw Result", "Reverse Derivation", "Gap Analysis", "Gap Closure",
    "Re-run", "Normalized Claim",
]
GATES = ["I", "R", "Q", "Q_inverse", "Omega", "X", "L"]
ORDER = {
    "OBSERVATION": 0, "EMPIRICAL": 1, "STRONG_LOCAL": 2,
    "FORMAL_PARTIAL": 2, "CANDIDATE": 2, "VERIFIED": 3,
}


def strength(value):
    if isinstance(value, int):
        return value
    return ORDER.get(str(value).upper(), -1)


def load(path: pathlib.Path):
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {n}: invalid JSON: {exc}") from exc
        row["_line"] = n
        rows.append(row)
    return rows


def validate(rows):
    errors = []
    ids = set()
    verified = set()
    for row in rows:
        line = row["_line"]
        missing = sorted(REQUIRED - row.keys())
        if missing:
            errors.append(f"line {line}: missing fields: {', '.join(missing)}")
        pid = row.get("primitive_id")
        if pid in ids:
            errors.append(f"line {line}: duplicate primitive_id={pid}")
        ids.add(pid)
        parents = row.get("parent_ids", [])
        if not isinstance(parents, list):
            errors.append(f"line {line}: parent_ids must be a list")
        elif any(p == pid for p in parents):
            errors.append(f"line {line}: primitive cannot parent itself")
        stages = row.get("stage_chain", [])
        if stages != STAGES:
            errors.append(f"line {line}: stage_chain must equal the canonical 11-stage chain")
        claim = strength(row.get("claim_strength"))
        evidence = strength(row.get("evidence_strength"))
        if claim < 0 or evidence < 0 or claim > evidence:
            errors.append(f"line {line}: ClaimStrength > EvidenceStrength or unknown strength")
        status = str(row.get("evidence_class", "")).upper()
        gates = row.get("gates", {})
        if status == "VERIFIED":
            verified.add(pid)
            if not isinstance(gates, dict) or any(gates.get(g) is not True for g in GATES):
                errors.append(f"line {line}: VERIFIED requires I,R,Q,Q_inverse,Omega,X,L all true")
            for key in ("S_measured", "S_verified"):
                if not isinstance(row.get(key), (int, float)):
                    errors.append(f"line {line}: VERIFIED requires numeric {key}")
            if not row.get("run_hash") or not row.get("scenario_hash"):
                errors.append(f"line {line}: VERIFIED requires scenario_hash and run_hash")
        else:
            if row.get("S_verified") is not None:
                errors.append(f"line {line}: non-VERIFIED record must not carry S_verified")
        composition = row.get("composition_id")
        if composition and status == "VERIFIED":
            if not row.get("parent_ids"):
                errors.append(f"line {line}: verified composition requires parent_ids")
            if row.get("S_composed") is None or row.get("S_cumulative") is None:
                errors.append(f"line {line}: verified composition requires independently measured S_composed and S_cumulative")
            if row.get("interaction_factor") is None:
                errors.append(f"line {line}: verified composition requires interaction_factor")
    # Parents must precede children in the append-only chronology.
    seen = set()
    for row in rows:
        for p in row.get("parent_ids", []):
            if p not in seen and p not in {"GENESIS"}:
                errors.append(f"line {row['_line']}: parent {p} is not an earlier ledger event")
        seen.add(row.get("primitive_id"))
    return errors, verified


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ledger", nargs="?", default="evidence/ledger/RECURSIVE_PRIMITIVE_LEDGER.jsonl")
    args = ap.parse_args()
    path = pathlib.Path(args.ledger)
    if not path.exists():
        print(f"FAIL: missing ledger: {path}")
        return 2
    try:
        rows = load(path)
        errors, verified = validate(rows)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 2
    if errors:
        print("FAIL: recursive speedup ledger validation")
        for error in errors:
            print(" -", error)
        return 1
    print("PASS: recursive speedup ledger validation")
    print(f"records={len(rows)} verified_primitives={len(verified)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
