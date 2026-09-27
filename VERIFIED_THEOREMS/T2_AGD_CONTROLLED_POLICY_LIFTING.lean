/-
T2 — AGD Controlled Quotient Refinement and Safe Policy Lifting

This module formalizes the controlled quotient refinement layer for AGD systems.
It extends the existing uncontrolled intertwining framework to controlled transitions
and establishes policy lifting with closed-loop commutation properties.

Dependencies: Existing AGD intertwining (Intertwines π T T̄), section (π ∘ σ = id),
and iterate lemmas from ChronoFold/GODS/AGDGemmProjection.
-/

namespace Chronofold.AGD.T2

universe u v w

/-- Controlled transition on concrete state space: T : X → U → X -/
def ControlledStep (X : Type u) (U : Type w) := X → U → X

/-- Controlled transition on quotient state space: quotientStep : Q → U → Q -/
def QuotientStep (Q : Type v) (U : Type w) := Q → U → Q

/-- Controlled intertwining law: π (T x u) = quotientStep (π x) u -/
def ControlledIntertwines (T : ControlledStep X U) (Tbar : QuotientStep Q U) (π : X → Q) : Prop :=
  ∀ (x : X) (u : U), π (T x u) = Tbar (π x) u

/-- Policy on quotient space: κ̄ : Q → U -/
def QuotientPolicy (Q : Type v) (U : Type w) := Q → U

/-- Lifted policy on concrete space: κ x = κ̄ (π x) -/
def LiftedPolicy (κbar : QuotientPolicy Q U) (π : X → Q) : X → U :=
  fun x => κbar (π x)

/-- Policy well-definedness: if π x = π y then κ x = κ y -/
theorem policy_lift_respects_equiv
    (π : X → Q) (κbar : QuotientPolicy Q U) :
    ∀ (x y : X), π x = π y → LiftedPolicy κbar π x = LiftedPolicy κbar π y := by
  intro x y h
  simp only [LiftedPolicy]
  rw [h]

/-- Controlled iterate: iterates a controlled transition with a policy -/
def ControlledIterate (T : ControlledStep X U) (κ : X → U) : Nat → X → X
  | 0, x => x
  | n + 1, x => T (ControlledIterate T κ n x) (κ (ControlledIterate T κ n x))

/-- Quotient controlled iterate -/
def QuotientControlledIterate (Tbar : QuotientStep Q U) (κbar : QuotientPolicy Q U) : Nat → Q → Q
  | 0, q => q
  | n + 1, q => Tbar (QuotientControlledIterate Tbar κbar n q) (κbar (QuotientControlledIterate Tbar κbar n q))

/-- Closed-loop quotient commutation (single step):
    π (T x (κ x)) = quotientStep (π x) (κ̄ (π x)) -/
theorem closed_loop_quotient_commutes
    (T : ControlledStep X U) (Tbar : QuotientStep Q U) (π : X → Q)
    (κbar : QuotientPolicy Q U)
    (h : ControlledIntertwines T Tbar π) :
    ∀ (x : X), π (T x (LiftedPolicy κbar π x)) = Tbar (π x) (κbar (π x)) := by
  intro x
  have h₁ : π (T x (LiftedPolicy κbar π x)) = Tbar (π x) (LiftedPolicy κbar π x) := by
    apply h
  simp only [LiftedPolicy] at h₁ ⊢
  exact h₁

/-- Finite-horizon execution refinement:
    If xₖ₊₁ = T xₖ (κ xₖ) and qₖ₊₁ = quotientStep qₖ (κ̄ qₖ)
    then π xₖ = qₖ for all k -/
theorem closed_loop_trace_projection
    (T : ControlledStep X U) (Tbar : QuotientStep Q U) (π : X → Q)
    (κbar : QuotientPolicy Q U)
    (h : ControlledIntertwines T Tbar π) :
    ∀ (n : Nat) (x₀ : X),
      π (ControlledIterate T (LiftedPolicy κbar π) n x₀) =
        QuotientControlledIterate Tbar κbar n (π x₀) := by
  intro n
  induction n with
  | zero =>
    intro x₀
    simp [ControlledIterate, QuotientControlledIterate]
  | succ n ih =>
    intro x₀
    have h₁ := ih x₀
    have h₂ : π (T (ControlledIterate T (LiftedPolicy κbar π) n x₀) (LiftedPolicy κbar π (ControlledIterate T (LiftedPolicy κbar π) n x₀))) =
      Tbar (π (ControlledIterate T (LiftedPolicy κbar π) n x₀)) (κbar (π (ControlledIterate T (LiftedPolicy κbar π) n x₀))) := by
      apply h
    simp [ControlledIterate, QuotientControlledIterate, LiftedPolicy] at h₁ h₂ ⊢
    <;> simp_all

/-- Quotient invariant structure -/
structure QuotientInvariant (Tbar : QuotientStep Q U) (κbar : QuotientPolicy Q U) (P : Q → Prop) : Prop where
  base : ∀ q, P q → P (Tbar q (κbar q))

/-- Closed-loop invariant preservation over finite horizon:
    If quotient invariant holds on π x₀, then concrete invariant holds on all xₖ -/
theorem closed_loop_invariant_preservation
    (T : ControlledStep X U) (Tbar : QuotientStep Q U) (π : X → Q)
    (κbar : QuotientPolicy Q U)
    (h : ControlledIntertwines T Tbar π)
    (Pconcrete : X → Prop) (Pquotient : Q → Prop)
    (h_inv : ∀ x, Pquotient (π x) → Pconcrete x)
    (hq : QuotientInvariant Tbar κbar Pquotient)
    (x₀ : X) (hx₀ : Pquotient (π x₀)) :
    ∀ n, Pconcrete (ControlledIterate T (LiftedPolicy κbar π) n x₀) := by
  have h₁ : ∀ n, Pquotient (π (ControlledIterate T (LiftedPolicy κbar π) n x₀)) := by
    intro n
    induction n with
    | zero =>
      simp [ControlledIterate] at hx₀ ⊢
      exact hx₀
    | succ n ih =>
      have h₂ : π (T (ControlledIterate T (LiftedPolicy κbar π) n x₀) (LiftedPolicy κbar π (ControlledIterate T (LiftedPolicy κbar π) n x₀))) =
        Tbar (π (ControlledIterate T (LiftedPolicy κbar π) n x₀)) (κbar (π (ControlledIterate T (LiftedPolicy κbar π) n x₀))) := by
        apply h
      have h₃ : Pquotient (π (ControlledIterate T (LiftedPolicy κbar π) n x₀)) := ih
      have h₄ : Pquotient (Tbar (π (ControlledIterate T (LiftedPolicy κbar π) n x₀)) (κbar (π (ControlledIterate T (LiftedPolicy κbar π) n x₀)))) :=
        hq.base (π (ControlledIterate T (LiftedPolicy κbar π) n x₀)) h₃
      simp [ControlledIterate] at h₂ h₄ ⊢
      <;> simp_all
  intro n
  have h₂ : Pquotient (π (ControlledIterate T (LiftedPolicy κbar π) n x₀)) := h₁ n
  exact h_inv (ControlledIterate T (LiftedPolicy κbar π) n x₀) h₂

/-- Refinement relation between concrete and quotient closed-loop systems -/
structure ClosedLoopRefinement
    (T : ControlledStep X U) (Tbar : QuotientStep Q U) (π : X → Q)
    (κbar : QuotientPolicy Q U) : Prop where
  intertwines : ControlledIntertwines T Tbar π
  trace_projection : ∀ (n : Nat) (x₀ : X),
    π (ControlledIterate T (LiftedPolicy κbar π) n x₀) =
      QuotientControlledIterate Tbar κbar n (π x₀)

/-- The commuting square: π ∘ T_κ = T̄_κ̄ ∘ π -/
theorem commuting_square
    (T : ControlledStep X U) (Tbar : QuotientStep Q U) (π : X → Q)
    (κbar : QuotientPolicy Q U)
    (h : ControlledIntertwines T Tbar π) :
    (fun x => π (T x (LiftedPolicy κbar π x))) = (fun q => Tbar q (κbar q)) ∘ π := by
  funext x
  have h₁ : π (T x (LiftedPolicy κbar π x)) = Tbar (π x) (κbar (π x)) :=
    closed_loop_quotient_commutes T Tbar π κbar h x
  simp only [Function.comp_apply, LiftedPolicy] at h₁ ⊢
  <;> rw [h₁]
  <;> rfl

/-- Packaged T2 closure theorem -/
theorem T2_AGD_CONTROLLED_POLICY_LIFTING
    (T : ControlledStep X U) (Tbar : QuotientStep Q U) (π : X → Q)
    (κbar : QuotientPolicy Q U)
    (h : ControlledIntertwines T Tbar π) :
    (∀ (x : X), π (T x (LiftedPolicy κbar π x)) = Tbar (π x) (κbar (π x))) ∧
    (∀ (n : Nat) (x₀ : X),
      π (ControlledIterate T (LiftedPolicy κbar π) n x₀) =
        QuotientControlledIterate Tbar κbar n (π x₀)) ∧
    (∀ (x y : X), π x = π y → LiftedPolicy κbar π x = LiftedPolicy κbar π y) ∧
    (∀ (Pconcrete : X → Prop) (Pquotient : Q → Prop),
      (∀ x, Pquotient (π x) → Pconcrete x) →
      QuotientInvariant Tbar κbar Pquotient →
      (∀ (x₀ : X), Pquotient (π x₀) → ∀ n, Pconcrete (ControlledIterate T (LiftedPolicy κbar π) n x₀))) ∧
    (fun x => π (T x (LiftedPolicy κbar π x))) = (fun q => Tbar q (κbar q)) ∘ π := by
  refine' ⟨
    fun x => closed_loop_quotient_commutes T Tbar π κbar h x,
    closed_loop_trace_projection T Tbar π κbar h,
    policy_lift_respects_equiv π κbar,
    fun Pconcrete Pquotient h_inv hq x₀ hx₀ => closed_loop_invariant_preservation T Tbar π κbar h Pconcrete Pquotient h_inv hq x₀ hx₀,
    commuting_square T Tbar π κbar h⟩

end Chronofold.AGD.T2