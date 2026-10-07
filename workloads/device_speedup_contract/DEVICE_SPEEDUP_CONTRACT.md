# DEVICE SPEEDUP CONTRACT — measured on this phone

Date: 2026-10-07 · host: `aarch64`, PRoot, Android kernel 6.17.0-PRoot-Distro
SoC: **4× Cortex-A55 @1.80 GHz** (cpu0–3) + **4× Cortex-A78 @2.40 GHz** (cpu4–7)
governor `walt` (**not writable** — no root), NEON/ASIMD 4-lane, BLAS forced to 1 thread.

Everything below is a **measurement on this device**, not an extrapolation.
Harnesses: `device_speedup_contract.py`, `ab_affinity.py`, `r_impl_bench.py`,
`isolated_stage_bench.py`. Raw output in `*_results.json`.

---

## 1. The headline

`build_quotient(n)` in `AGD_QUANTUM_GENERALITY_DEFINITIVE_EOF.py` defines

```
pi = I_q ⊗ p        p = m^{-1/2}·1_{1×m}        (πx)_i = m^{-1/2} Σ_j x_{im+j}
R  = I_q ⊗ pᵀ                                   (Rz)_{im+j} = z_i/√m
d = 2^n,  q = 2^⌈n/2⌉,  m = 2^⌊n/2⌋,  U = Ū ⊗ I_m
```

The generator **times π and R as dense `(d×q)` matvecs.** Both have `O(d)` block
implementations. Replacing them with those implementations is the entire change —
no new mathematics.

**Measured, `isolated_stage_bench.py`, median of 5 trials × 15 reps, correctness asserted:**

| n | d | kernel | E2E **as generated today** | E2E **block π + R** | improvement | FLOP bound | efficiency |
|---|---|---|---|---|---|---|---|
| 10 | 1 024 | 327.1× | 14.0× | **53.2×** | 3.81× | 21.7× | 0.18 |
| 11 | 2 048 | 680.1× | 14.6× | **172.9×** | 11.81× | 32.5× | 0.36 |
| 12 | 4 096 | 2 649.9× | 28.6× | **624.9×** | 21.86× | 43.0× | 0.51 |
| 13 | 8 192 | 3 644.6× | 31.7× | **1 480.2×** | **46.70×** | 64.5× | 0.72 |

**Cross-validation:** my harness measures E2E dense = **14.0×** at n = 10. The corpus
artifact `AGD_QUANTUM_GENERALITY_RESULTS.csv` reports **13.647×** for the same n.
Independent agreement to 2.6 % — the harness reproduces the original experiment.

**Efficiency against the FLOP bound rises 0.18 → 0.36 → 0.51 → 0.72.** That is the
overhead term `c/α` becoming negligible, exactly as the cost model in
`docs/assessments/2026-10-07/AGD_MASTER_DERIVATION_20261007.md` §6 predicts. The
optimisation is not hand-waving; it converges to its theoretical ceiling.

---

## 2. What each stage is worth

Component medians at n = 12 (`isolated_stage_bench.py`):

| stage | dense | block | gain | note |
|---|---|---|---|---|
| kernel `Ū @ q'` | 8.0 µs | — | — | already tiny |
| `π @ ψ` | 325 µs | **14.4 µs** | **22.5×** | dense reads a 4 MB matrix; block reads 64 KB |
| `R @ z` | 410 µs | **11.6 µs** | **35.5×** | dense reads 4 MB; block writes 64 KB |
| full `U @ ψ` | 21.3 ms | — | — | the thing being beaten |

**`R` is already at its floor.** `r_impl_bench.py` compared four implementations of the
same output (byte-identical, asserted):

| impl | n=12 | n=13 |
|---|---|---|
| `np.repeat(z/√m, m)` | 11.7 µs | 17.4 µs |
| prealloc broadcast fill | **11.2 µs** | **16.4 µs** |
| `np.broadcast_to(...).reshape(-1)` | 22.6 µs | 27.2 µs |

Only **1.05×** is available. `np.tile` and `np.concatenate` were tested and **rejected**:
they repeat the whole array rather than each element, so they compute the wrong
operator. Do not "optimise" `R` any further — it is bounded by write bandwidth
(64 KB in 11.6 µs ≈ 5.5 GB/s).

---

## 3. Affinity: measured, and it does nothing

`taskset -c 4-7` (A78 cluster only) vs default (all 8 cores), interleaved within one
process, 6 paired trials:

| n | default E2E_block | a78-pinned E2E_block | default kernel | a78 kernel |
|---|---|---|---|---|
| 10 | 21.19× | 20.56× | 382.9× | 341.3× |
| 11 | 25.59× | 25.52× | 633.5× | 641.7× |
| 12 | 56.30× | 55.39× | 2536.7× | 2558.8× |

Differences are ≤ 3 % and not consistently signed. **Conclusion: do not bother pinning.**
The workload is single-threaded and `walt` already places it on a big core. This is a
clean negative result and it removes a step from every future run.

---

## 4. Two measurement bugs I introduced and corrected

Recording these because they changed the answer materially.

1. **`device_speedup_contract.py`** timed each stage once per `n` in sequence. Cache
   state and thermal drift between stages biased the dense arm. First report showed a
   "21.04× gain at n=12."
2. **`ab_affinity.py`** timed `r_block(m, q, Ū @ (π @ ψ))` — it recomputed the **dense
   projection inside the timed region**, inflating `t_R_block` ~30× (354 µs reported for
   an 11.6 µs operation) and understating the gain.

**Single-shot sequential timing on this device is not trustworthy.** `isolated_stage_bench.py`
precomputes every stage input outside the timed region and is the only harness here
whose numbers should be quoted. The correct n=12 figure is **21.86×**, not 21.04× from
the flawed run and not the 2.87× the buggy interleaved run reported.

---

## 5. The size gate — the block path is NOT always faster

From `device_speedup_contract.py` (small-`n` rows are reliable; the large-`n` rows were
the flawed ones):

| n | block gain |
|---|---|
| 2 | 0.44× (**slower**) |
| 3 | 0.45× |
| 4 | 0.47× |
| 5 | 0.52× |
| 6 | 0.53× |
| 7 | 0.90× |
| 8 | 1.13× |

For `n ≤ 7` the reshape/sum overhead of the block form exceeds what it saves, and the
quotient path is **slower than doing nothing**. **Gate the optimisation at n ≥ 9.**

---

## 6. What is still not established

- **This is numpy, single-threaded, complex128.** It is not a NEON GEMM kernel. The
  `PCSS_NEON_GEMM` sweep (7.3–14.6×, `max_abs ≤ 2.0e-5`, PASS) is a *different*
  substrate layer and its speedups do not multiply with these.
- **Frequency is not controlled.** `walt` is not writable. Thermal ran 46–56 °C across
  runs. Every number above is a median over 5 trials with MAD; a single run is noise.
- **Break-even is n = 7** for the dense path, unchanged by the block optimisation.
- No claim is made about GPU/NPU, multi-thread scaling (`OPENBLAS_NUM_THREADS=1`), or
  workloads other than the random-unitary `Ū ⊗ I_m` family.

---

## 7. How to reproduce

```bash
cd workloads/device_speedup_contract
python3 isolated_stage_bench.py        # the numbers that matter (authoritative)
python3 r_impl_bench.py                # R implementation floor
python3 device_speedup_contract.py r.json      # size gate / small-n behaviour
python3 ab_affinity.py 6 10,11,12      # affinity A/B (expect: no effect)
```

Gate before trusting any future claim:
`correctness == ALL PASS` **and** `block_gain > 1` **and** `n >= 9`.