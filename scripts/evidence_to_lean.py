#!/usr/bin/env python3
"""Generate deterministic Lean 4 obligations from a PCSS evidence certificate.

This generator never marks a result verified. It emits a scaffold that must compile
and be checked by the formal gate.
"""
import json
import sys
from pathlib import Path


def lean_bool(value: bool) -> str:
    return "true" if value else "false"


def generate(cert: dict) -> str:
    gates = cert.get("gates", {})
    values = {k: bool(gates.get(k, False)) for k in (
        "integrity", "reproducibility", "quotient_forward",
        "reconstruction_reverse", "invariants", "performance", "lean"
    )}
    return f'''import PCSSCertificate

namespace PCSS.Generated

structure InstantiatedEvidence where
  scenarioHash : String := "{cert.get('scenario_hash', '')}"
  sourceHash : String := "{cert.get('source_hash', '')}"
  certificateHash : String := "{cert.get('certificate_hash', '')}"
  integrity : Bool := {lean_bool(values['integrity'])}
  reproducibility : Bool := {lean_bool(values['reproducibility'])}
  quotientForward : Bool := {lean_bool(values['quotient_forward'])}
  reconstructionReverse : Bool := {lean_bool(values['reconstruction_reverse'])}
  invariants : Bool := {lean_bool(values['invariants'])}
  performance : Bool := {lean_bool(values['performance'])}
  lean : Bool := {lean_bool(values['lean'])}

axiom evidence_integrity : (InstantiatedEvidence.integrity) = true
axiom evidence_reproducibility : (InstantiatedEvidence.reproducibility) = true
axiom evidence_quotient_forward : (InstantiatedEvidence.quotientForward) = true
axiom evidence_reconstruction_reverse : (InstantiatedEvidence.reconstructionReverse) = true
axiom evidence_invariants : (InstantiatedEvidence.invariants) = true
axiom evidence_performance : (InstantiatedEvidence.performance) = true

/-- Generated scaffold only. Replace axioms with actual derived/proved obligations. --/
theorem instantiated_publish_gate :
    InstantiatedEvidence.integrity = true ∧
    InstantiatedEvidence.reproducibility = true ∧
    InstantiatedEvidence.quotientForward = true ∧
    InstantiatedEvidence.reconstructionReverse = true ∧
    InstantiatedEvidence.invariants = true ∧
    InstantiatedEvidence.performance = true := by
  exact ⟨evidence_integrity, evidence_reproducibility,
    evidence_quotient_forward, evidence_reconstruction_reverse,
    evidence_invariants, evidence_performance⟩

end PCSS.Generated
'''


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: evidence_to_lean.py CERTIFICATE.json OUTPUT.lean", file=sys.stderr)
        return 2
    src, dst = map(Path, sys.argv[1:])
    cert = json.loads(src.read_text(encoding="utf-8"))
    dst.write_text(generate(cert), encoding="utf-8")
    print(f"generated {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
