import Mathlib

namespace SpeedupMathlib

universe u v w

variable {X : Type u} {Q : Type v} {Y : Type w}
variable (π : X → Q) (T : X → X) (Tbar : Q → Q)
variable (σ : Q → X) (obs : X → Y) (obsBar : Q → Y)

def Intertwines : Prop := ∀ x, π (T x) = Tbar (π x)
def Section : Prop := ∀ q, π (σ q) = q
def ObservablePreserved : Prop := ∀ x, obs x = obsBar (π x)

def Iterate {α : Type u} (f : α → α) : Nat → α → α
  | 0, x => x
  | n + 1, x => f (Iterate f n x)

theorem finite_descent (h : Intertwines π T Tbar) :
    ∀ n x, π (Iterate T n x) = Iterate Tbar n (π x) := by
  intro n
  induction n with
  | zero => intro x; rfl
  | succ n ih =>
      intro x
      simp [Iterate, h, ih]

theorem reconstructed_operator
    (hσ : Section π σ) (hT : Intertwines π T Tbar) :
    ∀ q, π (T (σ q)) = Tbar q := by
  intro q
  rw [hT, hσ]

theorem observable_iterate
    (hT : Intertwines π T Tbar)
    (hobs : ObservablePreserved π obs obsBar) :
    ∀ n x, obs (Iterate T n x) = obsBar (Iterate Tbar n (π x)) := by
  intro n x
  rw [hobs, finite_descent π T Tbar hT]

def fullWork (m n k : Nat) : Nat := 2 * m * n * k
def quotientWork (r s k : Nat) : Nat := 2 * r * s * k

theorem canonical_work_ratio :
    fullWork 1024 1024 1024 = 16 * quotientWork 256 256 1024 := by
  norm_num [fullWork, quotientWork]

theorem strict_work_reduction :
    quotientWork 256 256 1024 < fullWork 1024 1024 1024 := by
  norm_num [fullWork, quotientWork]

end SpeedupMathlib
