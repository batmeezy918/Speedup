# AGD QUANTUM GENERALITY — BLOCK-STRUCTURED QUOTIENT RE-RUN

Date 2026-10-07 · `AGD_QUANTUM_GENERALITY_BLOCKQUOTIENT_EOF.py` ·
raw: `AGD_BLOCKQUOTIENT_RESULTS.csv` / `.json`
Contract: `workloads/device_speedup_contract/DEVICE_SPEEDUP_CONTRACT.md`

## What changed

`build_quotient(n)` defines

```
pi = I_q ⊗ p,  p = m^{-1/2}·1_{1×m}     (πx)_i    = m^{-1/2} Σ_j x_{im+j}   O(d)
R  = I_q ⊗ pᵀ                            (Rz)_{im+j} = z_i/√m             O(d)
```

The generator **times** `π` and `R` as dense `(d×q)` matvecs. This run executes the
block forms. **No new mathematics, no change to any gate quantity.**

## Discipline

1. **Semantic identity by construction.** The original module is `import`ed, not copied.
   Every gate quantity — `closure_residual`, `pi_r_err`, `state_max`, `state_l2`,
   `obs_err`, `reverse_error`, composition depths — is produced by the original
   functions from the original source. Transcription error is impossible.
   The original file was not modified.
2. **Correctness before timing.** Both block operators are checked against dense on
   the *actual operands* before any clock is read.
3. **No inputs inside timed regions.** Every stage operand is precomputed outside the
   timed lambda. (An earlier harness recomputed the dense projection inside the `R`
   timer and inflated `t_R` ~30×.)
4. **Interleaved A/B.** Dense and block arms alternate rep-by-rep inside each row, so
   cache state, thermal drift and background load hit both arms equally.
5. **Reps raised** from `WARMUPS=2, REPS=5` to `WARMUPS=3, REPS=15`, pooled over 3
   inner trials. MAD reported alongside std.
6. **Size gate at n ≥ 9**, chosen from measurement: the block form is *slower* below it.
7. **Telemetry per row**: frequency, governor, thermal, memory.

## Result

231 positive rows, 24 negative controls.

| n | d | kernel | E2E **as generated today** | E2E **block π+R** | improvement | block selected |
|---|---|---|---|---|---|---|
| 2 | 4 | 1.0× | 0.28× | 0.12× | 0.42× | no |
| 3 | 8 | 1.0× | 0.29× | 0.12× | 0.42× | no |
| 4 | 16 | 1.2× | 0.31× | 0.14× | 0.43× | no |
| 5 | 32 | 1.5× | 0.39× | 0.18× | 0.46× | no |
| 6 | 64 | 3.3× | 0.76× | 0.38× | 0.50× | no |
| 7 | 128 | 9.0× | 1.53× | 1.05× | 0.68× | no |
| 8 | 256 | 30.7× | 3.83× | 3.50× | 0.91× | no |
| **9** | 512 | 84.0× | 5.88× | **11.68×** | 1.99× | **yes** |
| **10** | 1 024 | 337.4× | 13.52× | **45.05×** | 3.33× | **yes** |
| **11** | 2 048 | 711.2× | 15.02× | **106.86×** | 7.12× | **yes** |
| **12** | 4 096 | 2 632.4× | 29.50× | **305.71×** | 10.36× | **yes** |

### Gates

| gate | result |
|---|---|
| positive rows PASS | **231 / 231** |
| negative controls correctly rejected | **24 / 24** (0 false passes) |
| block operators match dense within `GATE_TOL=1e-10` | **231 / 231** |
| block operators byte-identical (diff exactly 0.0) | 189 / 231 |
| max \|block π − dense π\| | 1.119e-16 |
| max \|block R − dense R\| | **0.000e+00** |
| break-even vs full operator | **n = 7**, both arms |
| worst case (n=2) block/dense | 0.42× — **gate correctly refuses** |

## The one correction this run forced

I had asserted the block operators were **byte-identical** to dense. The gate
**refuted that**, which is the point of having it:

- `block_R` *is* byte-identical — diff exactly `0.0` on all 231 rows.
- `block_pi` is **not** byte-identical at every n. `reshape(q,m).sum(axis=1)` and the
  BLAS matvec accumulate in a different order, giving up to **one ULP** (1.119e-16 at
  n=10 and n=11). Requiring exactly `0.0` is *stricter than the experiment's own
  standard* (`GATE_TOL = 1e-10`). Both flags are now reported separately and selection
  gates on `GATE_TOL`, not on exact zero.

## What this replaces

The pooled headline "median end-to-end 0.7268×, i.e. slower" is the **n = 6** value.
It understates the n ≥ 9 regime entirely. The per-n ladder above is the honest report:
**break-even at n = 7, and 305.71× at d = 4096** with the block operators.

## Limits — recorded, not glossed

- **n = 13 was not run.** The generator materialises `U = Ū ⊗ I_m` densely; at
  d = 8192 that is **1.07 GB** and the host had ~2.4 GB available. The attempt was
  killed. `isolated_stage_bench.py` did measure n = 13 (single instance) at
  **1 480.2×**, but that is one Ū, not the 21-row family sweep, and is not claimed here.
- Frequency is uncontrolled: `walt` is not writable, thermal ran 46–56 °C. Medians
  over 3 inner trials; single runs are noise.
- Affinity pinning was measured and does nothing (≤3%, not consistently signed).
- This is numpy, single-threaded, complex128. It is **not** a NEON GEMM kernel;
  `PCSS_NEON_GEMM` is a separate substrate layer and does not compose with these.
- Family sweep is 7 positive families × 3 seeds = 21 rows per n, unchanged from the
  original. Negative controls are the original's 4 types × 3 sizes × 2 seeds.

## Reproduce

```bash
python3 AGD_QUANTUM_GENERALITY_BLOCKQUOTIENT_EOF.py 10   # faithful scope
python3 AGD_QUANTUM_GENERALITY_BLOCKQUOTIENT_EOF.py 12   # extended
# OVERALL must print PASS
```