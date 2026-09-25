# PCSS COMPOSITION REPORT — C1 = QMULT-02 ∘ AQGE-02

Composition Closure Execution Prompt — 2026-09-23. This is the honest, strict-gated
record of composing two VERIFIED primitives into one natively measured implementation.

## A. ES/Nomenclature
- Primitives: QMULT-02, AQGE-02 (both VERIFIED, exact-invariant-sector, matrix family).
- Composed implementation: O_C = σ ∘ Tbar^14 ∘ π (fused stay-in-Q trajectory, 8+6=14 steps).
- Baseline: T_full^14 in full space R^512x512.
- S_composed = T_B / T_C measured on native wall clock. NO ratio multiplication.

## B. Provenance
- Repo: /root/Speedup @ 2701651a9a (branch fix/lean4-green), clean before changes.
- source_hash 5f3b2d9d15573a98 (unchanged by composition artifacts; hash covers *.py/*.lean only).
- Component certs: evidence/final/2026-09-23/pcss/{qmult02,aqge02}_matrix.certificate.json.
- Ledger publish: run_id pcss-run-1790200585, hash a587395593c6d8fd... (canonical sha verified).

## C. Composition Matrix & Selection
- composition_matrix.csv: 3 matrix-family pairs COMPOSABLE (trajectory deepening), all
  matrix∘SIM2XR pairs INCOMPATIBLE (no certified morphism). C1 selected in
  composition_selection.md; rejected list in composition_rejected.csv.

## D. Implementation (STAGE 3)
- O_C = σ ∘ Tbar^14 ∘ π; single projection, 14 reduced steps, single reconstruction.
- Schema validated; static check: T_full^14 == σ(Tbar^14(π(x0))) EXACT.

## E. Correctness (STAGE 4)
- Quotient forward: π(T x) = Tbar(π x) over all 15 trajectory states: PASS.
- Reconstruction reverse: σ(π(e)) == e, max error 0.0 (15/15 states): PASS.
- Invariant: omega_matrix True on ALL baseline and candidate states: PASS.
- Trace identities (by-design exactness): baseline == candidate.

## F. Performance (STAGE 5)
- Measured natively, affinity {2,3}, OPENBLAS/OMP=1, 30 reps / 5 warmups.
- T_B median 7,008,500,362 ns; T_C median 337,018,958 ns; S_composed = 20.80.
- Interaction factor I12 = 0.142 vs modeled S1*S2 = 146.24. Ratio-product over-claims ~7x.
  THIS IS THE PROTOCOL-DEMANDED DEMONSTRATION: never multiply isolated ratios.

## G. Reproducibility (STAGE 6)
- Same-affinity rerun: S = 21.67 (Δ 4.2% vs first). PASS under certified conditions.
- Big-core rerun ({4,5,6,7}): S = 24.94 — CPU heterogeneity (little vs big core) documented,
  NOT instability (see failure_ledger F4).

## H. Amortization (STAGE 7)
- Per-step: baseline 480,186,224 ns; candidate 2,035,379 ns (×14 amplified by stay-in-Q).
- One-off π 935,793 ns; one-off σ 306,118,488 ns; break-even N* = 0.642 steps → at 14 steps
  fully amortized. Composition is amortization-positive.

## I. Formal Closure (STAGE 8)
- O_C is an INSTANTIATION at n=14 of the ∀n-verified closure theorems in
  lean4/chronofold/ExactQuotientClosure.lean (quotient_iterate, reconstructed_iterate,
  observable_preserved_iterate, exact_quotient_closure). No new/unverified math added.

## J. End-to-End Certification (STAGE 9)
- Full pcss_native_runner run on composed scenario (pinned {2,3}, certified condition):
  speedup 22.15, all 7 gates True. strict_gate enforce → STRICT_GATE=VERIFIED (exit 0).
- Integrity incident: strict_gate.publish() default path collided with existing C-cluster
  SIMD cert at verified/sim2xr/2026-09-23/pcss_certificate.json. Overwritten file RESTORED
  from git; composed cert relocated to its suffixed dir
  verified/sim2xr/2026-09-23-qm02_aqge02_composed/ (mirrors the 4 primitives' convention);
  the ledger publish row artifact path corrected; canonical-hash binding re-verified
  (match=True). No certificates destroyed.
- Ledger: publish row appended, bound by canonical sha256 of the published cert.

## K. Result & Recommendation
- S_composed = 22.15x (native, PCSS-verified). Interaction I12=0.152 confirms that the
  modeled product S1*S2 = 146.24 is NOT the composed speedup; the fused stay-in-Q trajectory
  yields a real, measured, amortization-positive speedup bounded by the operator-count family,
  and composing the two verified primitives into one measured implementation is CONFIRMED.
- Escalation to C2 = QMULT-02 ∘ AGD-GEMM (16-step family) or a 3-way composition is only
  admissible after operator authorization and would reuse this exact pipeline
  (scenario → runner → compose_certificate → strict_gate → ledger).

## Required artifacts (delivered)
- composition_matrix.csv, composition_selection.md, composition_rejected.csv, composition_results.csv,
  composition_raw_timings.csv, composition_interaction.csv, composition_amortization.csv,
  composition_claims.jsonl, composition_certificate.json, composition_failure_ledger.csv,
  composition_provenance.json, composition_report.md (this file),
  pcss/qmult02_o_aqge02_composed.certificate.json, stage_records/STAGE_0..9.

## Honesty declaration
- S_composed is a NATIVE wall-clock measurement (T_B/T_C) of the composed implementation
  executed as one fused operator. The product S1*S2 is labeled MODELED reference ONLY and is
  deliberately NOT achieved — the interaction factor quantitatively proves why multiplication
  of isolated speedups is prohibited by the PCSS composition constitution.