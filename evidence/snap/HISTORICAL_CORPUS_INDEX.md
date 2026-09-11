# Historical SNAP Optimizer Evidence Corpus

Imported/indexed from the authorized Dropbox corpus on 2026-09-11.

## Located artifacts

1. `Snap_Benchmark/Snap_9_24.py` — direct SNAP vs CMA-ES benchmark runner; 5 trials, up to 20,000 evaluations; Sphere, Ellipsoid, Rosenbrock, Rastrigin, rotated variants, and noisy Sphere across 10D/30D/50D. Source metadata: Dropbox server modified 2026-08-05.
2. `Omega_Tensor_Research_Archive/Snap_before_intelligence_lean_verifiied.txt` — canonical SNAP invariant/Lean archive; records Ω and Ξ invariance statements.
3. `Lean Verified Snap method Theroum.docx` — Lean/mathlib formalization of Hilbert-space operator algebra and Full SNAP theorem demo.
4. `Candidate_Theorum/Ω-SNAP⁴ Theorum.docx` — Ω-SNAP⁴ theorem/empirical report; records 209.23x structured-search result and O(N^3) -> O(NR) construction.
5. `AGD System Speedups, Transformations, and Claims.xlsx` — consolidated speedup/verification ledger; includes GS254 254.30x, S8 80.9x, SIM2XR-C 1024x theoretical scaling, Omega Tensor Mobile 4.91x, and related status fields.
6. `Chronofold suite/chronofold/chronofold_vs_cmaes.sh` — separate ChronoFold/CMA-ES runner using Sphere, Rastrigin, Rosenbrock, DIM=10, ITER=400, RUNS=10.
7. `Snap_Benchmark` folder — Dropbox container for SNAP benchmark artifacts.
8. `HPC Dominance/Silicon Speedup` folder — broader speedup corpus.

## Recorded direct SNAP/CMA-ES margins

Rastrigin: 10D 3.29x; 30D 8.87x; 50D 17.19x.
Rotated Rastrigin: 10D 3.73x; 30D 12.61x; 50D 15.71x.

## Evidence handling

These are historical source records. Claim strength must not exceed evidence strength. PCSS publication gate:

`PUBLISH := I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L`

Raw benchmark observations remain empirical; Lean artifacts establish only the mathematical obligations they actually formalize. Historical artifacts should be promoted to `VERIFIED` only after their scenario manifests, hashes, raw outputs, reconstruction, invariant, performance, and formal gates are explicitly satisfied.