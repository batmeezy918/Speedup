# Evidence model

The rule this file exists to enforce:

> **CLAIM_STRENGTH ≤ EVIDENCE_STRENGTH** — `CONSTITUTION.md` Article 1.

Two separate ladders, because conflating them is how a system talks itself into
a result it does not have. **Evidence** asks *what exists*. **Claim** asks *what
may be said*. A record may only say what its evidence supports.

## The evidence ladder

Ordered, weakest to strongest. Implemented as `EVIDENCE_LADDER` in
`scripts/ssproof.py`; the Lean statement is `Strength` in
`formal/SSProofCore.lean`.

| # | Level | What must exist |
|---|---|---|
| 0 | `UNEVIDENCED` | nothing. The only honest level for a proposal with no artifact. |
| 1 | `OBSERVED` | a run id, a command, and at least one recorded artifact with a hash. |
| 2 | `EXECUTED` | a native execution with exit status, environment, and raw timing samples. |
| 3 | `REPRODUCED` | ≥ 2 independent runs whose results agree within the declared tolerance (default: relative delta ≤ 0.05). |
| 4 | `CORRECTNESS` | forward equivalence and reverse reconstruction evidence, each with an artifact reference. |
| 5 | `MECHANISM` | a counterfactual, ablation, hardware counter, microarchitectural trace, or model fit. Not a prior-work citation. |
| 6 | `FORMAL` | a named theorem target, the exact command, exit status 0, and `kernel_checked: true`. |
| 7 | `SCOPED_VERIFIED` | every required gate for the declared scope, each bound to an artifact. |

## The claim ladder

`NONE < CANDIDATE < STRONG_LOCAL < FORMAL_PARTIAL < VERIFIED`.

The upper four match `CLAIM_LATTICE` in `speedup/const.py`. `NONE` is added
below them so that "there is no claim here" is representable rather than
implied by an empty field.

## The floor table

The invariant alone is too weak. `STRONG_LOCAL` has rank 2 and `REPRODUCED` has
rank 3, so rank ordering alone would accept a `STRONG_LOCAL` performance claim
backed by `REPRODUCED` evidence — but it would *also* accept one backed by
`EXECUTED` evidence, which is a single run. A single run is not reproduction.

So admissibility is the conjunction of two independent constraints
(`Acceptable` in the Lean core):

```
Claim.rank(c) <= Strength.rank(e)          # the constitutional invariant
AND Strength.rank(e) >= floor(c, k).rank   # the kind-specific floor
```

`floor` is declared for all 35 `(claim, kind)` pairs in `MINIMUM_EVIDENCE`.
A test asserts the table is total and that each floor is itself admissible, so
the table cannot silently contradict the invariant.

| claim | kind | minimum evidence |
|---|---|---|
| `NONE` | any | `UNEVIDENCED` |
| `CANDIDATE` | any | `OBSERVED` |
| `STRONG_LOCAL` | performance, composition, cumulative | `REPRODUCED` |
| `STRONG_LOCAL` | implementation | `CORRECTNESS` |
| `STRONG_LOCAL` | hardware_mechanism | `MECHANISM` |
| `STRONG_LOCAL` | formal | `FORMAL` |
| `STRONG_LOCAL` | none | `EXECUTED` |
| `FORMAL_PARTIAL` | formal | `FORMAL` |
| `FORMAL_PARTIAL` | hardware_mechanism | `MECHANISM` |
| `FORMAL_PARTIAL` | everything else | `CORRECTNESS` |
| `VERIFIED` | any | `SCOPED_VERIFIED` |

## What each rule catches

| Situation | Rule | Code |
|---|---|---|
| Exit 0, no timing result | an execution is not a measurement | `R-TIME-1/2/3`, `L-EXE-3` |
| Single run presented as reproduction | `REPRODUCED` needs two agreeing runs | `R-TIME-4`, `R-CLM-1` |
| Performance claim with no correctness evidence | correctness is a separate gate | `R-CLM-1` |
| Equivalence failed | promotion rejected outright | `R-CORR-1/2`, `L-CLM-1` |
| Mechanism claimed from a timing delta | restrict to "unexplained observed effect" | `R-MECH-1` |
| Unresolved dependency | claim relying on it is rejected | `R-DEP-1`, `L-DEP-1` |
| Repeat run contradicts earlier result | preserve the contradiction, downgrade | `L-CNT-1/2` |
| "verified" assigned by hand | a label is not evidence | `R-CLM-2/3`, `L-CLM-2/3` |
| Composition of verified components, no fresh run | component status is necessary, not sufficient | `L-CMP-3` |
| All-vacuous validation batch | test count is not coverage | `R-VAC-1/3`, `L-VAC-1` |

## Limitations of this model

Stated because a model without its failure modes is a slogan.

1. **The ladder is ordinal, not cardinal.** It says nothing about how much
   evidence, only what kind. Two artifacts and two hundred are both `OBSERVED`.
2. **Reproduction is threshold-based.** `0.05` relative delta is a declared
   tolerance, not a statistical test. Two runs that agree within 5% may still
   share an unrecorded confound (same thermal state, same cache, same input
   file). The model cannot see confounders it was not told about. Use
   `differential-benchmarking` for interleaving and noise-floor discipline;
   this ladder only records that you said you did it.
3. **`CORRECTNESS` is quotient-relative.** `CONSTITUTION.md` Article 3 makes
   equivalence relative to a declared observable quotient `Q`. Passing does not
   mean "identical", it means "identical under `Q` with tolerance ε". A poor
   choice of `Q` hides a real difference.
4. **`FORMAL` is about the encoded proposition.** A kernel-checked theorem
   proves the proposition as stated, with its stated assumptions. Lean cannot
   prove that your benchmark measures what the theorem talks about. Formal and
   empirical evidence stay separate — `PROTOCOL.md`, `CONSTITUTION.md`
   Article 7.
5. **`SCOPED_VERIFIED` is local.** It is a statement about a declared workload,
   environment, input domain, and protocol. It is never a statement about a
   class of hardware, about optimality, or about general composability.
6. **The validators check declared fields.** They cannot tell you the
   environment block is a lie. `R-PROV-*` verifies hashes and paths, not
   truth. A dishonest record with correct hashes passes.
7. **The floor table is a policy choice.** It encodes this repository's reading
   of `CLAIM_POLICY.md`. A different project may set different floors; the
   mechanism is what transfers, not the specific rows.
8. **The ladder is total, so a stronger level satisfies a weaker floor.** A
   record at `CORRECTNESS` satisfies the `REPRODUCED` floor for a performance
   claim, because the order means "has at least". That is intentional, but it
   means the floor table cannot express "this evidence must be of *this* kind" —
   only "at least this strong".
9. **An unrecognised claim kind is held to the strictest floor, not exempted.**
   A typo in `claim.kind` must never widen what a record may assert. The JSON
   Schema enum is a second line of defence; the library does not depend on it.

## How a level is raised

Never by assignment. Every raise is an append-only event with an `event_ref`
(validator `L-CLM-3`; Lean `Acceptable`). The chain must start at
`UNEVIDENCED`, visit every rung in order, and terminate at the claimed level:

```json
"transition_records": [
  {"from": "UNEVIDENCED", "to": "OBSERVED",     "event_ref": "runs/0001/stdout.txt"},
  {"from": "OBSERVED",     "to": "EXECUTED",     "event_ref": "runs/0001/timing.json"},
  {"from": "EXECUTED",     "to": "REPRODUCED",   "event_ref": "runs/0002/timing.json"}
]
```

A chain that skips a rung, runs backwards, or carries an empty `event_ref` is
rejected. So is `claim.assigned_manually: true` above `CANDIDATE`
(`R-CLM-2`, `L-CLM-2`).

**Both record types enforce this.** `validate-ledger.py` checks it on primitive
records (`L-CLM-3`); `validate-run.py` checks it on evidence records
(`R-CLM-3`). An evidence level above `OBSERVED` is therefore not self-declarable
in either place. This was not true of the first implementation: `validate-run.py`
omitted the check and its schema made the honest fix illegal, so a `VERIFIED`
claim could pass on a self-typed `SCOPED_VERIFIED` scalar. The regression is
pinned in `tests/test_falsification_regressions.py`.

## Relationship to the repository's lattices

This model extends, and does not replace, `speedup/const.py`. That file remains
the publication authority via `publisher/strict_gate.py`. This skill adds the
claim-kind floor table, the evidence ladder, and the vacuity accounting that
`const.py` does not model. Where they overlap, they agree:

| `speedup/const.py` | this document |
|---|---|
| `CLAIM_LATTICE` | the claim ladder |
| `gates_ok(...)` | levels 2–7, one per gate |
| `FAILED_STATUSES` | `regressed`, `blocked`, `quarantined` statuses |
| — | the floor table, the vacuity model, the composition rules |