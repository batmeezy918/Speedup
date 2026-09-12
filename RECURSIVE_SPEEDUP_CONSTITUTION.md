# Recursive Speedup Constitution v1.0

## Purpose

This document extends PCSS from isolated speedup claims to a chronologized, recursively composable evidence system.

## 1. Verified implementation primitive

A speedup becomes a **verified operational implementation primitive** only when its declared evidence gate passes. A primitive is not merely a timing/log artifact.

For primitive `P_i`, retain:

- immutable scenario identity
- source/input/environment hashes
- operator/derivation identity
- native execution trace
- raw measurements
- forward quotient/equivalence evidence
- reverse reconstruction evidence
- invariant evidence
- formal/Lean evidence when required
- attribution evidence
- hardware mechanism evidence when claimed
- normalized claim and evidence class
- chronology and parent primitives

`VERIFIED(P_i)` never implies `VERIFIED(P_i ∘ P_j)`.

## 2. Recursive state transition

Every new stage MUST consume prior verified primitives as explicit inputs:

`State_{k+1} = Compose(State_k, P_i)`

The composed implementation MUST be rerun as one implementation. Isolated speedup ratios MUST NOT be multiplied to produce the cumulative result.

## 3. Required derivation chain

Every stage follows:

`Requirement -> Derivation -> Operator -> Implementation -> Native Run -> Raw Result -> Reverse Derivation -> Gap Analysis -> Gap Closure -> Re-run -> Normalized Claim`

A missing stage is a gap, not an implicit pass.

## 4. Three speedup quantities

Record separately:

`S_i` = individual primitive speedup against its declared baseline.

`S_composed` = measured speedup of the newly composed implementation against the composition's declared baseline.

`S_cumulative` = measured speedup from the canonical original baseline to the fully composed implementation.

Never compute `S_composed` or `S_cumulative` by multiplying `S_i` values.

## 5. Four evidence values

Maintain separately:

- `S_ideal`: analytical/model prediction
- `S_measured`: native observed ratio
- `S_verified`: ratio whose required evidence gates are verified for the declared scope
- `S_cumulative`: native cumulative ratio of canonical baseline to composed implementation

A numerical value does not inherit another evidence class merely because it is numerically derived from verified values.

## 6. Composability factor

For two primitives with measured individual ratios `S_1`, `S_2`, define the observed interaction/composability factor:

`K_12 = S_composed / (S_1 * S_2)`

This is diagnostic only. It does not justify multiplying ratios.

Interpretation:

- `K > 1`: positive interaction/superadditivity relative to the multiplicative reference
- `K = 1`: multiplicative reference agrees with observation
- `K < 1`: interference/overhead/double-counting

The denominator is a comparison statistic, not a predicted cumulative speedup.

For the canonical cumulative baseline, report the direct measured ratio independently.

## 7. Gap taxonomy

Preserve, never erase:

- `NEGATIVE`
- `FAILED`
- `DEPENDENCY_GAP`
- `EQUIVALENCE_GAP`
- `MEASUREMENT_GAP`
- `ATTRIBUTION_GAP`
- `SCALING_GAP`
- `COMPOSITION_GAP`
- `HARDWARE_MECHANISM_GAP`
- `RECONSTRUCTION_GAP`
- `OBSERVABLE_COMPLETENESS_GAP`
- `FORMAL_GAP`

Closure of one gap does not delete historical failures; it creates a new evidence event.

## 8. Recursive reuse rule

A verified primitive may be reused downstream only when its assumptions and scope remain valid for the new scenario.

Required transition:

`Verified(P_i) + ValidInstantiation(P_i, W_{k+1}) -> CandidateComposed(P_i, W_{k+1})`

followed by a fresh native run and fresh evidence gates.

## 9. Attribution and double-counting

For every composition, identify which work is removed by each primitive and whether primitives act on overlapping work.

Do not attribute the same saved operation to multiple primitives.

Record:

`SavedWork_i`, `Overlap_ij`, `NewOverhead_i`, `Interaction_ij`, `NetSavedWork`.

## 10. Claim/evidence invariant

The global invariant is:

`ClaimStrength <= EvidenceStrength`

A composition receives its own evidence state. Component verification cannot automatically elevate the composition.

## 11. Chronology

Each primitive and composition MUST have:

`primitive_id`
`parent_ids`
`timestamp`
`scenario_hash`
`implementation_hash`
`run_hash`
`proof_hash`
`evidence_class`
`S_ideal`
`S_measured`
`S_verified`
`S_composed`
`S_cumulative`
`interaction_factor`
`gap_status`

## 12. Canonical recursive ledger

The canonical ledger is append-only. A later result supersedes a prior normalized claim only through a new evidence event with explicit parentage. Historical values remain preserved.

## 13. Publication gate

A composed implementation is publishable only when its own required gates pass. Component `VERIFIED` status is necessary where the composition depends on it, but never sufficient.

## 14. Mathematical representation

Where applicable, represent the proof-state evolution as:

`psi_{k+1} = O_k psi_k`

and a composed implementation as:

`O_total = O_n o ... o O_2 o O_1`.

Preserve declared invariants, including `Omega(O psi)` and any domain-specific invariant signatures.

## 15. Non-claims

This constitution does not assert universal speedup, universal optimality, automatic hardware acceleration, or general composability. These remain hypotheses until independently demonstrated.

## 16. Enforcement

The canonical machine-readable ledger is `evidence/ledger/RECURSIVE_PRIMITIVE_LEDGER.jsonl`.

`governor/recursive_speedup_ledger.py` is the fail-closed validator. It MUST reject:

- missing required chronology or evidence fields;
- `ClaimStrength > EvidenceStrength`;
- a `VERIFIED` record without `I`, `R`, `Q`, `Q_inverse`, `Omega`, `X`, and `L` all true;
- a `VERIFIED` record without native scenario/run identity;
- a non-verified record carrying `S_verified`;
- a verified composition without explicit parents, independently measured `S_composed`, independently measured `S_cumulative`, and an interaction factor;
- a composition whose parent primitive has not already appeared in the append-only ledger.

GitHub Actions workflow `.github/workflows/recursive-speedup-ledger.yml` runs this validator on ledger and governing-specification changes. CI is an independent verification event; it does not promote an artifact to `VERIFIED` by itself.

The ledger currently records no `VERIFIED` primitive. Existing empirical/formal artifacts remain at their declared lower evidence classes until their own complete PCSS gates close.
