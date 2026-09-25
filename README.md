# Proof-Carrying Speedup Scheduler (PCSS)

A proof-gated execution and publication system for computational speedup claims.

## Purpose

PCSS turns a proposed optimization into a reproducible evidence pipeline:

`scenario -> baseline/candidate -> capture -> quotient -> reverse reconstruction -> invariants -> performance -> Lean obligations -> publication gate`

The system is deliberately conservative. A fast benchmark is **not** a verified speedup claim by itself.

## Publication law

An artifact may enter `verified/` only when all required gates pass:

`PUBLISH := I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L`

Where:
- `I` = integrity/provenance/hash gate
- `R` = reproducibility gate
- `Q` = forward quotient preservation
- `Q⁻¹` = reverse reconstruction gate
- `Ω` = invariant preservation
- `X` = performance evidence gate
- `L` = Lean/formal verification gate

Any failed gate produces a **quarantined** result and cannot upgrade claim strength.

## Evidence classes

- `VERIFIED`: every mandatory gate passed and artifacts are immutable/hash-linked.
- `FORMAL_PARTIAL`: formal obligations are proven for a bounded/modelled domain, but empirical scope is incomplete.
- `STRONG_LOCAL`: reproducible local empirical evidence without complete equivalence/formal closure.
- `CANDIDATE`: promising result awaiting required gates.
- `FAILED`: a required test failed or contradicted an assumption.
- `QUARANTINED`: retained but explicitly excluded from verified claims.

## Core principle

Implementation identity is not required for acceptance-level equivalence **when** the declared observable quotient and invariants are formally shown to be preserved. This repository treats that as a proof obligation, not an automatic assumption.

## Non-claims

PCSS does not make hardware speedup, universal optimality, physical impossibility, or mathematical novelty claims merely because a benchmark reports them. Such claims require their own evidence and scope.

## Repository contract

`CONSTITUTION.md` is the governing contract. `PROTOCOL.md` defines execution and evidence transitions. `CLAIM_POLICY.md` controls claim strength. `verifier/` contains gates. `lean4/` contains generated/proof-bound obligations. `publisher/` enforces the final publication decision.

## Verified claims (chronicle)

Every entry in `verified/` was promoted by `publisher/strict_gate.py` (the single
publication authority) only after all seven gates passed, with every gate hash
bound to the real sha256 of its artifact file. Each certificate carries its
measured speedup, claim boundary, and Lean obligation hash.

| date | claim | speedup (measured) | dir |
|------|-------|--------------------|-----|
| 2026-09-23 | qmult02 (QMult02 oracle) | 2.5x | `verified/sim2xr/2026-09-23-qmult02/` |
| 2026-09-23 | aqge02 (AQ-GE02) | 9.78x | `verified/sim2xr/2026-09-23-aqge02/` |
| 2026-09-23 | sim2xr oracle | 15.14x | `verified/sim2xr/2026-09-23-sim2xr/` |
| 2026-09-23 | agd (AGD GEMM) | 5.02x | `verified/sim2xr/2026-09-23-agd/` |
| 2026-09-23 | qm02_aqge02 composed | 22.15x | `verified/sim2xr/2026-09-23-qm02_aqge02_composed/` |
| 2026-09-23 | qm02_aqge02_agd composed | 35.82x | `verified/sim2xr/2026-09-23-qm02_aqge02_agd_composed/` |
| 2026-09-25 | equivalence-faithful (gaussian) | 18.89x (max 459.76x) | `verified/sim2xr/2026-09-25-equivalence_faithful/` |
| 2026-09-25 | unfolding compiler v2 | 485.7x (max 2891x) | `verified/sim2xr/2026-09-25-unfold_bench2/` |

Closure-only certifications that passed their gates but measured no wall-clock
speedup (and so are **not** promoted to VERIFIED) are recorded in the ledger as
`publish_closure` entries: SIM2xr threadlock v4 (closure rate 1.0), nonlinear
eod v5 (120/120 gates PASS), SIC maximal-response probe (R1=0, reconstruction
~1e-16), and the Lean obligation lane (`lean4/SIM2xrEquivalenceClosure.lean`).

Honest negatives (claims that failed PCSS gates) are recorded in the ledger as
`refutation_claim`/`quarantine` entries rather than being deleted.
