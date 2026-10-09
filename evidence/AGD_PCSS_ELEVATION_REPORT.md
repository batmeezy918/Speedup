# AGD PCSS Elevation Report — Full Closure and Amortized Quotient Descent

**Run:** `AGD_PCSS_ELEVATION_20261009T060000Z`  
**GitHub branch:** `agd-pcss-elevation-20261009`  
**Base PCSS status:** `PCSS_PASS`, 8/8 gates within the declared tensor-family scope.  
**Additional overhead sweep:** v3 PASS, 12 depths, exact numerical and bytewise equality; plan destruction included in end-to-end quotient time.

## 1. Formal domain and recursive identity

The proved/implemented family is (U=\bar U\otimes I_m), with (d=rm), on states that are block-constant across each identity fiber. Projection (P), quotient evolution (Q), and reconstruction (R) satisfy the one-step commuting relation (P U(x)=Q P(x)) on the declared invariant sector. Induction gives (P U^n(x)=Q^n P(x)), and exact reconstruction gives (R Q^n P(x)=U^n(x)) for finite trajectories in that sector.

The Lean 4.29.0 quotient core and tensor instantiation compile. The recursive forward-refinement and exact-reconstruction theorem checks are axiom-free in the recorded Lean output. This does not prove arbitrary transformer equivalence or automatically discover invariants in arbitrary programs.

## 2. Replayed gates

- PCSS receipt: `PCSS_PASS`, closure `8/8`, residual gap empty within declared scope.
- Lean quotient core and tensor instantiation: exit 0; required axiom checks clean.
- Adversarial suite: 20/20 pass.
- Bytewise audit: PASS; exact `memcmp` comparisons and fail-closed handling for inadmissible/non-finite inputs.
- Recursive trajectory benchmark: PASS.
- Native Debian PRoot/AArch64 callable receipt: 64.113911× at (d=4096,m=64,r=64,n=64), reported max absolute error 0.
- Termux Clang/Bionic runtime receipt: 20.050822× at (d=512,m=16,r=32,n=32), reported max absolute error 0. This is a second runtime/ABI on the same physical device, not independent-hardware replication.
- Formal certificate, recursive proof-input manifest, source-set manifest, binaries, receipts and artifact hashes revalidated. See `PCSS_CLOSURE_RECEIPT.json`, `AGD_RECURSIVE_CERTIFICATE.manifest`, `AGD_ARTIFACT_HASHES.sha256`, and `AGD_ELEVATION_ARTIFACT_HASHES.sha256`.

## 3. Cost model

Let the full-state path cost be (T_F(n)=C_F+n c_F). The quotient path is measured as (T_Q(n)=C_P+n c_Q+C_R+C_D), where (C_P) is plan creation/admissibility/projection, (C_R) reconstruction, and (C_D) plan destruction. The reported end-to-end quotient time includes all four measured components: (C_P), quotient steps, (C_R), and (C_D). Plan teardown is no longer excluded.

The local linear-model break-even estimate is (n_*=(C_P+C_R+C_D)/(c_F-c_Q)), where (c_F>c_Q). This estimate is descriptive for this run, not a universal performance theorem.

## 4. Final warmed overhead sweep v3

AArch64 Debian 13 PRoot, GCC 14.2.0, `-O3 -march=native -funroll-loops -fno-fast-math -ffp-contract=off`; (d=4096,m=64,r=64); depths 0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1,024; two warm-ups, seven trials, five repetitions. Plan creation/projection, quotient steps, reconstruction, and plan destruction are separately measured. All rows passed exact `memcmp` equality, max absolute error 0, admissibility true, and fallback false.

| Steps | Full path ms | Create/project ms | Quotient steps ms | Reconstruct ms | Destroy ms | Quotient end-to-end ms | Speedup |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.002562 | 0.009302 | 0.000271 | 0.001292 | 0.000521 | 0.011385 | 0.225× |
| 1 | 0.238823 | 0.011354 | 0.003729 | 0.001865 | 0.000813 | 0.017760 | 13.447× |
| 2 | 0.464906 | 0.010666 | 0.007000 | 0.001781 | 0.000729 | 0.020177 | 23.042× |
| 4 | 0.927334 | 0.012563 | 0.013708 | 0.002115 | 0.000989 | 0.029375 | 31.569× |
| 8 | 1.848813 | 0.014208 | 0.026979 | 0.002510 | 0.001240 | 0.044938 | 41.142× |
| 16 | 3.706479 | 0.016969 | 0.053688 | 0.002740 | 0.001604 | 0.075000 | 49.420× |
| 32 | 7.378552 | 0.018302 | 0.106448 | 0.002521 | 0.001646 | 0.128917 | 57.235× |
| 64 | 14.741146 | 0.019385 | 0.215646 | 0.002281 | 0.001833 | 0.239146 | 61.641× |
| 128 | 29.464271 | 0.018875 | 0.424010 | 0.002427 | 0.002250 | 0.447563 | 65.833× |
| 256 | 58.921698 | 0.019333 | 0.848688 | 0.002396 | 0.002281 | 0.872698 | 67.517× |
| 512 | 117.826125 | 0.019302 | 1.705833 | 0.002365 | 0.002583 | 1.730084 | 68.104× |
| 1,024 | 235.644990 | 0.019729 | 3.406250 | 0.002406 | 0.002656 | 3.431042 | 68.680× |

Machine-readable results: `elevation/overhead_amortization_v3.csv`. Exact source and binary: `elevation/overhead_amortization_v3.c` and `elevation/overhead_amortization_v3`. The earlier v2 sweep is retained as historical evidence; v3 is the final cost accounting because it includes teardown.

## 5. Setup amortization and operational rule

At one step, plan creation + reconstruction + destruction is (11.354+1.865+0.813=14.032\) μs; quotient execution is 3.729 μs, giving 17.760 μs total versus 238.823 μs for the full path.

At 64 steps, fixed costs total (19.385+2.281+1.833=23.499\) μs, about 9.83% of quotient end-to-end time. At 1,024 steps, fixed costs total (19.729+2.406+2.656=24.791\) μs, about 0.72% of end-to-end time.

Using the 64-step local rates, (c_F=230.330\) μs/step and (c_Q=3.369\) μs/step, the estimated break-even is (n_*=23.499/(230.330-3.369)\approx0.104) steps. Thus the first integer horizon is one step for this particular configuration. The zero-step negative control is slower: 11.385 μs quotient setup/teardown versus 2.562 μs full path. That is the intended warning against applying the quotient when no useful work follows.

**Operational policy:** validate the certificate and invariant, create/project once, execute as many certified quotient steps as possible, and reconstruct only at an observation boundary. Do not recreate the plan or reconstruct the full state between quotient steps unless the caller changes the input/operator/certificate or requires a full-state observation. The current API evidence does not establish cross-input plan reuse.

## 6. Scope boundary

The formal and empirical claim is limited to (U=\bar U\otimes I_m), block-constant invariant inputs, finite trajectories, and the tested native implementation. No claim is made for arbitrary transformer models, arbitrary invariant discovery, universal speedup, or independent hardware. The GitHub PR is a draft for review; it has not been merged.