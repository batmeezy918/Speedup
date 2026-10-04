# LIVE PROVEN-THEOREM LEDGER — 2026-10-03

## Counting law

A theorem is **GREEN / PROVEN** only when:
1. it is a Lean theorem/lemma/example declaration in an identified source file,
2. the source is included in a successful Lean kernel check/build,
3. no `sorry`/unresolved proof hole is used for that theorem,
4. the result is not merely an empirical certificate or README assertion.

A runtime benchmark, JSON receipt, or numerical certificate is **not** a Lean theorem.

## Current local Speedup scan

- Local source root: `/root/Speedup/lean4`
- Lean toolchain observed: Lean 4.29.0 / aarch64
- Literal declarations scanned in the current local Speedup Lean source set: **368**
- Current local source set includes the newly added `ToProve*.lean` files.
- A full `lake build` was started against that source set on 2026-10-03, but the remote execution session became unresponsive before a terminal exit status could be captured.
- Therefore **368 is NOT stamped as 368 GREEN** in this ledger yet. It is the declaration count pending the captured build result.

## Existing repository-level green corpus already recognized

The repository's prior theorem corpus records green Lean lanes for:
- `batmeezy918/chronofold` — CFPC Lean CI v2 green at `69a544fb6af1c9f747600e5938ce35cca39868ba`.
- `batmeezy918/OIC-Core-Calculus` — Lean verification CI green at `830f75c8fb01c23dfafbd3941f3a6420638a0906`.
- Speedup historical green kernels including GODSQuotientClosure, ChronoFoldProof, LinearQuotientProof, AGDGemmWork, AGDGemmProjection, AGDGemmReconstruction, AGDMaximallyTypedClaim, and PCSSCertificate.

This ledger intentionally does not convert those module names into a theorem count without re-running/counting their exact source declarations under the recorded green CI references.

## Important distinction

**Do not use the number 368 as a publication-grade theorem count.** The authoritative green count will be updated only after the build/CI exit status is captured and the declaration set is counted from the exact successful source snapshot.

## Next consolidation target

The definitive ledger should contain one row per kernel-checked theorem with:
`ID, repo, path, declaration, source commit, Lean version, CI/build evidence, dependencies, axioms, status, operational consequence`.
