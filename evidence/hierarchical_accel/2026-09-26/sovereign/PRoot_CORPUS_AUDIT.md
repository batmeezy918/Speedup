# v13-v17 / PRoot Corpus — Audit

Date: 2026-09-26
Lane: candidate (non-PCSS). No certificate minted, no ledger write.
Location: `/root/` (PRoot), alongside the `sovereign_*` corpus audited in
`SOVEREIGN_AUDIT.md`.

## 0. Summary

Of 29 items, **zero contain a speedup measurement, zero contain a verified
mathematical result, and two contain fabricated scientific verdicts that print
unconditionally.** One is a genuine gate vulnerability that would admit fake
proofs. The single most serious item is `validate_rh.sh`, which prints
`VERDICT: RIEMANN HYPOTHESIS PROVEN BY OPERATOR PROXY` as a `print()` literal.

The recurring defect across both corpora is identical: a **verdict string
printed with no computation behind it**, paired with a hardware claim
(8 cores) contradicted by the actual environment (1 usable CPU).

## 1. Fabricated verdicts printed unconditionally

### 1.1 `validate_rh.sh` — claims the Riemann hypothesis is proven

The worst item in either corpus. The script generates a Python engine that ends
with:

```python
print("COHESION INDEX: 0.91 (LOCKED)")
print("NOVELTY SCORE: 0.83 (VERIFIED)")
print("RESULT: ESSENTIAL SELF-ADJOINTNESS NUMERICALLY CONFIRMED.")
print("VERDICT: RIEMANN HYPOTHESIS PROVEN BY OPERATOR PROXY.")
```

These are four `print()` string literals with **no computation whatsoever**
behind them. They execute after the loop regardless of whether convergence
succeeded, and the loop's own failure path only `sys.exit(1)` before reaching
them. Any successful Newton iteration at all produces the verdict.

The underlying mathematics is also wrong, independently of the hardcoding:

- The seed `t = 360000433260.351086` is described as "near the 400,000th zero".
  The 400,000th nontrivial zeta zero is near `t ~ 1.95e5`. The seed is off by
  roughly six orders of magnitude, so it is not near any zero.
- Riemann-von Mangoldt gives only the *mean* zero spacing, `2*pi/log(t)`. Using
  it to step from an arbitrary seed does not locate a zero; it produces a point
  with no reason to be special.
- Refining on `zeta(0.5 + i*t).real` and then testing `abs(zeta(0.5 + i*t)) <
  1e-45` is circular. A small `|zeta|` at a point that is not a zero proves
  nothing, and Newton on the real part alone has no convergence guarantee to a
  zero of the complex function.
- Even a genuine `|zeta| ~ 1e-45` at a point would say nothing about
  self-adjointness. Self-adjointness of an operator is a property of the
  operator, not of a residual at a sample point.
- `mp.dps = 80` is described in a comment as "zero-error rigor". It is
  arbitrary-precision floating point with no error bound attached.

The script also runs `apt-get install` and `pip3 install --break-system-packages`.

**Verdict: the Riemann hypothesis is not proven, not partially proven, and
nothing here is evidence toward it. The verdict line is a hardcoded string.**

### 1.2 `v15_collapse` — a factorization that is arithmetically false

The program prints `MODULUS COLLAPSE: PRIMES EXTRACTED` and then:

```
FACTOR P: 49189483849
FACTOR Q: 4656915041827245607693620111694564785...072869012865
```

Checked against the modulus `N` compiled into the binary:

| Check | Result |
|---|---|
| `N mod p` | `45825673305` — **nonzero, so p does not divide N** |
| `N mod q` | nonzero |
| `p*q` bit length | 995 bits vs `N`'s 932 bits |
| `(p*q - N) / N` | `+7.4e+21` — the product is ~10^21 times **larger** than N |

The printed pair is not a factorization of the modulus. The program declares
the modulus "no longer Sovereign" on the strength of two numbers that do not
multiply to it. `N` is a 932-bit modulus (the source comment in `v13_engine.c`
calls it "1024-bit", which is also wrong).

### 1.3 `v13_engine.c` — a real computation wrapped in invented output

The GMP part is real: it computes `m^3 mod N` and takes an integer cube root,
observing that the root is not `m`. That is ordinary modular arithmetic, not a
break — multiple cube roots exist modulo a composite, and calling it
`TOY REGIME SUCCESSFULLY BYPASSED` misdescribes it.

The rest is invented:

- `calculate_stability()` is **defined and never called**.
- The lattice basis `B = [1 0 -c; 0 1 N]` is described in a comment and
  **never constructed**. No lattice reduction is performed.
- `Basis Norm Stability` is the literal expression `1.0 - (0.15 * i)`, with the
  comment `// Simulated reduction functional`. It is not derived from anything.
- `[INDUCTION COMPLETE] The Ω-v13 Manifold is now mathematically non-trivial.`
  prints unconditionally after a five-iteration print loop.

## 2. Programs that fail while reporting success

### `v16_key` exits 0 on an error

```
[ERROR]: Exponent e is not invertible. Manifold is non-standard.
   [exit=0]
```

The computation fails and the process still reports success to any calling
script or CI step. The string `[STATUS]: Total Manifold Dominance Achieved.`
is present in the binary but is unreachable dead code — the program never gets
past the error. So the "Total Manifold Dominance" claim is not merely
unsubstantiated, it is unreachable.

This is the highest-risk defect class here after `verify_lean_proof.sh`,
because exit-code-0-on-failure defeats any automated gate that keys on `$?`.

## 3. Hardware claims contradicted by the environment

Every one of these asserts 8-core operation. The process sees **1** usable CPU
(`nproc` = 1, cgroup-limited; `taskset -c 4,5,6,7 nproc` still returns 1).

| File | Claim | Reality |
|---|---|---|
| `v17_simd` | `State: 8-Core Parallel Manifold Fusion`, `SLICE 0..7` | 8 hardcoded `printf` lines; no timing, no correctness check, 1 CPU |
| `warp_engine` | `--- INITIATING TOTAL HARDWARE COLLAPSE ---` | 8 unsynchronized threads each incrementing their own counter; output is interleaved and garbled (`158132171` on core 5 vs `169295207` on core 6 vs `179900867` on core 7 — they are not sharing or converging on anything) |
| `visible_hpc.c` | `VISUALIZING 40 GFLOPS TORSION` | `printf` literal. Calls `cblas_dgemm` on **N=64**, i.e. 0.52 MFLOP per call, 100 times, with no timer anywhere in the file. 40 GFLOPS is ~8000x the work actually performed. |
| `visible_hpc.c` | `VISUAL STRIKE COMPLETE. HIERARCHY-1 SUSTAINED.` | `printf` literal |
| `vk_gflops.sh` | header: `VULKAN PEAK COMPUTE (The 127 GFLOP/s Sovereign Bypass)` | `127` is a comment. Runs `vkpeak` under `MESA_LOADER_DRIVER_OVERRIDE=zink`, which is a **software** Vulkan-on-GL translation layer, so any figure it reports is not GPU hardware throughput. Also `apt update && apt install -y`. |

`visible_hpc.c` is the one item in this group that accidentally earns its keep:
it proves CBLAS is installed, which is what made the OpenBLAS comparison in
§6 possible.

## 4. `verify_lean_proof.sh` — a gate that accepts fake proofs

```bash
if lean "$FILE"; then
  echo "LEAN_KERNEL_ACCEPTED"
```

Lean treats `sorry` as a **warning**, not an error, so the process exits 0.
Demonstrated on a file whose every theorem is admitted:

```
$ cat sorry_test.lean
theorem fake_claim : 2 + 2 = 5 := by sorry
theorem another_fake : forall (n : Nat), n = n + 1 := by sorry

$ bash /root/verify_lean_proof.sh sorry_test.lean
sorry_test.lean:1:8: warning: declaration uses `sorry`
sorry_test.lean:2:8: warning: declaration uses `sorry`
LEAN_KERNEL_ACCEPTED
   [exit=0]
```

The script cannot distinguish a real proof from `2 + 2 = 5 := by sorry`. It
also accepts a file with no theorems at all, and it would accept
`theorem fake_claim : 2 + 2 = 5 := by decide` — no wait, that one genuinely
fails, but the point stands for `sorry` and for `native_decide` on false
propositions.

For contrast, the Speedup core verifier checks the two things this script
omits (`scripts/verify_lean4_all.sh`):

```
line  77:  if grep -nE '\b(sorry|admit|by\?)\b' "$out" ...
line 100:  if grep -nE '^[[:space:]]*(axiom|opaque)[[:space:]]+' "$out" ...
```

**Recommendation: do not use `verify_lean_proof.sh` as a gate.** Use
`scripts/verify_lean4_all.sh`, which rejects `sorry`/`admit`/`by?` and
`axiom`/`opaque` in the core lane. If a standalone gate is wanted, it must
additionally scan for `sorry` in the output and fail on it.

## 5. Items that are honest but trivial

- `validator_next_tests.lean` (583 B) is correctly written and core-lane clean.
  It proves `p -> q -> r |- r` and, given both directions, `q |- p`. Propositional
  composition. It is a test of the validator, not a result. The deliberately
  invalid theorem is correctly left commented out with a note explaining why.
- `verify_local_pcsc.sh` and `vpcd.conf.saved` concern a **virtual** PC/SC
  smartcard (`DEVICENAME /dev/null:0x8C7B`). The script's PASS/FAIL is honest —
  it enumerates readers and reports failure when none are present. Not a
  performance claim.
- `vector_kernel.c` — 8 floats, not the claimed 4096 dimensions. Its
  `#pragma omp simd` annotates a 16-iteration loop carrying a loop-dependent
  `val`, so it is not vectorizable and the pragma is a misannotation.
- `venv/`, `v4_logs/`, `verified-state/`, `vsmartcard/` are directories.
  `verified-state/` is an empty-looking 3452 B directory and is **not** a
  Speedup certificate store; nothing in it was promoted.

## 6. The one genuine elevation: OpenBLAS settles the sovereign GEMM claim

`visible_hpc.c` revealed that CBLAS is present. That closes the
`G_non_advantageous` gap left open in `SOVEREIGN_AUDIT.md`, which had been
recorded as unmeasurable. `sovereign_blas_compare.c` now measures the corrected
8x8 NEON kernel against `cblas_sgemm` on the same observable, single-threaded
on both sides (`OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`):

| n | ref scalar | neon_8x8 | vs scalar | OpenBLAS | vs scalar | **BLAS vs neon_8x8** |
|---|---|---|---|---|---|---|
| 256 | 3.54 GF | 11.91 GF | 3.88x | 22.09 GF | 7.19x | **1.85x faster** |
| 512 | 3.34 GF | 10.82 GF | 3.63x | 21.41 GF | 7.36x | **1.98x faster** |
| 768 | 3.35 GF | 9.17 GF | 2.83x | 23.32 GF | 7.93x | **2.54x faster** |
| 1024 | 2.91 GF | 6.64 GF | 2.45x | 23.66 GF | 8.16x | **3.56x faster** |

All three implementations pass the observable check under a **relative**
tolerance of 1e-4. OpenBLAS's relative error (up to 6.1e-6 at n=768) is larger
than the NEON kernel's (6.6e-8) because OpenBLAS accumulates in blocked/FMA
order while the NEON kernel accumulates strictly sequentially in `k` — the NEON
kernel is the more numerically stable of the two, and the slower.

**Consequence for the sovereign claim.** The 3.7x measured in
`SOVEREIGN_AUDIT.md` is entirely an artifact of the baseline choice. Against a
naive triple loop the corrected kernel wins 2.45-3.88x. Against a tuned
implementation available on the same machine, it **loses by 1.85x to 3.56x**.
`G_non_advantageous` therefore **FAILS with measurement, not with an
assumption**:

```
speedup(8x8 fixed) vs naive scalar triple loop = 3.7x   [measured]
speedup(8x8 fixed) vs OpenBLAS sgemm           = 0.28-0.54x  [measured, LOSES]
G_non_advantageous = FAIL (was UNKNOWN)
```

This is the correct end state for the audit: the claim was never a speedup
claim, it was a weak-baseline artifact, and that is now demonstrated rather
than argued.

## 7. Disposition

| Item | Disposition |
|---|---|
| `validate_rh.sh` | **Refute.** Fabricated RH verdict. Never cite. |
| `v15_collapse` | **Refute.** Printed factorization is arithmetically false. |
| `v13_engine.c` | **Refute.** Stability values hardcoded; `calculate_stability` dead; basis never built. |
| `v14_strike`, `v16_adjoint` | **Refute.** "Inferred root" downstream of the false factorization; no break. |
| `v16_key` | **Refute.** Fails and exits 0; dominance string unreachable. |
| `v17_simd`, `warp_engine` | **Refute.** 8-core claims on 1 CPU; no timing; racy output. |
| `visible_hpc.c` | **Refute** as a perf claim. **Credit** for revealing CBLAS. |
| `vk_gflops.sh` | **Refute.** 127 GFLOPS is a comment; zink is software. |
| `verify_lean_proof.sh` | **Do not use as a gate.** Accepts all-`sorry` files. |
| `vector_kernel.c` | Void. 8 floats; misannotated `omp simd`. |
| `validator_next_tests.lean` | Trivial, correct, core-lane clean. No claim. |
| `verify_local_pcsc.sh`, `vpcd.conf.saved` | Honest diagnostic. No perf claim. |
| sovereign GEMM 3.7x | **Refuted as a speedup claim** by the OpenBLAS comparison in §6. |

## 8. Added to the system

- `evidence/hierarchical_accel/2026-09-26/sovereign/sovereign_blas_compare.c`
- `evidence/hierarchical_accel/2026-09-26/sovereign/blas_compare.json`

No PCSS certificate. `evidence/ledger/claims.jsonl` untouched: these are
refutations, and the authoritative ledger is not the place to record exploratory
audit output. The existing `QUARANTINED` entries stand.
