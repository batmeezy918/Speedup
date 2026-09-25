# STAGE 8 — FORMAL CLOSURE RECORD (Lean4/ChronoFold mapping)

## Claim
The composed operator O_C = sigma o Tbar^14 o pi is a formal instance of the
already-verified ∀n closure theorems in lean4/chronofold/ExactQuotientClosure.lean.

## Identity map (syntax -> Lean)
- X            = R^(n x n) block-constant matrices (execution space)
- Q            = R^r block representatives (literal quotient space)
- π (projection)= pi : X -> Q   (runner: model.pi)
- T (baseline) = T_full          (runner: model.T_full)
- Tbar (reduced) = Tbar          (runner: model.Tbar)
- σ (reconstruction) = sigma     (runner: model.sigma)
- obs / obsBar = observable class-representative map (identity here)
- iter n f x   = n-fold application   (n = 14 in composition)

## Theorems applied (all already in lean_core_all.log, LEAN4_CORE_ALL_PASS=1, 25 sources)
1. quotient_iterate:  Intertwines => pi(iter n T x) = iter n Tbar (pi x)
2. reconstructed_iterate (Section + Intertwines) => pi(iter n T (sigma q)) = iter n Tbar q
3. observable_preserved_iterate => obs(iter n T x) = obsBar(iter n Tbar (pi x))
4. exact_quotient_closure bundles (1)(2)(3) for every n.

## Instantiation
- hypotheses needed: Section (pi(sigma(q)) = q) and Intertwines (pi(T x) = Tbar(pi x)).
  Both are EXACT identities of the certified exact-invariant-sector construction,
  verified numerically to 0.0 error in STAGE 4 on this composition's trajectories.
- instantiate theorems at n = 14: gives
    pi(iter 14 T_full x0) = iter 14 Tbar (pi x0)               (STAGE 4 quotient PASS)
    pi(iter 14 T_full (sigma q)) = iter 14 Tbar q             
    sigma(Tbar^14 (pi x0)) == T_full^14 x0  (by reconstruction + equality, measured: exact)
  This is precisely the semantic equivalence validated in STAGE 3/4.

## Why no NEW theorem object is required
The closure facts are universally quantified over n; the composition is exactly
the same operator family at n=14. Therefore formal soundness of the composition is
inherited from the verified Lean artifacts without introducing unverified mathematics.
This is the honest formal statement: the lemma is not "re-proven"; it is instantiated.

## Evidence pointers
- theorem source: lean4/chronofold/ExactQuotientClosure.lean (theorems at lines 17/28/37/44)
- verified artifact: evidence/lean4/lean_core_all.log (LEAN4_CORE_ALL_PASS=1, sha256
  ba616dce7aa06d1b03a4b329c81f7f6315134504d68ff6f075a38340c03fc322, toolchain v4.29.0)
- numerical hypotheses: evidence/composition/2026-09-23/stage4/* (quotient/recon/invariant PASS)

## Residual note
The .olean/.lean are present; a from-scratch `lake build` recompilation was NOT re-run in
this composition stage (environment disk 100%, mathlib fetch not performed). The artifact
evidence bit is carried by the existing verified core-lane log per repo convention.