# SNAP / Optimizer Evidence Inventory

This directory records optimizer and speedup artifacts located in the authorized Dropbox corpus. Raw benchmark artifacts remain in Dropbox; this repository records provenance, extracted metadata, and publication-gate status.

## Located source artifacts

1. `/Agdgovenor Team Folder/Snap_Benchmark/Snap_9_24.py`
   - Exact runner discovered in Dropbox.
   - Modified: 2026-08-05T13:56:12Z
   - Declared suite: Sphere, Ellipsoid, Rosenbrock, Rastrigin, rotated variants, NoisySphere across 10D/30D/50D.
   - Runner uses 5 trials and max_evals=20000 in the captured output.

2. `/Agdgovenor Team Folder/Lean Verified Snap  method Theroum.docx`
   - Lean/Mathlib theorem artifact.
   - Modified: 2026-08-19T06:32:15Z
   - Contains a formalized Hilbert-space/operator construction and a `FullSnapDemo` theorem.

3. `/Agdgovenor Team Folder/Omega_Tensor_Research_Archive/Snap_before_intelligence_lean_verifiied.txt`
   - Canonical SNAP operator/invariant archive.
   - Modified: 2026-08-05T13:56:12Z
   - Records Omega/Xi invariants and SNAP invariance statements.

4. `/Agdgovenor Team Folder/Candidate_Theorum/Ω-SNAP⁴ Theorum.docx`
   - Modified: 2026-08-19T06:32:07Z
   - Reports a 209.23x structured-search result in the RSA-1024 siege audit and an O(N^3) to O(NR) construction.

5. `/Agdgovenor Team Folder/AGD System Speedups, Transformations, and Claims.xlsx`
   - Modified: 2026-08-19T06:32:00Z
   - Aggregates reported speedup artifacts including GS254 (254.30x), S8 Optimizer (80.9x), SIM2XR-C theoretical scaling (1024x), Omega Tensor Mobile v2.0 (4.91x), and related claims with verification-status fields.

## Governance

The Speedup repository's PCSS constitution requires:

`CLAIM_STRENGTH <= EVIDENCE_STRENGTH`

and the publication predicate:

`PUBLISH := I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L`

Therefore this inventory does not promote every historical speedup into `verified/`. Each result remains tied to its source artifact until the required provenance, reproducibility, quotient/reconstruction, invariant, performance, and formal gates are satisfied.

## Known direct CMA-ES benchmark evidence

The captured `Snap_9_24.py` output contains direct SNAP-vs-CMA-ES runs. The strongest reported Rastrigin-family margins in the benchmark record are:

- Rastrigin 10D: 3.29x reported advantage
- Rastrigin 30D: 8.87x reported advantage
- Rastrigin 50D: 17.19x reported advantage
- Rotated Rastrigin 10D: 3.73x reported advantage
- Rotated Rastrigin 30D: 12.61x reported advantage
- Rotated Rastrigin 50D: 15.71x reported advantage

These figures are benchmark outputs and must retain the exact scenario manifest, aggregation rule, environment, and raw logs when promoted to `verified/`.
