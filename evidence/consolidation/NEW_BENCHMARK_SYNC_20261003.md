# NEW BENCHMARK / SPEEDUP SYNC REGISTER — 2026-10-03

## Purpose

Central index for new benchmark evidence discovered locally and on GitHub. Evidence is synchronized by **claim strength**, not by raw speedup magnitude.

## 1. Fresh composition witness

GitHub PR: #14, branch `pcss/composition-20261003`, head `99f2102581c563c74f3185978c72be68f8e7b824`.

Recorded median ratio: **82.287116050x** over five fresh executions.

Mechanisms claimed:
- shared-prefix elimination
- 64-branch -> 8-class quotient/reconstruction
- AArch64 NEON FMA

Status: **STRONG_LOCAL_COMPOSITION_WITNESS / NOT VERIFIED**.

Review blockers recorded on the PR include:
- checked-in source hash mismatch against the receipt;
- reconstruction error reported as 0 without an independently constructed reconstruction artifact;
- numerical tolerance is displayed but not enforced by the executable;
- NEON is not performance-material enough to support the full three-mechanism attribution.

Therefore this result is synchronized as **evidence/quarantine**, not as `VERIFIED`.

## 2. Fresh elevated adversarial suite

GitHub PR: #15, branch `pcss/elevated-adversarial-20261003`, head `dcf5beb4e1112d6f8ab1362fea5429256fd8f868`.

Fresh ratios:
- balanced: **9.601571x**
- quotient pressure: **19.978818x**
- class fragmentation: **10.001282x**
- numerical-cancellation regime: **9.595680x**

The executable reported a global pass, but repository review identified:
- hardcoded/unbound Lean gate literals;
- quotient/reconstruction gates asserted without corresponding artifacts;
- cancellation regime does not actually cancel as claimed;
- replay hashes/binaries are not fully preserved;
- missing defensive checks in the C harness.

Status: **ADVERSARIAL LOCAL WITNESS / QUARANTINED FOR PROMOTION**.

## 3. Canonical verified speedups already in the repository

The canonical PCSS index previously recorded:
- network telemetry: **1.3824592615x — VERIFIED**
- AGD QG FHET N10 S3: **115.4264988764x — VERIFIED**
- canonical formal-partial result: **2.5429035653x — FORMAL_PARTIAL**

These remain distinct claims. They must not be multiplied together.

## 4. Earlier verified/strong local families

Keep separate by mechanism/workload/evidence:
- SIM2XR shared-prefix: ~17.54x strong local / reproduced witness
- SIM2XR invariant-sector: up to ~168.14x strong local witnesses
- AGD quotient: qualifying ratios up to ~6.2563x
- QRT-EJ: ~19.72135x local
- native NEON GEMM N=512: 11.294605x certificate-bound
- OMEGA/GF2: ~41.88–43.55x workload-specific
- composition witness: 82.287116050x, not verified
- elevated adversarial: 9.60–19.98x, not verified

Non-speedup ratios remain excluded from the runtime-speedup registry (e.g. slope ratios and objective/error ratios).

## Promotion law

No fresh benchmark is promoted to VERIFIED until its evidence satisfies the repository publication law:
`I && R && Q && Q^-1 && Omega && X && L`.

The two 2026-10-03 PRs are therefore synchronized as evidence, but not falsely promoted.
