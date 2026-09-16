"""PCSS canonical scenario manifest handling.

A scenario manifest uniquely determines workload, mathematical object,
baseline, candidate, quotient, reconstruction, invariants, parameters,
dimensions, repetitions, warmups, timing source, seed, expected
observables and environment requirements.  The manifest is canonicalized
(sorted JSON) then hashed.  Every derived artifact references the exact
scenario hash.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .jsonutil import canonical_bytes, sha256


class ScenarioError(ValueError):
    pass


def load_manifest(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ScenarioError("scenario manifest must be a JSON object")
    return data


def canonicalize_manifest(manifest: dict) -> dict:
    """Return a deep-copied manifest with deterministically sorted keys
    nested at every level so hashing is independent of key insertion order."""
    return _canonical(manifest)


def _canonical(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _canonical(v) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if isinstance(obj, list):
        return [_canonical(v) for v in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    raise ScenarioError(f"non-JSON value in manifest: {obj!r}")


def scenario_hash(manifest: dict) -> str:
    """SHA-256 over canonical manifest bytes."""
    return sha256(canonicalize_manifest(manifest))


def validate_manifest(manifest: dict) -> None:
    """Structural validation of the manifest before execution.

    This is a fail-fast gate.  It does not replace schema validation when a
    JSON schema tool is available, but it must never pass a manifest that is
    missing the mandatory identity fields.
    """
    required = (
        "scenario_id",
        "workload",
        "mathematical_object",
        "baseline",
        "candidate",
        "quotient",
        "reconstruction",
        "invariants",
        "parameters",
        "dimensions",
        "repetitions",
        "warmups",
        "timing_source",
        "seed",
        "expected_observables",
        "environment_requirements",
    )
    missing = [name for name in required if manifest.get(name) is None]
    if missing:
        raise ScenarioError(f"scenario manifest missing required fields: {', '.join(missing)}")
    if not isinstance(manifest.get("repetitions"), int) or manifest["repetitions"] < 1:
        raise ScenarioError("repetitions must be a positive integer")
    if not isinstance(manifest.get("warmups"), int) or manifest["warmups"] < 0:
        raise ScenarioError("warmups must be a non-negative integer")
    if not isinstance(manifest.get("dimensions"), dict) or not isinstance(
        manifest["dimensions"].get("d"), int
    ):
        raise ScenarioError("dimensions.d must be a positive integer")
    if manifest["dimensions"]["d"] < 1:
        raise ScenarioError("dimensions.d must be positive")
    if not isinstance(manifest.get("reconstruction"), dict):
        raise ScenarioError("reconstruction must be an object with metric/tolerance")
    tolerance = manifest["reconstruction"].get("tolerance")
    if isinstance(tolerance, (int, float)) and float(tolerance) < 0:
        raise ScenarioError("reconstruction tolerance must be non-negative")
    if manifest.get("timing_source") not in (
        "perf_counter_ns",
        "process_time_ns",
        "clock_gettime",
        "declared",
    ):
        raise ScenarioError(f"unknown timing_source: {manifest.get('timing_source')}")


def resolve_manifest(path: str | Path) -> tuple[dict, str]:
    """Load, validate, canonicalize and hash a scenario manifest.

    Returns (canonical_manifest, scenario_hash).
    """
    manifest = load_manifest(path)
    validate_manifest(manifest)
    canonical = canonicalize_manifest(manifest)
    return canonical, scenario_hash(canonical)


def save_canonical(manifest: dict, path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def verify_manifest_bytes(manifest: dict) -> None:
    """Verify canonical manifest encodes without loss (round-trip safely)."""
    canonical = canonicalize_manifest(manifest)
    data = json.loads(canonical_bytes(canonical).decode("utf-8"))
    if data != canonical:
        raise ScenarioError("manifest canonicalization is not deterministic")