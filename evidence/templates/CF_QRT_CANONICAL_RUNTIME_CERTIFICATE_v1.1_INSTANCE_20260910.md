# CF-QRT/1.1 — QRT-EJ-1.0 Runtime Certificate Instance

- Certificate ID: `QRT-EJ-1.0-20260910`
- Template: `CF-QRT/1.1`
- Suite: `QRT-EJ-1.0`
- Seed: `20260910`
- Host: `Android-16-aarch64-64bit-ELF`
- Python: `3.14.6`
- Literal states: `80000`
- Quotient classes: `4000`
- Quotient collapse: `20.0x`
- Eliminated fraction: `0.95`
- Full operations: `160000`
- Quotient operations: `8000`
- Work reduction: `20.0x`
- Full median runtime: `5254823488 ns`
- Quotient median runtime: `266453542 ns`
- Measured median runtime speedup: `19.721349727826098x`
- Witness: `PASS` (1000 checks)
- Descent: `PASS` (1000 checks)
- Observable preservation: `PASS` (2000 checks)
- Semantic equality: `PASS` (`0 == 0`)
- Reconstruction: `PASS` (4000 checks)
- Projected replay: `PASS` (5000 checks)
- Runtime evidence gate: `PASS`
- Full runtime outliers: `2`
- Quotient runtime outliers: `3`
- Evidence hash: `299a554031a1de2030db3687b899cb196a1b309d0adbe1ee3ec9014dc65940e4`

## Status boundary

This instance establishes a closed local quotient-runtime result for the declared QRT-EJ workload. It does **not** establish a COCO/BBOB speedup claim. COCO claims require the official `cocoex` workload and the registered benchmark protocol.

## Derived relation

`ρ_Q = 20.0x`

`ρ_W = 20.0x`

`S_runtime = 19.721349727826098x`

`S_runtime / ρ_W ≈ 0.986067486`

The runtime result is therefore measured evidence for this closed instance, not a universal performance theorem.
