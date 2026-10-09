# AGD PCSS Elevation Addendum — One-Time Overhead and Deep Quotient Descent

**Run:** `AGD_PCSS_ELEVATION_20261009T060000Z`  
**Base evidence:** copied without edits from `AGD_PCSS_FULL_CLOSURE_20261009T050000Z`  
**Formal scope:** `U = Ubar ⊗ I_m`, block-constant invariant sector, finite trajectories.  
**Status:** base PCSS closure replayed successfully; overhead sweep v2 passed.

## What was replayed

- Lean 4.29.0 quotient core and tensor instantiation compile successfully.
- The recursive theorem axiom checks remain clean.
- Adversarial suite: 20/20 pass.
- Bytewise audit: pass, including exact `memcmp` checks through 1,000 steps and fail-closed edge cases.
- Recursive end-to-end trajectory benchmark: pass.
- Formal certificate, recursive proof-input manifest, and source-set hashes revalidated by `finalize_closure.py`.
- `sha256sum -c AGD_ARTIFACT_HASHES.sha256`: all base entries pass.
- Additional `overhead_amortization_v2` sweep: 12 trajectory depths, two warm-up rounds per depth, 7 trials × 5 repetitions, exact numerical and bytewise output checks for each depth.

## Cost model

For a trajectory of (n) quotient steps, measure

[
T_F(n) = C_F + n,c_F
]

for the original full-state path and

[
T_Q(n) = C_P + n,c_Q + C_R
]

for the quotient path, where (C_P) is plan creation/admissibility/projection overhead and (C_R) is reconstruction overhead. The observed speedup is (S(n)=T_F(n)/T_Q(n)). The setup break-even estimate is

[
n_* = rac{C_P+C_R}{c_F-c_Q}, quad c_F>c_Q.
]

This is an empirical model for this binary, device, compiler, shape, and workload—not a theorem about other systems.

## Fresh overhead sweep

Configuration: Debian 13 PRoot on AArch64, GCC `-O3 -march=native -funroll-loops -fno-fast-math -ffp-contract=off`; (d=4096, m=64, r=64); depths 0–1024; each measured trajectory creates one plan, runs all quotient steps, reconstructs once, and destroys the plan outside timing. Two warm-ups precede timing at each depth.

| Steps | Full path (ms) | Create/project (ms) | Quotient steps (ms) | Reconstruct (ms) | Quotient end-to-end (ms) | Speedup |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.013375 | 0.055417 | 0.000698 | 0.002875 | 0.058990 | 0.227× |
| 1 | 0.240156 | 0.011114 | 0.003688 | 0.001729 | 0.016531 | 14.528× |
| 2 | 0.466552 | 0.011344 | 0.007052 | 0.001719 | 0.020115 | 23.194× |
| 4 | 0.925927 | 0.012552 | 0.013677 | 0.001990 | 0.028218 | 32.813× |
| 8 | 1.847969 | 0.012042 | 0.026927 | 0.001791 | 0.040760 | 45.337× |
| 16 | 3.697073 | 0.014062 | 0.053458 | 0.002031 | 0.069552 | 53.156× |
| 32 | 7.391968 | 0.017834 | 0.106406 | 0.002468 | 0.126708 | 58.339× |
| 64 | 14.750114 | 0.018708 | 0.216635 | 0.002541 | 0.237885 | 62.005× |
| 128 | 29.687969 | 0.019500 | 0.424989 | 0.002448 | 0.446937 | 66.425× |
| 256 | 59.176229 | 0.018125 | 0.845917 | 0.002333 | 0.866375 | 68.303× |
| 512 | 118.421104 | 0.020000 | 1.702854 | 0.002479 | 1.725333 | 68.637× |
| 1024 | 236.963948 | 0.018531 | 3.417594 | 0.002521 | 3.438646 | 68.912× |

Every row reports max absolute error 0, `memcmp_equal=1`, `admissible=1`, and `fallback=0`. Machine-readable raw data is `elevation/overhead_amortization_v2.csv`; the exact benchmark source and binary are retained alongside it.

## Overhead interpretation

- At 1 step, setup plus reconstruction is (11.114+1.729=12.843) μs, versus approximately (240.156) μs for the full path. The measured quotient end-to-end time is 16.531 μs.
- At 64 steps, setup plus reconstruction is (21.249) μs against (14.750114) ms total full-path time. The fixed overhead is about 8.93% of quotient end-to-end time.
- At 1,024 steps, setup plus reconstruction is (21.052) μs against (236.964) ms full-path time. Fixed overhead is about 0.612% of quotient end-to-end time.
- The 64-step and 1,024-step results give a conservative local per-step comparison of roughly (230)–(231) μs full path versus (3.34)–(3.39) μs quotient step. Using the 64-step fixed overhead, the linear-model break-even estimate is about (21.249/(230.471-3.385) = 0.094) steps. The first meaningful integer horizon is therefore one step for this configuration. The 0-step row is intentionally a negative control: it shows that setup alone loses when no useful work follows.
- The largest measured speedup in this sweep is 68.912× at 1,024 steps. This is a fresh, configuration-specific result; it does not replace or multiply the separate 64-step 64.113911× receipt.

## Operational conclusion

Perform the admissibility check, certificate validation, plan creation, and projection once per trajectory; descend into the quotient for as many certified steps as the workload permits; reconstruct once at the required observation boundary. Avoid repeated plan creation and reconstruction between quotient steps unless the caller needs a full-state observation or the input/invariant contract changes. This recommendation follows the measured cost decomposition and the API's current contract. It does **not** claim that plan objects are reusable for unrelated inputs, or that validation can be cached across changing operators or changed certificates.

## Gate and scope statement

The base formal and native closure is still `PCSS_PASS 8/8` within the declared tensor-family scope. The new sweep adds timing evidence and exact output comparisons; it does not broaden the theorem to arbitrary transformer models, arbitrary software, automatic invariant discovery, or independent hardware. The Android Termux witness remains a separate runtime/ABI on the same physical device.