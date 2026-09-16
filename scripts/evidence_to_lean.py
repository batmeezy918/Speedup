#!/usr/bin/env python3
"""Generate deterministic Lean 4 obligations from a PCSS evidence certificate.

This generator NEVER asserts that a gate passed. It instantiates the
certificate's declared gate booleans as DATA and proves the fail-closed
publication LAW:

    PCSS.publishable c  ->  every gate true
    c.lean = false      ->  not PCSS.publishable c
    c.performance = false -> not PCSS.publishable c  (and so on)

The Lean gate (L) is satisfied only when this file plus the repository's
mathematical obligations (quotient preservation, reconstruction, invariant
closure) compile under the canonical verifier.  No `axiom` is emitted.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

GATES = (
    "integrity",
    "reproducibility",
    "quotient_forward",
    "reconstruction_reverse",
    "invariants",
    "performance",
    "lean",
)


def lean_bool(value: bool) -> str:
    return "true" if value else "false"


def field_name(gate: str) -> str:
    parts = gate.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def generate(cert: dict) -> str:
    gates = {k: bool(cert.get("gates", {}).get(k, False)) for k in GATES}
    hashes = {k: str(cert.get(f"{k}_hash", "")) for k in GATES}

    struct_fields = "\n".join(
        f"  {field_name(g)} : Bool := {lean_bool(gates[g])}"
        for g, p in {"integrity": None, "reproducibility": None,
                     "quotientForward": "quotient_forward",
                     "reconstructionReverse": "reconstruction_reverse",
                     "invariants": None, "performance": None, "lean": None}.items()
        for g, _ in [()]
    )

    # instantiate EvidenceCertificate with the ordered gates
    field_lines = [
        f'  scenarioHash := "{cert.get("scenario_hash", "")}"',
        f'  sourceHash := "{cert.get("source_hash", "")}"',
        f'  inputHash := "{cert.get("input_hash", "")}"',
        f'  environmentHash := "{cert.get("environment_hash", "")}"',
        f'  traceHash := "{cert.get("baseline_trace_hash", "")}"',
        f'  quotientHash := "{cert.get("quotient_hash", "")}"',
        f'  reverseHash := "{cert.get("reconstruction_hash", "")}"',
        f'  integrity := {lean_bool(gates["integrity"])}',
        f'  reproducibility := {lean_bool(gates["reproducibility"])}',
        f'  quotientForward := {lean_bool(gates["quotient_forward"])}',
        f'  reconstructionReverse := {lean_bool(gates["reconstruction_reverse"])}',
        f'  invariants := {lean_bool(gates["invariants"])}',
        f'  performance := {lean_bool(gates["performance"])}',
        f'  lean := {lean_bool(gates["lean"])}',
    ]
    instantiation = "\n".join("    " + line for line in field_lines)
    if not instantiation:
        instantiation = "    lean := false"

    obligations = []

    # The law: publishable -> every gate true (provable from definitions).
    obligations.append(
        """theorem publication_law_on_generated_cert :
    PCSS.publishable cert → cert.integrity = true ∧
      cert.reproducibility = true ∧ cert.quotientForward = true ∧
      cert.reconstructionReverse = true ∧ cert.invariants = true ∧
      cert.performance = true ∧ cert.lean = true :=
  PCSS.publish_requires_all_gates cert"""
    )

    # Fail-closed corollaries for each declared-false gate.
    for gate in GATES:
        if not gates[gate]:
            fname = field_name(gate)
            obligations.append(
                f"""theorem generated_cert_{fname}_false_is_not_publishable :
    cert.{fname} = false → ¬ PCSS.publishable cert := by
  intro h hp
  have heq : cert.{fname} = true := by
    exact PCSS.publish_requires_all_gates cert hp.{_proj_path(gate)}
  rw [h] at heq
  cases heq"""
            )

    # All-true certificates: state that publishable follows from the gates
    # (constructor proof, no axioms) — this is the correctness of the law,
    # not a claim that the empirical gates are true.
    if all(gates[g] for g in GATES):
        obligations.append(
            """theorem generated_cert_all_gates_imply_publishable :
    cert.integrity = true ∧ cert.reproducibility = true ∧
    cert.quotientForward = true ∧ cert.reconstructionReverse = true ∧
    cert.invariants = true ∧ cert.performance = true ∧ cert.lean = true →
    PCSS.publishable cert := by
  intro h
  exact h"""
        )

    body = """
/-! Generated from a PCSS evidence certificate. Declared gate booleans are DATA,
   not proof. The Lean gate is satisfied only when the repository obligations
   compile under scripts/verify_lean4_all.sh and when publisher/strict_gate.py
   actually evaluates the certificate. -/
import PCSSCertificate

namespace PCSS.Generated

def cert : PCSS.EvidenceCertificate := {
%(instantiation)s
}

%(obligations)s

end PCSS.Generated
"""
    return body % {"instantiation": instantiation, "obligations": "\n\n".join(obligations)}


def _proj_path(gate: str) -> str:
    """Project the gate out of the nested And chain in `publishable c`."""
    order = ["integrity", "reproducibility", "quotient_forward",
             "reconstruction_reverse", "invariants", "performance", "lean"]
    idx = order.index(gate)
    # publishable c = i ∧ (r ∧ (q ∧ (qr ∧ (o ∧ (x ∧ l)))))
    # nested position from the left (0-indexed from outermost left)
    # components after the first are reached via tail projections.
    if idx == 0:
        return ".2.2.2.2.2.1"  # integrity is the head
    # determine projection chain: for k-th gate after integrity, the tail chain
    # begins at position (idx). We build the .n path manually.
    # Formula: head of each level: integrity head; then tails.
    # For integrity: .1 is left; publishable c = ⟨i, rest⟩; i = hp.1 hence not used here.
    if idx == 1:
        return ".2.1"
    # reproducibility = hp.2.1
    parts = []
    # each level: hp.2 ... with .1 returning the current gate
    # idx=2 quotientForward -> .2.2.1 ; idx=3 reconstructionReverse -> .2.2.2.1 ; etc.
    tails = idx  # number of .2 tails, then .1
    return ".2" * (idx) + ".1"


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("usage: evidence_to_lean.py CERTIFICATE.json OUTPUT.lean [OBLIGATIONS.lock]", file=sys.stderr)
        return 2

    cert = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = Path(sys.argv[2])

    generated = generate(cert)
    # self-hash: bind lean_hash to the generated source
    digest = hashlib.sha256(generated.encode("utf-8")).hexdigest()
    cert["lean_hash"] = digest
    cert["lean"] = {"pass": False, "obligation_source": str(output), "source_sha256": digest}

    output.write_text(generated, encoding="utf-8")

    if len(sys.argv) == 4:
        lock = {
            "certificate": Path(sys.argv[1]).name,
            "generated": str(output),
            "source_sha256": digest,
            "mathlib_free": True,
        }
        Path(sys.argv[3]).write_text(json.dumps(lock, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    print(f"generated {output} (obligation source sha256={digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())