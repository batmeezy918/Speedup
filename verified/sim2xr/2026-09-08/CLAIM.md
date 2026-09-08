# Exact Invariant-Sector Speedup — 2026-09-08

## Claim class
**STRONG_LOCAL / INTERNALLY VERIFIED; Lean workflow binding pending for this artifact.**

The tested implementation performs exact coordinate reduction onto an invariant sector of diagonal propagation. The reduced engine is semantically coupled to the dense engine by an independently measured zero intertwining residual, zero task error, and zero reconstruction error at the stated tolerance.

## Measured result

Five fresh bidirectional witnesses passed. The observed speedups were approximately 1.12x, 1.64x, 4.09x, 15.93x, and 168.14x. Median = 4.09x; maximum = 168.14x.

These are **local wall-clock measurements on the specified Android/aarch64 Termux environment**. They are not an asymptotic theorem, hardware-independent guarantee, or universal SIM2XR speedup.

## Proof obligations

1. Define the state space, projection, reduced state, dense operator, and reduced operator.
2. Prove the exact invariant-sector relation and one-step intertwining/descent.
3. Prove finite recursive descent from the one-step relation.
4. Prove the stated reconstruction relation for the represented observables/state sector.
5. Preserve acceptance-relevant invariants under the quotient.
6. Bind the formal theorem to the immutable benchmark/certificate identity without claiming Lean proves wall-clock timing.
7. Re-run the established verified Lean4 workflow and record its result.

## Negative evidence retained

The separate learned bidirectional quotient suite failed forward semantic preservation and reported `QUOTIENT REQUIRES REFINEMENT`. It remains quarantined and is not used to support this exact invariant-sector claim.

## Publication boundary

The governing PCSS publication condition remains `I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L`. GitHub storage is provenance/transport, not proof authority. Universal-speedup claims remain rejected.
