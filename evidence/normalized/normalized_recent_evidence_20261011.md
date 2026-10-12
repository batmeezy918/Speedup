# Normalized Recent Evidence — AGD / MuNi / SIM2XR
Snapshot: 2026-10-11 UTC. Repository: batmeezy918/Speedup.

## Best scoped recent result

MUNI v4 on SM6475 AArch64, Android 16 / Debian PRoot; d=4096, r=64, m=64, steps=256; 7 trial clusters x 5 reps, CPU affinity cores 4–7. Other device processes were active.

- Run-loop: 68.475875 ms baseline / 0.992219 ms quotient = **69.012892x**.
- Full E2E: 68.325552 ms baseline / 1.013927 ms quotient = **67.387039x**.
- Reported max_abs_error=0.
- Exploratory bootstrap interval of paired E2E ratios: [66.641278x, 67.851996x].
- Claim class: **FORMAL_PARTIAL_MEASURED_LOCAL**. The Lean theorem addresses a bounded algebraic model, not a verified C/IEEE-754/compiler refinement.
- Inadmissible control fell back: E2E 68.649937 ms / 68.515438 ms = 1.001963x ratio of medians; paired interval [0.999187x, 1.001963x] includes 1. No fallback speedup claimed.

## Other recent results (keep separate)

| Receipt/run | Baseline -> optimized | Reported result | Scope/caveat |
|---|---|---:|---|
| Formal-gap bench d=2048, m=64, r=32, 32 steps, 5 trials x 3 reps | structured 1.724844 ms -> quotient 0.025243 ms | **68.329596x** | reported max errors all 0 for this invocation |
| Same invocation against general dense | dense 169.228958 ms -> quotient 0.025243 ms | **6703.995497x** | dense is a structural reference for U(x)I_m, not generic BLAS superiority |
| Nine-session aggregate d=2048 | structured -> quotient | median **78.348905x**, range **24.828234x–146.954659x** | 9 sessions + 9 A/A sessions; A/A median 1.000506, max deviation 0.38%; substantial between-session timing shifts |
| Same nine-session aggregate vs dense | dense -> quotient | median **8790.308827x**, range **6715.496509x–12671.738194x** | reference-only result, noisy dense timing |
| Heat workload, d=2048, 32 steps | structured 1.549358 ms -> quotient 0.022691 ms | **68.280713x** | separate heat receipt: 1.780295 -> 0.025156 ms = **70.770194x**; do not merge runs; direct stencil delta 2.22e-16 |
| SOTA differential sweep, 5 sizes d=512…65536 | quotient vs structured operator | **34.7x–572.5x** | local report: rotating interleave, 2 warmups, 9 trials, 2 reps, GCC -O3 -march=native. Against OpenBLAS dense dgemv: 678x–3201x where feasible. Exact error 0 and zero fallback in timed runs. A/A interval [0.864x,1.152x]; d=512 drift +11% flagged. Applies to U(x)I_m only. |
| MUNI replay d=2048, r=32, m=64, 32 steps | run-loop 1.560125 -> 0.022740 ms; E2E 1.554781 -> 0.027833 ms | **68.608287x loop; 55.860276x E2E** | max error 0, but compiler/flags/target and source manifest SHA are unknown; adversarial suite not run in this process; FORMAL_PARTIAL_MEASURED_LOCAL |
| Dual-snapshot recovery pilot d=2048, injected fault at height 13 | prior quotient median 0.171041 ms vs original ~10.980 ms; recovery median 10.509 ms | prior path ~**64.20x**; recovery ~**1.045x** by ratio of medians | five runs, max error 0, detection/recovery/re-entry passed, adversarial 23/23, fuzz 20k/0 observed violations. Recovery reuses existing quotient; no new quotient synthesis or complete state-machine proof yet. |

All speedups are workload, implementation, environment and protocol specific. Dense BLAS is not the fairest algorithmic baseline for the structured U(x)I_m operator.

## Formal gaps, adversarial results, integrity

- Recursive ledger: depth 5, 13 iterations; **8 CLOSED, 1 OPEN, 1 RESIDUAL, 1 ASSUMED**.
- Adversarial suite: **23/23 PASS** in separate receipt. Property fuzz: **20,000 cases, 0 violations**; finite testing is not an exhaustive proof.
- Exact-tolerance self-test says CLAIM_TOL0=EXACT_BITWISE; positive tolerance is APPROX_UNBOUNDED.
- Open O2b: max_tol=9.99e-10, max_err=3.15199e-7, error/tolerance **315.514x**. Do not label positive-tolerance output bit-exact.
- Residual O4c: no C/IEEE-754/compiler refinement artifact binding native binary to Lean model.
- Assumed O1: block-constant/tensor-separable invariant is assumed by design; automatic invariant discovery is out of scope.
- Lean axiom logs include Quot.sound, propext, and for one theorem Classical.choice. The whole framework is not axiom-free.
- The 46-source formal-gap verification log contains dependency-order “unknown module prefix” errors on an early pass; another report describes a successful ordered core-lane pass. Do not claim all formal verification passed without identifying lane and run.
- deliverables_check_fresh.txt reports adjusted_full_run.log FAILED against deliverables.post-rerun.sha256 while other entries were OK. Regenerate/validate the manifest after the log is stable before claiming it is clean.
- SOTA sweep ran on a single visible core in Debian PRoot with WALT governor. v4 used affinity but had background load. Bootstrap intervals do not establish across-day/device/thermal generality.

## Claim ladder

Supported: strong local speedup for the admitted structured workload; fail-closed behavior for inadmissible input; bounded algebraic-model proof; 23 adversarial tests and 20k fuzz cases with zero observed violations.

Not established: generic LLM attention speedup, arbitrary-matrix speedup, universal/cross-device gains, verified native refinement, automatic invariant discovery, new quotient synthesis in the recovery pilot, production generalization.

## Local receipt pointers

- evidence/formal_gap_elevation_20261010/REPORT.md and SOTA_REPORT.md; receipts/bench.json, bench.txt, session_stats.json/txt, session_1–9.json, noise_1–9.json, adversarial.txt, fuzz.txt, gap_ledger.json/txt, provenance.txt, lean_core_verification.log, lean_refinement.log, deliverables.post-rerun.sha256, deliverables_check_fresh.txt.
- evidence/live_silicon_elevation_20261010T0835Z/AGD_RESEARCH_GRADE_ELEVATION_REPORT.md, timing_statistics.md, muni_v4_admissible/inadmissible.json/.txt, adversarial_v4_samples.txt, benchmark_environment_v4.txt, source_manifest.sha256/digest.
- evidence/nrebbi_muni_replay_20261010/receipts/muni_d2048_m64.json/.txt and source/proof receipts.
- evidence/dual_snapshot_reentry_20261010/REPORT.md, run.txt, repeats.txt, fuzz.txt, adversarial.txt, SHA256SUMS.
