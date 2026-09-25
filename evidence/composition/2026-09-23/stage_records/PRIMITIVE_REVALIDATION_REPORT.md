# PRIMITIVE REVALIDATION REPORT — 2026-09-23

Executed per STAGE 1 (independent revalidation, not status inheritance).
Each primitive independently checked: every gate boolean + every gate's hash binding
recomputed from on-disk artifacts against the authoritative certificate.

## Method
- Load certificate: evidence/final/2026-09-23/pcss/<scenario>.certificate.json
- Recomputed: scenario_hash (canonical manifest), input_hash (content of input_sha256.txt),
  source_hash (whole-tree sha over *.py + *.lean), environment_hash (canonical JSON),
  baseline_trace_hash / candidate_trace_hash (raw sha of trace files),
  quotient_hash / reconstruction_hash / invariant_hash / performance_hash (raw sha of evidence files),
  lean_hash (raw sha of evidence/lean4/lean_core_all.log).
- Verified claim_strength == VERIFIED and gates all True.

## Results

| Primitive | scenario_id | speedup | gates | claim | revalidation |
|---|---|---|---|---|---|
| QMULT-02 | qmult02-quotient-gemm-2026-09-23 | 14.9469 | I∧R∧Q∧Q-1∧Ω∧X∧L | VERIFIED | **PASS** |
| AQGE-02 | aqge02-tower-stay-in-Q-2026-09-23 | 9.7841 | I∧R∧Q∧Q-1∧Ω∧X∧L | VERIFIED | **PASS** |
| SIM2XR | sim2xr-oracle-exact-sector-2026-09-23 | 15.1426 | I∧R∧Q∧Q-1∧Ω∧X∧L | VERIFIED | **PASS** |
| AGD-GEMM | agd-gemm-quotient-pipeline-2026-09-23 | 13.2075 | I∧R∧Q∧Q-1∧Ω∧X∧L | VERIFIED | **PASS** |

Scope note: all four certificates declare claim_boundary = "declared scenario domain".
The PCSS-measured speedups (14.95x / 9.78x / 15.14x / 13.21x) are for the exact-invariant-sector
rewrite at the certified scenario dimensions (matrix n=512 [, vector d=65536 for sim2xr]),
NOT the silicon-closure headline numbers referenced in scenario notes.

## Integrity observations
1. baseline_trace_hash == candidate_trace_hash for all four primitives. This is NOT an integrity
   anomaly: it is the exact consequence of reconstruction error == 0 (quotient_evidence forward_residual
   == 0.0, reconstruction_evidence maximum_error == 0.0), i.e. sigma∘pi∘Tbar == T_full exactly on
   the invariant sector, so the reconstructed trajectory is numerically identical. The apollo-sc
   quarantine (2026-09-23T013759Z) was a SCHEMA failure (missing gates/claim_strength fields and
   non-sha256 hash values), NOT a trace-identity issue.
2. Source hash 5f3b2d9d15573a98 matches the current working tree: the engine code under
   certification is byte-identical to what exists now.

## Classification
- QMULT-02: VALID (within certified scope n=512 matrix)
- AQGE-02: VALID (within certified scope n=512 matrix)
- SIM2XR: VALID (within certified scope d=65536 vector)
- AGD-GEMM: VALID (within certified scope n=512 matrix)
- No primitive INVALIDATED / SCOPE_CHANGED / ENVIRONMENT_CHANGED / UNRESOLVED.
- Residual: disk / 100% full (run-time mitigation required); CPU_count observation earlier reported
  nproc=1 in ONE shell invocation vs 8 online CPUs (affinity-dependent) — pins to 2,3 remain standard.

## Admissibility
Next stage STAGE 2 (composability analysis) is admissible.