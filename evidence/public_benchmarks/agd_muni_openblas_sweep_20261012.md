# AGD / MuNi Public-Baseline Differential Sweep

**Run window:** 2026-10-12 UTC  
**Status:** Exploratory multi-size kernel differential sweep completed. Not an MLPerf submission or a full application E2E benchmark.

## Headline

On the structured operator \(\bar U\otimes I_m\), the AGD/MuNi candidate was faster than the direct structured reference in all five configurations. Ratios of medians ranged from **37.50× to 1,026.16×**. Against OpenBLAS 0.3.29 dense dgemv, ratios of medians ranged from **1,659.49× to 6,431.40×** where dense BLAS was enabled.

These are workload- and implementation-specific kernel observations, not universal claims. The dense baseline materializes a highly structured operator, so the structured reference is the more informative algorithmic comparison. At d=65,536, the dense matrix would require 34,359,738,368 bytes (~32 GiB), so BLAS was disabled by the harness memory guard.

## Environment and protocol

- Android ARM64 device, Debian GNU/Linux 13 in PRoot; Linux kernel reported as 6.17.0-PRoot-Distro.
- CPU: 8 online CPUs; Cortex-A55 and Cortex-A78 clusters reported by lscpu.
- Compiler: GCC 14.2.0; flags: -O3 -march=native -mtune=native -funroll-loops -fomit-frame-pointer -DNDEBUG -std=c11.
- Dense baseline: OpenBLAS 0.3.29, dynamic architecture build.
- Workload: repeated application of \(\bar U\otimes I_m\).
- Protocol: two warm-up rounds, 9 timed trials, 2 repetitions per trial; faster repetition recorded; path order rotates.
- Timing boundary: candidate timing includes agd_plan_run and reconstruction but excludes agd_plan_create. Baseline matrix construction and input-buffer copies are outside the timed interval. This is a repeated-kernel microbenchmark, not cold-start E2E.
- Correctness: one-step outputs were checked before timing. Candidate and structured-reference maximum absolute errors were 0 for every configuration; BLAS error was 0 where enabled. Timed multi-step final states were not independently compared in this harness version.
- Candidate gate: every configuration reported admissible=1, certified=1, fallback=0.

## Results

Times are milliseconds per configured repeated-kernel run. Ratios are ratios of medians. Step counts vary by size; compare ratios within each row, not absolute time across rows.

| d | m | r | steps | Candidate median (min–max) | Structured median (min–max) | OpenBLAS median (min–max) | vs structured | vs OpenBLAS |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 512 | 32 | 16 | 1000 | 0.488177 (0.476355–0.743177) | 27.364167 (22.396146–41.559948) | 810.125625 (553.896875–983.766249) | **56.05×** | **1,659.49×** |
| 1024 | 32 | 32 | 64 | 0.139115 (0.138178–0.195469) | 5.216302 (4.768542–17.576614) | 606.839427 (244.189166–720.242552) | **37.50×** | **4,362.14×** |
| 2048 | 64 | 32 | 16 | 0.046875 (0.046770–0.047239) | 3.346563 (3.214115–4.053177) | 301.471666 (232.413906–454.492240) | **71.39×** | **6,431.40×** |
| 4096 | 64 | 64 | 8 | 0.093802 (0.077344–0.114115) | 7.039740 (6.858854–28.368802) | 291.020885 (269.707239–432.623073) | **75.05×** | **3,102.50×** |
| 65536 | 256 | 256 | 4 | 0.802916 (0.800417–0.834635) | 823.916927 (677.362344–1188.891562) | not run | **1,026.16×** | not comparable |

## Raw trial vectors

Each vector contains nine trial times in milliseconds, in trial order.

| d | Candidate raw trials |
|---:|---|
| 512 | 0.743177, 0.734427, 0.734480, 0.487761, 0.489375, 0.476355, 0.488177, 0.478646, 0.482187 |
| 1024 | 0.139115, 0.138490, 0.138490, 0.181145, 0.140417, 0.195469, 0.138178, 0.138438, 0.140208 |
| 2048 | 0.046875, 0.046823, 0.046770, 0.047239, 0.046928, 0.046927, 0.046875, 0.046771, 0.046875 |
| 4096 | 0.094375, 0.114115, 0.093698, 0.094219, 0.093750, 0.093802, 0.093698, 0.094010, 0.077344 |
| 65536 | 0.823385, 0.804687, 0.834635, 0.802031, 0.802344, 0.801302, 0.800417, 0.805730, 0.802916 |

| d | Structured raw trials |
|---:|---|
| 512 | 25.759844, 26.669271, 26.256042, 31.188854, 27.364167, 22.396146, 40.352240, 36.201458, 41.559948 |
| 1024 | 6.832917, 4.768542, 4.792239, 14.753646, 5.216302, 7.244844, 4.808489, 4.770000, 17.576614 |
| 2048 | 3.240885, 3.396927, 4.053177, 3.706980, 3.295313, 3.214115, 3.265417, 3.346563, 4.030885 |
| 4096 | 11.117760, 28.368802, 10.876667, 7.375573, 7.039740, 6.858854, 7.038646, 6.864531, 6.941146 |
| 65536 | 1050.240520, 1188.891562, 726.500208, 868.037656, 732.975312, 689.474479, 834.968645, 677.362344, 823.916927 |

| d | OpenBLAS raw trials |
|---:|---|
| 512 | 889.098124, 853.148333, 810.125625, 553.896875, 782.525624, 886.904843, 559.778385, 725.228073, 983.766249 |
| 1024 | 566.501823, 606.839427, 670.622812, 691.565208, 720.242552, 680.429635, 429.491458, 244.189166, 310.459583 |
| 2048 | 454.492240, 369.476614, 390.153333, 232.413906, 315.274323, 301.471666, 261.104635, 241.258906, 281.566458 |
| 4096 | 428.823541, 403.983073, 432.623073, 291.020885, 269.707239, 284.159531, 280.651406, 321.874427, 282.082291 |
| 65536 | not run; dense matrix exceeds the configured memory guard |

## Stability and scope limitations

- Candidate A/A repeat ratio range: **1.0022–1.3033**.
- Structured-baseline trial-order drift: **−36.9% to +36.8%**.
- The process was not pinned to a CPU core; background workload/governor activity was present.
- Step counts differ by size to keep the sweep operationally tractable. The d=512 receipt was completed in the first pass; d=1024 was stopped after excessive runtime at 500 steps and rerun at 64; larger sizes were run with reduced steps.
- The candidate's plan creation is excluded from timing; therefore these ratios are not cold-start or complete E2E results.
- The harness verifies one-step outputs, not the final state after all timed steps. Add a multi-step trajectory comparison before upgrading the claim.
- A/A ratios and baseline drift are too large for benchmark-grade confidence. Pinning to a performance core, controlling OpenBLAS thread count, recording thermal/governor state, adding timed-trajectory correctness checks, and repeating the sweep are required next.
- This is not an MLPerf Inference result: MuNi is not yet integrated as an MLPerf model backend, and no official model/dataset/accuracy submission was run. Eigen's generic linear-algebra suite was not run because it would not by itself constitute a fair same-operator comparison.

## References

- OpenBLAS: https://github.com/OpenMathLib/OpenBLAS
- MLCommons Inference (future end-to-end integration target; not run): https://github.com/mlcommons/inference
- Eigen benchmark workflow (separate generic suite; not run): https://libeigen.gitlab.io/pages/how_to_run_the_benchmark_suite/

## Verdict

**Exploratory multi-size differential sweep completed.** Candidate/structured ratios: **37.50×–1,026.16×**. Candidate/OpenBLAS dense ratios where enabled: **1,659.49×–6,431.40×**. The one-step correctness/admissibility checks passed. Timing drift and the kernel-only timing boundary prevent this from being presented as a stable, full-E2E, official benchmark result. The next gate is a pinned controlled rerun plus multi-step output validation.
