#!/usr/bin/env python3
"""Validate one Silicon Speedup evidence record (one native run).

Read-only. This program never promotes a claim, never writes a record, and
never invents a missing artifact. It produces findings and an exit code.

Exit codes:
  0  no ERROR findings (warnings may be present)
  1  at least one ERROR finding
  2  usage / IO error

Usage:
  validate-run.py RECORD.json [--repo-root DIR] [--json] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ssproof as S  # noqa: E402

SCHEMA = "evidence-record.schema.json"

PERFORMANCE_KINDS = ("performance", "composition", "cumulative")


def _wants_perf(record: dict) -> bool:
    claim = record.get("claim") or {}
    return claim.get("kind") in PERFORMANCE_KINDS and claim.get("strength") not in (None, "NONE")


def _arms(record: dict) -> list:
    timing = record.get("timing") or {}
    return timing.get("arms") or []


def _arm_by_name(arms: list, *names: str):
    for arm in arms:
        if str(arm.get("name", "")).lower() in names:
            return arm
    return None


def check_schema(record: dict, where: str) -> list:
    errs = S.validate_against_schema(record, SCHEMA)
    return [
        S.Finding("R-SCHEMA", S.ERROR, f"{e}", where=where)
        for e in errs
    ]


def check_execution(record: dict, where: str) -> list:
    out: list = []
    kind = record.get("executed_kind")
    claim = record.get("claim") or {}
    strength = claim.get("strength", "NONE")

    if kind != "native" and S.CLAIM_RANK.get(strength, 0) > S.CLAIM_RANK["CANDIDATE"]:
        out.append(S.Finding(
            "R-EXEC-1", S.ERROR,
            f"executed_kind={kind!r} cannot support claim strength {strength}; "
            "only a native execution can",
            where=where,
        ))

    exit_code = record.get("exit_code")
    if exit_code is None:
        out.append(S.Finding(
            "R-EXIT-1", S.WARN,
            "exit_code is null: verdict is UNKNOWN, not PASS",
            where=where,
        ))
    elif exit_code == 0 and _wants_perf(record):
        out.append(S.Finding(
            "R-EXIT-2", S.INFO,
            "exit_code 0 recorded; a successful exit is not a timing result and not a correctness result",
            where=where,
        ))

    if not str(record.get("command", "")).strip():
        out.append(S.Finding("R-CMD-1", S.ERROR, "no command line recorded", where=where))
    return out


def resolve_artifact(raw_path: str, record_path: Path, repo_root: Path | None) -> Path | None:
    """Locate a recorded artifact.

    Records legitimately refer to artifacts either repository-relative or
    relative to the record itself. Try both, then walk up from the record's own
    directory, so a fixture that ships with its own raw artifacts resolves
    without the caller knowing where the skill was installed.
    """
    if not raw_path:
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate if candidate.exists() else None
    roots: list[Path] = []
    if repo_root is not None:
        roots.append(Path(repo_root))
    base = record_path.resolve().parent
    roots.append(base)
    roots.extend(base.parents[:3])
    for root in roots:
        probe = root / candidate
        if probe.exists():
            return probe
    return None


def check_provenance(record: dict, where: str, repo_root: Path | None,
                     record_path: Path | None = None) -> list:
    out: list = []
    run_id = record.get("run_id")
    if not str(run_id or "").strip():
        out.append(S.Finding("R-PROV-1", S.ERROR, "missing run_id", where=where))

    artifacts = record.get("artifacts") or []
    if not artifacts:
        sev = S.ERROR if S.CLAIM_RANK.get((record.get("claim") or {}).get("strength", "NONE"), 0) > S.CLAIM_RANK["CANDIDATE"] else S.WARN
        out.append(S.Finding(
            "R-PROV-2", sev,
            "no raw artifact recorded: an exit code without an artifact is not a result",
            where=where,
        ))
    seen_ids = set()
    for art in artifacts:
        art_id = f"{art.get('role')}::{art.get('path')}"
        if art_id in seen_ids:
            out.append(S.Finding("R-PROV-3", S.WARN, f"duplicate artifact {art_id!r}", where=where))
        seen_ids.add(art_id)
        if not S.is_sha256(art.get("sha256")):
            out.append(S.Finding("R-PROV-4", S.ERROR, f"artifact {art_id!r} has no valid sha256", where=where))
        if record_path is not None:
            full = resolve_artifact(str(art.get("path", "")), record_path, repo_root)
            if full is None:
                out.append(S.Finding(
                    "R-PROV-5", S.ERROR,
                    f"artifact path does not exist: {art.get('path')}", where=where,
                ))
            elif S.is_sha256(art.get("sha256")):
                actual = S.sha256_file(full)
                if actual != art.get("sha256"):
                    out.append(S.Finding(
                        "R-PROV-6", S.ERROR,
                        f"artifact hash mismatch for {art.get('path')}: recorded {art.get('sha256')} actual {actual}",
                        where=where,
                    ))
    return out


def check_timing(record: dict, where: str) -> list:
    out: list = []
    if not _wants_perf(record):
        return out
    arms = _arms(record)
    if not arms:
        out.append(S.Finding(
            "R-TIME-1", S.ERROR,
            "performance claim with no timing arms: a successful exit without a timing result is not a speedup",
            where=where,
        ))
        return out

    positive = []
    for arm in arms:
        stats = S.arm_stats(arm.get("samples") or [])
        if not stats["has_timing"]:
            out.append(S.Finding(
                "R-TIME-2", S.ERROR,
                f"arm {arm.get('name')!r} has no positive sample (n={stats['n']}): timing domain is empty",
                where=where,
            ))
        else:
            positive.append((arm, stats))

    if len(positive) < 2:
        out.append(S.Finding(
            "R-TIME-3", S.ERROR,
            "fewer than two arms with real timings: a ratio needs a baseline and a candidate",
            where=where,
        ))

    for arm, stats in positive:
        if stats["n"] < S.MIN_SAMPLES:
            out.append(S.Finding(
                "R-TIME-4", S.WARN,
                f"arm {arm.get('name')!r} has n={stats['n']} < {S.MIN_SAMPLES}: "
                "REPRODUCED (and therefore STRONG_LOCAL performance) is not supported",
                where=where,
            ))

    scopes = [a.get("scope") for a in arms]
    if not S.scopes_compatible(scopes):
        out.append(S.Finding(
            "R-TIME-5", S.ERROR,
            f"timing scopes are not comparable: {scopes}",
            where=where,
        ))

    base = _arm_by_name(arms, "baseline")
    cand = _arm_by_name(arms, "candidate")
    if base is None or cand is None:
        out.append(S.Finding(
            "R-TIME-6", S.WARN,
            f"arms should be named baseline/candidate; got {[a.get('name') for a in arms]}",
            where=where,
        ))
    else:
        bs = S.arm_stats(base.get("samples") or [])
        cs = S.arm_stats(cand.get("samples") or [])
        if bs["has_timing"] and cs["has_timing"]:
            if cs["median"] > bs["median"]:
                out.append(S.Finding(
                    "R-TIME-7", S.ERROR,
                    f"candidate median {cs['median']} > baseline median {bs['median']}: "
                    "this is a regression, not a speedup",
                    where=where,
                ))
            bm = base.get("memory_bytes")
            cm = cand.get("memory_bytes")
            if isinstance(bm, int) and isinstance(cm, int) and cm > bm:
                sev = S.ERROR if cs["median"] <= bs["median"] else S.WARN
                out.append(S.Finding(
                    "R-MEM-1", sev,
                    f"candidate memory {cm} > baseline memory {bm}: "
                    "a memory increase must be recorded, not hidden behind a passing gate",
                    where=where,
                ))
    return out


def check_correctness(record: dict, where: str) -> list:
    out: list = []
    claim = record.get("claim") or {}
    kind = claim.get("kind")
    strength = claim.get("strength", "NONE")
    corr = record.get("correctness") or {}

    eq = corr.get("equivalence")
    rev = corr.get("reverse_reconstruction")

    eq_failed = eq is not None and eq.get("pass") is False
    if eq_failed:
        out.append(S.Finding(
            "R-CORR-1", S.ERROR,
            f"equivalence gate failed ({eq.get('note') or eq.get('metric') or 'no detail'}): "
            "correctness promotion is rejected",
            where=where,
        ))
        if S.CLAIM_RANK.get(strength, 0) > S.CLAIM_RANK["CANDIDATE"]:
            out.append(S.Finding(
                "R-CORR-2", S.ERROR,
                f"claim strength {strength} asserted over a failed equivalence check",
                where=where,
            ))

    needs_equivalence = kind in ("implementation", "composition", "cumulative", "hardware_mechanism")
    if needs_equivalence and S.CLAIM_RANK.get(strength, 0) >= S.CLAIM_RANK["STRONG_LOCAL"]:
        if eq is None:
            out.append(S.Finding(
                "R-CORR-3", S.ERROR,
                f"{strength}/{kind} requires equivalence evidence; none recorded",
                where=where,
            ))
        elif eq.get("pass") is None:
            out.append(S.Finding("R-CORR-4", S.WARN, "equivalence pass is UNKNOWN (null)", where=where))
        elif not str(eq.get("artifact_ref", "")).strip():
            out.append(S.Finding(
                "R-CORR-5", S.ERROR,
                "equivalence pass carries no artifact_ref: an unexplained PASS is a quarantine",
                where=where,
            ))
        if eq is not None and eq.get("vacuous") is True:
            out.append(S.Finding(
                "R-CORR-6", S.ERROR,
                "equivalence evidence is self-declared vacuous: it cannot support any correctness claim",
                where=where,
            ))

    if S.CLAIM_RANK.get(strength, 0) >= S.CLAIM_RANK["VERIFIED"]:
        if rev is None or rev.get("pass") is not True:
            out.append(S.Finding(
                "R-CORR-7", S.ERROR,
                "VERIFIED requires a passing reverse reconstruction (CONSTITUTION.md Article 4)",
                where=where,
            ))
        if corr.get("invariant") is None:
            out.append(S.Finding(
                "R-CORR-8", S.ERROR,
                "VERIFIED requires recorded invariant evidence (CONSTITUTION.md Article 5)",
                where=where,
            ))
    return out


def check_scaling(record: dict, where: str) -> list:
    out: list = []
    claim = record.get("claim") or {}
    if claim.get("strength") in (None, "NONE", "CANDIDATE"):
        return out
    statement = str(claim.get("statement", "")).lower()
    scaling = record.get("scaling") or {}
    sizes = scaling.get("sizes") or []
    sizes = [s for s in sizes if S.is_number(s)]
    if any(word in statement for word in ("scal", "complexity", "asymptot", "across sizes", "linear time")):
        if len(sizes) < 2:
            out.append(S.Finding(
                "R-SCL-1", S.ERROR,
                f"scaling claim with {len(sizes)} size(s): a single-size result does not establish scaling",
                where=where,
            ))
        else:
            if len(scaling.get("ratios") or []) != len(sizes):
                out.append(S.Finding(
                    "R-SCL-2", S.ERROR, "scaling sizes and ratios are not aligned", where=where
                ))
            if any(S.is_number(s) and s <= 1 for s in sizes):
                out.append(S.Finding(
                    "R-SCL-3", S.WARN,
                    f"scaling sizes include a trivial point {sizes}",
                    where=where,
                ))
    return out


def check_mechanism(record: dict, where: str) -> list:
    out: list = []
    claim = record.get("claim") or {}
    if claim.get("kind") != "hardware_mechanism":
        return out
    mech = record.get("mechanism") or {}
    evidence = mech.get("evidence") or []
    substantive_kinds = {"counterfactual", "ablation", "hardware_counter",
                         "microarchitectural_trace", "model_fit"}
    have = [e for e in evidence if e.get("kind") in substantive_kinds]
    if S.CLAIM_RANK.get(claim.get("strength", "NONE"), 0) > S.CLAIM_RANK["CANDIDATE"]:
        if not have:
            out.append(S.Finding(
                "R-MECH-1", S.ERROR,
                "hardware mechanism claim without mechanism-specific evidence: "
                "the claim is restricted to 'unexplained observed effect'",
                where=where,
            ))
        elif mech.get("mechanism_specific") is not True:
            out.append(S.Finding(
                "R-MECH-2", S.ERROR,
                "mechanism evidence present but mechanism_specific is not asserted true",
                where=where,
            ))
        if record.get("executed_kind") != "native":
            out.append(S.Finding(
                "R-MECH-3", S.WARN,
                "mechanism claims require the declared platform; a non-native run cannot establish hardware mechanism",
                where=where,
            ))
    return out


def check_formal(record: dict, where: str) -> list:
    out: list = []
    claim = record.get("claim") or {}
    formal = record.get("formal")
    wants = claim.get("kind") == "formal" or S.CLAIM_RANK.get(claim.get("strength", "NONE"), 0) >= S.CLAIM_RANK["FORMAL_PARTIAL"]
    if not wants:
        return out
    if formal is None:
        out.append(S.Finding("R-FRM-1", S.ERROR, "formal claim with no formal block", where=where))
        return out
    if not str(formal.get("theorem_target", "")).strip():
        out.append(S.Finding("R-FRM-2", S.ERROR, "no theorem target recorded", where=where))
    if not str(formal.get("file", "")).strip():
        out.append(S.Finding("R-FRM-3", S.ERROR, "no Lean source file recorded", where=where))
    if not str(formal.get("command", "")).strip():
        out.append(S.Finding("R-FRM-4", S.ERROR, "no proof command recorded", where=where))
    if formal.get("exit_status") != 0:
        out.append(S.Finding(
            "R-FRM-5", S.ERROR,
            f"proof exit_status is {formal.get('exit_status')!r}, not 0: no proof was completed",
            where=where,
        ))
    if formal.get("kernel_checked") is not True:
        out.append(S.Finding(
            "R-FRM-6", S.ERROR,
            "kernel_checked is not true: an informal derivation is not a formal proof",
            where=where,
        ))
    return out


def check_vacuity(record: dict, where: str) -> list:
    out: list = []
    checks = record.get("checks") or []
    report = S.substantive_coverage(checks)
    claim_strength = (record.get("claim") or {}).get("strength", "NONE")

    if report.all_vacuous:
        out.append(S.Finding(
            "R-VAC-1", S.ERROR,
            f"{report.total} declared validation(s), 0 substantive: a batch of vacuous checks "
            "does not become evidence by its test count",
            where=where,
            detail=report.to_dict(),
        ))
    elif report.vacuous:
        out.append(S.Finding(
            "R-VAC-2", S.WARN,
            f"{report.vacuous}/{report.total} validation(s) vacuous and excluded from substantive coverage",
            where=where,
            detail=report.to_dict(),
        ))

    if (checks and report.substantive == 0
            and S.CLAIM_RANK.get(claim_strength, 0) > S.CLAIM_RANK["CANDIDATE"]):
        out.append(S.Finding(
            "R-VAC-3", S.ERROR,
            f"claim strength {claim_strength} rests only on vacuous validations",
            where=where,
        ))

    for check in checks:
        result = S.analyze_check(check)
        if not result.substantive:
            out.append(S.Finding(
                "R-VAC-4", S.INFO,
                f"check {check.get('check_id')!r} excluded as vacuous: " + "; ".join(result.reasons),
                where=where,
            ))
    return out


def check_dependencies(record: dict, where: str) -> list:
    out: list = []
    deps = record.get("dependencies") or []
    claim = record.get("claim") or {}
    blocks = [d for d in deps if d.get("status") in ("unresolved", "assumed")]
    if blocks:
        strong = S.CLAIM_RANK.get(claim.get("strength", "NONE"), 0) > S.CLAIM_RANK["CANDIDATE"]
        sev = S.ERROR if strong else S.WARN
        for dep in blocks:
            out.append(S.Finding(
                "R-DEP-1", sev,
                f"dependency {dep.get('id')!r} is {dep.get('status')}: "
                "a successful partial test does not hide an unresolved dependency",
                where=where,
            ))
    return out


def check_claim(record: dict, where: str) -> list:
    out: list = []
    claim = record.get("claim") or {}
    strength = claim.get("strength", "NONE")
    kind = claim.get("kind", "none")
    evidence_strength = record.get("evidence_strength", "UNEVIDENCED")

    reason = S.claim_exceeds_evidence(strength, evidence_strength, kind)
    if reason:
        out.append(S.Finding(
            "R-CLM-1", S.ERROR,
            f"{reason} (claim: {strength}/{kind})",
            where=where,
        ))
    if claim.get("assigned_manually") is True and S.CLAIM_RANK.get(strength, 0) >= S.CLAIM_RANK["STRONG_LOCAL"]:
        out.append(S.Finding(
            "R-CLM-2", S.ERROR,
            "strength assigned manually above CANDIDATE: a label without evidence references must not pass",
            where=where,
        ))
    if not S.transition_chain_is_complete(evidence_strength, record.get("transition_records") or []):
        out.append(S.Finding(
            "R-CLM-3", S.ERROR,
            f"evidence_strength {evidence_strength} is not backed by an ordered, event-bound "
            "transition chain from UNEVIDENCED: an evidence level above OBSERVED cannot be "
            "self-declared",
            where=where,
        ))
    if not str(claim.get("scope", "")).strip():
        out.append(S.Finding(
            "R-CLM-4", S.ERROR, "claim has no scope: an unscoped claim is an unscoped claim",
            where=where,
        ))
    return out


def check_synthetic(record: dict, where: str) -> list:
    out: list = []
    if record.get("synthetic") is True:
        out.append(S.Finding(
            "R-SYN-1", S.INFO,
            "record is marked synthetic: excluded from substantive coverage and from hardware evidence",
            where=where,
        ))
    else:
        for check in record.get("checks") or []:
            if check.get("synthetic") is True:
                out.append(S.Finding(
                    "R-SYN-2", S.WARN,
                    f"check {check.get('check_id')!r} is synthetic inside a non-synthetic record: "
                    "label the whole record or the check, do not mix silently",
                    where=where,
                ))
    return out


def validate_record(record: dict, where: str, repo_root: Path | None,
                    record_path: Path | None = None) -> list:
    if not isinstance(record, dict):
        return [S.Finding(
            "R-SCHEMA", S.ERROR,
            f"document is a JSON {type(record).__name__}, expected an object",
            where=where,
        )]
    findings: list = []
    findings += check_schema(record, where)
    findings += check_execution(record, where)
    findings += check_provenance(record, where, repo_root, record_path)
    findings += check_timing(record, where)
    findings += check_correctness(record, where)
    findings += check_scaling(record, where)
    findings += check_mechanism(record, where)
    findings += check_formal(record, where)
    findings += check_vacuity(record, where)
    findings += check_dependencies(record, where)
    findings += check_claim(record, where)
    findings += check_synthetic(record, where)
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate one Silicon Speedup evidence record.")
    ap.add_argument("record", help="path to evidence-record JSON")
    ap.add_argument("--repo-root", default=None,
                    help="resolve artifact paths and hashes under this directory")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--fast", action="store_true",
                    help="use the bundled schema checker; skips the jsonschema import")
    args = ap.parse_args(argv)
    if args.fast:
        S.set_backend("builtin")
        S._force_builtin(True)

    path = Path(args.record)
    if not path.exists():
        print(f"usage error: {path} does not exist", file=sys.stderr)
        return 2
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        print(f"ERROR R-SCHEMA [{path.name}] not valid UTF-8: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR R-SCHEMA [{path.name}] invalid JSON: {exc}", file=sys.stderr)
        return 1

    repo_root = Path(args.repo_root) if args.repo_root else None
    findings = validate_record(record, where=path.name, repo_root=repo_root, record_path=path)

    if args.json:
        print(S.findings_to_json(findings))
    elif not args.quiet:
        print(S.human(findings))

    if any(f.severity == S.ERROR for f in findings):
        return 1
    if args.strict and any(f.severity == S.WARN for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())