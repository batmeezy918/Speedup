# MUNI v4 timing statistics — on-device witness

- Device: TMRV08P5G / Android 16 / AArch64, Debian PRoot
- CPU affinity: cores 4–7
- Workload: d=4096, r=64, m=64, 256 steps
- Trial design: 7 trial clusters, 5 repetitions per cluster. The JSON stores each cluster's mean per-call timing. E2E arm order alternates per repetition.
- Source manifest SHA-256: 39f50f330db8b6c020a21a6a86a3d99ea1683206f481bc79e81bd58d4f41162a
- Output comparison: max_abs_error=0, bitwise exactness PASS.
- Background activity: other device processes existed. This is not an isolated laboratory run.

## Admissible input

| Metric | Full baseline | Quotient path | Result |
|---|---:|---:|---:|
| Run-loop median per call | 68.475875 ms | 0.992219 ms | 69.012892x |
| End-to-end median per call | 68.325552 ms | 1.013927 ms | 67.387039x |

End-to-end includes full-path allocations, input copy, 256 steps, and cleanup versus quotient plan creation, certificate/admissibility gate, run, reconstruction, and cleanup. This is the application-facing comparison.

Paired per-trial speedup ratios:
- Run-loop: 68.6685, 69.3821, 68.3002, 68.7696, 69.0129, 69.9149, 69.3945
- End-to-end: 63.5804, 67.0910, 67.8520, 66.6413, 68.1508, 67.5403, 67.3870

Exploratory percentile bootstrap (20,000 resamples of the 7 trial-cluster ratios; deterministic seed 20261010):
- Run-loop median speedup 69.012892x; 95% bootstrap interval [68.668529x, 69.394543x].
- End-to-end median speedup 67.387039x; 95% bootstrap interval [66.641278x, 67.851996x].

These intervals describe resampling variability within this one run, not between-day, thermal, device, or workload variation. Seven clusters are insufficient for a broad generalization.

## Inadmissible input / fallback

| Metric | Full baseline | Guarded fallback | Result |
|---|---:|---:|---:|
| Run-loop median per call | 68.510323 ms | 68.015875 ms | 1.007270x |
| End-to-end median per call | 68.649937 ms | 68.515438 ms | 1.001963x |

Paired per-trial E2E ratios: 0.9976, 1.0015, 1.0236, 0.9997, 1.0004, 1.0020, 0.9992. Median paired ratio 1.000440x; 95% bootstrap interval [0.999187x, 1.001963x], including 1.0. No fallback speedup is claimed.

## Raw data

Full raw trial arrays are retained in:
- muni_v4_admissible.json
- muni_v4_inadmissible.json

Each JSON contains the run-loop and end-to-end per-trial means, plus compiler, flags, target, source-manifest hash, proof hash, certificate state, and claim class.
