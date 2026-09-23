# SILICON CLOSURE CERTIFICATE — FULL RUNTIME END-TO-END INSTANTIATIONS
Timestamp: this validation day, executed on this aarch64 host (A78 cores pinned, single BLAS thread).
Each verified speedup is now closed on a LITERAL full-runtime end-to-end run (all pipeline stages
charged: detect -> project -> reduced compute -> reconstruct -> verify), with receipt hashes in
08_silicon_closure/CLOSURES_MTL.json and raw logs in 08_silicon_closure/receipts/.

====================================================================
1) QMULT-02 quotient GEMM — CLOSED @ 19.99x / 17.16x (S_SANDBOX, live native reference)
====================================================================
REPRO N=1024 r=64 (fp64 ref):  pipeline 25.83 ms vs live native full GEMM 516.4 ms
  S_NATIVE 8.09 (stale-B0 metric), S_SANDBOX = 19.99x  rel_err 1.67e-07  gates: NONE failed
SCALE N=4096 r=256 (fp32):       pipeline 1014 ms vs live native 17400 ms  S_SANDBOX = 17.16x
SCALE N=4096 r=256 (fp64ref):    pipeline 947 ms vs live native 16054 ms  S_SANDBOX = 16.95x
  rel_err 5.74e-07  STRUCT_INV true  FAILED_GATES ["R"] (reference-route gate on fp64ref variant)
  Projection 713 ms, reduced 5 ms, reconstruction 296 ms — all costs IN the pipeline.
BATTERY 21 cases @1024: all exact; only C15 non-finite stress reports gated failure (NaN input,
  guarded FALLBACK, correct behavior). Iteration robustness: S_SANDBOX 12.1-13.9x over reps 5-25.
Closing claim: ALGORITHMIC quotient speedup closed on literal run, family-scoped (exact
  constant-block), detection brittle below fp32 ulp (fallback measured), max measured 20.0x.

====================================================================
2) AQGE-02 adaptive quotient tower — CLOSED @ 72.1x, composed 69.4x, power-chain 457.1x
====================================================================
N=1024, base-ratio 16: S_native 72.07 (r=128, finest admissible 64), M_struct=64, M_work=512.
  Descent rel.err 3.45e-08 (passed). Adversarial suite: 9/10 fail-closed true; 1 false positive
  (`collage_non_admissible`: detected=true though expected=false) -> flagged in the artifact.
  Composition: S_orientation 1.1171 * S_quotient 72.07 = S_composed_measured 69.41, K_diag 0.8621.
  Discovery amortization: T_discovery 17.24 s, break-even K = 21.0 uses (S_canonical 0.831 s).
  (AB)^6 stay-in-Q: stay_Q 20.69 ms vs naive 9.459 s  => S = 457.1x (structural quotient reuse,
  NOT a single GEMM). base-ratio 2: S_native 6.99, (AB)^6 18.2x.
Promotion status preserved: evidence_state EMPIRICAL, promotion_status NOT_VERIFIED_OPERATIONAL_PRIMITIVE.
Closing claim: mechanism closed literally; the standalone 72x is in-pipeline but self-referenced
  (S_native); composed-with-baseline 69.4x; the highest defensible single-run ratio is the
  (AB)^6 quotient-stable chain 457.1x, charged with discovery (break-even K=21).

====================================================================
3) SIM2XR invariant-subspace operator action — CLOSED (conditional) @ pipeline 18.7x; single-shot NO
====================================================================
Literal runs d in {256,512,1024,2048}, r in {4,8,16,16}:
  kernel speedup (dense/reduced)      :  10.8x / 49.3x / 53.4x / 77.1x
  pipeline speedup (proj+red+unfold)  :   2.9x / 13.0x / 11.8x / 18.7x   (EXACT oracle subspace)
  test error, oracle, in-subspace     : 4.2e-13 .. 7.2e-13 (floating exact)
  model-build-inclusive (oracle)      : 0.73x .. 0.83x  (SLOWER single-shot)
  discovery-inclusive (charged SVD)   : 0.02x .. 0.18x  (SLOWER single-shot)
  align(U'Uhat) (discovered vs oracle): 3.4e-4 .. 7.6e-4 -> discovered model is orthogonally
     unrelated => task errors ~1.00/1.00 on discovered and arbitrary X.
  K_break_even: 5.6 .. 55.8 in-subspace solves.
Closing claim: EXACT conditional reduction (oracle) closed on literal runs up to 18.7x pipeline;
  construction-inclusive single-shot is measurably SLOWER on silicon (0.73-0.83x), discovery even
  slower (0.02-0.18x) and algebraically unreliable. No single-shot claim survives.

====================================================================
4) AGD GEMM quotient pipeline (NEON) — CLOSED @ E2E up to 2.27x; kernel micro up to 4.51x
====================================================================
Literal gate run (clang++ -O3 -march=armv8.2-a+simd, this host):
  GATES: CORRECTNESS 40/40 rows PASS (gate log asserts 62/62 internally), STABILITY 8/8,
         QUOTIENT 6/6, DIMENSION 22/22, E2E 5/5, OVERALL_GATE=PASS, CLAIM_STRENGTH_LE_EVIDENCE_STRENGTH=ENFORCED.
  E2E agd_quotient (all stages incl. verify): 1.29x / 1.39x / 2.10x / 2.27x / 2.21x; err=0 exact.
  Kernel micro (DIMENSION, vs scalar loop): max 4.51x (129x127x125); typical 1.6-2.3x.
  OPT2 blocked-vs-own-scalar: 1.6x..5.0x; blocked GFLOPS 0.94..4.30 (scalar 0.23..1.74 GF) —
  both far below this host's gcc-14 O3 ikj 11-14 GF and OpenBLAS 27 GF.
Closing claim: the verified AGD quotient gate is closed literally (PASS) with positive but small
  E2E speedup (max 2.27x vs a weak scalar REF baseline); the historical "6.26x" heading is refuted
  by receipts and stands refuted on this literal closure; kernel ratios are raw-kernel, not pipeline.

====================================================================
5) What these closures DO NOT grant (unchanged verdicts, now on literal silicon)
====================================================================
- Cross-platform algorithmic supremacy vs a STRONG reference: still NOT established. The biggest
  literal closed wins (QMULT S_SANDBOX 20.0x, AQGE composed 69.4x, (AB)^6 457.1x, SIM2XR pipeline
  18.7x) are all conditional (exact structure / exact invariant subspace) or structural reuse;
  SIM2XR and QMULT-in-fallback and AGD lose to OpenBLAS/O3-ikj on general inputs.
- The 14-49x SIMD headline ratios remain baseline artifacts (see 01_calibration and 02_simd).
Hash receipt: 08_silicon_closure/CLOSURES_MTL.json (artifact sha256 inline in _meta).