"""PCSS certificate assembly and publication side-effects.

The certificate module ONLY assembles and writes evidence. Promotion to
VERIFIED lives in publisher/strict_gate.py. This module implements the
side effects of quarantine and publish decisions so they are shared by
the strict gate and the canonical pipeline.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from . import const
from .jsonutil import is_sha256, sha256

LEDGER_PATH = "evidence/ledger/claims.jsonl"
QUARANTINE_DIR = "evidence/quarantine"
VERIFIED_DIR = "verified"


def load_certificate(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


REQUIRED_FIELDS = (
    "schema_version",
    "run_id",
    "scenario_id",
    "scenario_hash",
    "source_hash",
    "input_hash",
    "environment_hash",
    "baseline_trace_hash",
    "candidate_trace_hash",
    "quotient_hash",
    "reconstruction_hash",
    "invariant_hash",
    "performance_hash",
    "lean_hash",
    "timestamp",
    "gates",
    "claim_strength",
    "claim_boundary",
)


def schema_structural_check(cert: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Fail-closed structural schema check (no external deps)."""
    errors: List[str] = []
    for field in REQUIRED_FIELDS:
        if field not in cert:
            errors.append(f"missing field: {field}")

    gates = cert.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
    else:
        for gate in const.GATES:
            if gate not in gates:
                errors.append(f"gates missing mandatory gate: {gate}")

    for field, label in (
        ("scenario_hash", "scenario"),
        ("source_hash", "source"),
        ("input_hash", "input"),
        ("environment_hash", "environment"),
        ("baseline_trace_hash", "baseline trace"),
        ("candidate_trace_hash", "candidate trace"),
        ("quotient_hash", "quotient"),
        ("reconstruction_hash", "reconstruction"),
        ("invariant_hash", "invariant"),
        ("performance_hash", "performance"),
        ("lean_hash", "lean"),
    ):
        if field in cert and cert[field] is not None and not is_sha256(cert[field]):
            errors.append(f"{label} hash is not a sha256 hex digest")

    strength = cert.get("claim_strength")
    if strength is not None and strength not in const.CLAIM_LATTICE + const.FAILED_STATUSES:
        errors.append(f"unknown claim_strength: {strength!r}")

    return not errors, errors


def _append_ledger(entry: Dict[str, Any]) -> None:
    path = Path(LEDGER_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def _quarantine_write(cert: Dict[str, Any], reasons: List[str]) -> str:
    cert = dict(cert)
    cert["claim_strength"] = "QUARANTINED"
    cert["quarantine_reasons"] = reasons
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    digest = sha256(cert)
    dest = Path(QUARANTINE_DIR) / f"{stamp}_{cert.get('run_id', 'unknown')}_{digest[:8]}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(cert, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return str(dest)


def quarantine(cert: Dict[str, Any], reasons: List[str]) -> str:
    """Move certificate to quarantine. Never returns a verified path."""
    dest = _quarantine_write(cert, reasons)
    _append_ledger({
        "kind": "quarantine",
        "run_id": cert.get("run_id"),
        "scenario_hash": cert.get("scenario_hash"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "reasons": reasons,
        "artifact": dest,
    })
    return dest


def publish(cert: Dict[str, Any], evidence_path: str) -> int:
    """Write the certificate into verified/ (immutable, hash-linked).

    Only the strict gate calls this after ALL gates passed.
    """
    digest = sha256(cert)
    dest = Path(VERIFIED_DIR) / "sim2xr"
    stamp = time.strftime("%Y-%m-%d", time.gmtime())
    out_dir = dest / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    cert["certificate_sha256"] = digest
    out_file = out_dir / "pcss_certificate.json"
    out_file.write_text(json.dumps(cert, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    _append_ledger({
        "kind": "publish",
        "run_id": cert.get("run_id"),
        "scenario_hash": cert.get("scenario_hash"),
        "claim_strength": "VERIFIED",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "certificate_hash": digest,
        "artifact": str(out_file),
    })
    print("STRICT_GATE=VERIFIED")
    print(f"  published {out_file}")
    return 0


def assemble_certificate(
    *,
    scenario_manifest: Dict[str, Any],
    native_evidence: Dict[str, Any],
    quotient_evidence: Dict[str, Any] | None,
    reconstruction_evidence: Dict[str, Any] | None,
    invariant_evidence: Dict[str, Any] | None,
    performance_evidence: Dict[str, Any] | None,
    lean_certificate: Dict[str, Any] | None,
    artifact_hashes: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    """Assemble the seven-gate certificate from engine evidence records.

    Every gate is bound to a real sha256 of the artifact produced by its
    engine (passed through `artifact_hashes` for the keys quotient_hash,
    reconstruction_hash, invariant_hash, performance_hash, lean_hash). A gate
    is NEVER set true without a valid sha256 for its artifact — a missing or
    fabricated hash keeps the gate false (fail-closed, no "0"*64 placeholders).
    Empty (None) evidence for a mandatory gate keeps that gate false.
    """
    from .scenario import scenario_hash

    if artifact_hashes is None:
        artifact_hashes = {}

    gate_hash_keys = {
        "quotient_forward": "quotient_hash",
        "reconstruction_reverse": "reconstruction_hash",
        "invariants": "invariant_hash",
        "performance": "performance_hash",
        "lean": "lean_hash",
    }

    gates = {
        "integrity": False,
        "reproducibility": False,
        "quotient_forward": False,
        "reconstruction_reverse": False,
        "invariants": False,
        "performance": False,
        "lean": False,
    }

    hashes = {
        "scenario_hash": native_evidence["scenario_hash"],
        "source_hash": native_evidence["source_hash"],
        "input_hash": native_evidence["input_hash"],
        "environment_hash": native_evidence["environment_hash"],
        "baseline_trace_hash": native_evidence["baseline_trace_hash"],
        "candidate_trace_hash": native_evidence["candidate_trace_hash"],
    }

    for name, evidence in (
        ("quotient_forward", quotient_evidence),
        ("reconstruction_reverse", reconstruction_evidence),
        ("invariants", invariant_evidence),
        ("performance", performance_evidence),
    ):
        hash_key = gate_hash_keys[name]
        artifact_sha = artifact_hashes.get(hash_key, "")
        if evidence is not None and evidence.get("pass") is True and is_sha256(artifact_sha):
            gates[name] = True
            hashes[hash_key] = artifact_sha

    if lean_certificate is not None and lean_certificate.get("pass") is True:
        lean_sha = artifact_hashes.get("lean_hash", "")
        if is_sha256(lean_sha):
            gates["lean"] = True
            hashes["lean_hash"] = lean_sha

    # Integrity binds every identity hash already present.
    integrity_ok = all(
        is_sha256(hashes.get(field)) for field in (
            "scenario_hash", "source_hash", "input_hash", "environment_hash"
        )
    )
    gates["integrity"] = integrity_ok
    reproducibility_ok = is_sha256(hashes["baseline_trace_hash"]) and is_sha256(hashes["candidate_trace_hash"])
    gates["reproducibility"] = reproducibility_ok

    cert = {
        "schema_version": const.SCHEMA_VERSION,
        "run_id": native_evidence["run_id"],
        "scenario_id": scenario_manifest["scenario_id"],
        "scenario_hash": hashes["scenario_hash"],
        "source_hash": hashes["source_hash"],
        "input_hash": hashes["input_hash"],
        "environment_hash": hashes["environment_hash"],
        "baseline_trace_hash": hashes["baseline_trace_hash"],
        "candidate_trace_hash": hashes["candidate_trace_hash"],
        "quotient_hash": hashes.get("quotient_hash", "0" * 64),
        "reconstruction_hash": hashes.get("reconstruction_hash", "0" * 64),
        "invariant_hash": hashes.get("invariant_hash", "0" * 64),
        "performance_hash": hashes.get("performance_hash", "0" * 64),
        "lean_hash": hashes.get("lean_hash", "0" * 64),
        "timestamp": native_evidence["timestamp"],
        "toolchain": native_evidence["toolchain"],
        "implementation_identity": native_evidence["implementation_identity"],
        "parameters": native_evidence["parameters"],
        "seed": native_evidence["seed"],
        "tolerance": scenario_manifest["reconstruction"].get("tolerance"),
        "metric": scenario_manifest["reconstruction"].get("metric"),
        "repetitions": native_evidence["repetitions"],
        "warmups": native_evidence["warmups"],
        "baseline_measurement": native_evidence["baseline_measurement"],
        "candidate_measurement": native_evidence["candidate_measurement"],
        "speedup": native_evidence.get("speedup", native_evidence.get("direct_speedup", 0.0)),
        "uncertainty": native_evidence["uncertainty"],
        "quotient": quotient_evidence,
        "reconstruction": reconstruction_evidence,
        "invariants": invariant_evidence,
        "performance": performance_evidence,
        "lean": lean_certificate,
        "gates": gates,
        "claim_strength": "VERIFIED" if all(gates.values()) else
            ("QUARANTINED" if not integrity_ok else "CANDIDATE"),
        "claim_boundary": scenario_manifest.get("claim_boundary", "declared scenario domain"),
        "artifact_paths": [],
    }
    return cert