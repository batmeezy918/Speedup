/-
  ChronoFold lane — Progress–Target Coupling.

  Lean core only. No Mathlib. No unfinished-proof markers.
  Standalone: no sibling-module import (lean --root compiles each file).
-/

namespace SiliconSpeedup

set_option autoImplicit false

universe u v

variable {X : Type u} {Q : Type v}

def Intertwines (pi : X → Q) (T : X → X) (Tbar : Q → Q) : Prop :=
  ∀ x, pi (T x) = Tbar (pi x)

def Section (pi : X → Q) (sigma : Q → X) : Prop :=
  ∀ q, pi (sigma q) = q

def iter {α : Type u} (n : Nat) (f : α → α) (x : α) : α :=
  match n with
  | 0 => x
  | n + 1 => f (iter n f x)

theorem quotient_iterate
    (pi : X → Q) (T : X → X) (Tbar : Q → Q)
    (h : Intertwines pi T Tbar) :
    ∀ n x, pi (iter n T x) = iter n Tbar (pi x) := by
  intro n
  induction n with
  | zero =>
      intro x
      rfl
  | succ n ih =>
      intro x
      change pi (T (iter n T x)) = Tbar (iter n Tbar (pi x))
      rw [h, ih]

theorem reconstructed_iterate
    (pi : X → Q) (T : X → X) (Tbar : Q → Q) (sigma : Q → X)
    (hσ : Section pi sigma)
    (hT : Intertwines pi T Tbar) :
    ∀ n q, pi (iter n T (sigma q)) = iter n Tbar q := by
  intro n q
  rw [quotient_iterate pi T Tbar hT]
  exact congrArg (iter n Tbar) (hσ q)

def Reaches (Target : Q → Prop) (Tbar : Q → Q) (q : Q) : Prop :=
  ∃ n, Target (iter n Tbar q)

theorem progress_target_coupling
    (D : Q → Nat)
    (Target : Q → Prop)
    (Tbar : Q → Q)
    (h_zero : ∀ q, D q = 0 → Target q)
    (h_dec : ∀ q, ¬ Target q → D (Tbar q) < D q) :
    ∀ q, Reaches Target Tbar q := by
  intro q0
  have rec : ∀ n q, D q < n → Reaches Target Tbar q := by
    intro n
    induction n with
    | zero =>
        intro q hq
        cases hq
    | succ n ih =>
        intro q hq
        by_cases ht : Target q
        · exact ⟨0, by simpa [iter] using ht⟩
        · have hlt : D (Tbar q) < D q := h_dec q ht
          have hbound : D (Tbar q) < n :=
            Nat.lt_of_lt_of_le hlt (Nat.le_of_lt_succ hq)
          obtain ⟨k, hk⟩ := ih (Tbar q) hbound
          exact ⟨k + 1, by simpa [iter] using hk⟩
  exact rec (D q0 + 1) q0 (Nat.lt_succ_self _)

theorem zero_defect_is_target
    (D : Q → Nat)
    (Target : Q → Prop)
    (h_zero : ∀ q, D q = 0 → Target q) :
    ∀ q, D q = 0 → Target q := by
  intro q hq
  exact h_zero q hq

theorem literal_target_transfer
    (pi : X → Q)
    (T : X → X)
    (Tbar : Q → Q)
    (Target : Q → Prop)
    (hT : Intertwines pi T Tbar)
    (x : X)
    (hreach : Reaches Target Tbar (pi x)) :
    ∃ n, Target (pi (iter n T x)) := by
  obtain ⟨n, hn⟩ := hreach
  exact ⟨n, by
    rw [quotient_iterate pi T Tbar hT]
    exact hn
  ⟩

theorem reconstructed_target_transfer
    (pi : X → Q)
    (T : X → X)
    (Tbar : Q → Q)
    (sigma : Q → X)
    (Target : Q → Prop)
    (hσ : Section pi sigma)
    (hT : Intertwines pi T Tbar)
    (q : Q)
    (hreach : Reaches Target Tbar q) :
    ∃ n, Target (pi (iter n T (sigma q))) := by
  obtain ⟨n, hn⟩ := hreach
  exact ⟨n, by
    have hrec := reconstructed_iterate pi T Tbar sigma hσ hT n q
    rw [hrec]
    exact hn
  ⟩

theorem progress_target_literal_closure
    (pi : X → Q)
    (T : X → X)
    (Tbar : Q → Q)
    (sigma : Q → X)
    (D : Q → Nat)
    (Target : Q → Prop)
    (h_zero : ∀ q, D q = 0 → Target q)
    (h_dec : ∀ q, ¬ Target q → D (Tbar q) < D q)
    (hσ : Section pi sigma)
    (hT : Intertwines pi T Tbar) :
    ∀ q, ∃ n, Target (pi (iter n T (sigma q))) := by
  intro q
  apply reconstructed_target_transfer pi T Tbar sigma Target hσ hT q
  exact progress_target_coupling D Target Tbar h_zero h_dec q

end SiliconSpeedup
