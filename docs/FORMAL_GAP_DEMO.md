# Public-source formal-gap demonstration

## Purpose

This demo pairs a kernel-checkable bounded transport theorem with a separately labelled local performance witness. It does not claim a universal speedup theorem.

## Public source and provenance

- Repository: https://github.com/batmeezy918/Speedup
- Baseline source branch: `feat/silicon-speedup-proof-skill`
- Baseline commit for the performance report: `8f2789e308498fa496da074a99a95e3883e87c87`
- New proof source: `lean4/AGDTransportGapTheorem.lean`
- Build registration: `lean4/lakefile.lean`
- Lean toolchain: Lean 4.29.0

## Literal gap theorem

The concrete model defines a full operator A, projection P, lift S, and reduced operator B. Its transport defect is

`Gamma(x) = P(A(x)) - B(P(x))`.

For this model, the defect expands exactly to the two within-fiber differences:

`Gamma(x) = (x1 - x0, x3 - x2)`.

The kernel-checked theorem `gap_zero_iff_admissible` establishes that the defect is zero if and only if the state is pairwise-constant. `gap_zero_iff_transport_exact` identifies that same condition with exact forward transport. `lift_project_of_admissible` establishes exact reconstruction on the declared sector. `full_preserves_admissible` proves the sector is invariant. `iterated_transport` proves that projection of the full trajectory equals the reduced trajectory for every natural iteration count, when the initial state is admissible. A concrete inadmissible state witnesses a nonzero gap.

### Operational consequences

1. **Admission is load-bearing:** the exactness condition cannot be dropped; the counterexample has a nonzero defect.
2. **Fail closed:** only states admitted by the declared invariant may use this exact reduced path; otherwise reject or fall back.
3. **Exact reconstruction is domain-scoped:** it is proved on the admissible sector, not for arbitrary states.
4. **Iteration composes:** preservation of the invariant plus one-step transport gives exact projected trajectories for every finite step count.
5. **No performance theorem is smuggled in:** Lean proves the stated algebraic facts, not wall-clock speed, general operator eligibility, or silicon/compiler correspondence.

## Reproduce the formal check

From the repository root:

```sh
cd lean4
lean AGDTransportGapTheorem.lean
lake build
```

The file emits `#print axioms` output for its key theorems. The expected baseline Lean logical axioms include standard core items such as `propext`, `Classical.choice`, and `Quot.sound`; the acceptance check must reject `sorryAx` or any unreviewed extra axiom. A local direct Lean check succeeded for the theorem file before the iterated-transport extension; the final extension must be confirmed by CI/build before promotion to VERIFIED.

## Separately scoped performance witness

The public SOTA report at the pinned baseline commit records this configuration:

| Metric | Reported value |
|---|---:|
| State dimension d | 1,024 |
| Reduced dimension r | 32 |
| Iterations | 500 |
| Trials | 9 |
| Candidate median | 0.3894 ms |
| Structured-path median | 13.4935 ms |
| Candidate / structured ratio | 34.7x |
| A/A control ratio | 1.000 |
| Reported output error | 0 |
| Candidate fallbacks | 0 |

Source: `evidence/formal_gap_elevation_20261010/receipts/sota_report.txt` and the corresponding raw receipt files.

**Evidence status: local measured witness; not a release-grade verified claim.** This is one declared workload/configuration on one environment. The broader report has noisier A/A controls in other configurations, and the full PCSS closure certificate has historically quarantined missing provenance/replay/reconstruction dependencies. Do not advertise 34.7x as universal or multiply it by other ratios. Re-run the exact pinned workload with fresh hashes, independent replay, reconstruction and invariant checks, and a complete end-to-end timing path before upgrading the claim class.

## Publication gate

The release gate remains fail-closed. Promotion requires all evidence to be bound to the exact source and run:

`PUBLISH = I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L`

where integrity/provenance, reproducibility, forward transport, reverse reconstruction, invariant preservation, performance evidence, and Lean proof checks all pass. Missing evidence is OPEN, not PASS.
