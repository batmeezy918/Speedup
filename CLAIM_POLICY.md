# Claim Strength Policy

PCSS uses a monotone evidence lattice. Stronger labels require strictly sufficient evidence.

| Status | Meaning | Automatic verified claim? |
|---|---|---|
| CANDIDATE | Unvalidated or exploratory | No |
| STRONG_LOCAL | Reproducible local empirical evidence | No |
| FORMAL_PARTIAL | Formal proof for bounded/modelled obligations | No, unless empirical gates also pass |
| VERIFIED | All declared empirical + formal gates pass | Yes, within declared scope |
| FAILED | Required condition contradicted | No |
| QUARANTINED | Evidence retained but excluded from claims | No |

## Speedup claim

A speedup factor `S = T_baseline / T_candidate` is scoped to the exact workload, environment, measurement protocol, and statistical treatment in its certificate.

The scheduler must not silently convert `S` into a universal or hardware-independent statement.

## Formal claim

A Lean theorem proves the proposition encoded by the theorem. It does not validate facts that were never encoded or supplied as assumptions. External measurements remain traceable empirical evidence.

## Novelty claim

"Novel architecture" means the repository contains a newly constructed design. "Scientifically novel" requires independent prior-art analysis. PCSS never auto-labels a result scientifically novel.

## Conflict rule

If raw measurements, quotient results, reconstruction, invariants, and formal results disagree, the strongest supported status is reduced or the artifact is quarantined until the conflict is resolved.
