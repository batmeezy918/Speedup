#!/usr/bin/env python3
"""Validate the canonical append-only Silicon Speedup primitive ledger.

Read-only. Never writes, never promotes, never repairs. A later successful run
never erases an earlier failure; this program enforces that.

Exit codes:
  0  no ERROR findings
  1  at least one ERROR finding
  2  usage / IO error

Usage:
  validate-ledger.py LEDGER.jsonl [--repo-root DIR] [--json] [--quiet]
                                  [--contradiction-tolerance 0.05]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ssproof as S  # noqa: E402

PRIMITIVE_SCHEMA = "primitive.schema.json"
GAP_SCHEMA = "gap-record.schema.json"
GENESIS = "GENESIS"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _where(line_no: int, pid: Optional[str] = None) -> str:
    base = f"L{line_no}"
    return f"{base}:{pid}" if pid else base


def timing_pair(record: Dict[str, Any]):
    """Locate the (baseline-arm, candidate-arm) pair that a ratio may be formed from.

    Composition records use composition_baseline/composition; they are still a
    real comparison and are still required to carry measured timings.
    """
    arms = {m.get("arm"): m for m in record.get("measurements") or []}
    for base_name, cand_name in (("baseline", "candidate"),
                                 ("composition_baseline", "composition")):
        if base_name in arms and cand_name in arms:
            return arms[base_name], arms[cand_name]
    return None


def _speedup_from_measurements(record: Dict[str, Any]) -> Optional[float]:
    pair = timing_pair(record)
    if pair is None:
        return None
    base, cand = pair
    bs = S.arm_stats(base.get("samples") or [])
    cs = S.arm_stats(cand.get("samples") or [])
    if not (bs["has_timing"] and cs["has_timing"]):
        return None
    try:
        return S.speedup(bs["median"], cs["median"])
    except S.CompositionError:
        return None


# --------------------------------------------------------------------------
# structural / schema
# --------------------------------------------------------------------------

def check_schema(lines, out: List[S.Finding]) -> None:
    for line in lines:
        if line.record is None:
            if line.parse_error:
                out.append(S.Finding("L-SCHEMA", S.ERROR, line.parse_error, where=f"L{line.index}"))
            continue
        schema = GAP_SCHEMA if S.is_gap_record(line.record) else PRIMITIVE_SCHEMA
        for err in S.validate_against_schema(line.record, schema):
            out.append(S.Finding(
                "L-SCHEMA", S.ERROR, err, where=_where(line.index, line.record.get("primitive_id") or line.record.get("gap_id"))
            ))


def check_ordering(lines, out: List[S.Finding]) -> None:
    """seq must strictly increase; the hash chain must be unbroken."""
    previous_seq: Optional[int] = None
    previous_hash = GENESIS
    previous_line = 0
    for line in lines:
        rec = line.record
        if rec is None or S.is_gap_record(rec):
            continue
        seq = rec.get("seq")
        if isinstance(seq, int):
            if previous_seq is not None and seq <= previous_seq:
                out.append(S.Finding(
                    "L-SEQ-1", S.ERROR,
                    f"seq {seq} does not exceed previous seq {previous_seq} (line {previous_line}): "
                    "the ledger is append-only and monotonic",
                    where=_where(line.index, rec.get("primitive_id")),
                ))
            previous_seq = seq
        expected = S.compute_record_hash(rec)
        if rec.get("record_hash") != expected:
            out.append(S.Finding(
                "L-HASH-1", S.ERROR,
                f"record_hash mismatch: recorded {rec.get('record_hash')} computed {expected}",
                where=_where(line.index, rec.get("primitive_id")),
            ))
        if rec.get("prev_hash") != previous_hash:
            out.append(S.Finding(
                "L-HASH-2", S.ERROR,
                f"prev_hash {rec.get('prev_hash')} does not chain to previous record_hash {previous_hash}",
                where=_where(line.index, rec.get("primitive_id")),
            ))
        previous_hash = rec.get("record_hash") or previous_hash
        previous_line = line.index


def check_status_lifecycle(lines, out: List[S.Finding]) -> None:
    """Legal transitions; negative evidence is never erased."""
    last_status: Dict[str, str] = {}
    negatives: Dict[str, Dict[str, int]] = defaultdict(dict)

    for line in lines:
        rec = line.record
        if rec is None or S.is_gap_record(rec):
            continue
        pid = rec.get("primitive_id", "<none>")
        status = rec.get("status")
        previous = last_status.get(pid)

        if previous is not None and not S.status_transition_legal(previous, status):
            out.append(S.Finding(
                "L-ST-1", S.ERROR,
                f"illegal status transition {previous} -> {status}; allowed: "
                f"{S.STATUS_TRANSITIONS.get(previous, ())}",
                where=_where(line.index, pid),
            ))
        last_status[pid] = status

        if status in S.NEGATIVE_STATUSES:
            negatives[pid][status] = line.index

        history = rec.get("status_history") or []
        recorded = {h.get("status") for h in history}
        for neg_status, neg_line in negatives[pid].items():
            if neg_line == line.index:
                continue
            if neg_status not in recorded:
                out.append(S.Finding(
                    "L-ST-2", S.ERROR,
                    f"status_history omits previously observed {neg_status!r} (first seen at line {neg_line}): "
                    "a later success appends, it does not erase",
                    where=_where(line.index, pid),
                ))


def check_claim_evidence(rec, out, line_index: int) -> None:
    claim = rec.get("claim") or {}
    evidence = rec.get("evidence") or {}
    strength = claim.get("strength", "NONE")
    kind = claim.get("kind", "none")
    ev = evidence.get("evidence_strength", "UNEVIDENCED")
    pid = rec.get("primitive_id", "<none>")
    where = _where(line_index, pid)

    reason = S.claim_exceeds_evidence(strength, ev, kind)
    if reason:
        out.append(S.Finding("L-CLM-1", S.ERROR, f"{reason} (claim: {strength}/{kind})", where=where))

    if claim.get("assigned_manually") is True and S.CLAIM_RANK.get(strength, 0) >= S.CLAIM_RANK["STRONG_LOCAL"]:
        out.append(S.Finding(
            "L-CLM-2", S.ERROR,
            "evidence/claim strength assigned manually above CANDIDATE with no evidentiary transition",
            where=where,
        ))

    if not S.transition_chain_is_complete(ev, evidence.get("transition_records") or []):
        out.append(S.Finding(
            "L-CLM-3", S.ERROR,
            f"evidence_strength {ev} is not backed by an ordered, event-bound transition chain "
            "from UNEVIDENCED",
            where=where,
        ))


def check_execution_binding(rec, out, line_index: int) -> None:
    pid = rec.get("primitive_id", "<none>")
    where = _where(line_index, pid)
    status = rec.get("status")
    run = rec.get("native_run") or {}
    executed_kind = run.get("executed_kind")

    if status in S.NATIVE_REQUIRED_STATUSES:
        if executed_kind != "native":
            out.append(S.Finding(
                "L-EXE-1", S.ERROR,
                f"status {status!r} requires executed_kind='native', record declares {executed_kind!r}: "
                "no native execution may be claimed from a simulation, dry run or inspection",
                where=where,
            ))
        if not str(run.get("run_id", "")).strip():
            out.append(S.Finding("L-EXE-2", S.ERROR, f"status {status!r} with no run_id", where=where))
        if timing_pair(rec) is None:
            out.append(S.Finding(
                "L-EXE-3", S.ERROR,
                f"status {status!r} with no baseline/candidate timing arms",
                where=where,
            ))

    if executed_kind == "native":
        for field in ("command", "cwd"):
            if not str(run.get(field, "")).strip():
                out.append(S.Finding(
                    "L-EXE-4", S.WARN,
                    f"native run does not record {field}",
                    where=where,
                ))
        if run.get("exit_code") is None:
            out.append(S.Finding(
                "L-EXE-5", S.WARN,
                "native run records no exit_code: verdict is UNKNOWN, not PASS",
                where=where,
            ))


def check_speedups(rec, out, line_index: int) -> None:
    pid = rec.get("primitive_id", "<none>")
    where = _where(line_index, pid)
    sp = rec.get("speedups") or {}
    claim_kind = (rec.get("claim") or {}).get("kind", "none")
    status = rec.get("status")

    if sp.get("computation") == "product_of_components":
        out.append(S.Finding(
            "L-SPD-1", S.ERROR,
            "speedups.computation == 'product_of_components': isolated component ratios must never "
            "be multiplied to produce a composed or cumulative result "
            "(RECURSIVE_SPEEDUP_CONSTITUTION.md section 4)",
            where=where,
        ))

    for field in ("S_composed", "S_cumulative"):
        value = sp.get(field)
        direct = sp.get(f"{field}_measured_direct")
        if value is None:
            continue
        if direct is not True:
            out.append(S.Finding(
                "L-SPD-2", S.ERROR,
                f"{field}={value} is present but {field}_measured_direct is not true: "
                "this quantity requires actual measured timings for its own comparison domain",
                where=where,
            ))
        if not S.is_number(value):
            out.append(S.Finding(
                "L-SPD-3", S.ERROR,
                f"{field}={value!r} is not a number: a speedup ratio must be measurable",
                where=where))
        elif value <= 0:
            out.append(S.Finding("L-SPD-3", S.ERROR, f"{field}={value} is non-positive", where=where))

    # Cross-check: a composition that declares S_composed must also have declared
    # its own measured arm pair (L-EXE-3 covers the missing-run case).
    sp_declares_composed = sp.get("S_composed") is not None
    if sp_declares_composed and timing_pair(rec) is None:
        out.append(S.Finding(
            "L-SPD-4", S.ERROR,
            "S_composed is declared without a baseline/composition timing pair in this record",
            where=where,
        ))

    ideal = sp.get("S_ideal")
    eta = sp.get("interaction_factor")
    if eta is not None:
        model = sp.get("S_ideal_model")
        if ideal in (None, 0) or model == "undefined":
            out.append(S.Finding(
                "L-SPD-5", S.ERROR,
                "interaction_factor requires a defined, nonzero S_ideal with a stated model",
                where=where,
            ))
        if not sp.get("S_ideal_assumptions"):
            out.append(S.Finding(
                "L-SPD-6", S.WARN,
                "S_ideal declared without assumptions: the ideal model's validity is unstated",
                where=where,
            ))
    if ideal is not None and not sp.get("S_ideal_assumptions") and sp.get("S_ideal_model") not in (None, "undefined"):
        out.append(S.Finding(
            "L-SPD-7", S.WARN,
            f"ideal model {sp.get('S_ideal_model')!r} declared without assumptions",
            where=where,
        ))

    if status in S.MEASURED_STATUSES and claim_kind in ("performance", "composition", "cumulative"):
        measured = _speedup_from_measurements(rec)
        declared = sp.get("S_i")
        if measured is None:
            out.append(S.Finding(
                "L-SPD-8", S.ERROR,
                f"status {status!r} with a performance claim but no usable baseline/candidate timings",
                where=where,
            ))
        elif declared is not None and not S.is_number(declared):
            out.append(S.Finding(
                "L-SPD-9", S.ERROR,
                f"declared S_i={declared!r} is not a number: a ratio must be measurable",
                where=where,
            ))
        elif declared is not None and abs(measured - declared) > 1e-9 * max(1.0, abs(measured)):
            out.append(S.Finding(
                "L-SPD-9", S.ERROR,
                f"declared S_i={declared} disagrees with the median ratio recomputed from raw samples ({measured:.6f})",
                where=where,
            ))


def check_operator(rec, out, line_index: int, repo_root: Optional[Path]) -> None:
    pid = rec.get("primitive_id", "<none>")
    where = _where(line_index, pid)
    op = rec.get("operator")
    if not isinstance(op, dict):
        return
    symbol = op.get("symbol")
    status = op.get("definition_status")
    registry = S.OPERATOR_REGISTRY.get(symbol, {})

    if status == "implemented":
        src = op.get("source_ref") or registry.get("source_ref")
        if not src:
            out.append(S.Finding(
                "L-OPR-1", S.ERROR,
                f"operator {symbol} declared implemented with no source_ref",
                where=where,
            ))
        elif repo_root is None:
            out.append(S.Finding(
                "L-OPR-2", S.WARN,
                f"operator {symbol} declares source_ref {src!r} but no --repo-root was supplied: "
                "the source could NOT be verified. Pass --repo-root to enable this check.",
                where=where,
            ))
        elif not (repo_root / src).exists():
            out.append(S.Finding(
                "L-OPR-2", S.ERROR,
                f"operator {symbol} source_ref {src!r} does not exist under the repository root",
                where=where,
            ))
    elif status in ("undefined", "specified"):
        out.append(S.Finding(
            "L-OPR-3", S.WARN,
            f"operator {symbol} definition_status={status!r} ({registry.get('note', 'no project definition located')}): "
            "record a DERIVATION gap rather than implying an implemented transformation",
            where=where,
        ))
        if (rec.get("claim") or {}).get("strength") in ("VERIFIED", "FORMAL_PARTIAL"):
            out.append(S.Finding(
                "L-OPR-4", S.ERROR,
                f"operator {symbol} is not implemented yet the claim asserts a strong formal/implementation result",
                where=where,
            ))

    for inv in op.get("invariants") or []:
        support = S.INVARIANT_SUPPORT.get(inv)
        if support is None:
            out.append(S.Finding(
                "L-OPR-5", S.WARN,
                f"invariant {inv!r} has no recorded support or definition in this project",
                where=where,
            ))
        elif support.startswith("undefined"):
            out.append(S.Finding(
                "L-OPR-6", S.WARN,
                f"invariant {inv!r} is undefined in the target project ({support}): "
                "notation is not a computation",
                where=where,
            ))


def check_dependencies(rec, out, line_index: int) -> None:
    """An unresolved dependency is never hidden by a passing partial test."""
    pid = rec.get("primitive_id", "<none>")
    where = _where(line_index, pid)
    deps = (rec.get("native_run") or {}).get("dependencies") or []
    blocking = [d for d in deps if d.get("status") in ("unresolved", "assumed")]
    if not blocking:
        return
    strength = (rec.get("claim") or {}).get("strength", "NONE")
    if S.CLAIM_RANK.get(strength, 0) > S.CLAIM_RANK["CANDIDATE"]:
        for dep in blocking:
            out.append(S.Finding(
                "L-DEP-1", S.ERROR,
                f"dependency {dep.get('id')!r} is {dep.get('status')} while the claim is {strength}: "
                "a claim that relies on an unresolved dependency is rejected",
                where=where,
            ))
    else:
        for dep in blocking:
            out.append(S.Finding(
                "L-DEP-2", S.WARN,
                f"dependency {dep.get('id')!r} is {dep.get('status')}",
                where=where,
            ))


def check_formal(rec, out, line_index: int) -> None:
    """A formal claim needs a theorem target AND a recorded successful proof."""
    pid = rec.get("primitive_id", "<none>")
    where = _where(line_index, pid)
    claim = rec.get("claim") or {}
    strength = claim.get("strength", "NONE")
    # CONSTITUTION.md Article 7/9: a formal claim needs a proof, and a VERIFIED
    # record has already declared that its formal gate passed.
    wants = claim.get("kind") == "formal" or strength == "VERIFIED"
    if not wants:
        return
    formal = rec.get("formal")
    if formal is None:
        out.append(S.Finding("L-FRM-1", S.ERROR, "formal claim with no formal block", where=where))
        return
    if not str(formal.get("theorem_target", "")).strip():
        out.append(S.Finding("L-FRM-2", S.ERROR, "no theorem target recorded", where=where))
    if not str(formal.get("command", "")).strip():
        out.append(S.Finding("L-FRM-3", S.ERROR, "no proof command recorded", where=where))
    if formal.get("exit_status") != 0:
        out.append(S.Finding(
            "L-FRM-4", S.ERROR,
            f"proof exit_status is {formal.get('exit_status')!r}, not 0: no proof was completed",
            where=where,
        ))
    if formal.get("kernel_checked") is not True:
        out.append(S.Finding(
            "L-FRM-5", S.ERROR,
            "kernel_checked is not true: an informal derivation is not a formal proof",
            where=where,
        ))


def check_composition(rec, index_by_pid, run_ids_by_pid, out, line_index) -> None:
    pid = rec.get("primitive_id", "<none>")
    where = _where(line_index, pid)
    prov = rec.get("provenance") or {}
    components = prov.get("component_ids") or []
    if rec.get("kind") != "composition":
        return
    if not components:
        out.append(S.Finding(
            "L-CMP-1", S.WARN,
            "record is a composition but declares no component_ids: the composition cannot be audited",
            where=where,
        ))
        return

    run = rec.get("native_run") or {}
    own_run_id = str(run.get("run_id", "")).strip()

    for comp in components:
        if comp not in index_by_pid:
            out.append(S.Finding(
                "L-CMP-2", S.WARN,
                f"component {comp!r} is not present in this ledger: its verification cannot be confirmed",
                where=where,
            ))
            continue
        comp_runs = run_ids_by_pid.get(comp, set())
        if own_run_id and own_run_id in comp_runs:
            out.append(S.Finding(
                "L-CMP-3", S.ERROR,
                f"composition run_id {own_run_id!r} is also a component run_id: "
                "the composition has no fresh native run of its own",
                where=where,
            ))

    if (rec.get("claim") or {}).get("kind") in ("composition", "cumulative"):
        if rec.get("status") in S.MEASURED_STATUSES and run.get("executed_kind") != "native":
            out.append(S.Finding(
                "L-CMP-4", S.ERROR,
                "composition claim without a native composed run: component VERIFIED status is "
                "necessary but never sufficient (RECURSIVE_SPEEDUP_CONSTITUTION.md section 13)",
                where=where,
            ))


def check_contradictions(rec, ratios_by_pid, out, line_index, tolerance) -> None:
    pid = rec.get("primitive_id", "<none>")
    where = _where(line_index, pid)
    declared = rec.get("contradictions") or []

    measured = _speedup_from_measurements(rec)
    if measured is not None:
        prior = ratios_by_pid.get(pid, [])
        for prev_seq, prev_value in prior:
            denom = max(abs(prev_value), abs(measured), 1e-12)
            if abs(prev_value - measured) / denom > tolerance and not declared:
                out.append(S.Finding(
                    "L-CNT-1", S.ERROR,
                    f"repeat run ratio {measured:.6f} conflicts with earlier {prev_value:.6f} "
                    f"(seq {prev_seq}, relative delta > {tolerance}) and no contradiction is recorded: "
                    "preserve the contradiction and downgrade or qualify the claim",
                    where=where,
                ))
        ratios_by_pid.setdefault(pid, []).append((rec.get("seq"), measured))

    if declared and S.CLAIM_RANK.get((rec.get("claim") or {}).get("strength", "NONE"), 0) >= S.CLAIM_RANK["STRONG_LOCAL"]:
        out.append(S.Finding(
            "L-CNT-2", S.ERROR,
            f"{len(declared)} unresolved contradiction(s) recorded; claim strength must not remain "
            "at or above STRONG_LOCAL",
            where=where,
        ))


def check_gaps(lines, out, line_index_gap_ids) -> None:
    open_blocking: Dict[str, List[str]] = defaultdict(list)
    for line in lines:
        rec = line.record
        if rec is None or not S.is_gap_record(rec):
            continue
        gid = rec.get("gap_id", "<none>")
        where = _where(line.index, gid)
        gap_class = rec.get("gap_class")
        if rec.get("legacy_alias") and rec["legacy_alias"] not in S.GAP_CLASS_ALIASES:
            out.append(S.Finding(
                "L-GAP-1", S.WARN,
                f"legacy alias {rec['legacy_alias']!r} is not in the canonical alias table",
                where=where,
            ))
        if rec.get("status") == "closed" and not str(rec.get("closed_by_evidence") or "").strip():
            out.append(S.Finding(
                "L-GAP-2", S.ERROR,
                "gap closed without closed_by_evidence: closure is an evidentiary event, not an edit",
                where=where,
            ))
        if rec.get("status") in ("open", "quarantined"):
            line_index_gap_ids.setdefault(rec.get("primitive_id", ""), []).append(gid)
            if rec.get("claim_impact") == "blocks_promotion":
                open_blocking[rec.get("primitive_id", "")].append(gid)


def check_open_gaps_against_claims(lines, open_blocking, out) -> None:
    if not open_blocking:
        return
    for line in lines:
        rec = line.record
        if rec is None or S.is_gap_record(rec):
            continue
        pid = rec.get("primitive_id")
        blockers = open_blocking.get(pid)
        if not blockers:
            continue
        strength = (rec.get("claim") or {}).get("strength", "NONE")
        if S.CLAIM_RANK.get(strength, 0) > S.CLAIM_RANK["CANDIDATE"]:
            out.append(S.Finding(
                "L-GAP-3", S.ERROR,
                f"open gap(s) {blockers} declare claim_impact=blocks_promotion but the claim is {strength}",
                where=_where(line.index, pid),
            ))


def check_vacuity_and_synthetic(lines, out) -> Dict[str, Any]:
    total = substantive = vacuous = 0
    all_synthetic = True
    for line in lines:
        rec = line.record
        if rec is None:
            continue
        if not (rec.get("provenance") or {}).get("synthetic", rec.get("synthetic", False)):
            all_synthetic = False
        checks = rec.get("checks") or []
        if not checks:
            continue
        report = S.substantive_coverage(checks)
        total += report.total
        substantive += report.substantive
        vacuous += report.vacuous
        if report.all_vacuous:
            out.append(S.Finding(
                "L-VAC-1", S.ERROR,
                f"{report.total} declared validation(s), 0 substantive (vacuous ids: {report.vacuous_ids}): "
                "a high raw test count is not coverage",
                where=_where(line.index, rec.get("primitive_id") or rec.get("gap_id")),
            ))
    if all_synthetic and any(l.record for l in lines):
        out.append(S.Finding(
            "L-SYN-1", S.INFO,
            "every record in this ledger is synthetic: this is a validator fixture, not hardware evidence",
        ))
    return {
        "checks_total": total,
        "checks_substantive": substantive,
        "checks_vacuous": vacuous,
        "all_synthetic": all_synthetic,
    }


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------

def validate_ledger(path: Path, repo_root: Optional[Path] = None,
                    contradiction_tolerance: float = 0.05) -> Tuple[List[S.Finding], Dict[str, Any]]:
    lines = S.load_ledger(path)
    out: List[S.Finding] = []
    records = [l.record for l in lines if l.record is not None]

    # A truncated, empty or mis-pathed ledger is not a ledger that verified.
    if not records:
        for line in lines:
            if line.parse_error:
                out.append(S.Finding("L-SCHEMA", S.ERROR, line.parse_error,
                                     where=f"L{line.index}"))
        out.append(S.Finding(
            "L-EMPTY", S.ERROR,
            "ledger contains no records: an empty ledger is not a verified ledger "
            "(check the path, and that the ledger was not truncated)",
        ))
        return out, {
            "ledger": str(path), "lines": len(lines), "records": 0, "primitives": 0,
            "schema_backend": S.schema_backend(), "checks_total": 0,
            "checks_substantive": 0, "checks_vacuous": 0, "all_synthetic": True,
        }

    check_schema(lines, out)
    check_ordering(lines, out)
    check_status_lifecycle(lines, out)
    check_gaps(lines, out, {})

    index_by_pid = {r.get("primitive_id"): r for r in records if not S.is_gap_record(r)}
    run_ids_by_pid: Dict[str, set] = defaultdict(set)
    for r in records:
        if S.is_gap_record(r):
            continue
        run_id = ((r.get("native_run") or {}).get("run_id") or "").strip()
        if run_id:
            run_ids_by_pid[r.get("primitive_id", "")].add(run_id)

    ratios_by_pid: Dict[str, List[Tuple[Any, float]]] = defaultdict(list)
    open_blocking: Dict[str, List[str]] = defaultdict(list)

    for line in lines:
        rec = line.record
        if rec is None or S.is_gap_record(rec):
            continue
        check_claim_evidence(rec, out, line.index)
        check_execution_binding(rec, out, line.index)
        check_speedups(rec, out, line.index)
        check_operator(rec, out, line.index, repo_root)
        check_dependencies(rec, out, line.index)
        check_formal(rec, out, line.index)
        check_composition(rec, index_by_pid, run_ids_by_pid, out, line.index)
        check_contradictions(rec, ratios_by_pid, out, line.index, contradiction_tolerance)

    # blocking gaps, recomputed after the record scan
    for line in lines:
        rec = line.record
        if rec is not None and S.is_gap_record(rec) and rec.get("status") in ("open", "quarantined") \
                and rec.get("claim_impact") == "blocks_promotion":
            open_blocking[rec.get("primitive_id", "")].append(rec.get("gap_id", "?"))
    check_open_gaps_against_claims(lines, open_blocking, out)

    coverage = check_vacuity_and_synthetic(lines, out)

    summary = {
        "ledger": str(path),
        "lines": len(lines),
        "records": len(records),
        "primitives": len(index_by_pid),
        "schema_backend": S.schema_backend(),
        **coverage,
    }
    return out, summary


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Validate a Silicon Speedup primitive ledger.")
    ap.add_argument("ledger", help="path to the JSONL ledger")
    ap.add_argument("--repo-root", default=None, help="repository root for source_ref/artifact resolution")
    ap.add_argument("--contradiction-tolerance", type=float, default=0.05)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--fast", action="store_true",
                    help="use the bundled schema checker; skips the jsonschema import")
    args = ap.parse_args(argv)
    if args.fast:
        S.set_backend("builtin")
        S._force_builtin(True)

    path = Path(args.ledger)
    if not path.exists():
        print(f"usage error: {path} does not exist", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_root) if args.repo_root else None
    findings, summary = validate_ledger(path, repo_root, args.contradiction_tolerance)

    if args.json:
        payload = {
            "schema_version": S.SCHEMA_VERSION,
            "summary": summary,
            "findings": [f.to_dict() for f in findings],
            "errors": sum(1 for f in findings if f.severity == S.ERROR),
            "warnings": sum(1 for f in findings if f.severity == S.WARN),
        }
        payload["verdict"] = "FAIL" if payload["errors"] else "PASS"
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif not args.quiet:
        print(S.human(findings))
        print("SUMMARY " + json.dumps(summary, sort_keys=True))

    if any(f.severity == S.ERROR for f in findings):
        return 1
    if args.strict and any(f.severity == S.WARN for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())