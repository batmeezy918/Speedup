---
name: silicon-speedup-proof
description: Use when claiming or reviewing a speedup, an optimization result, or an operator composition - "make it faster", "X times speedup", "is this correct and faster", "does the gain hold end-to-end", "compose these primitives", "verify the speedup", "cumulative speedup", "does the hardware explain this". Converts an optimization task into an append-only, auditable state transition whose claim strength can never exceed its evidence strength, with machine-validatable gates for correctness, composition, vacuity, formal proof, and provenance.
compatibility: opencode
metadata:
  role: proof-carrying-optimization-protocol
  governing-invariant: claim-strength-must-not-exceed-evidence-strength
  validators: scripts/validate-run.py, scripts/validate-ledger.py
  test-runner: python3 -m unittest discover -s tests -t tests
---

# Silicon Speedup — proof-carrying optimization

An optimization result is a state transition with a history, not a number. This
skill makes each step auditable, keeps a verified primitive reusable without
letting its verification leak into a new claim, and refuses to let a label
outrun the evidence under it.

```
Requirement -> Derivation -> Operator -> Implementation -> Native Run
  -> Raw Result -> Reverse Derivation -> Gap Analysis -> Gap Closure
  -> Re-run -> Normalized Claim
```

The workflow may stop at any stage. **A blocked, failed, or incomplete stage
keeps its actual status.** The remaining stages are not filled in, narrated,
or implied.

## The one law

> **CLAIM_STRENGTH ≤ EVIDENCE_STRENGTH** — `CONSTITUTION.md` Article 1.

Two ladders, checked in code. Read `references/evidence-model.md` before making
any claim; the short version:

```
evidence:  UNEVIDENCED < OBSERVED < EXECUTED < REPRODUCED
                    < CORRECTNESS < MECHANISM < FORMAL < SCOPED_VERIFIED
claim:     NONE < CANDIDATE < STRONG_LOCAL < FORMAL_PARTIAL < VERIFIED
```

Rank ordering alone is too weak, so a kind-specific **floor** table applies too:
a `STRONG_LOCAL` performance claim needs `REPRODUCED` (two agreeing runs), an
`implementation` claim needs `CORRECTNESS`, a `hardware_mechanism` claim needs
`MECHANISM`. All 35 `(claim, kind)` pairs are declared and machine-checked.

## Run it

```bash
# one native run
python3 scripts/validate-run.py evidence/runs/<run>.json --repo-root .

# the append-only primitive ledger
python3 scripts/validate-ledger.py evidence/ledger/primitives.jsonl --repo-root .

# machine-readable
python3 scripts/validate-ledger.py <ledger> --json

# ~2x faster single invocation; skips the jsonschema import
python3 scripts/validate-ledger.py <ledger> --fast

# the test suite (no third-party dependency)
python3 -m unittest discover -s tests -t tests
```

`--fast` selects the bundled schema checker and keeps `jsonschema` out of the
process entirely. Measured on this machine, interleaved, n=25 per arm:

| | default | `--fast` | ratio |
|---|---|---|---|
| single `validate-ledger.py` | 778 ms `[654, 948]` | 391 ms `[319, 466]` | **1.99x**, disjoint |
| 33-file corpus sweep | 21.97 s | 13.66 s | **1.61x**, disjoint |

Root cause: the module-level `import jsonschema` costs ~0.5-0.7 s, against ~13 ms
of actual validation work. The two backends produce **identical finding codes and
identical verdicts on every fixture** — asserted in
`tests/test_backend_equivalence.py`, not assumed.

This is a speedup of the *validation harness*, measured on a busy shared machine
with ~35% run-to-run variance. It is not a claim about any kernel, device, or
workload. If the intervals overlap on your machine, report `INCONCLUSIVE`.

Exit `0` = no errors, `1` = errors found, `2` = usage error. Warnings do not
fail the run unless `--strict`. An **empty ledger is an error** (`L-EMPTY`), not
a pass: a truncated or mis-pathed ledger must not look verified. **These
validators never write, promote, or repair.** They report; a human decides.

Both validators are hardened against malformed input: a non-object ledger line,
undecodable bytes, a non-numeric sample, or a non-numeric ratio is *reported*,
never raised. One bad line must not void the audit of the lines after it.

## Operator model

State `ψₖ ∈ H`; a validated transformation is `ψₖ₊₁ = Oₖ ψₖ`; a chain composes
as `O_total = Oₙ ∘ … ∘ O₁`.

**The named operators are not all implemented in this repository.** That is
recorded, not papered over. `OPERATOR_REGISTRY` in `scripts/ssproof.py`, each
entry carrying the exact command used to establish its status:

| Symbol | Operator | Status in this repo |
|---|---|---|
| `Ω` | invariant signature (`engines/invariant.py`) | **implemented** — but scenario-declared, so only as specific as the scenario |
| `S` | spectral inversion | **undefined** — no routine located |
| `Δ` | Laplacian perturbation | **undefined** — no routine located |
| `Ξ` | quantum Fisher curvature | **undefined** — no computation located |
| `identity` | baseline / no-op arm | **implemented** |

Invariants: `Ω(O ψ)` has support. **`heat_trace(O)` and `curvature(psi)` do
not** — no definition was located for either. A theorem *named*
`curvature_convergence` in `lean4/ProvenAgd/AGDTheoremSeries.lean` is a name,
not a computation.

So: do not invent a missing operator definition. Do not let notation imply a
theorem. Do not present a conceptual analogy as an implemented transformation.
Record an unresolved operator specification as a **`derivation` gap**
(`L-OPR-3`, and `L-OPR-4` when a strong claim rests on it). A declared
`implemented` operator whose `source_ref` does not resolve is an error
(`L-OPR-1`, `L-OPR-2`).

## Three speedup quantities

```
S_i          = T_baseline,i / T_candidate,i
S_composed   = T_baseline,composition / T_new_composed
S_cumulative = T_original_baseline,end-to-end / T_final_composition,end-to-end
```

The last two compare over **different domains** and require their own measured
timings. **Never multiply isolated component ratios.** Two stages at 60→20 give
`S_1·S_2 = 9` while `S_composed = 120/40 = 3`. The validator rejects the pattern
(`L-SPD-1`, `L-SPD-2`).

`S_ideal = ΣTᵢ,baseline / ΣTᵢ,candidate,ideal` applies **only** to sequential
stages with compatible, non-overlapping baseline domains. State the assumptions
(`L-SPD-7`). Otherwise derive another model or declare it undefined. When the
ideal is defined and nonzero:

```
η_interaction = S_composed,measured / S_ideal
```

Diagnostic only. Not evidence for a mechanism, not a cumulative speedup. Full
reading in `references/composition-model.md`.

## Composition is a new object

`VERIFIED(P_i)` never implies `VERIFIED(P_i ∘ P_j)`. A composition needs its own
`run_id` — reusing a component's run id is an error (`L-CMP-3`) — its own gates,
its own evidence strength, and its own gaps.

## Statuses

`proposed → implemented → measured → reproduced → verified`, with `regressed`,
`blocked`, `superseded`, `quarantined`. Transitions outside
`STATUS_TRANSITIONS` are rejected (`L-ST-1`), so `measured → verified` without
an intervening `reproduced` fails.

A `verified` primitive may be reused downstream **only as evidence for its
original scope and conditions**. Applicability to the new workload is assessed
separately, via `applicability_conditions`, followed by a fresh run and fresh
gates.

## Negative evidence survives

A later success appends; it never erases. Once a `regressed`, `blocked`, or
`quarantined` status is observed, later records must still carry it in
`status_history` (`L-ST-2`). The ledger is hash-chained: `seq` strictly
increases and `prev_hash` links each record to the previous `record_hash`
(`L-SEQ-1`, `L-HASH-1`, `L-HASH-2`).

Contradictory runs are preserved and downgrade the claim (`L-CNT-1`), never
smoothed away.

## Gaps

Twelve classes, kept separately identifiable — see `references/gap-taxonomy.md`:

`dependency`, `equivalence_correctness`, `measurement`, `attribution`,
`scaling`, `hardware_mechanism`, `composition`, `formal_proof`, `vacuity`,
`provenance`, `reproducibility`, `derivation`.

Each carries `claim_impact`, observable evidence, a falsifiable
`closure_criterion`, an owner, and a responsible action. Closing a gap requires
`closed_by_evidence` (`L-GAP-2`). Closure creates a new event; it does not
delete the failure.

**Implication chains that do not hold:** exit 0 ⇏ correctness · correctness ⇏
speedup · one size ⇏ scaling · benchmark ⇏ hardware mechanism · component
`VERIFIED` ⇏ composition `VERIFIED` · Lean proof ⇏ the benchmark measures the
theorem's object.

## Vacuity

A validation is substantive only if it **could have failed**. Recomputed from
the record, not trusted from a `passed: true`:

- declared `parameter_roles` exist, and at least one parameter is non-trivial for
  its role (`n=1` as a dimension, `iters=0` as an iteration count → vacuous; a
  zero `tolerance` is *stricter*, so it stays substantive)
- the assertion is not trivially true
- `expected_source != "self"` — an expected value produced by the code under
  test proves nothing
- something was actually observed

`R-VAC-1` / `L-VAC-1` reject a batch where **every** check is vacuous, however
high the raw count. A claim above `CANDIDATE` resting only on vacuous
validations is rejected (`R-VAC-3`). Each vacuous check is listed individually
with its reason (`R-VAC-4`).

## Formal proof

Keep five things separate: the mathematical derivation, the formal theorem
statement, the kernel-checked proof, empirical correctness, and performance
measurement.

`formal/SSProofCore.lean` is checked with Lean 4 core and states the discipline
laws — the claim lattice, vacuity counting, non-multiplicativity, negative
evidence preservation, gap and conflict downgrades, composition freshness.
Evidence record: `formal/evidence/SSProofCore.formal.json`.

**Mathlib is not available in this repository** — `lean4/lake-manifest.json`
has an empty package list and `import Mathlib` fails. The file therefore depends
on Lean core only, and anything requiring Mathlib is a recorded `formal_proof`
gap rather than an assertion.

Never label an informal derivation formally proven. Never report a proof
without the exact theorem target, command, exit status, and toolchain
(`R-FRM-1`…`R-FRM-6`; `kernel_checked: false` is refused).

**A successful proof here upgrades nothing empirical.** It proves propositions
about a discrete lattice and about integers.

## Recursive improvement

At the start of every task:

1. Load relevant `verified` primitives **and their applicability constraints**.
2. Identify reusable implementations and measurements.
3. Derive the intended composition and state its assumptions.
4. Establish the new baseline, correctness checks, and measurement plan.
5. Run the candidate against the controlled baseline.
6. Compare predicted against observed. Record `η_interaction`.
7. Record regressions, dependencies, and every unresolved gap.
8. Append to the ledger. Never rewrite.
9. Promote claim status only after its required gates pass.
10. Convert each failure into a regression test and an enforceable rule.

Do not silently revise the meaning of an existing claim to accommodate a new
result. A claim that turns out wrong is closed by a new event, not by
redefinition.

## Safety and reproducibility

- Inspect existing artifacts before changing them.
- Preserve original benchmarks and their evaluators.
- **Never tune the measurement harness to manufacture a gain.**
- **Never modify reference outputs to pass a correctness gate.**
- Keep raw-result artifacts immutable and hashed (`R-PROV-6` verifies them).
- Record the exact command, working directory, environment, compiler flags, and
  software versions.
- Run benchmark comparisons sequentially when concurrency would distort them.
- Do not clear caches, delete artifacts, or do disk cleanup without
  authorization.
- **Never claim native execution from a static inspection, simulated test, or
  dry run** — `executed_kind != "native"` forbids every measured, reproduced,
  and verified status (`L-EXE-1`).
- Record platform-specific limitations. Do not silently substitute hardware.

## The adversarial battery

The validators are tested against twelve ways an optimization result goes
wrong. All fixtures are **synthetic** and labelled as such; none is evidence
about any device.

| # | Attack | Detected by |
|---|---|---|
| 1 | exits 0, no timing result | `R-TIME-1/2/3`, `L-EXE-3` |
| 2 | passes a gate while slower and using more memory | `R-TIME-7`, `R-MEM-1` |
| 3 | vacuous because a parameter is trivial | `R-VAC-1`, `R-VAC-4` |
| 4 | many validations, all vacuous | `R-VAC-1`, `L-VAC-1` |
| 5 | `S_i` multiplied to claim cumulative | `L-SPD-1`, `L-SPD-2` |
| 6 | verified components, no fresh composition run | `L-CMP-3` |
| 7 | hardware explanation, no mechanism evidence | `R-MECH-1` |
| 8 | missing run id or raw artifact | `R-PROV-1/2/5`, `L-EXE-2` |
| 9 | repeat run conflicts with the earlier result | `L-CNT-1` |
| 10 | Lean proof claimed with no target or execution | `R-FRM-1`…`6`, `L-FRM-4/5` |
| 11 | unresolved dependency behind a passing partial test | `R-DEP-1`, `L-DEP-1` |
| 12 | evidence status raised by hand | `L-CLM-2/3`, `R-CLM-2/3` |

`R-CLM-3` is the run-level counterpart of `L-CLM-3`: an evidence level above
`OBSERVED` may not be self-declared on a run record either. Both record types
carry `transition_records` and both enforce the chain.

Plus regression tests that a previously regressed status stays visible
(`L-ST-2`), that vacuous checks are excluded from substantive coverage
(`R-VAC-1`), and that the validator itself never fabricates evidence.

`tests/test_falsification_regressions.py` is different in kind: it pins five
real defects that an external adversarial pass found in this skill's own
validators after they were first written — a self-declared `VERIFIED`, a
non-object ledger line crashing the audit, a floor table that failed open on
an unrecognised claim kind, an empty ledger passing, and `--repo-root`
silently disabling a check. Each pairs the attack with a control, because a
gate that rejects everything is not a gate. If you change the validators, run
these first.

## Layout

```
SKILL.md
references/    evidence-model.md  composition-model.md  gap-taxonomy.md  normalization.md
schemas/       primitive.schema.json  evidence-record.schema.json  gap-record.schema.json
scripts/       ssproof.py  validate-run.py  validate-ledger.py
formal/        SSProofCore.lean  evidence/SSProofCore.formal.json
native/        run_native_verification.py  make_native_ledger.py
               artifacts/*.json (+ .sha256)   evidence/native_ledger.jsonl
tests/         test_ledger_validation.py  test_claim_strength.py  test_composition.py
               test_vacuity.py  test_provenance.py  test_falsification_regressions.py
               make_fixtures.py  _harness.py
               fixtures/ledgers/*.jsonl  fixtures/runs/*.json  fixtures/raw/*
```

`scripts/ssproof.py` is the shared library the two CLIs and the tests import.
`tests/make_fixtures.py` regenerates `tests/fixtures/` deterministically — it
reads no clock, so the fixtures are reproducible rather than merely present.

`native/` is the one **non-synthetic** evidence set in this skill: a real,
bounded baseline/candidate run on this machine, hashed, with its own ledger.
It is a demonstration of the workflow, not a result about any Speedup kernel.
Its scope is written into the record's `claim.scope` field and says so
explicitly. Everything under `tests/fixtures/` is synthetic and is labelled so
on every record.

Regenerate the fixtures and run everything:

```bash
python3 tests/make_fixtures.py
python3 -m unittest discover -s tests -t tests
```

Reproduce the native run (overwrites its own artifacts):

```bash
python3 native/run_native_verification.py --n 512 --blocks 32 --reps 15 --warmups 3
python3 native/make_native_ledger.py
python3 scripts/validate-ledger.py native/evidence/native_ledger.jsonl --repo-root ../../..
```

## Reading order

1. This file.
2. `references/evidence-model.md` — before making any claim.
3. `references/composition-model.md` — before composing anything.
4. `references/gap-taxonomy.md` — before declaring a result complete.
5. `references/normalization.md` — before trusting a ratio.