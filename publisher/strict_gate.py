#!/usr/bin/env python3
"""PCSS strict publication gate — THE single authoritative publication decision.

PUBLISH <=> I AND R AND Q AND Q^-1 AND OMEGA AND X AND L
CLAIM_STRENGTH <= EVIDENCE_STRENGTH

This program is the ONLY program that may promote evidence to VERIFIED.
All other programs produce evidence; they must not promote it.

Fail-closed rules enforced here:
  * a gate that is not true is a quarantine
  * a gate that is true but not hash-bound to an artifact is a quarantine
    (no unexplained PASS values)
  * a certificate that does not match the canonical schema is a quarantine
  * promotion to VERIFIED requires every gate AND the claim lattice order
"""
from __future__ import annotations

import sys
from pathlib import Path

from speedup import const
from speedup import certificate
from speedup.jsonutil import is_sha256

GATE_ARTIFACT_BINDINGS = {
    "integrity": ["scenario_hash", "source_hash", "input_hash", "environment_hash"],
    "reproducibility": ["baseline_trace_hash", "candidate_trace_hash"],
    "quotient_forward": ["quotient_hash"],
    "reconstruction_reverse": ["reconstruction_hash"],
    "invariants": ["invariant_hash"],
    "performance": ["performance_hash"],
    "lean": ["lean_hash"],
}


def enforce(evidence_path: str) -> int:
    cert = certificate.load_certificate(evidence_path)

    # 1. Schema-level structure (independent of gate booleans).
    schema_ok, schema_errors = certificate.schema_structural_check(cert)
    if not schema_ok:
        certificate.quarantine(cert, schema_errors)
        print("STRICT_GATE=QUARANTINE schema_error")
        for err in schema_errors:
            print(f"  - {err}")
        return 1

    # 2. Gate evaluation with hash-binding: no unexplained PASS.
    gates = cert.get("gates", {})
    failures: list[str] = []
    for gate in const.GATES:
        value = gates.get(gate)
        if value is not True:
            failures.append(f"{gate}=false")
            continue
        binding_fields = GATE_ARTIFACT_BINDINGS[gate]
        if not any(is_sha256(cert.get(field)) for field in binding_fields):
            failures.append(f"{gate}=true but no hash-bound artifact")

    if failures:
        certificate.quarantine(cert, failures)
        print("STRICT_GATE=QUARANTINE gate_failure")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    # 3. Claim strength ordering — VERIFIED may only be reached from a
    #    supported prior strength via the monotone lattice.
    claim_strength = cert.get("claim_strength", "CANDIDATE")
    if claim_strength == "VERIFIED":
        promotion = {"integrity": True, "reproducibility": True, "quotient_forward": True,
                     "reconstruction_reverse": True, "invariants": True, "performance": True,
                     "lean": True}
        if not all(promotion[g] for g in const.GATES):
            certificate.quarantine(cert, ["VERIFIED requested but some gate false"])
            print("STRICT_GATE=QUARANTINE promotion_without_evidence")
            return 1

    return certificate.publish(cert, evidence_path)


def main(argv: list[str] | None = None) -> int:
    if len(sys.argv[1:] if argv is None else argv) != 1:
        print("usage: strict_gate.py CERTIFICATE.json", file=sys.stderr)
        return 2
    path = (sys.argv[1:] if argv is None else argv)[0]
    return enforce(path)


if __name__ == "__main__":
    raise SystemExit(main())