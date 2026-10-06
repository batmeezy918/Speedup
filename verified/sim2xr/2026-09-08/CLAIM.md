# Exact Invariant-Sector Speedup — 2026-09-08

## Claim class
**STRONG_LOCAL / FORMALLY BOUND RECORD; wall-clock evidence remains local and non-universal.**

The tested implementation performs exact coordinate reduction onto an invariant sector of diagonal propagation. The reduced engine is semantically coupled to the dense engine by an independently measured zero intertwining residual, zero task error, and zero reconstruction error at the stated tolerance.

## Measured result

Five fresh bidirectional witnesses passed. The observed speedups were approximately 1.12x, 1.64x, 4.09x, 15.93x, and 168.14x. Median = 4.09x; maximum = 168.14x.

These are **local wall-clock measurements on the specified Android/aarch64 Termux environment**. They are not an asymptotic theorem, hardware-independent guarantee, or universal SIM2XR speedup. This is **not a universal speedup theorem**.

## Proof obligations

1. Define the state space, projection, reduced state, dense operator, and reduced operator.
2. Prove the exact invariant-sector relation and one-step intertwining/descent.
3. Prove finite recursive descent from the one-step relation.
4. Prove the stated reconstruction relation for the represented observables/state sector.
5. Preserve acceptance-relevant invariants under the quotient.
6. Bind the formal theorem to the immutable benchmark/certificate identity without claiming Lean proves wall-clock timing.
7. Re-run the established Lean4 workflow and record its result.
8. Independently validate the evidence packet's internal hashes, witness vector, and registry consistency in CI.

## Negative evidence retained

The separate learned bidirectional quotient suite failed forward semantic preservation and reported `QUOTIENT REQUIRES REFINEMENT`. It remains quarantined and is not used to support this exact invariant-sector claim.

## Publication boundary

The governing PCSS publication condition remains `I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L`. GitHub storage is provenance/transport; the CI binding records exact source/evidence hashes and the Lean kernel checks the generated binding theorem. This closes the formal-record binding gate, not the wall-clock theorem. Universal-speedup claims remain rejected.
