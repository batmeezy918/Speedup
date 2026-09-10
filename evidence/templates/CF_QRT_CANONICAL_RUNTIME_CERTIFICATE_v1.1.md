# CF-QRT/1.1 — Canonical Quotient Runtime Certificate

**Purpose:** bind a formally specified quotient to literal execution, measured runtime, reconstruction/replay, integrity hashes, and claim strength without conflating structural collapse with physical speedup.

## 0. Evidence law

`CLAIM_STRENGTH <= EVIDENCE_STRENGTH`

Publication gate:

`PUBLISH := I ∧ R ∧ Q ∧ Q^-1 ∧ Ω ∧ X ∧ L`

A runtime ratio is **not** accepted as a quotient speedup claim unless the same scenario passes the required semantic and integrity gates.

## 1. Canonical identity

- Certificate ID:
- Template version: `CF-QRT/1.1`
- Operator ID:
- Framework:
- Scenario ID:
- Scenario hash:
- Source commit:
- Source hash:
- Environment hash:
- Toolchain:
- Host/architecture:
- Timestamp:
- Seed:

## 2. Literal system

- State space: `S`
- Transition: `T : S ⇀ S`
- Observable: `A : S → Y`
- Invariant: `Ω : S → I`
- Budget / horizon: `B`
- Initial state: `s₀`

## 3. Constructive equivalence

- Equivalence relation: `~`
- Witness construction: `W(s,s')`
- Witness hash:
- Witness sample count:
- Witness result: `PASS | FAIL`

Required implication:

`W(s,s') ⇒ s ~ s'`

## 4. Quotient

`Q := S / ~`

`π : S → Q`

`R : Q → S` (representative/reconstruction)

`F(q) := π⁻¹(q)`

Measured:

- `N := |S|`
- `K := |Q|`
- Collapse factor: `ρ_Q := N/K`
- Eliminated fraction: `η_Q := 1-K/N`

## 5. Operator descent

Required:

` s ~ s' ⇒ T(s) ~ T(s') `

Define:

`T̄([s]) := [T(s)]`

- Descent checks:
- Result: `PASS | FAIL`

## 6. Observable preservation

Required:

` s ~ s' ⇒ A(s)=A(s') `

- Checks:
- Result: `PASS | FAIL`

## 7. Invariant preservation

Required:

`Ω̄(π(s)) = Ω(s)`

- Checks:
- Result: `PASS | FAIL`

## 8. Reverse reconstruction

Required:

`R(π(s)) ~ s`

and, where applicable,

`π(R(q)) = q`.

- Checks:
- Result: `PASS | FAIL`

## 9. Exact projected replay

Required:

`π(Tⁿ(s)) = T̄ⁿ(π(s))`

- Horizon:
- Replay checks:
- Replay hash:
- Result: `PASS | FAIL`

## 10. Semantic equality

Compare the literal and quotient executions on the declared observable:

`A_full = A_quotient`

- Full result:
- Quotient result:
- Result: `PASS | FAIL`

## 11. Computational work

- Full work `W_full`:
- Quotient work `W_Q`:
- Work reduction `ρ_W := W_full/W_Q`:
- Eliminated fraction:

**Do not label `ρ_W` as wall-clock speedup.**

## 12. Runtime

Measure identical workload semantics under the same declared environment.

- Full median runtime:
- Quotient median runtime:
- Full samples:
- Quotient samples:
- Warmups:
- Outlier rule:
- Full MAD:
- Quotient MAD:
- Full p95:
- Quotient p95:

Measured runtime speedup:

`S_runtime := t_full,median / t_quotient,median`

## 13. Overhead accounting

- Projection cost:
- Witness cost:
- Quotient construction cost:
- Representative/reduced execution cost:
- Reconstruction cost:
- Verification cost:
- Audit/bookkeeping cost:
- Total one-shot quotient cost:
- Total reusable-build cost:

If reusable:

`S_m := m C_full / (C_build + m C_run)`

Break-even:

`m_BE := ceil(C_build / (C_full-C_run))`, when `C_full > C_run`.

## 14. Integrity

- Raw execution artifact hash:
- Runtime log hash:
- Replay artifact hash:
- Scenario hash:
- Certificate hash:
- Git commit:

All hashes must be computed from canonical serialized artifacts.

## 15. Evidence gates

| Gate | Meaning | Result |
|---|---|---|
| I | Integrity/provenance | |
| R | Reproducibility | |
| Q | Forward quotient preservation | |
| Q^-1 | Reverse reconstruction | |
| Ω | Invariant preservation | |
| X | Measured performance | |
| L | Formal verification | |

Final gate:

`PUBLISH := I ∧ R ∧ Q ∧ Q^-1 ∧ Ω ∧ X ∧ L`

## 16. Evidence class

Choose exactly one:

- `VERIFIED`
- `FORMAL_PARTIAL`
- `STRONG_LOCAL`
- `CANDIDATE`
- `FAILED`
- `QUARANTINED`

## 17. Mandatory nonclaims

Record anything not established. In particular:

- A finite/local runtime result does not establish universal speedup.
- Quotient collapse does not by itself establish wall-clock speedup.
- A COCO result must use the official `cocoex` workload and declared metric.
- A benchmark win against CMA-ES alone does not establish SOTA.
- Formal proof of the quotient mechanism does not prove physical/silicon speedup.

## 18. Reuse contract

This template is the canonical schema for subsequent ChronoFold/Speedup quotient-runtime experiments. New benchmark instances must instantiate this schema rather than inventing a benchmark-specific certificate format.
