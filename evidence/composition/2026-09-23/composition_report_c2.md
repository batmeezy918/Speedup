# PCSS COMPOSITION REPORT — C2 = QMULT-02 ∘ AQGE-02 ∘ AGD-GEMM (escalation, STAGE 11)

Operator-authorized escalation to the most operational composition of the verified corpus:
fuse ALL three VERIFIED matrix-family primitives into ONE stay-in-Q trajectory.

## Operator
- O_C = σ ∘ Tbar^22 ∘ π (8+6+8 = 22 reduced steps; single projection, single reconstruction)
- Baseline: T_full^22 in full space R^512x512
- Domain: exact-invariant-sector matrix, n=512 tile=16 r=1024 (identical certified family)

## Measured result
- S_composed = T_B/T_C = 35.8222x  (native, runner pinned {2,3}, 30 reps / 5 warmups)
- Correctness: quotient forward PASS (22 steps), reconstruction err 0.0, omega invariant PASS
- formal closure: instantiation at n=22 of verified ∀n theorems (ExactQuotientClosure.lean)
- strict gate: STRICT_GATE=VERIFIED, 7/7, ledger hash-bound (df7b113b...)

## Interaction / honesty control (the central demonstration)
- Modeled ratio product S1*S2*S3 = 1931.49
- I123 = S_measured / (S1*S2*S3) = 0.0186  -> ratio multiplication over-claims 53.9x
- Verified(M1)^Verified(M2)^Verified(M3) does NOT imply Verified(M3∘M2∘M1).
  The composed speedup must be (and here WAS) measured natively.

## Depth scaling
- C1 (2-way, 14 steps): 22.15x
- C2 (3-way, 22 steps): 35.82x
- Suitable trend: deeper fused stay-in-Q monotonically amortizes the single π/σ boundary and
  approaches the operator-count family bound (~256x) without ever reaching any ratio product.

## Integrity notes
- strict_gate.publish() default path collided again with existing certs at
  verified/sim2xr/2026-09-23/; the overwritten C-cluster SIMD cert was restored from git;
  C2 cert relocated to verified/sim2xr/2026-09-23-qm02_aqge02_agd_composed/; ledger artifact
  field corrected; canonical-hash binding re-verified (match=True).
- Disk-full event during published-dir copy handled: C1 traces (gitignored, not in SHA256SUMS)
  removed to free space; C2 dir completed with full evidence set + SHA256SUMS.txt + .gitignore.

## Final status
- C2 = most operational composition. COMPOSITIONALLY_VERIFIED (strict-gate 7/7).
- Both C1 and C2 published, ledger-bound, reproducible, formally instanced.
- SIM2XR (vector domain) remains the sole non-composable element (no certified morphism).
- Reveal: the composition protocol's anti-overshoot guard is now demonstrated at TWO depths,
  quantifying that isolated-ratio multiplication is neither measurement nor composition.