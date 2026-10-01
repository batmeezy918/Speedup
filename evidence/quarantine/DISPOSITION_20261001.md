# Quarantine disposition 2026-10-01

Executed against PCSS Article 9: PUBLISH <=> I and R and Q and Qinv and Omega and X and L.

Gate execution: scripts/execute_quarantine_gates.py wrote evidence/quarantine/EXECUTION_20261001.json.
published=0, executed=9. Missing gates were not invented.
Lean file lean4/PCSSQuarantine.lean proves each recorded gate vector is not publishable.
Core lane verify: LEAN4_CORE_ALL_PASS=1, source count 22, zero sorry.

| Id | Disposition | Blocking gates |
|---|---|---|
| cocoex-bbob-dim10-budget1000-20260910 | stays NEGATIVE | Q false, X false, L false on the run |
| sim2xr-invariant-sector-20260908 | STRONG_LOCAL, formal L discharged by lean4/PCSS_SIM2XR_20260908.lean | historical L false; identity stack proved; wall-clock not Lean-measured |
| s6-s7-s8-coco-equivalent-20260515 | stays QUARANTINED | unofficial suite, all gates false |
| vault-canonical-decider-20260531T112101Z | stays CANDIDATE | X not established |
| iqvf-coco | stays QUARANTINED | official suite empty or stale |
| snap-24-case-vs-cma | stays CANDIDATE | not a speedup pair |
| ledger 254.30x / 1024x / 80.9x / 209.23x | stays THEORETICAL_OR_SIMULATED | no PCSS bundle |
| graph500 reference and chronophole | stay MEASURED_BASELINE | no candidate win |
| PCSS_NEON_GEMM_N512_20261001T052954Z | CERTIFICATE_BOUND, not VERIFIED | Q, Qinv, Omega absent from the frozen record |

verified_count remains 0.
