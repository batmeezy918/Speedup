# TENSOR-SEPARABLE OPERATOR RESULT — 2026-10-08

Artifact: `agd_tensored_amortized.c` → `agd_tensored_amortized` (AArch64, gcc 14.2.0,
`-O3 -march=native -mtune=native -funroll-loops -fomit-frame-pointer -DNDEBUG`)
Raw: `agd_tensored_run.txt`. Gate: **TENSORSEPARABLE_GATE=PASS**, 48/48 configurations,
**`maxerr = 0` everywhere**.

## Why this was built

The existing runtime (`agd_amortized_total.c`) uses a **diagonal / block-diagonal**
operator and measured an asymptotic per-step ratio of **124.3× at tile = 64** — that is
1.94× the compression ratio `m = 64`. The explanation offered there was that the full
arm pays an `i/tile` integer division per element.

**Prediction stated before running:** replace the operator with the tensor-separable
form `U = Ū ⊗ I_m` (so the full arm is a dense `r×r` matvec broadcast across each
block, `d·r` ops, **no division**). Then the asymptotic ratio should be **≈ m = 64**,
not ≈ 124.

## Result

| fam | d | tile | r | a = C_fix/C_full | b = C_quot/C_full | asymptote = 1/b | excess / tile | R² |
|---|---|---|---|---|---|---|---|---|
| dense | 4 096 | 32 | 128 | 0.01083 | 0.026809 | 37.3× | 1.17× | 0.351 |
| dense | 4 096 | 64 | 64 | 0.00738 | 0.014217 | 70.3× | **1.10×** | 0.991 |
| dense | 16 384 | 32 | 512 | 0.00651 | 0.014688 | 68.1× | 2.13× | 0.965 |
| dense | 16 384 | 64 | 256 | 0.00452 | 0.006513 | 153.5× | **2.40×** | 0.9996 |
| diagphase | 4 096 | 64 | 64 | 0.00783 | 0.013808 | 72.4× | 1.13× | 0.998 |
| diagphase | 16 384 | 64 | 256 | 0.00336 | 0.006748 | 148.2× | 2.32× | 0.983 |
| perm | 4 096 | 64 | 64 | 0.00697 | 0.013991 | 71.5× | 1.12× | 0.998 |
| perm | 16 384 | 64 | 256 | 0.00413 | 0.006599 | 151.5× | 2.37× | 0.999 |

## Verdict on the prediction: **partially confirmed, and the model is corrected**

**Confirmed at d = 4 096.** Excess/tile fell from **1.94×** (diagonal, same d and tile)
to **1.10×** (tensor-separable). So removing the integer division was a real effect,
and the original explanation was directionally right at that dimension.

**Refuted at d = 16 384.** Excess/tile is **2.13–2.40×**, i.e. asymptote 148–153× where
the prediction was ~64×.

**The corrected mechanism is cache, not the operator.** The excess factor is
essentially **independent of operator family** — dense, diagonal-phase and permutation
agree to within a few percent at every (d, tile) — but it **doubles from d = 4 096 to
d = 16 384**. The cause is the full arm's inner-loop stride:

```c
for (c = 0; c < r; c++) acc += row[c] * src[c * m];   /* src stride = m doubles */
```

At d = 4 096, tile = 64, `Ū` is 32 KB and the whole working set fits cache; both arms
are FLOP-bound and the ratio is the work ratio. At d = 16 384 the `src` stride is
512 bytes, so each 8-byte load pulls a distinct cache line — roughly 8× read
amplification — and the full arm becomes **memory-bound** while the quotient arm
(`acc += row[c] * q[c]`, fully contiguous, `q` in L1) stays FLOP-bound. FLOP counting
stops predicting the ratio once one arm leaves the FLOP-bound regime.

## Correction this forces on the earlier elevation document

`CERTIFIED_DESCENT_CALCULUS_ELEVATION.md` §2.1 states **"path gain ≤ q"**, derived by
counting the quotient path's dense vs block FLOPs in the *numpy* setting. **That bound
is empirically false in native code**:

- d = 4 096, tile = 64, dense: asymptote **70.3×** vs `q = r = 64` → **violated**
- d = 16 384, tile = 64, dense: asymptote **153.5×** vs `q = 256` → holds
- and asymptote is violated against `m = 64` in both.

The FLOP bound is valid **only when both arms are FLOP-bound**. Where memory access
dominates, the native asymptote is governed by the ratio of achieved bandwidths, which
no operation count predicts. §2.1 is amended accordingly.

## What IS established

1. **`maxerr = 0` for the tensor-separable operator, 48/48 configurations.** This is
   the substantive gain. Level-4 exact reconstruction on the invariant sector was
   previously verified only for a *diagonal* operator; it now holds for
   `U = Ū ⊗ I_m` across three operator families (dense, diagonal-phase, permutation),
   two dimensions and two tile sizes, at 1/4/16/64 steps. The invariant hypothesis is
   still **constructed and then validated**, not discovered — that limitation is
   unchanged.
2. **The amortization law transfers to the new operator:** `1/E2E(k) = a/k + b` holds
   at **R² = 0.965–0.9996** in 11 of 12 fits. The outlier is dense / d=4096 /
   tile=32 at R² = 0.351 with an anomalous asymptote of 37.3×, which is flagged as
   **unexplained** and not fitted away.
3. **Operator-independence of the asymptote** is now measured, not assumed: three
   structurally different operators agree within a few percent.

## What is NOT established

- **Not a general workload result.** The block-constant input is constructed and then
  validated by `validate_block_constant`. Nothing here exercises a state where the
  invariant might fail, and no claim is made about unrestricted `d`-dimensional state.
- **Not a GEMM.** `Ū ⊗ I_m` is the tensor-separable family, which is a genuine
  generalization of the previous diagonal case, but it is still not a dense GEMM with
  a non-separable operator.
- **Not a device ceiling.** 48 configurations, trials = 3, reps = 3. The low rep count
  is why one fit is poor; rerun at trials ≥ 7 / reps ≥ 10 before quoting any single
  asymptote.
- **The 2.3× excess at d = 16 384 is diagnosed but not fixed.** The fix is a blocked
  or transposed full arm (accumulate over `c` into a `d`-length accumulator, or block
  the `j` loop so the stride is amortized). That would test whether the asymptote
  collapses to `m`, which is the discriminating experiment.

## Highest-value next operation

**Re-run `agd_tensored_amortized` at d = 16 384 with a cache-blocked full arm** and
check whether the asymptote collapses from 153.5× toward 64× (= `m`). If it does, the
excess is purely memory layout and the FLOP bound is recovered. If it does not, the
asymptote is bounded by something neither `m`, `q`, nor cache explains, and the cost
model needs a third term. Single discriminating experiment; ~10 minutes.