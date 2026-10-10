# Normalization

How raw run output becomes a normalized claim, and where that transformation is
allowed to stop. Implemented in `scripts/ssproof.py`:
`median`, `mad`, `arm_stats`, `speedup`, `ideal_sequential`,
`interaction_factor`, `scopes_compatible`.

## The contract

Raw samples in, one normalized claim out, with every intermediate recorded.
Nothing is imputed. A missing input produces a missing output, never a default.

## Steps

### 1. Discard warmup, and say how many

```python
{"warmup_discarded": 2, "samples": [118.0, 119.0, 120.0, 121.0, 122.0]}
```

The first iterations pay for page faults, JIT, cache population, and frequency
ramp. `MIN_SAMPLES = 5` is enforced after the discard; fewer than five post-warmup
samples cannot support a `REPRODUCED` evidence level (`R-TIME-4`).

### 2. Require a positive timing domain

`arm_stats` computes `has_timing` from the count of strictly positive samples.
An arm of all zeros has `n = 5` and `has_timing = False`. It is a timing
absence, not a fast measurement. `R-TIME-2` rejects it.

This distinction matters: a benchmark that divides by zero, or that times an
empty workload, reports something that looks like a number and is not one.

### 3. Aggregate with a single declared rule

`aggregation` is one of `median`, `mean`, `min`, `p95`, `p99`, and it must be
the **same** for baseline and candidate. Median by default.

`speedup` and `ideal_sequential` both require strictly positive arguments and
raise `CompositionError` otherwise. `S.speedup(0.0, 1.0)` is an error, not
`0.0`.

### 4. Report median and spread, never one number

`arm_stats` returns `median`, `mad`, `min`, `max`, `n`, `n_positive`. MAD
(`mad`) travels with the median because an effect smaller than the spread is
not an effect.

### 5. Cross-check the declared ratio against the raw samples

The ledger validator recomputes `S_i` from the stored samples and compares it
to the declared value (`L-SPD-9`). A record that says `S_i = 3.0` while its
samples give `2.975` fails. Declared values that disagree with their own
artifacts are not results.

### 6. Form the ratio within one timing domain

`scopes_compatible` requires every non-empty declared `scope` to agree.
Comparing a `stage-2 only` baseline against an `end-to-end` candidate is a
category error, and `R-TIME-5` rejects it.

### 7. Compose only from measured totals

`S_composed` is formed from the composition's own baseline/candidate arms.
`S_cumulative` from the canonical original baseline and the final composed
implementation, both end to end. Neither is derived from component ratios. See
`composition-model.md`.

## Normalized claim shape

```json
{
  "run_id": "2026-10-08-AGD-PI-0001",
  "metric": "wall_time",
  "unit": "ms",
  "scope": "end-to-end",
  "baseline":  {"median": 120.5, "mad": 1.0, "min": 119.0, "max": 122.0,
                "n": 5, "memory_bytes": 2048},
  "candidate": {"median": 40.5,  "mad": 1.0, "min": 39.0,  "max": 42.0,
                "n": 5, "memory_bytes": 1024},
  "S_i": 2.975,
  "aggregation": "median",
  "interleaved": true,
  "warmup_discarded": 2,
  "environment": {"platform": "...", "cpu": "...", "governor": "...", "versions": {"...": "..."}},
  "claim": {
    "strength": "STRONG_LOCAL",
    "kind": "performance",
    "scope": "workload W, input size 4096x4096, protocol P, machine M",
    "statement": "..."
  }
}
```

Note `S_i = 2.975`, not `3.0`. The normalized number is the one the data
supports. Rounding it up to make it match a prediction is exactly the
`L-SPD-9` failure mode in reverse.

## What normalization never does

- **Never** fabricate a sample for a missing arm.
- **Never** mix units. `unit` is declared once per record; `ns` and `ms` are
  not combined.
- **Never** mix scopes inside one ratio.
- **Never** impute a missing median from the other arm.
- **Never** discard an inconvenient sample. Outliers get reported (`max`/`min`),
  not deleted.
- **Never** reuse a normalized number from another record's samples. Each record
  carries its own artifacts with hashes.
- **Never** let a favorable aggregate hide an unfavorable `memory_bytes` or a
  failing correctness check. Those are separate fields with separate gates.

## Interleaving and the noise floor

Normalization assumes the two arms were measured under comparable conditions.
The recorded facts that make that assumption checkable:

| Field | What it establishes |
|---|---|
| `interleaved` | A and B were alternated, so thermal drift is common-mode |
| `n` (≥ 5) | a spread exists at all |
| `mad` | the size of that spread |
| `environment` | same machine, same governor, same toolchain |
| `input_size` | same input domain |

If `interleaved` is `false` or `n < 5`, the honest verdict is
`INCONCLUSIVE`, not a smaller number. See the `differential-benchmarking`
skill for the full protocol including noise-floor estimation.

## Determinism

`S.sha256_json` and `S.canonical_bytes` follow `publisher/evidence_lib.py`:
`sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False`, trailing
newline. Same object → same hash on any machine. This is what makes the ledger
hash chain and the artifact hashes verifiable by someone who was not present.

Fixture regeneration is deterministic for the same reason — `tests/make_fixtures.py`
takes no timestamps from the clock — so `tests/fixtures/` is reproducible rather
than merely present.