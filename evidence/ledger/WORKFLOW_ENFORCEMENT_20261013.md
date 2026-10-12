# Recursive Speedup Workflow Enforcement Audit — 2026-10-13

## Source snapshot

Repository: batmeezy918/Speedup. Audited main snapshot: 80034a0dbaa01cc1b7f74cd2146bd7eef724825a (2026-10-10T08:06:37Z).

## Current promotion state

The canonical recursive primitive ledger contains three records and zero VERIFIED primitives. Existing records are preserved unchanged.

- SIM2XR-SANDBOX-20260912 remains CANDIDATE with dependency, measurement, attribution, and formal gaps.
- MASQ-EOF-V2-20260912 remains CANDIDATE with measurement, attribution, scaling, and formal gaps.
- The AArch64 N=512 NEON certificate reports median 11.294605x and correctness/reproducibility/performance PASS, but forward quotient, reverse reconstruction, and invariant gates are false.
- The SIM2XR local certificate has its Lean gate false. The sandbox closure receipt explicitly states pcss_verified_primitive=false.

No historical ratio is promoted by this audit. No new native run was performed because connected Remote Desktop Commander devices were offline.

## Enforcement state

The v2 validator and adversarial tests are staged on the enforcement branch. Once integrated, CI will validate both the legacy ledger and v2 evidence requirements. New verified rows must hash-bind each passed stage, recompute speedups from raw timing inputs, preserve gap codes, require verified parents for compositions, and directly measure S_composed and S_cumulative in separate run batches. S_product is diagnostic only.

ClaimStrength <= EvidenceStrength. Composition verification is independent of component verification.
