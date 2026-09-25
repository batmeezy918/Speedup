# COMPOSITION SELECTION — STAGE 2 (2026-09-23)

## Selected first composition
### C_1 = QMULT-02 ∘ AQGE-02
- Composition type: trajectory_deepening (combined stay-in-Q)
- Operator semantics: both are the certified exact-invariant-sector reduced operator Tbar
  (matrix n=512, tile=16, nclasses=8, a=3,b=1, weights w = [1.0,1.25,0.9,1.1,1.5,0.8,1.3,0.95])
- Composed execution: ONE projection pi, then (8+6)=14 reduced steps Tbar_(8+6), then ONE reconstruction sigma
- Canonical baseline: T_full applied 14 times in full space R^512x512 (same seed construction)
- Measured quantity: S_composed = T_B(14 full steps) / T_C(1 pi + 14 Tbar + 1 sigma)
- THIS IS NOT S_1 * S_2. It is a native wall-clock measurement of the fused trajectory.

## Why this composition
1. Exact equivalence available: same operator family, identical weights -> pi∘Tbar = T_full∘pi exactly,
   reconstruction err stays 0.0. Maximally auditable.
2. Compatible representation: both R^512x512, block-constant, row-major.
3. Compatible invariants: block-constancy Omega, nclasses=8.
4. Minimal engineering risk: O_C = sigma ∘ Tbar^14 ∘ pi, single fused op build.
5. Measurable baseline: T_full^14 natively.
6. Meaningful interaction data: I_12 = S_measured / (S_1*S_2) ~ far below the modeled product proves
   that multiplying isolated ratios over-claims (the intended honesty control).

## Rejected / deferred
- QMULT-02 ∘ AGD-GEMM: same family, 16 steps — deferred to escalation (needs C_1 certified first).
- AQGE-02 ∘ AGD-GEMM: same family, 14 steps — equivalent; C_1 chosen for operator-depth 8+6.
- ANY matrix∘SIM2XR: INCOMPATIBLE (no certified morphism R^512x512 <-> R^65536). Rejected; would require
  a NEW candidate reshape morphism => CANDIDATE mechanism, outside verified preconditions.

## Show-stoppers rejected explicitly
- Multiplied ratio "composition" (S_1*S_2): NOT a composition. Rejected. Reported only as ideal/modeled reference.
- SIM2XR single-shot discovery-inclusive: previously REFUTED (0.73-0.83x) in ledger; not composable here.