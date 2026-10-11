# Nrebbi–El × MUNI × AGD Gap Replay

Date: 2026-10-10. Target: Moto G Power 5G (2024), Android 16, ARM64 Debian PRoot. Workload: `d=2048, m=64, r=32, steps=32, trials=5, reps=5`.

## What was run

Built the existing MUNI C entry point against the current AGD certificate/runtime sources in `evidence/formal_gap_regime_20261008/src/`, then ran the same shape and step count as the existing AGD formal-gap benchmark. Ran both the admissible input and the deliberate `--inadmissible` path. The existing AGD gap derivation source and previous Lean receipts were inspected; a fresh standalone Lean build attempt did not complete because the local `.olean` dependency chain was not built/in the search path (`AGDDescentCore` / `AGDRefinement`). The earlier saved core receipt states `LEAN4_CORE_ALL_PASS=1`, source count 46; this replay does not claim a fresh full Lean pass.

## Results

Admissible MUNI run:

- Run-loop baseline: 1.560 ms
- Run-loop quotient: 0.023 ms
- Run-loop speedup: 68.608× (excludes plan/gate/reconstruction)
- Full-call baseline E2E: 1.555 ms
- Full-call quotient E2E: 0.028 ms
- End-to-end speedup: 55.860×
- Maximum absolute error: 0
- MUNI claim class: `FORMAL_PARTIAL_MEASURED_LOCAL`
- Instantiation gate: `LEAN_ALGEBRAIC_MODEL_ONLY`

Deliberately inadmissible run:

- MUNI reports `Invariant: VIOLATED -> REFUSED`
- Execution path: `ORIGINAL (fallback)`
- Run-loop speedup: 1.008×
- End-to-end speedup: 0.993×
- Maximum absolute error: 0
- Claim class: `QUARANTINED_OPTIMISATION_NOT_APPLIED`

## Comparison with the existing same-shape AGD run

The earlier 9-session AGD run reported median speedup 68.303× versus the structured baseline and 6762.064× versus the general dense baseline. The new MUNI replay's 68.608× run-loop speedup is in the same range. MUNI's 55.860× end-to-end result is lower because it includes plan/gate/reconstruction overhead. These are different timing scopes and must not be conflated. Dense-baseline speedup is not recomputed by this MUNI invocation.

## How Nrebbi–El and the gap derivation are applied

The operational contract is: quotient execution is permitted only for the certified invariant sector; the full transition and quotient transition must agree under projection/descent; reconstruction must recover the same admissible full-state result; if admissibility fails, execute the original path. The successful run has zero observed reconstruction error, and the negative control correctly falls back. The formal AGD gap derivation identifies the block-constant invariant as sufficient and provides a non-block-constant counterexample where the gap is nonzero.

Important boundary: this is a runtime witness for the contract, not proof that the Nrebbi–El Lean theorem is compiled into or independently enforced by the C binary. The MUNI receipt explicitly reports `LEAN_ALGEBRAIC_MODEL_ONLY`; the C/IEEE-754-to-Lean refinement remains residual. The current local checkout did not contain the Nrebbi–El Lean source when searched, so no claim is made that its source was freshly compiled as part of this run. The theorem supplies no speedup by itself; the measured reduction comes from the quotient algorithm under the assumed tensor-separable invariant.

## Evidence files

- `receipts/muni_d2048_m64.txt` and `.json`
- `receipts/muni_inadmissible.txt` and `.json`
- `receipts/source_binary_sha256.txt`
- `receipts/gap_derivation_lean.txt` (failed dependency-path attempt; retained transparently)

## Verdict

**Measured: positive and material local speedup, exact output on the admissible test, fail-closed fallback on the negative control.** The end-to-end MUNI result is 55.860× on this run. Formal closure is not complete: native C-to-Lean refinement is residual, operator structure is assumed, and the fresh Lean rebuild in this replay failed due to missing local `.olean` dependencies.
