# SNAP vs CMA-ES Benchmark Manifest

## Source
Dropbox source: `/Agdgovenor Team Folder/Snap_Benchmark/Snap_9_24.py`

Source modified: 2026-08-05T13:56:12Z.

## Captured configuration
- Candidate: SNAP-S4 (curvature-aware, stable)
- Comparator: CMA-ES via Python `cma`
- Trials: 5
- Maximum evaluations: 20,000 per trial for the captured benchmark
- Dimensions: 10, 30, 50
- Problem families in captured output: Sphere, Ellipsoid, Rosenbrock, Rastrigin, rotated Sphere, rotated Ellipsoid, rotated Rastrigin, NoisySphere

## Direct benchmark results recorded in the corpus

| Scenario | Reported SNAP/CMA-ES advantage |
|---|---:|
| Rastrigin 10D | 3.29x |
| Rastrigin 30D | 8.87x |
| Rastrigin 50D | 17.19x |
| Rotated Rastrigin 10D | 3.73x |
| Rotated Rastrigin 30D | 12.61x |
| Rotated Rastrigin 50D | 15.71x |

## Raw excerpted medians in the captured runner
- Rastrigin 10D: SNAP median 2.718723e+00; CMA-ES median 8.954626e+00.
- Rastrigin 30D: SNAP median 3.814913e+00; CMA-ES median 3.382858e+01.
- Rotated Rastrigin 30D: SNAP median 3.864928e+00; CMA-ES median 4.875292e+01.

The full Dropbox runner contains the complete trial output and should remain the canonical raw artifact.

## Evidence handling
PCSS publication rule: `PUBLISH := I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L`.

This manifest records benchmark evidence; it does not independently promote the results to `VERIFIED` unless the corresponding scenario manifest, hashes, raw artifacts, quotient/reconstruction checks, invariant checks, and formal obligations are present and passing.
