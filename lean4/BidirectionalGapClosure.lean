/-!
# Bidirectional Gap Closure — proof-governed problem derivation

Lean 4 core only; no Mathlib; no `sorry`; no `axiom` in this module.
This module coalesces already-proven Speedup quotient/reconstruction/work/PCSS
interfaces into one client-facing proof boundary. It proves consequences of
supplied formal witnesses; it does not certify a concrete external embedding or
external LLM client connection merely by naming one.
-/

import SpeedupLean

namespace BidirectionalGapClosure

open AGDGemmProjection
open AGDGemmReconstruction
open AGDGemmSpeedup
open AGDGemmWork
open PCSS

universe u v w

structure SemanticClosure
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs) where
  intertwines : Intertwines T Tbar π
  observable : ObservablePreserved π observe observeReduced
  section : Section π σ

theorem forward_gap_closure
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (hI : Intertwines T Tbar π)
    (hO : ObservablePreserved π observe observeReduced) :
    WellDefined π T ∧
    (∀ n x, π (iterate T n x) = iterate Tbar n (π x)) ∧
    (∀ n x, observe (iterate T n x) =
      observeReduced (iterate Tbar n (π x))) := by
  have h := projection_closure T Tbar π observe observeReduced hI hO
  exact ⟨h.1, h.2.2.1, h.2.2.2.1⟩

theorem reverse_gap_closure
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (hS : Section π σ)
    (hI : Intertwines T Tbar π) :
    (π ∘ σ = id) ∧
    Function.Injective σ ∧
    Function.Surjective π ∧
    (π ∘ T ∘ σ = Tbar) ∧
    (∀ n q, π (iterate T n (σ q)) = iterate Tbar n q) := by
  exact reconstruction_closure π σ T Tbar hS hI

theorem bidirectional_semantic_closure
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (H : SemanticClosure T Tbar π σ observe observeReduced) :
    (∀ n x, π (iterate T n x) = iterate Tbar n (π x)) ∧
    (∀ n x, observe (iterate T n x) =
      observeReduced (iterate Tbar n (π x))) ∧
    (π ∘ σ = id) ∧
    Function.Injective σ ∧
    Function.Surjective π ∧
    (π ∘ T ∘ σ = Tbar) := by
  have hf := forward_gap_closure T Tbar π observe observeReduced
    H.intertwines H.observable
  have hr := reverse_gap_closure T Tbar π σ H.section H.intertwines
  exact ⟨hf.2.1, hf.2.2, hr.1, hr.2.1, hr.2.2.1, hr.2.2.2.1⟩

theorem bidirectional_work_closure
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (H : SemanticClosure T Tbar π σ observe observeReduced) :
    (∀ n x, π (iterate T n x) = iterate Tbar n (π x)) ∧
    (∀ n x, observe (iterate T n x) =
      observeReduced (iterate Tbar n (π x))) ∧
    (π ∘ σ = id) ∧
    Function.Surjective π ∧
    WorkModelHolds := by
  have hs := bidirectional_semantic_closure T Tbar π σ observe observeReduced H
  exact ⟨hs.1, hs.2.1, hs.2.2.1, hs.2.2.2.2.1, work_model_closure⟩

theorem evidence_gate_closure
    (c : EvidenceCertificate)
    (h : publishable c) :
    c.integrity = true ∧
    c.reproducibility = true ∧
    c.quotientForward = true ∧
    c.reconstructionReverse = true ∧
    c.invariants = true ∧
    c.performance = true ∧
    c.lean = true :=
  publish_requires_all_gates c h

theorem verified_claim_requires_full_gate
    (c : EvidenceCertificate)
    (h : verifiedResult c) :
    publishable c := h

theorem runtime_boundary_preserved :
    measuredHundredths = 1596 ∧
    workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 ∧
    measuredHundredths ≠
      workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) * 100 := by
  exact ⟨rfl, canonical_workRatio,
    measured_hundredths_neq_work_ratio_times_100⟩

inductive DerivationResult
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    where
  | closed (closure : SemanticClosure T Tbar π σ observe observeReduced)
  | boundary (reason : String)

def closeProblem
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (h : SemanticClosure T Tbar π σ observe observeReduced) :
    DerivationResult T Tbar π σ observe observeReduced :=
  .closed h

theorem closeProblem_is_closed
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (h : SemanticClosure T Tbar π σ observe observeReduced) :
    ∃ closure,
      closeProblem T Tbar π σ observe observeReduced h = .closed closure :=
  ⟨h, rfl⟩

end BidirectionalGapClosure
