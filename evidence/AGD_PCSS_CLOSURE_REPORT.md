# AGD / MUNI Proof-Carrying Tensor Quotient — Closure Report

**Run directory:** `/root/AGD_PCSS_FULL_CLOSURE_20261009T050000Z`  
**Status:** `PCSS_PASS` — 8/8 gates for the declared tensor-family callable workload  
**Transformation:** `quotient-descent-v2-tensor`

## 1. Formal definition and domain

The implemented full transition is the tensor-separable operator

`U = Ubar tensor I_m`,

where the full state has `d = r*m` coordinates and each quotient block contains `m` repeated identity-fiber coordinates. The admissible invariant sector consists of states that are constant within each block. The theorem is scoped to this declared family and sector; it is not a theorem about arbitrary operators or arbitrary programs.

Let `P` project each block to its canonical representative, let `Q` apply `Ubar` to the quotient state, and let `R` replicate quotient coordinates across each block. On the declared invariant sector, the implementation establishes the one-step commuting identity

`P(U_full(x)) = Q(P(x))`.

Induction on finite `n` gives

`P(U_full^n(x)) = Q^n(P(x))`.

The reconstruction theorem then gives

`R(Q^n(P(x))) = U_full^n(x)`

for every finite trajectory starting in that sector. This is the mathematical basis of the callable optimization; it does not, by itself, imply a speedup.

## 2. Lean proof

Freshly compiled with Lean 4.29.0:

- `AGD.QuotientCore.iterate_projection_commutes`
- `AGD.QuotientCore.iterate_reconstruction_exact`
- `AGD.QuotientCore.iterate_preserves_invariant`
- `AGD.recursive_forward_refinement`
- `AGD.recursive_exact_reconstruction`
- `AGD.exact_reconstruction_on_invariant_orbit`
- `AGD.forward_refinement`
- `AGD.reconstruction_exact`

The two recursive tensor theorems and the generic quotient-core theorems reported no axiom dependencies. Lean source SHA-256: `907c730b1f0a160330b0349cd5dfeffcb287057e1a8720c318d0e31ead932d2d`.

## 3. Callable safety contract

The native callable plan has two permitted paths:

1. `CERTIFIED` certificate plus admissible block-constant input → quotient path.
2. Any unverified/partial certificate or inadmissible input → original full-state fallback.

At zero tolerance, admissibility compares binary representations for block equality and refuses non-finite values. The independent bytewise audit uses `memcmp`, not only a floating-point absolute-error metric.

## 4. Fresh validation results

### Adversarial suite

`ADVERSARIAL_SUITE=PASS passed=20 failed=0`.

The cases cover dense, diagonal and phase operator families; admissible and perturbed/random states; tolerance behavior; unverified and partial certificates; illegal shapes; `m=1`; `m=d`; a 1,000-step trajectory; and a multi-size/multi-family sweep.

### Bytewise audit

`BITWISE_AUDIT=PASS failures=0`.

Exact `memcmp` checks passed for invariant trajectories at depths 0, 1, 2, 8, 64 and 1,000; for finite inadmissible fallback; and for signed-zero, NaN and infinity cases that must refuse the quotient path.

### Recursive end-to-end benchmark

Fresh compiled binary, `d=4096`, `m=64`, `r=64`, 5 trials × 3 repetitions; each row includes baseline input copy/full steps versus plan creation/projection, quotient steps and reconstruction:

| Steps | Baseline ms | Quotient end-to-end ms | Speedup | Max absolute error |
|---:|---:|---:|---:|---:|
| 1 | 0.467136 | 0.030087 | 15.526× | 0 |
| 8 | 2.137414 | 0.057725 | 37.027× | 0 |
| 64 | 17.003837 | 0.271458 | 62.639× | 0 |
| 256 | 68.015486 | 1.009861 | 67.351× | 0 |

`RECURSIVE_ONCE_GATE=PASS`.

### Main native callable benchmark

Fresh GCC 14.2.0 build in Debian GNU/Linux 13 PRoot on AArch64; `-O3 -march=native -funroll-loops -fno-fast-math -ffp-contract=off`; `d=4096`, `m=64`, `r=64`, 64 steps, 7 trials × 5 repetitions:

- Baseline: 85.071 ms
- Quotient end-to-end: 1.327 ms
- Speedup: 64.113911×
- Reported max absolute error: 0
- Path: quotient optimized

### Cross-runtime callable benchmark

Fresh Termux Clang 21.1.8 build, Android Bionic ABI/runtime on the same physical ARM64 device; `-O2 -fno-fast-math -ffp-contract=off`; `d=512`, `m=16`, `r=32`, 32 steps, 3 trials × 5 repetitions:

- Baseline: 3.929 ms
- Quotient end-to-end: 0.196 ms
- Speedup: 20.050822×
- Reported max absolute error: 0
- Path: quotient optimized

This is a separate runtime/ABI witness on the same hardware, **not** an independent-hardware replication.

### Fail-closed control

The deliberately perturbed native input took the original fallback path:

- Baseline: 85.154 ms
- Fallback: 84.544 ms
- Ratio: 1.007×
- Reported max absolute error: 0
- Claim: `QUARANTINED_OPTIMISATION_NOT_APPLIED`

## 5. Provenance binding

The formal manifest hash is `ef60162893f59ee1446af27005e332a0b7978e2822e424511611644713b24ff1`. The recursive proof-input manifest hash is `557bc991cd6845b2b83fd62eb09fc55b7e323c6bc90183dca94344c0e53b8037`. The full native source-set manifest hash is `cdd2aa469d2f6cb695c54ada0efb0cc2b4355823e7750cd4b8fccff3f3dcd1c1`.

The finalizer independently recomputed and checked:

- Lean source hash against the formal manifest and compiled-in certificate field;
- recursive proof-input manifest hash against the formal manifest and compiled-in certificate field;
- formal certificate manifest hash against the compiled-in certificate identity;
- all entries in the recursive and full source-set hash manifests;
- both run receipts against the same formal certificate and source-set hash;
- cross-runtime receipt against the actual current Android binary hash;
- semantic, adversarial, bytewise, recursive and fallback test outcomes.

Run-level artifact hashes are in `AGD_ARTIFACT_HASHES.sha256`.

## 6. Closure boundary

**Closed:** the formal finite-trajectory identity, its concrete declared tensor-family instantiation, callable native implementation, tested invariant-sector exactness, fail-closed fallback, adversarial and bytewise validation, fresh native measurement, cross-runtime/ABI measurement, and evidence hashes for this run.

**Not claimed:** general discovery of invariant sectors in arbitrary binaries; correctness for arbitrary transformer architectures; universal or hardware-independent speedup; independent-hardware replication; or transfer of these speedup factors to other workloads. The `D` gate in this run means declared-family closure aggregation, not universal automatic program analysis.

## 7. Exact primary commands

```sh
lean AGD_EQUIVALENCE_QUOTIENT_CORE.lean
lean AGD_TENSOR_INSTANTIATION.lean
./bin/agd_adversarial_fresh
./bin/agd_bitwise_audit_fresh
./bin/recursive_once_fresh
./bin/muni_fresh elevate --d 4096 --m 64 --steps 64 --trials 7 --json receipts/muni_fresh.json
./bin/muni_fresh elevate --d 4096 --m 64 --steps 64 --trials 7 --inadmissible --json receipts/muni_inadmissible_fresh.json
./bin/muni_android elevate --d 512 --m 16 --steps 32 --trials 3 --json receipts/muni_android.json
python3 finalize_closure.py
sha256sum -c AGD_ARTIFACT_HASHES.sha256
```