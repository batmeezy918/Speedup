# PCSS Proof-Path Closure — 2026-09-13

## Purpose

Exercise and document the complete logical gate surface of the Proof-Carrying Speedup Scheduler (PCSS) without promoting unsupported evidence.

## Seven mandatory gates

| Gate | Meaning | Current repository state |
|---|---|---|
| I | Integrity / artifact identity | **OPEN for real runs**; strict gate now verifies artifact hashes |
| R | Reproducibility | **Executable**; native runner computes deterministic-output result |
| Q | Forward quotient | **OPEN**; must be supplied by independent quotient artifact |
| Q⁻¹ | Reverse reconstruction | **OPEN**; must be supplied by independent reconstruction artifact |
| Ω | Invariants | **OPEN**; must be supplied by independent invariant artifact |
| X | Performance | **Executable**; native runner measures baseline/candidate directly |
| L | Lean | **OPEN** for a promoted primitive; CI verifies repository Lean sources |

Publication remains:

`PUBLISH ⇔ I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L`

## Exhaustive boolean proof-path test

There are `2^7 = 128` possible truth assignments to the seven gates. CI now executes all 128 combinations using intact synthetic artifacts. Expected result:

- exactly **1** vector is accepted: `(true,true,true,true,true,true,true)`;
- **127** vectors are rejected;
- an all-true vector with missing artifacts is rejected;
- an all-true vector whose artifact is tampered is rejected.

This proves the **decision logic** of the strict gate, not the scientific validity of arbitrary supplied artifacts.

## Native execution path

`scripts/pcss_native_runner_v2.py` now provides the executable path:

`locked scenario → source/input hashes → environment fingerprint → warmups → repeated native baseline/candidate runs → raw trace → direct median speedup → native-run-only certificate`

The runner intentionally leaves `Q`, `Q⁻¹`, `Ω`, attribution, and `L` unproven. Timing cannot manufacture those gates.

## Recursive promotion path

`candidate → native evidence → normalization → quotient → reconstruction → invariants → performance → Lean → publication gate → recursive ledger`

A primitive is not promoted merely because the native runner reports a speedup. A composition requires independent composed measurement and interaction evidence.

## Remaining real-world closure

The remaining blockers are evidence-producing rather than boolean-logic blockers:

1. Execute the locked canonical workload on the target native environment.
2. Supply literal forward quotient evidence.
3. Supply reverse reconstruction evidence.
4. Supply invariant evidence with declared tolerance.
5. Supply source/input/environment hashes bound to the exact run.
6. Supply attribution evidence and residual accounting.
7. Generate and verify the corresponding Lean theorem/proof.
8. Feed the complete certificate to `publisher/strict_gate.py`.
9. Record the resulting primitive in the append-only recursive ledger only if every required gate is actually true.
10. For compositions, directly measure the composed implementation and calculate `K12`; never multiply isolated speedups as a substitute.

## Evidence boundary

This document establishes coverage of the proof-path logic and executable infrastructure. It does **not** assert that a real speedup primitive has reached `VERIFIED` status. The recursive ledger remains the authority for promotion.
