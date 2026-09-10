# Lean4 Workflow Isolation

This directory isolates the formal-verification lane from empirical runtime evidence.

## Authority boundary

Lean proves typed mathematical propositions: quotient equivalence, intertwining,
finite descent, reconstruction, observable preservation, and exact arithmetic
work identities. Wall-clock timing remains external evidence and must be bound
by provenance hashes rather than asserted as a theorem.

## Canonical proof chain

    Definition
      -> Operator
      -> Quotient
      -> Intertwining
      -> Finite descent
      -> Reconstruction
      -> Observable preservation
      -> Exact work theorem
      -> External runtime certificate
      -> Hash binding
      -> CI verification

## PCSS gate

Publication requires:

    I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L

where L is satisfied only by an actual successful Lean workflow run.

## Current scaffold

`../SpeedupExactInvariant.lean` contains the core descent and bidirectional
semantic interface. The next formalization unit should bind the concrete
pre-Lean certificate without converting a measured speedup into a formal
axiom.
