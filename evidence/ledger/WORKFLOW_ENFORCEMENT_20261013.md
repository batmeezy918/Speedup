# Recursive Speedup Workflow Enforcement Audit — 2026-10-13

## Source snapshot and ledger state

Repository: batmeezy918/Speedup. Audited main snapshot: 80034a0dbaa01cc1b7f74cd2146bd7eef724825a (2026-10-10T08:06:37Z).

The canonical ledger now contains 14 records: 3 immutable v1 historical entries and 11 v2 evidence events. It contains zero VERIFIED primitives. Eight MUNI sweep points are candidate primitives, the m=1 control is preserved as a negative/control result, and two failed/attribution events retain the benchmark-instrumentation and headline-claim gaps.

## MUNI sweep — measured, not promoted

The native fiber sweep in muni-production/ops/bench/msweep.txt holds r=64 and steps=256, with 3 warm-ups and 9 interleaved trials of 3 repetitions. S_i was recomputed from the logged baseline_ms / quot_ms medians (the medians are printed to five decimal places); S_ideal=m is the operation-count prediction.

| m | d | S_ideal | recomputed S_i | status |
|---:|---:|---:|---:|---|
| 1 | 64 | 1 | 1.032889x | EMPIRICAL negative/control record; no replication gain established |
| 2 | 128 | 2 | 2.056500x | CANDIDATE |
| 4 | 256 | 4 | 4.034106x | CANDIDATE |
| 8 | 512 | 8 | 8.166454x | CANDIDATE |
| 16 | 1024 | 16 | 16.250270x | CANDIDATE |
| 32 | 2048 | 32 | 32.240205x | CANDIDATE |
| 64 | 4096 | 64 | 51.475274x | CANDIDATE; scaling gap retained |
| 128 | 8192 | 128 | 229.241665x | CANDIDATE; scaling and hardware-mechanism gaps retained |
| 256 | 16384 | 256 | 409.650304x | CANDIDATE; scaling and hardware-mechanism gaps retained |

These are direct ratios of the displayed baseline and quotient medians, not ratios multiplied from other runs. The evidence shows a strong bounded local quotient effect, but these rows remain unverified because the compiled libmuni.so is gitignored and absent from the tracked tree (dependency/integrity gap), the raw per-trial timings and a run-bound manifest are absent, and the operational report's m=64/128/256 table differs from the checked-in msweep.txt values. The source-to-binary correspondence is not machine-checked by Lean. Gates I and R therefore remain false; S_verified is null for every MUNI row.

## Failed evidence preserved

- MUNI-OPSBENCH-EXACTNESS-FIELD-FAIL-20261010: ops_bench.c computes a worst-error value, discards it, and prints the literal string 0 in the exactness column. The associated ops_bench.txt is not accepted as correctness evidence. This is stored as FAILED with MEASUREMENT_GAP and ATTRIBUTION_GAP, not silently treated as a pass.
- MUNI-D4096-M64-STEPS64-CLAIM-CONFLICT-20261010: the commit message reports 63.35x, while OPERATIONAL_CONSEQUENCES.md reports 63.8358x for the d=4096, m=64, steps=64 workload. Neither has a committed raw paired-timing receipt. Both claims are preserved as reported claims, with S_i and S_measured null. The m=64, steps=256 sweep point is a different workload and is not substituted for either.

## Existing records retained

- SIM2XR-SANDBOX-20260912 remains CANDIDATE with dependency, measurement, attribution, and formal gaps.
- MASQ-EOF-V2-20260912 remains CANDIDATE with measurement, attribution, scaling, and formal gaps.
- PCSS_NEON_GEMM_N512 has a measured 11.294605x median and correctness/reproducibility/performance marked PASS, but forward quotient, reverse reconstruction, and invariant gates are false.
- The SIM2XR local certificate has its Lean gate false; its sandbox closure receipt explicitly states pcss_verified_primitive=false.

## Enforcement decision

The v2 validator and adversarial tests are on the enforcement branch. They require hash-bound stage evidence, recompute S_i/S_composed/S_cumulative from raw timings, preserve recognized gap codes, require verified parents for verified compositions, and forbid multiplication from substituting for direct composed or cumulative runs. The tests cover valid composition, interaction-factor tampering, candidate-parent rejection, unmeasured candidates, negative/failed results, hash mismatches, and ClaimStrength <= EvidenceStrength.

No new native run was performed during this audit because the connected Remote Desktop Commander devices were offline. No existing ratio is promoted by the audit. The next promotion attempt requires a rebuilt/hash-matched native binary, a fresh receipt with raw paired timings and per-trial data, corrected exactness instrumentation, reconciliation of the conflicting sweep table, and fresh PCSS gates.

ClaimStrength <= EvidenceStrength. Composition verification remains independent of component verification.
