# Composition model

`RECURSIVE_SPEEDUP_CONSTITUTION.md` sections 2, 4, 5, 6, 9, 13. This file is
the operational reading of those sections, with the arithmetic the validators
actually enforce.

## The rule

> `VERIFIED(P_i)` never implies `VERIFIED(P_i ∘ P_j)`.

A composition is a new object. It gets its own run, its own gates, its own
evidence strength, and its own gaps. Component verification is **necessary**
where the composition depends on it and **never sufficient**.

Enforced by `L-CMP-3`: a composition whose `native_run.run_id` also appears
among its components' run ids has no fresh composed run. Enforced by
`L-CMP-4`: a composition claim without a native composed run is rejected.

## Three quantities, kept distinct

```
S_i          = T_baseline,i / T_candidate,i
S_composed   = T_baseline,composition / T_new_composed
S_cumulative = T_original_baseline,end-to-end / T_final_composition,end-to-end
```

The last two are **ratios over different comparison domains** than `S_i`:

- `S_composed` compares the composed implementation against the baseline *of
  the composition*.
- `S_cumulative` compares the final composed implementation, end to end,
  against the *canonical original baseline* — the thing the user would have
  run before any of this work started.

They are usually different numbers, and neither is the product of the `S_i`.

**Never compute either by multiplying isolated component ratios.** Enforced by
`L-SPD-1` (the record declares `computation: "product_of_components"`) and
`L-SPD-2` (the value is present but `*_measured_direct` is not `true`).

Why, concretely. Two stages each taking 60 → 20:

```
S_1 = 60/20 = 3,  S_2 = 60/20 = 3,  product = 9
S_composed = (60+60) / (20+20) = 120/40 = 3
```

The multiplicative reference is 9 and the truth is 3. The product is not a
slightly wrong prediction; it is wrong by the same factor the pipeline already
amortises. `formal/SSProofCore.lean` states this as
`SSProof.composed_is_not_the_product`.

`S.individual_speedup([...])` exists in `scripts/ssproof.py` for exactly one
reason: so the validator can recognise the pattern and reject it. It refuses
non-positive and undefined ratios rather than returning a plausible number.

## The ideal model

For sequential stages with **compatible, non-overlapping baseline timing
domains**:

```
S_ideal = Σᵢ Tᵢ,baseline / Σᵢ Tᵢ,candidate,ideal
```

Assumptions, all of which must be stated in `S_ideal_assumptions` (`L-SPD-7`
warns when they are missing):

1. The stages run sequentially, not concurrently.
2. Each stage's baseline time is attributable to that stage alone.
3. The candidate's per-stage ideals are consistent with one another — the same
   work reaches every stage boundary.
4. No stage's cost depends on what another stage did (no shared cache
   pressure, no branch-predictor interference, no allocator coupling).

If the stages overlap, or have different input/output semantics, or occupy
different timing domains, **do not use this model**. Derive a suitable one, or
declare `S_ideal_model: "undefined"` and skip the interaction factor. There is
no penalty for an undefined ideal; there is a large penalty for a wrong one.

`S.ideal_sequential` raises `CompositionError` rather than returning a number
when the model does not apply (mismatched stage counts, non-positive sums, no
stages).

## The interaction factor

When the ideal is defined and nonzero:

```
η_interaction = S_composed,measured / S_ideal
```

With a shared baseline total this simplifies to `Σ T_c,ideal / Σ T_c,measured`
(Lean: `SSProof.eta_one_iff_measured_equals_ideal`). Reading:

| η | Reading |
|---|---|
| `> 1` | the composition beat the ideal model. Investigate whether the model was wrong before celebrating. |
| `= 1` | the measured composed run matched the model. |
| `< 1` | interference: added overhead, cache pressure, allocator behaviour, serialization, or double-counting. |

**What η is not.** It is a diagnostic ratio between a measurement and a model.
It is not independent evidence for the hardware mechanism, and it is not a
cumulative speedup. The model in the denominator was built on assumptions; if
those assumptions are wrong, η measures the error of the assumptions, not a
physical effect.

The repository's older `K_12 = S_composed / (S_1 · S_2)` vocabulary is the same
kind of statistic with a multiplicative reference in the denominator.
`S.multiplicative_reference` implements it for comparison purposes.

## Measuring cumulative performance

Directly, with controlled and equivalent conditions:

- The **same** baseline binary, commit, flags, and machine for both arms.
- **End-to-end** timing of the whole composed pipeline — not a sum of stage
  timings measured in different sessions.
- Interleaved A/B, warmup discarded, N ≥ 5 (`differential-benchmarking`).
- Retained: every raw sample, the repeat count, memory (baseline and candidate),
  input size, and the environment block.
- One timing domain per comparison. `R-TIME-5` rejects a ratio formed from arms
  whose declared `scope` differs.

If the end-to-end measurement is not possible, say so and leave `S_cumulative`
absent. An absent cumulative number is honest; a multiplied one is not.

## Attribution: who saved what

Record, per composition:

| Quantity | Meaning |
|---|---|
| `SavedWork_i` | work removed by primitive `i` |
| `Overlap_ij` | work claimed by both `i` and `j` (double-counted) |
| `NewOverhead_i` | work added by primitive `i` |
| `Interaction_ij` | residual not explained by the above — this is η's territory |
| `NetSavedWork` | `Σ SavedWork_i − Σ NewOverhead_i − Σ Overlap_ij` |

Attribution failure is the `attribution` gap class. A speedup with no
attribution is an unexplained observed effect, not a result.

## Applicability carry-forward

A `VERIFIED` primitive may be reused downstream only when its assumptions and
scope remain valid for the new scenario
(`RECURSIVE_SPEEDUP_CONSTITUTION.md` section 8):

```
Verified(P_i) + ValidInstantiation(P_i, W_{k+1}) -> CandidateComposed(P_i, W_{k+1})
```

followed by a **fresh native run and fresh gates**. `ValidInstantiation` is a
separate assessment, never implied by the first conjunct. An empty
`applicability_conditions` list means the primitive carries forward to nothing.

## Statuses

`proposed → implemented → measured → reproduced → verified`, with
`regressed`, `blocked`, `superseded`, `quarantined` reachable from most states.
The transition table is `STATUS_TRANSITIONS`; `L-ST-1` rejects anything else,
so `measured → verified` without an intervening `reproduced` is refused.

`verified → regressed` is legal and is the point: a regression discovered later
appends a new event. It never removes the earlier `verified` from
`status_history` (`L-ST-2`).