import Mathlib

namespace LinearQuotient

universe u v w

variable {X : Type u} {Q : Type v} {Y : Type w}
variable (π : X → Q) (T : X → X) (Tbar : Q → Q)
variable (σ : Q → X) (obs : X → Y) (obsBar : Q → Y)

/-- Forward quotient closure / intertwining. -/
def Intertwines : Prop := ∀ x, π (T x) = Tbar (π x)

/-- Exact reconstruction section. -/
def Section : Prop := ∀ q, π (σ q) = q

/-- Acceptance-relevant observable factors through the quotient. -/
def ObservablePreserved : Prop := ∀ x, obs x = obsBar (π x)

/-- Finite iteration of an operator. -/
def iter : Nat → (X → X) → X → X
  | 0, f, x => x
  | n + 1, f, x => f (iter n f x)

/-- One-step intertwining recursively implies finite-step intertwining. -/
theorem finite_descent
    (h : Intertwines π T Tbar) :
    ∀ n x, π (iter n T x) = iter n Tbar (π x) := by
  intro n
  induction n with
  | zero =>
      intro x
      rfl
  | succ n ih =>
      intro x
      simp [iter, h, ih]

/-- Reconstruction is exact on quotient representatives. -/
theorem reconstruction
    (hσ : Section π σ) :
    ∀ q, π (σ q) = q := by
  exact hσ

/-- The reconstructed full operator agrees with reduced evolution. -/
theorem reconstructed_operator
    (hσ : Section π σ)
    (hT : Intertwines π T Tbar) :
    ∀ q, π (T (σ q)) = Tbar q := by
  intro q
  rw [hT, hσ]

/-- Observable preservation propagates through finite quotient trajectories. -/
theorem observable_iterate
    (hT : Intertwines π T Tbar)
    (hobs : ObservablePreserved π obs obsBar) :
    ∀ n x, obs (iter n T x) = obsBar (iter n Tbar (π x)) := by
  intro n x
  rw [hobs]
  rw [finite_descent π T Tbar hT n x]

/-- Scalar arithmetic-work model for a dense matrix multiplication. -/
def fullWork (m n k : Nat) : Nat := 2 * m * n * k

/-- Scalar arithmetic-work model for the reduced multiplication. -/
def quotientWork (r s k : Nat) : Nat := 2 * r * s * k

/-- Exact modeled work ratio for the canonical 1024 -> 256 reduction. -/
theorem exactWorkRatio16 :
    fullWork 1024 1024 1024 =
      16 * quotientWork 256 256 1024 := by
  norm_num [fullWork, quotientWork]

/-- Strict modeled work reduction. -/
theorem strictWorkReduction :
    quotientWork 256 256 1024 <
      fullWork 1024 1024 1024 := by
  norm_num [fullWork, quotientWork]

/-- Conditional runtime inequality under an abstract additive cost model. -/
theorem conditionalSpeedup
    (b p s ε : ℝ) (hb : 1 < b) :
    b * (p + s) > p + b * s + ε ↔
      (b - 1) * p > ε := by
  constructor <;> intro h <;> linarith

end LinearQuotient
