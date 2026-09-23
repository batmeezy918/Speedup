# SILICON CLOSURE EVIDENCE — 2026-09-23

Companion evidence to the `verified/` PCSS claims. These directories contain the
**literal full-runtime end-to-end silicon runs** performed on 2026-09-23 that
instantiate each verified-speedup family with every pipeline stage charged
(detect -> project -> reduced compute -> reconstruct -> verify).

NOT a PCSS promotion. Per `verified/README.md` an artifact may enter `verified/`
only after ALL mandatory PCSS gates pass, including the Lean4 lane (L). For these
closure runs the Lean4/mathlib lane was NOT re-executed, so `publish_satisfied=false`.
They are recorded as empirical silicon closures with their exact gate status.

## Status map (ClaimStrength <= EvidenceStrength)

| mechanism | silicon-closed max ratio | gates on literal run | PCSS/Lean status |
|---|---|---|---|
| QMULT-02 quotient GEMM | S_SANDBOX 19.99x (N=1024 r=64); 17.16x / fp64 16.95x (N=4096 r=256) | STRUCT_INV true; rel.err 1.7e-7 / 5.7e-7; battery 21/21 (C15 non-finite guarded) | EMPIRICAL; Lean L NOT_EXECUTED; family-scoped |
| AQGE-02 quotient tower | S_native 72.07x; composed 69.41x; (AB)^6 stay-in-Q 457.1x | descent 3.45e-8 pass; adversarial 9/10 fail-closed (+1 collage flagged); discovery break-even K=21 | EMPIRICAL; promotion NOT_VERIFIED_OPERATIONAL_PRIMITIVE; Lean L NOT_EXECUTED |
| SIM2XR invariant-subspace | pipeline 18.66x (oracle, exact 7.2e-13); single-shot construction-inclusive 0.73-0.83x (SLOWER) | oracle in-subspace exact; discovered alignment 3.4e-4 -> wrong subspace; discovery-inclusive 0.02-0.18x | single-shot claim REFUTED on silicon; SIM2XR PCSS certificates QUARANTINED (see campaign); Lean mathlib NOT_EXECUTED |
| AGD GEMM quotient pipeline | E2E 1.285-2.273x (vs scalar REF); kernel micro max 4.51x | OVERALL_GATE=PASS (correctness 40/40 rows, stability 8/8, quotient 6/6, dim 22/22, E2E 5/5, err=0) | "6.26x" heading REFUTED by these receipts; blocked 0.9-4.3 GF vs O3-ikj 11-14 GF |

## Files
- `SILICON_CLOSURE_CERTIFICATE.md` — full closing statement per mechanism.
- `CLOSURES_MTL.json` — aggregated closure values + per-receipt sha256 (`_meta.artifacts`).
- `final_certificate.json` — dated final certificate in repo's standard shape.
- `receipts/` — raw stdout/CSV from the literal runs (A78 cores pinned, single BLAS thread).