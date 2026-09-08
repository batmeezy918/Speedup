# Historical Speedup Closure — 2026-09-08

Target: actual Termux/Android device via Remote Desktop Commander.
OS: Android 15, Linux 6.6.98, aarch64; 7.5 GiB RAM reported.

Evidence rule: claim strength <= evidence strength. Runtime speedup is distinct from state/work reduction, projection ratios, objective ratios, and wall-clock. No universal or HPC dominance claim is permitted.

## SIM2XR shared-prefix — VALIDATED
Original: 16.808386x. Target rerun: 7 paired repeats using branches=24, prefix_steps=5000, suffix_steps=80, inner_work=48, seed=91820260531.

Observed speedups: 16.506075x, 17.569849x, 17.617531x, 17.469194x, 17.577857x, 17.509339x, 17.546782x.
Median: 17.544277x. Time reduction: 94.300136%. All seven output/hash equivalence checks passed.

Theoretical work: baseline 121920 steps; SIM2XR 6920; skipped 115000; work reduction 94.324147%; theoretical step ratio 17.618497x.

Definitive claim: on this target and declared shared-prefix workload, SIM2XR produced exact output equivalence while reducing measured verified runtime by median 17.544277x. Status: VALIDATED_LOCAL_MEASURED_REPRODUCED. Boundary: shared-prefix only; not universal/HPC/quantum.

## GS254 / RIMS E_EQ — BLOCKED
Original: 18.533401810344827x effective-time speedup. Target rerun: 5 paired baseline/candidate executions, all exit code 0. The proof gate returned INSTRUMENTATION_MISSING because semantic factor identity could not be extracted/proven from the outputs.

Definitive claim: historical 18.5334x is NOT re-elevated. Runtime alone is insufficient for E_eq. Status: BLOCKED_PENDING_SEMANTIC_WITNESS.

## Omega-BFGS v5 — PENDING
Historical 36.539x is a projection-slope ratio, not runtime speedup. Canonical executable runner and historical parameters were not recovered on target. Status: PENDING_RERUN.

## Sparse 1M projection — PENDING
Historical ~10.6667x is a structured sparse projection result. Canonical executable runner/parameters were not recovered. Status: PENDING_RERUN; no runtime elevation.

## Omega v6.3 96-bit factorization — NOT STABLE
Canonical runner executed on target. Trial 1: Pollard Rho 15.346055s; Omega 47.851657s; ratio 0.3208x. Trial 2: Pollard Rho 39.826648s; Omega 6.627971s; ratio about 6.009x. Both returned exact ground-truth factors.

Definitive claim: sampled 96-bit instances were correctly factored, but the target rerun does not support a stable 2.60x speedup. Status: NOT_VALIDATED_AS_STABLE_SPEEDUP. Boundary: small-number factorization only; no cryptographic break.

## Omega v7 aggregate — PENDING
Historical ~1969x is an objective/error ratio, not runtime-normalized. Canonical runner/parameters not recovered. Status: PENDING_RERUN.

## Haradax alpha projection — PENDING
Historical mean alpha 563.1747/final 2456.8106 is a projection/control metric, not compute speedup. Canonical target runner/parameters not recovered. Status: PENDING_RERUN.

## ChronoFold Quant / CFArena — SUPPORTING
25 zero-defect traces and local formal/proof-arena results remain supporting evidence; they are not speedup claims.

## Closure
One historical literal speedup was strengthened: SIM2XR shared-prefix, median 17.544277x with exact hash/output agreement. GS254 was actively rerun and correctly blocked by its semantic witness gate. Omega v6.3 was actively rerun and failed stability as a 2.60x claim. Remaining projection/aggregate claims remain quarantined until canonical executable parameters are recovered and rerun.

No artifact here asserts universal speedup, HPC dominance, quantum advantage, or cryptographic break.