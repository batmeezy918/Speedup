"""PCSS constants: the one gate regime and the one claim lattice.

Authoritative publication law (CONSTITUTION.md Article 9):

    PUBLISH <=> I AND R AND Q AND Q^-1 AND OMEGA AND X AND L

No program may invent a different definition of VERIFIED.
"""
from __future__ import annotations

SCHEMA_VERSION = "1.0"
CERTIFICATE_SCHEMA = "schemas/pcss_certificate.schema.json"
SCENARIO_SCHEMA = "schemas/scenario_manifest.schema.json"

GATES = (
    "integrity",
    "reproducibility",
    "quotient_forward",
    "reconstruction_reverse",
    "invariants",
    "performance",
    "lean",
)

GATE_SYMBOLS = {
    "integrity": "I",
    "reproducibility": "R",
    "quotient_forward": "Q",
    "reconstruction_reverse": "Q^-1",
    "invariants": "Omega",
    "performance": "X",
    "lean": "L",
}

# Monotone promotion lattice. Promotion is allowed only along this order
# and only when the evidence actually supports each transition.
CLAIM_LATTICE = ("CANDIDATE", "STRONG_LOCAL", "FORMAL_PARTIAL", "VERIFIED")

# Statuses that never promote and exclude from verified indexes.
FAILED_STATUSES = ("FAILED", "QUARANTINED", "NOT_VERIFIED")

# A certified certificate reaches STRONG_LOCAL (reproducible native evidence,
# semantic checks as declared) but is NOT VERIFIED until the Lean gate passes.
PUBLISHABLE = all  # placeholder to document intention only; see gates_ok below


def gates_ok(gates: dict) -> bool:
    """Fail-closed evaluation of the mandatory gate vector."""
    return all(bool(gates.get(name)) for name in GATES)


def strength_orders(strength_a: str, strength_b: str) -> bool:
    """True when strength_a may be promoted to strength_b (or is equal)."""
    if strength_a in FAILED_STATUSES:
        return False
    if strength_b in FAILED_STATUSES:
        return False
    try:
        return CLAIM_LATTICE.index(strength_a) <= CLAIM_LATTICE.index(strength_b)
    except ValueError:
        return False