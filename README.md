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
