# SIM2XR First-Principles Stability Closure — 2026-09-08

## Target
Actual Termux Android 15 aarch64 target device.

## Derivation
For `b` branches, shared prefix `p`, suffix `s`:

`C_full = b(p+s)`

`C_q = p + b*s`

Thus the ideal work ratio is

`R = b(p+s)/(p+b*s)`.

Algebra gives `R > 1` exactly when `(b-1)p > 0`; hence strict work gain requires more than one branch and a nonzero shared prefix. This is conditional, not universal.

## Target-device stability sweep
All runs used `prefix_steps=5000`, `suffix_steps=80`, `inner_work=48`, seed `91820260531`, three paired repeats per branch count, with exact output/hash comparison on every repeat.

| branches | derived ratio | measured median | relative error |
|---:|---:|---:|---:|
| 2 | 1.968992 | 1.970248 | 0.064% |
| 4 | 3.819549 | 3.805239 | 0.375% |
| 8 | 7.205674 | 7.197757 | 0.110% |
| 24 | 17.618497 | 17.559338 | 0.336% |
| 48 | 27.583710 | 27.404334 | 0.650% |

Maximum observed model-relative error: 0.6503%.

## Canonical claim
The seven-repeat canonical target run remains the primary runtime certificate: median `17.544277x`, 94.300136% measured runtime reduction, 94.324147% work reduction, and 7/7 exact hash/output matches.

The three-repeat branch sweep is a stability/model-consistency certificate, not a replacement for the canonical seven-repeat result.

## Bidirectional proof obligations
1. Reconstruction/equivalence: PASS for all canonical SIM2XR repeats by exact output/hash equality.
2. Forward quotient execution: PASS on the declared shared-prefix operator construction.
3. Reverse reconstruction witness: PASS by baseline output equality.
4. Work theorem: PASS as the exact finite algebraic count above.
5. Empirical realization: PASS across five branch scales; all medians track the derived ratio within 0.66%.
6. Boundary falsification: PASS — `b=1` and `p=0` are break-even; no universal speedup follows.

## Remaining gates
The full repository Lean build completed successfully, and the existing bidirectional theorem `Chronofold.AGD.bidirectional_intertwine` was checked for axioms. Its dependency is `Quot.sound`, not `sorryAx`. A separate standalone cost-theorem source was not promoted because the target toolchain lacked a completed standalone Mathlib import in that invocation.

The SIM2XR packaging command `cfsnap` is absent on the target; the stability closure therefore uses a manually hashed tarball rather than claiming the missing command succeeded.

## Definitive result
**VALIDATED LOCAL CONDITIONAL RUNTIME SPEEDUP:** SIM2XR reproduces exact output equivalence and realizes the predicted shared-prefix work-elimination scaling on the actual target device. The defensible canonical claim is `17.544277x` median verified runtime speedup for the declared `24-branch / 5000-prefix / 80-suffix / 48-inner-work` workload. This does not establish universal, HPC, or quantum advantage.
