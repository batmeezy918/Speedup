# Reusable Speedup Composition Templates

These templates encode the current proof-carrying performance model for reuse across experiments and implementations.

## Core rules

1. **Scalars are state-boundary aware.** A speedup vector is `P_i = (X_{i-1}, O_i, X_i, S_i, E_i, C_i)`.
2. **Multiplication is permitted for compatible vectors.** `S_product = product(S_i)` is a derived prediction/diagnostic, not the measured cumulative result.
3. **The composed run is authoritative.** Measure `S_composed = T_shared_baseline / T_actual_composed` directly.
4. **Interaction is explicit.** `K_comp = S_composed / S_product`.
5. **Recursive vectors must be non-overlapping.** If a downstream vector already includes an upstream operation, multiplication is rejected as double counting.
6. **Cumulative speedup is measured from the immutable canonical baseline.** Never multiply isolated ratios and call the product cumulative.
7. **Evidence cannot be upgraded by arithmetic.** `CLAIM_STRENGTH <= EVIDENCE_STRENGTH`.
8. **Failures and gaps remain part of the evidence record.** Unknown or failed gates quarantine the result.

## Files

- `speedup_vector_composition.yaml` — reusable experiment/composition manifest.
- `speedup_composition_metrics.yaml` — reusable metric and gate definitions.

## Current research status

The composition model is empirically demonstrated in bounded test campaigns. It is a candidate state-boundary/conditional interaction algebra. It is **not** a universal runtime law and does not automatically create `VERIFIED_OPERATIONAL_PRIMITIVE` status.

The governing repository constitution remains authoritative.
