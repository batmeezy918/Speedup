# Dual-Snapshot Recovery and Quotient Re-entry — Adversarial Pilot

Date: 2026-10-10. Device: Moto G Power 5G (2024), Android 16, AArch64 Debian PRoot. Workload inherited from the prior MUNI replay: `d=2048, m=64, r=32, steps=32`; injected quotient-state corruption at logical height 13.

## Scope and status

This is a live native C pilot layered over the existing AGD tensor-separable operators. It tests paired full-state/quotient snapshots, a deliberate mid-trajectory quotient-state perturbation, gap detection by snapshot-integrity check, full-state replay to the matching logical height, quotient reconstruction from recovered state, a one-step original-vs-quotient re-entry check, and continuation. It is not yet the complete automatic AGD formal-gap *new-quotient derivation* mechanism: this pilot repairs the existing quotient from recovered state, rather than deriving and proving a genuinely different quotient representation.

## Results

Five repeated native runs completed. Summary uses medians from `repeats.txt`:

- Original full-state reference: median 10.980 ms.
- Existing quotient path: median 0.171041 ms; median paired-run speedup about 64.20x.
- Dual-snapshot recovery path: median 10.509 ms; ratio of median original time to median recovery time about 1.045x.
- Dual-snapshot per-run speedup ratios: median 1.0606x; range 1.0109x–1.0749x.
- Maximum absolute error: 0 in all five runs.
- Injected gap detected; full-state snapshot integrity PASS; quotient-gap snapshot preserved PASS; checkpoint recovery PASS; re-entry check PASS; initial inadmissible negative control falls back.

The effective speedup is modest because the current pilot replays the original operator from the initial full-state snapshot through the recovery height. This is expected recovery overhead, not the quotient kernel's speed. Do not advertise the existing ~64x quotient-only ratio as the speedup of the new recovery path.

## Adversarial gates

- Existing adversarial suite: 23/23 PASS.
- Existing property fuzz: 20,000 cases, 0 violations; tolerance-positive probe exposed max error 3.15199e-7 at tolerance 9.99e-10 (315.514x tolerance). The existing policy correctly labels positive tolerance as approximate/unbounded; this remains an open mathematical budget issue.
- Existing MUNI admissible run: max absolute error 0, claim `FORMAL_PARTIAL_MEASURED_LOCAL`, `LEAN_ALGEBRAIC_MODEL_ONLY`.
- Existing MUNI inadmissible control: original fallback, max absolute error 0, claim `QUARANTINED_OPTIMISATION_NOT_APPLIED`.
- SHA-256 manifest validates all listed source, binary, run, adversarial, fuzz, and baseline receipts.

## What is demonstrated

1. A quotient-state perturbation at a later logical height can be detected.
2. Both snapshot records remain available and their integrity checks pass.
3. The authoritative full state can be recomputed from the preserved initial state to the matching checkpoint.
4. The quotient can be reconstructed from recovered full-state information and re-enter after a native one-step equivalence check.
5. The resulting final state matches the independent original trajectory exactly for this workload.

## What is not demonstrated yet

- The fault is a deliberately injected quotient-state corruption detected by an integrity check, not a naturally arising mathematical descent failure.
- The re-entry check is a runtime witness, not a Lean proof of C/IEEE-754/compiler refinement.
- No new quotient representation is synthesized from a formal-gap witness; the same quotient is reconstructed from full state.
- No proof artifact currently certifies the entire dual-snapshot recovery state machine.
- Timing is a local microbenchmark and needs repeated, alternating-order comparison against identical full-state and current-gated-MUNI paths under controlled thermal/load conditions.

## Next closure target

Extend the pilot so the perturbation violates a specific descent/invariant obligation, store that witness in the formal-gap ledger, derive a candidate expanded/refined quotient from the retrieved full-state residual, verify its domain and migration map, then inject another fault to prove fail-closed behavior. Include snapshot allocation, replay/recovery, derivation, verification, re-entry, and resumed execution in the end-to-end cost. Promote no candidate whose proof obligations are unresolved.
