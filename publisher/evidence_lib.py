#!/usr/bin/env python3
"""Canonical PCSS evidence library.

Shared helpers for: manifest canonicalization, artifact hashing, scenario
identity binding, certificate assembly, and certificate verification.

Every function that produces a hash uses the canonical-bytes convention from
CONSTITUTION.md / publisher/manifest.py. This library is a building block
only; it never promotes a certificate. Only publisher/strict_gate.py may
produce a publication decision.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence

HASH_RE = hashlib.sha256("canonical evidence_lib seed".encode()).hexdigest()

# ---------------------------------------------------------------------------
# Canonical bytes / hashing
# ---------------------------------------------------------------------------

def canonical_bytes(obj: Any) -> bytes:
    """Deterministic JSON serialization used for every hash in PCSS."""
    return (
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    return sha256_bytes(canonical_bytes(obj))


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Artifact ref helpers
# ---------------------------------------------------------------------------

def artifact_ref(path: str | pathlib.Path, data: bytes | None = None,
                 *, sha256: str | None = None) -> dict:
    """Return a standard artifact_ref entry. Exactly one of data/sha256 must be supplied."""
    if (data is None) == (sha256 is None):
        raise ValueError("supply exactly one of data or sha256")
    return {"path": str(path), "sha256": sha256 or sha256_bytes(data)}


def bind_artifact(artifact_path: pathlib.Path) -> dict:
    """Read a file and return its sha256 artifact ref."""
    return artifact_ref(path=artifact_path.as_posix(), sha256=sha256_file(artifact_path))


def bind_json_ref(path: pathlib.Path) -> dict:
    return bind_artifact(path)


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(obj: Any, path: pathlib.Path) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Gate-result helper (must carry at least one evidence path when true)
# ---------------------------------------------------------------------------

def gate_result(value: bool, evidence: Sequence[str], *, detail: Mapping[str, Any] | None = None) -> dict:
    """Build a gate_result dict conforming to the canonical schema.

    Raises if value is True but evidence is empty (no unexplained PASS).
    """
    ev = list(evidence)
    if value and not ev:
        raise ValueError("gate with value=True MUST carry at least one evidence path; no unexplained PASS")
    return {"value": value, "evidence": ev, **({"detail": dict(detail)} if detail else {})}


def gate_fail(evidence: Sequence[str], *, detail: Mapping[str, Any] | None = None) -> dict:
    return gate_result(False, evidence, detail=detail)


def gate_pass(evidence: Sequence[str], *, detail: Mapping[str, Any] | None = None) -> dict:
    return gate_result(True, evidence, detail=detail)


# ---------------------------------------------------------------------------
# Environment fingerprint
# ---------------------------------------------------------------------------

def environment_fingerprint() -> dict:
    return {
        "os": platform.platform(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "pid": None,
        "hostname": platform.node(),
    }


# ---------------------------------------------------------------------------
# Scenario hashing
# ---------------------------------------------------------------------------

def canonicalize_scenario(scenario: dict) -> dict:
    """Canonicalize a scenario manifest by stripping mutable/runtime fields,
    sorting keys, and normalizing types. Returns a new dict suitable for hashing."""
    out = {k: v for k, v in sorted(scenario.items()) if k not in ("_runtime", "_emitted_at")}
    return out


def scenario_hash(scenario: dict) -> str:
    return sha256_json(canonicalize_scenario(scenario))


def validate_scenario_against_schema(scenario: dict) -> None:
    """Validate a scenario manifest against schemas/pcss_scenario.schema.json
    without requiring the jsonschema package (which is not in requirements.txt).
    This performs strict key/enum/required checks compatible with our schema."""
    required = {
        "schema", "schema_version", "scenario_id", "workload", "mathematical_object",
        "baseline", "candidate", "quotient", "reconstruction", "invariant",
        "parameters", "dimensions", "repetitions", "warmup_policy",
        "timing_source", "seed", "expected_observables", "environment",
    }
    missing = required - set(scenario.keys())
    if missing:
        raise ValueError(f"scenario missing required fields: {sorted(missing)}")
    if scenario.get("schema") != "PCSS-SCENARIO":
        raise ValueError("scenario schema != PCSS-SCENARIO")
    if scenario.get("schema_version") != "1.0":
        raise ValueError("scenario schema_version != 1.0")
    kind = scenario.get("workload", {}).get("kind", "")
    if kind not in ("exact_invariant_sector", "projected_exact_diagonal",
                    "linear_exact_closure", "custom_command", "python_plugin"):
        raise ValueError(f"scenario workload.kind {kind!r} not admitted")
    if not scenario.get("quotient", {}).get("definition"):
        raise ValueError("scenario missing quotient.definition")
    if not scenario.get("reconstruction", {}).get("definition"):
        raise ValueError("scenario missing reconstruction.definition")
    if not scenario.get("invariant", {}).get("definition"):
        raise ValueError("scenario missing invariant.definition")


# ---------------------------------------------------------------------------
# Certificate builder / verifier helpers
# ---------------------------------------------------------------------------

def build_certificate(*, run_id: str, scenario: dict, scenario_sha: str,
                      source_sha: str, input_sha: str, env_sha: str,
                      baseline_trace_sha: str, candidate_trace_sha: str,
                      gate_results: dict[str, dict],
                      speedup: float,
                      baseline_measurement: dict,
                      candidate_measurement: dict,
                      metric: str,
                      repetitions: int,
                      warmups: int,
                      seed: int,
                      tolerance: float,
                      toolchain: dict,
                      implementation_identity: dict,
                      parameters: dict,
                      claim_boundary: dict,
                      artifact_refs: dict[str, dict],
                      attribution: dict | None = None) -> dict:
    """Assemble a canonical certificate dict. All sha fields must be pre-computed.
    Does NOT add certificate_sha256 (caller should sign after assembly)."""
    cert = {
        "schema": "PCSS-CERTIFICATE",
        "schema_version": "2.0",
        "run_id": run_id,
        "scenario_id": scenario["scenario_id"],
        "scenario_hash": scenario_sha,
        "source_hash": source_sha,
        "input_hash": input_sha,
        "environment_hash": env_sha,
        "baseline_trace_hash": baseline_trace_sha,
        "candidate_trace_hash": candidate_trace_sha,
        "quotient_hash": scenario.get("_quotient_sha", ""),
        "reconstruction_hash": scenario.get("_reconstruction_sha", ""),
        "invariant_hash": scenario.get("_invariant_sha", ""),
        "performance_hash": scenario.get("_performance_sha", ""),
        "lean_hash": scenario.get("_lean_sha", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "toolchain": toolchain,
        "implementation_identity": implementation_identity,
        "parameters": parameters,
        "seed": seed,
        "tolerance": tolerance,
        "metric": metric,
        "repetitions": repetitions,
        "warmups": warmups,
        "baseline_measurement": baseline_measurement,
        "candidate_measurement": candidate_measurement,
        "speedup": speedup,
        "uncertainty": {"method": "sampled_median_direct", "samples": repetitions},
        "gate_results": gate_results,
        "claim_boundary": claim_boundary,
        "artifact_refs": artifact_refs,
        "attribution": attribution or {},
        "generator": "pcss_native_runner",
    }
    cert["certificate_sha256"] = sha256_json(cert)
    return cert


def sign_certificate(cert: dict) -> dict:
    """Re-sign the certificate after mutation: clears signature, hashes, re-signs."""
    signed = dict(cert)
    signed.pop("certificate_sha256", None)
    signed["certificate_sha256"] = sha256_json(signed)
    return signed


def verify_certificate_binding(cert: dict) -> tuple[bool, str]:
    """Verify the certificate hash binding is consistent (not tampered)."""
    stored = cert.get("certificate_sha256")
    if not stored:
        return False, "missing certificate_sha256"
    recomputed = sha256_json({k: v for k, v in cert.items() if k != "certificate_sha256"})
    if recomputed != stored:
        return False, "certificate hash mismatch"
    return True, "hash binding consistent"


# ---------------------------------------------------------------------------
# Re-check gate evidence at validation time (Phase 14 compatibility)
# ---------------------------------------------------------------------------

def verify_gate_evidence(gate_results: dict) -> list[str]:
    """Return list of gate names with unexplained PASS (value=True, empty evidence)."""
    bad = []
    for name in ("integrity", "reproducibility", "quotient_forward", "reconstruction_reverse",
                 "invariants", "performance", "lean"):
        gr = gate_results.get(name, {})
        if gr.get("value") is True and not gr.get("evidence"):
            bad.append(name)
    return bad


# ---------------------------------------------------------------------------
# Offsets / statistics (for engines/performance to share)
# ---------------------------------------------------------------------------

def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    k = (len(vals) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(vals) - 1)
    frac = k - lo
    return vals[lo] + frac * (vals[hi] - vals[lo])


def median(values: list[float]) -> float:
    return percentile(values, 0.5)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    if len(sys.argv) < 2:
        print("usage: evidence_lib.py verify-batch CERT_PATH ...", file=sys.stderr)
        print("       evidence_lib.py hash-manifest MANIFEST.json", file=sys.stderr)
        return 2
    if sys.argv[1] == "hash-manifest":
        manifest = load_json(pathlib.Path(sys.argv[2]))
        print(scenario_hash(manifest))
        return 0
    if sys.argv[1] == "verify-batch":
        fail = 0
        for p in sys.argv[2:]:
            cert = load_json(pathlib.Path(p))
            ok, msg = verify_certificate_binding(cert)
            bad = verify_gate_evidence(cert.get("gate_results", {}))
            if not ok or bad:
                print(f"FAIL {p}: {msg}; unexplained_pass={bad}")
                fail += 1
            else:
                print(f"OK   {p}")
        return fail
    print(f"unknown command {sys.argv[1]!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
