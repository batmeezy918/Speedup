# PCSS Autonomous Audit Run

RUN_ID: 79eec983-c7fe-4d5b-be96-ac4200928fe7
Commit SHA observed: edfd02e6ffebc95f368e6093c6e7be8bab0feadc
Timestamp: 2026-11-26T08:26:04Z
Substrate: sandbox x86-64 (Debian, g++ 12.2.0)

## Audit Findings

All declared canonical paths exist:
- scripts/pcss_native_runner_v2.py
- publisher/strict_gate.py
- governor/coci_governor.py, formal_gap_isolator.py
- scripts/evidence_to_lean.py
- REMOTE_TERMUX_PROTOCOL.md
- merchant_assurance_benchmark_v2.py
- muni-production/muni/kernel.c, ops/bench/*
- benchmarks/qkxr_tower_native.cpp, qkxr_tower_native_v5.cpp
- lean4/AGDGemmSpeedup.lean, PCSS_NEON_N512.lean
- muni-production/proof/*.lean
- evidence/normalized/INDEX.md
- CI workflows listed

## Cross-Environment Witness (X gate)

Executed on independent substrate (this x86-64 sandbox, distinct from any prior aarch64 measurement):
- EXACTNESS: PASS (max_abs_error=0, bitwise equal, FNV-1a64 match)
- BENCHMARK: PASS (finite positive ~82.45x, informational only)
- FALLBACK: PASS
- CROSS_ENVIRONMENT=PASS

## Vacuity Gate (L gate)

Lean tooling unavailable in this environment. Existing vacuity_report.json reports VACUITY_PASS, but axes fields incomplete relative to current script. VACUITY_VERDICT=UNKNOWN (cannot re-execute).

## Gate Matrix (for this audit cycle)

No full PCSS candidate promotion attempted. No new measurements of AGD/NEON/SIM2XR beyond historical notes.

I: not applicable (no certificate)
R: not run
Q, Q^{-1}, Omega: not closed
X: PASS (for MUNI witness on this substrate)
L: UNKNOWN

Evidence class: AUDIT_ONLY / no promotion

No artifacts quarantined in this run. Historical items remain as previously classified (NEON not publishable, SIM2XR historical only).

## What remains unestablished

- Re-execution of AGD quotient on aarch64 to confirm 15.96x
- Full Lean vacuity re-run
- Any VERIFIED promotion
