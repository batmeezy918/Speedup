#!/usr/bin/env python3
"""Silicon Speedup Proof — shared validator library.

Read-only. Nothing in this module promotes a claim, writes a ledger, or
manufactures evidence. It computes findings; a human or a caller decides what
to do with them.

Design commitments:

* Fail closed. A missing field is never "fine".
* Never synthesize. If evidence is absent, the finding says so.
* Synthetic fixtures are structurally valid but explicitly marked, and are
  excluded from substantive coverage counts.
* No third-party dependency is required. ``jsonschema`` is used when
  importable; otherwise a small built-in checker covers the JSON Schema subset
  actually used by schemas/*.schema.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

SCHEMA_VERSION = "SSPROOF-1.0"
HERE = Path(__file__).resolve().parent
SCRIPTS_DIR = HERE
SKILL_ROOT = HERE.parent
SCHEMA_DIR = SKILL_ROOT / "schemas"

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"

# --------------------------------------------------------------------------
# Ordered ladders
# --------------------------------------------------------------------------

#: Evidence ladder, weakest to strongest. A level asserts the *existence and
#: quality* of evidence, not the strength of the resulting claim.
EVIDENCE_LADDER: Tuple[str, ...] = (
    "UNEVIDENCED",
    "OBSERVED",
    "EXECUTED",
    "REPRODUCED",
    "CORRECTNESS",
    "MECHANISM",
    "FORMAL",
    "SCOPED_VERIFIED",
)

#: Claim ladder. Kept aligned with speedup/const.py CLAIM_LATTICE, plus NONE.
CLAIM_LADDER: Tuple[str, ...] = (
    "NONE",
    "CANDIDATE",
    "STRONG_LOCAL",
    "FORMAL_PARTIAL",
    "VERIFIED",
)

EVIDENCE_RANK = {name: i for i, name in enumerate(EVIDENCE_LADDER)}
CLAIM_RANK = {name: i for i, name in enumerate(CLAIM_LADDER)}

CLAIM_KINDS = (
    "none",
    "performance",
    "implementation",
    "hardware_mechanism",
    "formal",
    "composition",
    "cumulative",
)

#: Minimum evidence required before a given (claim_strength, claim_kind) pair is
#: admissible. This is the table that makes "missing raw timings means no
#: measured speedup claim" machine-checkable instead of aspirational.
#:
#: Limitations are documented in references/evidence-model.md.
MINIMUM_EVIDENCE: Dict[Tuple[str, str], str] = {
    ("NONE", "none"): "UNEVIDENCED",
    ("NONE", "performance"): "UNEVIDENCED",
    ("NONE", "implementation"): "UNEVIDENCED",
    ("NONE", "hardware_mechanism"): "UNEVIDENCED",
    ("NONE", "formal"): "UNEVIDENCED",
    ("NONE", "composition"): "UNEVIDENCED",
    ("NONE", "cumulative"): "UNEVIDENCED",
    ("CANDIDATE", "none"): "OBSERVED",
    ("CANDIDATE", "performance"): "OBSERVED",
    ("CANDIDATE", "implementation"): "OBSERVED",
    ("CANDIDATE", "hardware_mechanism"): "OBSERVED",
    ("CANDIDATE", "formal"): "OBSERVED",
    ("CANDIDATE", "composition"): "OBSERVED",
    ("CANDIDATE", "cumulative"): "OBSERVED",
    ("STRONG_LOCAL", "performance"): "REPRODUCED",
    ("STRONG_LOCAL", "none"): "EXECUTED",
    ("STRONG_LOCAL", "implementation"): "CORRECTNESS",
    ("STRONG_LOCAL", "hardware_mechanism"): "MECHANISM",
    ("STRONG_LOCAL", "formal"): "FORMAL",
    ("STRONG_LOCAL", "composition"): "CORRECTNESS",
    ("STRONG_LOCAL", "cumulative"): "CORRECTNESS",
    ("FORMAL_PARTIAL", "performance"): "CORRECTNESS",
    ("FORMAL_PARTIAL", "none"): "CORRECTNESS",
    ("FORMAL_PARTIAL", "implementation"): "CORRECTNESS",
    ("FORMAL_PARTIAL", "hardware_mechanism"): "MECHANISM",
    ("FORMAL_PARTIAL", "formal"): "FORMAL",
    ("FORMAL_PARTIAL", "composition"): "CORRECTNESS",
    ("FORMAL_PARTIAL", "cumulative"): "CORRECTNESS",
    ("VERIFIED", "none"): "SCOPED_VERIFIED",
    ("VERIFIED", "performance"): "SCOPED_VERIFIED",
    ("VERIFIED", "implementation"): "SCOPED_VERIFIED",
    ("VERIFIED", "hardware_mechanism"): "SCOPED_VERIFIED",
    ("VERIFIED", "formal"): "SCOPED_VERIFIED",
    ("VERIFIED", "composition"): "SCOPED_VERIFIED",
    ("VERIFIED", "cumulative"): "SCOPED_VERIFIED",
}

#: Statuses that require executed_kind == "native" plus non-empty raw timing.
MEASURED_STATUSES = ("measured", "reproduced", "verified")
NATIVE_REQUIRED_STATUSES = ("measured", "reproduced", "verified")

#: Legal status transitions. Anything not listed is rejected.
STATUS_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    "proposed": ("implemented", "blocked", "regressed", "superseded", "quarantined"),
    "implemented": ("measured", "blocked", "regressed", "superseded", "quarantined"),
    "measured": ("reproduced", "regressed", "blocked", "superseded", "quarantined"),
    "reproduced": ("verified", "regressed", "blocked", "superseded", "quarantined"),
    "verified": ("regressed", "superseded", "blocked", "quarantined"),
    "regressed": ("implemented", "measured", "reproduced", "blocked", "superseded", "quarantined"),
    "blocked": ("proposed", "implemented", "measured", "reproduced", "superseded", "quarantined"),
    "superseded": (),
    "quarantined": ("implemented", "measured", "blocked", "superseded"),
}

#: Statuses that must never be erased from status_history once observed.
NEGATIVE_STATUSES = ("regressed", "blocked", "quarantined")

GAP_CLASSES: Tuple[str, ...] = (
    "dependency",
    "equivalence_correctness",
    "measurement",
    "attribution",
    "scaling",
    "hardware_mechanism",
    "composition",
    "formal_proof",
    "vacuity",
    "provenance",
    "reproducibility",
    "derivation",
)

#: Legacy vocabulary already present in the repository, preserved verbatim on
#: import and mapped into the canonical taxonomy above.
GAP_CLASS_ALIASES: Dict[str, str] = {
    "DEPENDENCY_GAP": "dependency",
    "EQUIVALENCE_GAP": "equivalence_correctness",
    "RECONSTRUCTION_GAP": "equivalence_correctness",
    "OBSERVABLE_COMPLETENESS_GAP": "equivalence_correctness",
    "MEASUREMENT_GAP": "measurement",
    "ATTRIBUTION_GAP": "attribution",
    "SCALING_GAP": "scaling",
    "HARDWARE_MECHANISM_GAP": "hardware_mechanism",
    "COMPOSITION_GAP": "composition",
    "FORMAL_GAP": "formal_proof",
    "VACUITY_GAP": "vacuity",
    "PROVENANCE_GAP": "provenance",
    "REPRODUCIBILITY_GAP": "reproducibility",
    "DERIVATION_GAP": "derivation",
    "NEGATIVE": "measurement",
    "FAILED": "measurement",
}

# --------------------------------------------------------------------------
# Operator registry — honest status of the framework's named operators
# --------------------------------------------------------------------------
#
# definition_status is asserted, not assumed:
#   undefined   -> no executable or mathematical definition was located in the
#                  target project at build time. Using it is a DERIVATION gap.
#   specified   -> prose only. Not an implemented transformation.
#   implemented -> a resolvable source_ref exists.
#
# `probe` records the exact command used to establish the status so a reader
# can re-derive it instead of trusting this table.

OPERATOR_REGISTRY: Dict[str, Dict[str, Any]] = {
    "S": {
        "name": "spectral inversion operator",
        "definition_status": "undefined",
        "source_ref": None,
        "symbol_ref": None,
        "note": (
            "No spectral inversion routine was located in speedup/, engines/, "
            "attribution.py, scripts/, publisher/ or governor/. Notation only."
        ),
        "probe": (
            "grep -rn 'spectral_inversion\\|S_inv' --include=*.py speedup engines "
            "attribution.py scripts publisher governor   -> no matches"
        ),
    },
    "Delta": {
        "name": "Laplacian perturbation operator",
        "definition_status": "undefined",
        "source_ref": None,
        "symbol_ref": None,
        "note": "No Laplacian perturbation routine located. Notation only.",
        "probe": (
            "grep -rn 'laplacian' --include=*.py speedup engines attribution.py "
            "scripts publisher governor   -> no matches"
        ),
    },
    "Omega": {
        "name": "invariant signature operator (gate Omega)",
        "definition_status": "implemented",
        "source_ref": "engines/invariant.py",
        "symbol_ref": "InvariantEngine.check",
        "note": (
            "The engine exists and compares a declared signature. The invariant "
            "function itself is supplied by the scenario, so Omega is only as "
            "specific as the scenario's declaration. CONSTITUTION.md Article 5."
        ),
        "probe": "grep -rn 'class InvariantEngine' engines/invariant.py",
    },
    "Xi": {
        "name": "quantum Fisher curvature operator",
        "definition_status": "undefined",
        "source_ref": None,
        "symbol_ref": None,
        "note": (
            "No QFI/curvature computation located. lean4/ProvenAgd/AGDTheoremSeries.lean "
            "declares a theorem NAMED curvature_convergence over a decay model; a "
            "theorem name is not an executable curvature operator."
        ),
        "probe": (
            "grep -rn 'quantum_fisher\\|QFI\\|curvature' --include=*.py speedup engines "
            "attribution.py scripts publisher governor   -> no matches"
        ),
    },
    "identity": {
        "name": "identity operator",
        "definition_status": "implemented",
        "source_ref": "speedup/reconstruction.py",
        "symbol_ref": None,
        "note": "Baseline / no-op arm. Used as the comparison reference.",
        "probe": "ls speedup/reconstruction.py",
    },
}

#: Invariants named by the framework and their actual support in the project.
INVARIANT_SUPPORT: Dict[str, str] = {
    "Omega(O psi)": "implemented — engines/invariant.py, scenario-declared invariant",
    "heat_trace(O)": "undefined — no definition located; prose only in SPECIFICATIONS.md",
    "curvature(psi)": "undefined — no executable definition located",
}

MIN_SAMPLES = 5

# --------------------------------------------------------------------------
# Vacuity model
# --------------------------------------------------------------------------
#
# A validation is substantive only when it *could have failed*. We recompute
# that from the record rather than trusting a `passed: true`.

TRIVIAL_VALUES_BY_ROLE: Dict[str, frozenset] = {
    "dimension": frozenset({0, 1}),
    "size": frozenset({0, 1}),
    "input_count": frozenset({0, 1}),
    "iteration_count": frozenset({0, 1}),
    "repeat_count": frozenset({0, 1}),
    "warmup_count": frozenset({0}),
    # tolerance / threshold / seed: 0 and 1 are stricter or neutral, not vacuous
    "tolerance": frozenset(),
    "threshold": frozenset(),
    "seed": frozenset(),
}

TRIVIAL_ASSERTIONS = frozenset(
    {"true", "1", "yes", "pass", "ok", "no-op", "noop", "assert true",
     "x == x", "t==t", "a==a", "always true", "vacuous"}
)


@dataclass
class VacuityResult:
    substantive: bool
    reasons: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:  # pragma: no cover - convenience only
        return self.substantive


def analyze_check(check: Dict[str, Any]) -> VacuityResult:
    """Decide whether a single declared check had any discriminating power."""
    reasons: List[str] = []

    roles = check.get("parameter_roles") or {}
    parameters = check.get("parameters") or {}
    if not roles:
        reasons.append("no_declared_parameter_roles: discriminating power is not reconstructible")
    else:
        material = 0
        for name, role in roles.items():
            if name not in parameters:
                reasons.append(f"missing_parameter:{name}")
                continue
            value = parameters[name]
            trivial = TRIVIAL_VALUES_BY_ROLE.get(role, frozenset())
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value in trivial:
                reasons.append(f"trivial_parameter:{name}={value!r} (role={role})")
            elif value is None:
                reasons.append(f"null_parameter:{name} (role={role})")
            else:
                material += 1
        if material == 0:
            reasons.append("all_declared_parameters_trivial")

    assertion = str(check.get("assertion", "")).strip().lower()
    if not assertion:
        reasons.append("empty_assertion")
    elif assertion in TRIVIAL_ASSERTIONS:
        reasons.append(f"trivial_assertion:{assertion!r}")

    if check.get("expected_source") == "self":
        reasons.append("self_referential_expectation: expected value came from the code under test")

    if check.get("observed") is None:
        reasons.append("nothing_observed")

    return VacuityResult(substantive=not reasons, reasons=reasons)


@dataclass
class CoverageReport:
    total: int
    substantive: int
    vacuous: int
    synthetic: int
    vacuous_ids: List[str] = field(default_factory=list)

    @property
    def all_vacuous(self) -> bool:
        return self.total > 0 and self.substantive == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "substantive": self.substantive,
            "vacuous": self.vacuous,
            "synthetic": self.synthetic,
            "vacuous_ids": list(self.vacuous_ids),
            "all_vacuous": self.all_vacuous,
        }


def substantive_coverage(checks: Sequence[Dict[str, Any]]) -> CoverageReport:
    """Count checks that could have failed. Vacuous entries are excluded."""
    total = substantive = vacuous = synthetic = 0
    vacuous_ids: List[str] = []
    for check in checks or []:
        total += 1
        if check.get("synthetic"):
            synthetic += 1
        result = analyze_check(check)
        if result.substantive:
            substantive += 1
        else:
            vacuous += 1
            vacuous_ids.append(str(check.get("check_id", "<unnamed>")))
    return CoverageReport(total, substantive, vacuous, synthetic, vacuous_ids)


# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------


@dataclass
class Finding:
    code: str
    severity: str
    message: str
    where: str = ""
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if k != "detail" or v}


def findings_to_json(findings: Sequence[Finding]) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "findings": [f.to_dict() for f in findings],
        "errors": sum(1 for f in findings if f.severity == ERROR),
        "warnings": sum(1 for f in findings if f.severity == WARN),
    }
    payload["verdict"] = "FAIL" if payload["errors"] else "PASS"
    return json.dumps(payload, indent=2, sort_keys=True)


def max_severity(findings: Sequence[Finding]) -> str:
    if any(f.severity == ERROR for f in findings):
        return "FAIL"
    if any(f.severity == WARN for f in findings):
        return "WARN"
    return "PASS"


# --------------------------------------------------------------------------
# Hashing / canonical bytes (matches publisher/evidence_lib.py)
# --------------------------------------------------------------------------


def canonical_bytes(obj: Any) -> bytes:
    return (
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_record_hash(record: Dict[str, Any]) -> str:
    payload = {k: v for k, v in record.items() if k != "record_hash"}
    return sha256_json(payload)


# --------------------------------------------------------------------------
# JSON Schema support
# --------------------------------------------------------------------------

# Lazily loaded. `import jsonschema` costs ~0.5-0.7 s of interpreter start-up,
# which dominates a CLI invocation whose validation work is ~13 ms, so the
# import is deferred until the jsonschema backend is actually selected.
_jsonschema = None
_jsonschema_loaded = False


def _ensure_jsonschema():
    """Import jsonschema once, on first use. Never required."""
    global _jsonschema, _jsonschema_loaded
    if not _jsonschema_loaded:
        _jsonschema_loaded = True
        try:
            import jsonschema as js  # type: ignore
            _jsonschema = js
        except Exception:  # pragma: no cover
            _jsonschema = None
    return _jsonschema


def _resolve_ref(root: Dict[str, Any], ref: str) -> Dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported $ref {ref!r} (external refs are not resolved)")
    node: Any = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        node = node[part]
    return node


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"unsupported type {expected!r}")


def _mini_validate(value: Any, schema: Dict[str, Any], root: Dict[str, Any], path: str) -> List[str]:
    """Validate the JSON Schema subset used by this skill's schemas."""
    errors: List[str] = []
    if "$ref" in schema:
        return _mini_validate(value, _resolve_ref(root, schema["$ref"]), root, path)

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in enum {schema['enum']!r}")

    if "type" in schema:
        expected = schema["type"]
        options = expected if isinstance(expected, list) else [expected]
        if not any(_type_ok(value, t) for t in options):
            errors.append(f"{path}: expected type {expected!r}, got {type(value).__name__}")
            return errors

    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match pattern {schema['pattern']!r}")
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} > maximum {schema['maximum']}")

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")
        props = schema.get("properties", {})
        for key, sub in props.items():
            if key in value:
                errors.extend(_mini_validate(value[key], sub, root, f"{path}.{key}"))
        additional = schema.get("additionalProperties", True)
        if additional is False:
            for key in value:
                if key not in props:
                    errors.append(f"{path}: additional property {key!r} is not allowed")
        elif isinstance(additional, dict):
            for key, item in value.items():
                if key not in props:
                    errors.extend(_mini_validate(item, additional, root, f"{path}.{key}"))

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "items" in schema:
            for i, item in enumerate(value):
                errors.extend(_mini_validate(item, schema["items"], root, f"{path}[{i}]"))

    return errors


def load_schema(name: str) -> Dict[str, Any]:
    path = SCHEMA_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def validate_against_schema(document: Any, schema_name: str) -> List[str]:
    schema = load_schema(schema_name)
    js = _jsonschema if _jsonschema is not None else (
        None if _builtin_forced else _ensure_jsonschema())
    if js is not None:
        validator_cls = js.validators.validator_for(schema)
        validator = validator_cls(schema)
        out = []
        for err in sorted(validator.iter_errors(document), key=lambda e: list(e.path)):
            loc = "$" + "".join(f"[{p!r}]" for p in err.path)
            out.append(f"{loc}: {err.message}")
        return out
    return _mini_validate(document, schema, schema, "$")


def set_backend(name: str) -> None:
    """Select the JSON Schema backend for this process.

    "jsonschema" uses the third-party validator when importable. "builtin" uses
    the bundled checker and skips that import entirely.

    The two agree on this skill's schema subset; the builtin path exists because
    `import jsonschema` costs ~456 ms of interpreter start-up, which dominates a
    CLI invocation whose actual validation work is ~13 ms.
    """
    global _jsonschema
    if name == "builtin":
        _jsonschema = None
    elif name == "jsonschema":
        _ensure_jsonschema()
    else:
        raise ValueError(f"unknown schema backend {name!r}")


_builtin_forced = False


def _force_builtin(forced: bool = True) -> None:
    """Keep the jsonschema backend out of the process entirely (used by --fast)."""
    global _builtin_forced
    _builtin_forced = forced


def schema_backend() -> str:
    if _builtin_forced:
        return "builtin-mini"
    return "jsonschema" if _ensure_jsonschema() is not None else "builtin-mini"


# --------------------------------------------------------------------------
# Composition mathematics
# --------------------------------------------------------------------------


class CompositionError(ValueError):
    """Raised when a composition quantity cannot be computed as declared."""


def speedup(t_baseline: float, t_candidate: float) -> float:
    """S = T_baseline / T_candidate. Refuses non-positive domains."""
    if t_baseline is None or t_candidate is None:
        raise CompositionError("missing timing: S is undefined without both arms")
    if not math.isfinite(t_baseline) or not math.isfinite(t_candidate):
        raise CompositionError("non-finite timing")
    if t_baseline <= 0 or t_candidate <= 0:
        raise CompositionError(f"non-positive timing domain: {t_baseline}/{t_candidate}")
    return t_baseline / t_candidate


def individual_speedup(individual: Sequence[float]) -> float:
    """Product of isolated component ratios.

    Provided ONLY so the validator can recognise and reject it. Using this value
    as S_composed or S_cumulative is a COMPOSITION gap (RECURSIVE_SPEEDUP_
    CONSTITUTION.md section 4).
    """
    out = 1.0
    for s in individual:
        if s is None or not math.isfinite(s) or s <= 0:
            raise CompositionError("non-positive or undefined component ratio")
        out *= s
    return out


def ideal_sequential(
    stage_baseline: Sequence[float],
    stage_candidate_ideal: Sequence[float],
) -> float:
    """S_ideal = sum_i T_i,baseline / sum_i T_i,candidate,ideal.

    Valid only for sequential stages with compatible, non-overlapping baseline
    timing domains. If that does not describe the workload, use a different
    model or declare the ideal composition undefined.
    """
    if len(stage_baseline) != len(stage_candidate_ideal):
        raise CompositionError("stage counts differ between baseline and candidate models")
    if not stage_baseline:
        raise CompositionError("no stages: ideal model undefined")
    sb = sum(stage_baseline)
    sc = sum(stage_candidate_ideal)
    if sb <= 0 or sc <= 0:
        raise CompositionError("ideal model denominators must be positive")
    return sb / sc


def interaction_factor(s_composed_measured: float, s_ideal: float) -> Optional[float]:
    """eta_interaction = S_composed,measured / S_ideal.

    Diagnostic ratio only. It is NOT independent proof of the hardware
    mechanism and NOT a cumulative speedup.
    """
    if s_ideal is None or not math.isfinite(s_ideal) or s_ideal == 0:
        return None
    if s_composed_measured is None or not math.isfinite(s_composed_measured):
        return None
    return s_composed_measured / s_ideal


def multiplicative_reference(individual: Sequence[float]) -> float:
    """Alias of individual_speedup under the repository's K_12 vocabulary."""
    return individual_speedup(individual)


def scopes_compatible(scopes: Sequence[Optional[str]]) -> bool:
    """All non-empty scopes must agree before a single ratio may be formed."""
    declared = [s for s in scopes if s]
    return len(set(declared)) <= 1


def median(values: Sequence[float]) -> float:
    vals = sorted(float(v) for v in values)
    if not vals:
        raise CompositionError("no samples")
    n = len(vals)
    mid = n // 2
    return vals[mid] if n % 2 else (vals[mid - 1] + vals[mid]) / 2.0


def mad(values: Sequence[float]) -> float:
    """Median absolute deviation — the spread companion to the median."""
    m = median(values)
    return median([abs(float(v) - m) for v in values])


def arm_stats(samples: Any) -> Dict[str, Any]:
    """Normalize a raw sample list. Never invents a value for an empty list and
    never raises on a malformed entry."""
    vals = as_numbers(samples)
    usable = len(samples) if isinstance(samples, (list, tuple)) else 0
    dropped = usable - len(vals)
    positive = [v for v in vals if v > 0]
    return {
        "n": len(vals),
        "n_positive": len(positive),
        "n_dropped": dropped,
        "median": median(vals) if vals else None,
        "mad": mad(vals) if vals else None,
        "min": min(vals) if vals else None,
        "max": max(vals) if vals else None,
        "has_timing": len(positive) > 0,
    }


# --------------------------------------------------------------------------
# Claim / evidence enforcement
# --------------------------------------------------------------------------


def minimum_evidence_for(claim_strength: str, claim_kind: str) -> str:
    """Evidence floor for a (claim_strength, claim_kind) pair.

    Fails CLOSED. An unrecognised claim kind is not silently exempt from the
    floor table; it is held to the strictest level, so a typo can never widen
    what a claim is allowed to assert.
    """
    if claim_kind not in CLAIM_KINDS:
        return EVIDENCE_LADDER[-1]
    floor = MINIMUM_EVIDENCE.get((claim_strength, claim_kind))
    return floor if floor is not None else EVIDENCE_LADDER[-1]


def claim_exceeds_evidence(
    claim_strength: str, evidence_strength: str, claim_kind: str
) -> Optional[str]:
    """Return a human-readable reason when the claim is inadmissible, else None."""
    if claim_strength not in CLAIM_RANK:
        return f"unknown claim strength {claim_strength!r}"
    if evidence_strength not in EVIDENCE_RANK:
        return f"unknown evidence strength {evidence_strength!r}"
    if CLAIM_RANK[claim_strength] > EVIDENCE_RANK[evidence_strength]:
        return (
            f"CLAIM_STRENGTH({claim_strength}, rank {CLAIM_RANK[claim_strength]}) > "
            f"EVIDENCE_STRENGTH({evidence_strength}, rank {EVIDENCE_RANK[evidence_strength]})"
        )
    floor = minimum_evidence_for(claim_strength, claim_kind)
    if floor is not None and EVIDENCE_RANK[evidence_strength] < EVIDENCE_RANK[floor]:
        return (
            f"claim ({claim_strength}/{claim_kind}) requires at least {floor} evidence, "
            f"record carries {evidence_strength}"
        )
    return None


def transition_chain_is_complete(
    claimed: str, transition_records: Sequence[Dict[str, Any]]
) -> bool:
    """A raised evidence level must be backed by an ordered transition chain.

    Every rung from UNEVIDENCED up to `claimed` must appear as a `to` value, in
    non-decreasing order, each bound to an event_ref, and the chain must
    actually start at UNEVIDENCED.
    """
    if claimed not in EVIDENCE_RANK:
        return False
    target = EVIDENCE_RANK[claimed]
    if target == 0:
        return True
    if not transition_records:
        return False
    seen_ranks: List[int] = []
    for rec in transition_records:
        to = rec.get("to")
        if to not in EVIDENCE_RANK:
            return False
        if not str(rec.get("event_ref") or "").strip():
            return False
        seen_ranks.append(EVIDENCE_RANK[to])
    if seen_ranks != sorted(seen_ranks):
        return False
    if transition_records[0].get("from") != "UNEVIDENCED":
        return False
    if seen_ranks[-1] != target:
        return False
    # Every rung must actually appear: a chain that skips EXECUTED and jumps
    # straight from OBSERVED to REPRODUCED is not a record of how it got there.
    return set(seen_ranks) == set(range(1, target + 1))


def status_transition_legal(previous: Optional[str], current: str) -> bool:
    if previous is None:
        return current == "proposed"
    if previous == current:
        return True
    return current in STATUS_TRANSITIONS.get(previous, ())


# --------------------------------------------------------------------------
# Ledger parsing
# --------------------------------------------------------------------------


@dataclass
class LedgerLine:
    index: int
    raw: str
    record: Optional[Dict[str, Any]]
    parse_error: Optional[str] = None


def load_ledger(path: Path) -> List[LedgerLine]:
    """Read a ledger. Every line becomes a LedgerLine; malformed lines carry a
    parse error rather than raising. A single bad line must not void the audit
    of every line after it."""
    lines: List[LedgerLine] = []
    raw_bytes = Path(path).read_bytes()
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [LedgerLine(1, "", None, f"ledger is not valid UTF-8: {exc}")]
    for i, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            lines.append(LedgerLine(i, stripped, None))
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as exc:
            lines.append(LedgerLine(i, stripped, None, f"json parse error: {exc}"))
            continue
        if not isinstance(parsed, dict):
            lines.append(LedgerLine(
                i, stripped, None,
                f"ledger line is a JSON {type(parsed).__name__}, expected an object"))
            continue
        lines.append(LedgerLine(i, stripped, parsed))
    return lines


def as_numbers(values: Any) -> List[float]:
    """Coerce a sample list, skipping entries that are not real numbers.

    A benchmark that emits a string where a float belongs has an incomplete
    measurement, not a reason to abort the audit."""
    out: List[float] = []
    for v in values or []:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        out.append(float(v))
    return out


def is_gap_record(record: Any) -> bool:
    """True only for a real object record. Non-dict records are not gap records;
    they are malformed input and are reported, never dispatched on."""
    return isinstance(record, dict) and record.get("record_type") == "gap"


# --------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA_RE.match(value))


def human(findings: Sequence[Finding]) -> str:
    lines: List[str] = []
    for f in findings:
        loc = f" [{f.where}]" if f.where else ""
        lines.append(f"{f.severity:5s} {f.code:22s}{loc} {f.message}")
    verdict = max_severity(findings)
    lines.append(f"VERDICT={verdict}  ({sum(1 for x in findings if x.severity == ERROR)} error(s), "
                 f"{sum(1 for x in findings if x.severity == WARN)} warning(s))")
    return "\n".join(lines)


def is_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float))


def repo_root_default() -> Path:
    """Best-effort repository root for operator source_ref resolution."""
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "CONSTITUTION.md").exists() and (candidate / "speedup").is_dir():
            return candidate
    return Path.cwd()


def rel_to_root(path: Path, root: Path) -> Optional[str]:
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve()))
    except ValueError:
        return None


def load_tool(name: str):
    """Import a hyphenated CLI script as a module (e.g. 'validate-run')."""
    import importlib.util

    path = HERE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"ssproof_tool_{name.replace('-', '_')}", path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
