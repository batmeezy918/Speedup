# Official Gold-Standard Campaigns

This directory is the competitive test harness for the Speedup/PCSS system.

The goal is not to manufacture a favorable benchmark. The goal is to put AGD on the benchmark's own turf and preserve the benchmark's official rules.

## Campaign order

Run independently:

1. `HPL` — dense HPC baseline.
2. `SPEC CPU 2026` — general CPU compute.
3. `cuBLAS/cuBLASLt` — NVIDIA GPU BLAS/GEMM.
4. `MLPerf Inference` — standardized ML inference.
5. `Lean/mathlib` — formal semantic closure rather than a speed leaderboard.

Each campaign must have its own scenario manifest and PCSS certificate.

## Start

```bash
./benchmarks/bootstrap_official.sh
```

This downloads public reference code for HPL and MLPerf Inference. It does not redistribute licensed SPEC CPU software or NVIDIA CUDA/cuBLAS binaries.

## What counts as a competitive result

For each benchmark family, report four separate comparisons:

1. **Official baseline** — the benchmark's prescribed/reference implementation or published official result.
2. **AGD transformed path** — the exact AGD transformation and its full overhead.
3. **Same-hardware delta** — direct comparison where the benchmark rules permit it.
4. **Official-result delta** — comparison to published results only with hardware/configuration differences explicitly disclosed.

Never collapse these into one number.

## PCSS requirements

Every run records:

`scenario -> baseline -> candidate -> quotient -> reconstruction -> invariants -> performance -> formal obligations -> publication decision`

A performance win without semantic gates remains empirical. A formal proof without timing evidence is not a speedup result.

## Expected output

Each campaign should eventually produce:

```text
benchmarks/runs/<family>/<version>/<scenario>/<run-id>/
  manifest.json
  environment.json
  baseline/
  agd/
  quotient.json
  reconstruction.json
  invariants.json
  performance.json
  formal.json
  comparison.json
  hashes.json
  final_certificate.json
```

The benchmark suite is therefore an adversarial test of the AGD claim: **if AGD is genuinely competitive, it must survive the benchmark definitions that established the corresponding field's own performance record.**
