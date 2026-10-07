# Sovereign GEMM Corpus — Speedup Normalization and Gap Derivation

Date: 2026-09-26
Lane: candidate (non-PCSS). Nothing here is published as a PCSS VERIFIED result.
Source corpus: `/data/data/com.termux/files/home/sovereign_*` (52 files) and
`/root/sovereign_*` (52 files).

## 1. Structural finding: the corpus contains no speedup measurement

None of the 31 GEMM/kernel programs times a baseline. The pattern in every one
of them is:

```c
t0 = omp_get_wtime();
neon_gemm(n,A,B,C1);     /* candidate only */
t1 = omp_get_wtime();
reference_gemm(n,A,B,C2);  /* runs AFTER the clock stops, for an error only */
```

The reference is executed purely to compute `max_error`; its runtime is never
measured, so no ratio is ever formed. The programs print candidate `GFLOPS`,
which is absolute throughput, not a speedup.

A corpus-wide grep for `speedup`, `ratio`, `times faster` returns no baseline
comparison anywhere. Therefore **every "N x faster" figure ever attributed to
this corpus was produced outside these files**, and none of them is reproducible
from the corpus as shipped.

## 2. Two of the three original kernels are wrong, and wrong in the fast direction

Compiled and run as shipped, `N=512`, `OMP_NUM_THREADS=1`:

| Program | Own STATUS | GFLOPS | Checksum | True checksum |
|---|---|---|---|---|
| `sovereign_gemm_verify.c` | **FAIL** | 8.21 | 40,600,912 | 324,807,296 |
| `sovereign_gemm_max.c` | **FAIL** | 6.47 | 81,201,824 | 324,807,296 |
| `sovereign_gemm_fixed_verify.c` | PASS | 2.06 | 324,807,296 | 324,807,296 |

The failures are structural, not numerical:

- `sovereign_gemm_verify.c`: the loop is `for(i=0;i<n;i+=TILE)` with `TILE=8`,
  but only `c0` and `c1` exist, holding rows `i` and `i+1`. Rows 2..7 of each
  block are never written. Worse, `c1` is accumulated from the *same* `b0`
  load as `c0`, so the odd rows are also missing columns `j+4..j+7`. Net
  coverage is exactly `2/8 x 4/8 = 1/8` of the matrix.
- `sovereign_gemm_max.c`: `b1` is loaded from `&B[k*n+j+4]` and never used, and
  only rows `i+0..i+3` are stored. Net coverage is exactly `4/8 x 4/8 = 1/4`.

`sovereign_gemm_max.c` also defines `KC 128` and never uses it, so the
k-blocking the file advertises was never implemented.

## 3. Normalized measurement: same observable, both sides timed

`sovereign_normalize.c` puts the corpus's own baseline and candidates on one
observable (the full `C = A*B` matrix, compared elementwise), times both, and
discards the timing of any candidate that fails to reproduce it.

```
baseline (scalar i-k-j)        median 81.42 ms   3.2968 GFLOPS

neon_correct      (gemm_fixed_verify)  PASS  111.64 ms   2.4044 GFLOPS  speedup 0.7293
neon_broken_verify (gemm_verify)       REJECT coverage 0.125  27.4592 GFLOPS  speedup null
neon_broken_max     (gemm_max)         REJECT coverage 0.250  26.1685 GFLOPS  speedup null
```

**Normalized result: the only correct kernel in the corpus is a slowdown, not a
speedup.** Across repeated runs it measures 0.56x to 0.73x against the scalar
baseline, and it never once exceeded parity. The reason is structural: it
handles one output row at a time, so each `vld1q_f32` of a B row is consumed by
a single FMA, and the kernel is bound by load latency rather than arithmetic
throughput. The scalar `i-k-j` baseline, by contrast, streams `B[k*n+j]` and
`C[i*n+j]` with unit stride and auto-vectorizes cleanly.

The two kernels that appear fast are fast precisely because they do one eighth
and one quarter of the work. `neon_broken_verify` is the worst offender: it
reports 27.46 GFLOPS, the highest number in the corpus, and it is the least
correct of the three.

This is the direct source of the inflated figures: 26.17 GFLOPS over a quarter
of the matrix is arithmetically consistent with ~105 GFLOPS over the full
matrix, which is exactly the kind of number that gets quoted as an achieved
speedup and cannot be reproduced.

## 4. Elevation: the idea was right, the implementation was not

`sovereign_gemm_max.c` was trying to do register blocking, which is the correct
way to make this kernel fast. The idea was sound; the code was wrong. Correctly
implemented, the speedup is real.

`sovereign_elevate.c` implements the same structure correctly at four tile
shapes, each verified against the timed scalar baseline on the same observable:

| Kernel | Coverage | Max error | Median | GFLOPS | Speedup |
|---|---|---|---|---|---|
| `neon_naive_1x4` (corpus's correct kernel) | 1.000 | 1.22e-4 | 147.57 ms | 1.819 | **0.64x** |
| `neon_4x4` | 1.000 | 1.22e-4 | 47.12 ms | 5.697 | **1.99x** |
| `neon_4x8` | 1.000 | 1.22e-4 | 30.89 ms | 8.690 | **3.04x** |
| `neon_8x8_fixed` | 1.000 | 1.22e-4 | 25.21 ms | 10.647 | **3.73x** |

The 8x8 tile needs 16 accumulators, one per (row, column-block) pair, to own
every output row-segment. `gemm_max.c` used 4 accumulators for 8 rows, which is
both why it lost three quarters of the matrix and why it could not have been
fast even if it had stored them.

The residual `max_error` of 1.22e-4 is float32 reassociation, not a defect: the
scalar baseline accumulates in a different order than the vector kernel. The
true element value is 1239.04, so the relative error is 1e-7, at the float32
epsilon.

Stability of the 8x8 result across problem size, from the saved
`elevate_sweep.json` (20/20 measurements passed the observable gate, 0 rejected):

| n | 128 | 256 | 384 | 512 | 640 |
|---|---|---|---|---|---|
| speedup | 3.97 | 3.85 | 4.01 | 3.77 | 3.88 |

Combining this sweep with earlier runs, the honest claim is a band of
**3.0x to 4.0x, median ~3.8x**, single-threaded, and it is flat-to-slightly-
degrading in n as C and B grow past cache. Run-to-run variance at fixed n is
about +-0.3x, which is why the band, not a point value, is the claim.

## 5. Other claims in the corpus that cannot be elevated at any effort

These are not speedup claims that need better code; they are not measurements.

- `sovereign_vector_harness.sh` prints `SATURATION_VERDICT: FULL_8_CORE_ENGAGEMENT`
  as a `printf` literal. It measures nothing. The process has 1 usable CPU
  (`nproc` = 1, cgroup-limited), so the verdict is false as written. Its
  "DETERMINISM: LOCKED" check hashes run logs that embed a wall-clock
  `EXECUTION_TIME`, so the hashes cannot match and the check cannot certify
  determinism even in principle. The kernel is 8 floats, not 4096 dimensions.
  The script also runs `apt-get install`, which mutates the system.
- `sovereign_neon_8x8.sh` prints `STATUS : PASS` unconditionally, with no error
  check whatsoever. `sovereign_neon_gemm.sh` prints `DETERMINISTIC_COMPUTE_PATH`
  and `sovereign_neon_pack_gemm.sh` prints `DETERMINISTIC_PASS` the same way.
  These are the same hardcoded-verdict pattern already refuted in the
  hierarchical experiment.
- `sovereign_init.sh` pins to cores 4-7 and launches `flutter run -d linux` on
  an Android device. It cannot run.
- The Julia, Python and C++ files print throughputs and durations against no
  baseline. `sovereign_apex.jl` reports a velocity; `sovereign_telemetry.py`
  reports a duration and a parity string. None is a speedup.
- The corpus also `apt-get install`s build tooling and writes to `/sdcard`.

## 6. Formal gap derivation

For the one claim that survived normalization, the gap from here to a published
`VERIFIED` PCSS speedup is exactly this. Let `S` be the claim and `G` the gate
set in `speedup/const.py`.

| Gate | Present? | Evidence / gap |
|---|---|---|
| `G_same_observable` | **SATISFIED** | Full `C=A*B`, elementwise vs scalar baseline, coverage 1.000, max error 1.22e-4. |
| `G_hardware` | PARTIAL | Runs on real aarch64 silicon. But cgroup allows 1 CPU while the kernel is single-threaded anyway, so no core-count claim is available. |
| `G_measured` | PARTIAL | 5 sizes x 4 kernels, 3 warmups + 15 repeats, median, band 3.0-4.0x. Missing: pinned-clock control, and repetition on a second machine. |
| `G_baseline` | SATISFIED | Corpus's own `reference_gemm`, now timed. Not a strawman: it is the exact code the corpus shipped. |
| `G_reproducible` | PARTIAL | Source + commands + JSON are in this directory. Missing: hash binding and a pinned toolchain record. |
| `G_independent` | **NOT SATISFIED** | Single kernel, single author, single machine, no independent reimplementation. This remains a binding constraint. |
| `G_non_advantageous` | **FAILS (measured)** | **Resolved by measurement, not assumption.** `visible_hpc.c` revealed CBLAS is installed, so the tuned reference could be measured after all. See `PRoot_CORPUS_AUDIT.md` §6: OpenBLAS `cblas_sgemm` runs at 22-24 GFLOPS on the same cores, i.e. **1.85x to 3.56x faster than the corrected 8x8 kernel**. The kernel loses to a tuned implementation. |
| `G_environment` | PARTIAL | Device hash obtainable, but governor is `walt` and unwritable, so frequency is not controlled. |

**Derivation of the verdict.** `G_independent` is unsatisfied and needs a
second implementer. `G_non_advantageous` is no longer merely unsatisfied — it
is affirmatively **failed by measurement**:

```
speedup(8x8 fixed) vs naive scalar triple loop = 3.7x        [measured]
speedup(8x8 fixed) vs OpenBLAS cblas_sgemm       = 0.28-0.54x [measured, LOSES]
G_non_advantageous                              = FAIL
```

The 3.7x is a weak-baseline artifact. Against the tuned implementation already
present on the same machine, the kernel is 1.85x to 3.56x **slower**. This is
the honest end state of the elevation attempt: the corpus's idea was sound, the
corrected kernel is genuinely faster than a naive loop, and it is still not a
speedup claim in any meaningful sense.

```
VERIFIED = NOT ESTABLISHED   [G_independent fails; G_non_advantageous fails]
```

The correct claim strength is `candidate`, and the candidate claim should be
stated as "3.7x over a naive triple loop, 0.3-0.5x of OpenBLAS" rather than as a
headline speedup. The corpus's implied "~26 GFLOPS achieved" and any
multi-thousand-fold figures are refuted, not merely unproven: they are
consequences of computing 1/4 and 1/8 of the observable.

## 7. What was added to the system

- `evidence/hierarchical_accel/2026-09-26/sovereign/sovereign_normalize.c`
- `evidence/hierarchical_accel/2026-09-26/sovereign/sovereign_elevate.c`
- `evidence/hierarchical_accel/2026-09-26/sovereign/normalize_n512.json`
- `evidence/hierarchical_accel/2026-09-26/sovereign/elevate_sweep.json`

`evidence/ledger/claims.jsonl` was deliberately **not** modified. The corpus was
audited in a lane that carries no PCSS authority, and the authoritative ledger
was previously polluted by exploratory writes. The existing `QUARANTINED` entry
for `11823.51x` is left in place; this report refutes the corpus story behind it
rather than superseding it.

Reproduction:

```sh
cd evidence/hierarchical_accel/2026-09-26/sovereign
gcc -O2 -fopenmp -o normalize sovereign_normalize.c
gcc -O2 -fopenmp -o elevate  sovereign_elevate.c
OMP_NUM_THREADS=1 ./normalize 512
for n in 128 256 384 512 640; do OMP_NUM_THREADS=1 ./elevate $n; done
```

No PCSS certificate is minted for this. Per `CONSTITUTION.md` the strict gate
fails while `G_independent` and `G_non_advantageous` are unsatisfied, and the
certificate publisher additionally hardcodes a colliding output path that must
not be used. The earlier ledger entry quoting `11823.51x` for
`sovereign_integrated.c / sovereign_proof.cpp` remains **quarantined**; this
report refutes the corpus-level speedup story behind it and does not elevate it.
