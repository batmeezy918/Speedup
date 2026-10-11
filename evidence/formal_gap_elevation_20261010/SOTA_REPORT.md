# Full SOTA differential report — AGD / MuNi quotient descent vs dense / BLAS

Operator under test: the exact dense operator `Ubar (x) I_m` applied for `steps`
iterations, `d = r * m`. All four paths compute the *same* operation.

## Claim

For a block-constant state (the admitted invariant), AGD quotient descent applies
the operator 34.7x-572.5x faster than the exact structured operator, and
678x-3201x faster than a SOTA dense BLAS (`OpenBLAS dgemv`), while remaining
**bit-exact** (`cand_err = 0`) and **never** falling back to the unoptimised path.

## Setup

- Repo: `Speedup` @ `feat/silicon-speedup-proof-skill`; harness `src/sota_bench.c`.
- Flags: `gcc -O3 -march=native -mtune=native -funroll-loops -fomit-frame-pointer
  -DNDEBUG -std=c11 -D_POSIX_C_SOURCE=200809L` (identical for all paths).
- Baseline identity: **OpenBLAS 0.3.29 DYNAMIC_ARCH armv8, MAX_THREADS=128,
  parallel_mode=1** (`receipts/sota_blas_config.txt`). Linked via `-lopenblas`.
- Machine: SM6475 (Cortex-A55/A78), Android/PRoot, single core visible (`nproc=1`),
  governor `walt`. Same session for A and B.
- Method: rotating interleave (path `p` at trial `t` runs at slot `(p+t) mod 4`),
  2 warmup rounds discarded, `N = 9` measured trials, `reps = 2` internal (min),
  inputs regenerated per rep, timing `CLOCK_MONOTONIC`.
- Paths: `cand` = AGD quotient descent (`agd_plan_run` + `reconstruct`);
  `struct` = `agd_original_apply`; `blas` = OpenBLAS `dgemv` on materialised A;
  `naive` = hand-written dense mat-vec.

## Result

| d | r | steps | cand ms | struct ms | blas ms | naive ms | x vs struct | x vs blas | x vs naive |
|------:|---:|------:|--------:|----------:|--------:|---------:|------------:|----------:|-----------:|
| 512   | 16  | 1000 | 0.1591 | 6.1666 | 120.13 | 856.64 | 38.8x | 755x | 5386x |
| 1024  | 32  | 500  | 0.3894 | 13.493 | 264.15 | 5747.6 | 34.7x | 678x | 14761x |
| 2048  | 32  | 200  | 0.1565 | 10.688 | 491.42 | - | 68.3x | 3141x | - |
| 4096  | 64  | 40   | 0.1335 | 9.2227 | 427.44 | - | 69.1x | 3201x | - |
| 65536 | 256 | 10   | 0.8463 | 484.48 | infeasible (A = 34 GB) | - | 572.5x | - | - |

`cand` spread (MAD) is 0.00005-0.008 ms; `struct` MAD 0.004-0.07 ms.

## Correctness gate

`cand_err = 0.0` (bit-exact vs `struct`) in all 5 configs; `blas`/`naive` errors
are 0 as well. `cand_fallback = 0` over `cand_runs = 38` timed runs per config, so
the optimised branch demonstrably executed (not a no-op speedup).

## Noise floor

Explicit A/A (same path timed twice): **cand ∈ [0.864x, 1.152x]**, blas ∈
[1.015x, 1.116x]. Every reported effect (34.7x-572x) is 30x-500x above this floor,
and cand-vs-struct / cand-vs-blas intervals are disjoint in all configs.

## Confounders checked

- Baseline artifact hash/mtime confirmed via `ldd` + OpenBLAS self-config.
- Governor `walt`, not `performance`; frequencies unpinnable under PRoot. Accepted
  as a bounded noise floor (measured above).
- Thermal drift: control-path (`struct`) first-half vs second-half median drift is
  -0.03% to -0.68% at d >= 2048, and **+11.0%** at d = 512. Interleaving makes
  drift common-mode; the d=512 row is flagged.
- Identical inputs, flags, and session for all paths; logging excluded from timed
  region; input buffers regenerated each rep.

## Verdict

**CONFIRMED** — like-for-like structured-operator speedup is 34.7x-572.5x (median,
intervals disjoint, N = 9, noise floor checked, optimised path asserted).
Dense-BLAS speedups (678x-3201x) are additionally **CONFIRMED** as a reference.

## Scope (honesty)

OpenBLAS `dgemv` is a *general dense* baseline and structurally **cannot** exploit
`Ubar (x) I_m`. The fair like-for-like comparison is `cand` vs `struct` (the same
operator). The BLAS/naive ratios measure structure exploitation and asymptotics;
the d=65536 row shows the quotient path stays feasible when the dense operator is
34 GB and BLAS cannot run at all. No claim is made that AGD beats BLAS on a
generic, non-structured operator.

## Reproduce

```
bash run_sota.sh          # builds, runs all 5 configs, writes receipts/sota_report.{txt,json}
```
Persisted evidence: `receipts/sota_raw_s*.txt`, `receipts/sota_report.{txt,json}`,
`receipts/sota_blas_config.txt`, `receipts/sota_blas_link.txt`.
