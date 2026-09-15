import ExactQuotientClosure

namespace SiliconSpeedup

universe u v

variable {X : Type u} {Q : Type v}

/-- A quotient-space target reached by an iterated transition. -/
def Reaches (Target : Q → Prop) (Tbar : Q → Q) (q : Q) : Prop :=
  ∃ n, Target (iter n Tbar q)

/-- Progress–Target Coupling: strict Nat-valued descent reaches a target. -/
theorem progress_target_coupling
    (D : Q → Nat)
    (Target : Q → Prop)
    (Tbar : Q → Q)
    (h_zero : ∀ q, D q = 0 → Target q)
    (h_dec : ∀ q, ¬ Target q → D (Tbar q) < D q) :
    ∀ q, Reaches Target Tbar q := by
  intro q
  induction h : D q using Nat.strong_induction_on with
  | h d ih =>
      by_cases ht : Target q
      · exact ⟨0, by simpa [iter] using ht⟩
      · have hlt : D (Tbar q) < d := by
          simpa [h] using h_dec q ht
        obtain ⟨n, hn⟩ := ih (D (Tbar q)) hlt (Tbar q) rfl
        exact ⟨n + 1, by simpa [iter] using hn⟩

theorem zero_defect_is_target
    (D : Q → Nat)
    (Target : Q → Prop)
    (h_zero : ∀ q, D q = 0 → Target q) :
    ∀ q, D q = 0 → Target q := by
  intro q hq
  exact h_zero q hq

theorem literal_target_transfer
    (π : X → Q)
    (T : X → X)
    (Tbar : Q → Q)
    (Target : Q → Prop)
    (hT : Intertwines π T Tbar)
    (x : X)
    (hreach : Reaches Target Tbar (π x)) :
    ∃ n, Target (π (iter n T x)) := by
  obtain ⟨n, hn⟩ := hreach
  exact ⟨n, by
    rw [quotient_iterate π T Tbar hT]
    exact hn
  ⟩

theorem reconstructed_target_transfer
    (π : X → Q)
    (T : X → X)
    (Tbar : Q → Q)
    (σ : Q → X)
    (Target : Q → Prop)
    (hσ : Section π σ)
    (hT : Intertwines π T Tbar)
    (q : Q)
    (hreach : Reaches Target Tbar q) :
    ∃ n, Target (π (iter n T (σ q))) := by
  obtain ⟨n, hn⟩ := hreach
  exact ⟨n, by
    have hrec := reconstructed_iterate π T Tbar σ hσ hT n q
    rw [hrec]
    exact hn
  ⟩

theorem progress_target_literal_closure
    (π : X → Q)
    (T : X → X)
    (Tbar : Q → Q)
    (σ : Q → X)
    (D : Q → Nat)
    (Target : Q → Prop)
    (h_zero : ∀ q, D q = 0 → Target q)
    (h_dec : ∀ q, ¬ Target q → D (Tbar q) < D q)
    (hσ : Section π σ)
    (hT : Intertwines π T Tbar) :
    ∀ q, ∃ n, Target (π (iter n T (σ q))) := by
  intro q
  apply reconstructed_target_transfer π T Tbar σ Target hσ hT q
  exact progress_target_coupling D Target Tbar h_zero h_dec q

end SiliconSpeedup
