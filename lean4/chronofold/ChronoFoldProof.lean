import Mathlib

namespace ChronoFold

universe u v w

/-- Concrete state space and reduced quotient space. -/
variable {X : Type u} {Q : Type v} {Y : Type w}
variable (π : X → Q)
variable (T : X → X)
variable (Tbar : Q → Q)
variable (σ : Q → X)
variable (obs : X → Y)
variable (obsBar : Q → Y)

/-- The reduced operator is induced by the full operator through π. -/
def Intertwines : Prop :=
  ∀ x, π (T x) = Tbar (π x)

/-- σ is a right inverse / reconstruction section of π. -/
def Section : Prop :=
  ∀ q, π (σ q) = q

/-- Acceptance-relevant observables factor through the quotient. -/
def ObservablePreserved : Prop :=
  ∀ x, obs x = obsBar (π x)

/-- Finite trajectory operator. -/
def iter : Nat → (X → X) → X → X
  | 0,      f, x => x
  | n + 1,  f, x => f (iter n f x)

/-- Forward quotient closure propagates recursively through every finite step. -/
theorem forward_iterate
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

/-- The reconstructed reduced operator agrees with the quotient evolution. -/
theorem reconstructed_operator
    (hσ : Section π σ)
    (hT : Intertwines π T Tbar) :
    ∀ q, π (T (σ q)) = Tbar q := by
  intro q
  rw [hT, hσ]

/-- Finite reconstructed trajectories equal reduced trajectories. -/
theorem reconstructed_iterate
    (hσ : Section π σ)
    (hT : Intertwines π T Tbar) :
    ∀ n q, π (iter n T (σ q)) = iter n Tbar q := by
  intro n q
  rw [forward_iterate π T Tbar hT n (σ q)]
  rw [hσ]

/-- Observable preservation lifts the quotient equality to task semantics. -/
theorem observable_iterate
    (hσ : Section π σ)
    (hT : Intertwines π T Tbar)
    (hobs : ObservablePreserved π obs obsBar) :
    ∀ n x,
      obs (iter n T x) = obsBar (iter n Tbar (π x)) := by
  intro n x
  rw [hobs]
  rw [forward_iterate π T Tbar hT n x]

/-- Exact work model used by the pre-Lean evidence layer. -/
def fullWork (m n k : Nat) : Nat := 2 * m * n * k
def quotientWork (r s k : Nat) : Nat := 2 * r * s * k

theorem exactWorkRatio16 :
    fullWork 1024 1024 1024 =
      16 * quotientWork 256 256 1024 := by
  norm_num [fullWork, quotientWork]

 theorem strictWorkReduction :
    quotientWork 256 256 1024 <
      fullWork 1024 1024 1024 := by
  norm_num [fullWork, quotientWork]

/-- Conditional speedup law for the additive branch/prefix model. -/
theorem conditionalSpeedup
    (b p s ε : ℝ)
    (hb : 1 < b) :
    b * (p + s) > p + b * s + ε ↔
      (b - 1) * p > ε := by
  constructor <;> intro h <;> linarith

end ChronoFold
