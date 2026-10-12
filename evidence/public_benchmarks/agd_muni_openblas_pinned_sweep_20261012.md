# AGD / MuNi Controlled Public-Baseline Sweep

**Run date:** 2026-10-12 UTC  
**Status:** Controlled single-core differential microbenchmark completed. Not an MLPerf submission or complete cold-start application benchmark.

## Result

With the candidate and baselines pinned to CPU 7 and OpenBLAS restricted to one thread, the A/A candidate ratios were **1.000–1.001**, and reported structured-baseline drift was approximately **−0.1% to +0.3%**. This is materially more stable than the unpinned pass.

On the structured operator \(\bar U\otimes I_m\), ratios of medians were **34.2×–563.3×** against the direct structured reference and **563.4×–2,802.7×** against OpenBLAS dense dgemv where enabled.

These are same-operator, kernel-level measurements for this implementation and device. The dense baseline materializes a highly structured operator; therefore it is not evidence of superiority over OpenBLAS for arbitrary matrices.

## Environment and protocol

- Android ARM64 device; Debian GNU/Linux 13 in PRoot; Linux kernel 6.17.0-PRoot-Distro.
- CPU: 8 online CPUs; Cortex-A55 and Cortex-A78 clusters reported by lscpu. The run was pinned to CPU 7 (A78 cluster expected).
- Compiler: GCC 14.2.0.
- Flags: -O3 -march=native -mtune=native -funroll-loops -fomit-frame-pointer -DNDEBUG -std=c11.
- Baseline: OpenBLAS 0.3.29, OPENBLAS_NUM_THREADS=1.
- Two warm-up rounds, 9 timed trials, 2 repetitions per trial, faster repetition recorded, rotating path order.
- Candidate timing includes agd_plan_run and reconstruction but excludes agd_plan_create; baseline matrix construction and buffer copies are also outside timing.
- Candidate and structured-reference one-step maximum absolute errors were 0 for all configurations; BLAS one-step error was 0 where enabled.
- Each configuration reported admissible=1, certified=1, fallback=0. The timed multi-step final states were **not** independently compared in this harness version.

## Results

Milliseconds per configured repeated-kernel run; ranges are min–max across nine trials. Step counts vary by size, so compare ratios within rows.

| d | m | r | steps | Candidate median (min–max) | Structured median (min–max) | OpenBLAS median (min–max) | vs structured | vs OpenBLAS |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 512 | 32 | 16 | 1000 | 0.471198 (0.470417–0.471563) | 16.991614 (16.956094–17.039584) | 307.412240 (306.867864–308.744948) | **36.1×** | **652.4×** |
| 1024 | 32 | 32 | 64 | 0.138333 (0.137968–0.139063) | 4.736771 (4.730573–4.750625) | 77.942760 (77.599739–78.549532) | **34.2×** | **563.4×** |
| 2048 | 64 | 32 | 16 | 0.036302 (0.036094–0.036615) | 2.341875 (2.340937–2.344167) | 86.972969 (86.595364–87.327500) | **64.6×** | **2,399.3×** |
| 4096 | 64 | 64 | 8 | 0.076198 (0.076041–0.076510) | 5.058542 (5.048437–5.065313) | 213.559114 (213.396042–213.599115) | **66.4×** | **2,802.7×** |
| 65536 | 256 | 256 | 4 | 0.805104 (0.801198–0.851354) | 453.476458 (452.096094–454.373698) | not run | **563.3×** | not comparable |

Dense BLAS was disabled at d=65,536 because the dense matrix would require 34,359,738,368 bytes (~32 GiB) before overhead, exceeding the harness's 700 MB guard.

## Raw trial vectors (milliseconds)

| d | Candidate |
|---:|---|
| 512 | 0.471563, 0.471406, 0.471146, 0.470417, 0.470833, 0.471198, 0.471354, 0.471563, 0.470885 |
| 1024 | 0.138594, 0.138489, 0.138333, 0.138177, 0.137968, 0.139063, 0.138385, 0.138178, 0.138125 |
| 2048 | 0.036615, 0.036198, 0.036354, 0.036302, 0.036407, 0.036250, 0.036146, 0.036094, 0.036146 |
| 4096 | 0.076354, 0.076250, 0.076146, 0.076250, 0.076510, 0.076146, 0.076198, 0.076042, 0.076041 |
| 65536 | 0.801979, 0.808802, 0.801198, 0.803594, 0.801355, 0.851354, 0.821511, 0.805104, 0.824063 |

| d | Structured reference |
|---:|---|
| 512 | 16.991614, 16.977239, 16.982709, 16.956094, 16.966719, 17.030937, 17.039584, 17.024063, 17.034635 |
| 1024 | 4.750625, 4.734479, 4.734739, 4.736771, 4.734739, 4.741666, 4.730573, 4.737917, 4.739427 |
| 2048 | 2.342500, 2.341459, 2.344167, 2.341823, 2.342396, 2.341875, 2.343021, 2.341406, 2.340937 |
| 4096 | 5.060052, 5.050729, 5.061302, 5.058542, 5.065208, 5.052500, 5.065313, 5.048437, 5.052448 |
| 65536 | 453.582708, 453.476458, 452.735364, 453.266354, 453.722499, 452.325052, 452.096094, 454.373698, 454.313646 |

| d | OpenBLAS |
|---:|---|
| 512 | 306.988177, 307.412240, 307.107864, 306.876302, 306.867864, 308.702709, 308.388229, 308.164375, 308.744948 |
| 1024 | 78.211510, 77.987292, 77.942760, 78.549532, 77.840729, 77.599739, 78.130312, 77.802187, 77.765312 |
| 2048 | 86.876406, 86.899740, 86.827448, 87.020729, 87.011094, 86.972969, 86.595364, 87.327500, 87.137656 |
| 4096 | 213.570782, 213.396042, 213.593177, 213.538802, 213.480261, 213.599115, 213.559114, 213.501719, 213.572656 |
| 65536 | not run |

## Interpretation and remaining gates

1. The pinned run's repeat stability is much stronger than the unpinned run; its A/A candidate ratios lie between 1.000 and 1.001.
2. The candidate beats the direct structured reference in each measured configuration. The public OpenBLAS comparison is against dense materialization of \(\bar U\otimes I_m\), not arbitrary-matrix superiority.
3. The reported one-step checks pass, but the harness does not yet compare final states after all timed repeated steps. Add this check before upgrading the correctness claim.
4. Candidate plan creation is excluded from the timing. These figures are not cold-start or full E2E results.
5. The next benchmark gate is to include a setup-inclusive run, validate multi-step final outputs for candidate/structured/BLAS paths, and preserve source/binary hashes with the raw receipt bundle.

## Public references

- OpenBLAS source and documentation: https://github.com/OpenMathLib/OpenBLAS
- MLCommons Inference (not run; MuNi is not yet an MLPerf model backend): https://github.com/mlcommons/inference
- Eigen benchmark workflow (not run; generic Eigen suite alone is not a same-operator comparison): https://libeigen.gitlab.io/pages/how_to_run_the_benchmark_suite/

## Verdict

**Controlled public-baseline kernel sweep completed.** Observed candidate/structured ratios: **34.2×–563.3×**; candidate/OpenBLAS dense ratios where enabled: **563.4×–2,802.7×**. A/A timing stability improved to 1.000–1.001. This is strong, scoped local evidence, not an official MLPerf result, universal claim, or verified-native E2E result.
