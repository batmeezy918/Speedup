namespace ChronoFold

universe u v w
variable {X : Type u} {Q : Type v} {Y : Type w}
variable (π : X → Q) (T : X → X) (Tbar : Q → Q)
variable (σ : Q → X) (obs : X → Y) (obsBar : Q → Y)

def Intertwines : Prop := ∀ x, π (T x) = Tbar (π x)
def Section : Prop := ∀ q, π (σ q) = q
def ObservablePreserved : Prop := ∀ x, obs x = obsBar (π x)

def iter : Nat → (X → X) → X → X
  | 0, _, x => x
  | n + 1, f, x => f (iter n f x)

theorem forward_iterate
    (h : Intertwines π T Tbar) :
    ∀ n x, π (iter n T x) = iter n Tbar (π x) := by
  intro n
  induction n with
  | zero => intro x; rfl
  | succ n ih =>
      intro x
      change π (T (iter n T x)) = Tbar (iter n Tbar (π x))
      rw [h, ih]

theorem reconstruction
    (hσ : Section π σ) : ∀ q, π (σ q) = q := hσ

theorem reconstructed_operator
    (hσ : Section π σ)
    (hT : Intertwines π T Tbar) :
    ∀ q, π (T (σ q)) = Tbar q := by
  intro q
  rw [hT, hσ]

theorem reconstructed_iterate
    (hσ : Section π σ)
    (hT : Intertwines π T Tbar) :
    ∀ n q, π (iter n T (σ q)) = iter n Tbar q := by
  rw [forward_iterate π T Tbar hT]
  exact hσ

theorem observable_iterate
    (hT : Intertwines π T Tbar)
    (hobs : ObservablePreserved π obs obsBar) :
    ∀ n x, obs (iter n T x) = obsBar (iter n Tbar (π x)) := by
  intro n x
  rw [hobs, forward_iterate π T Tbar hT]

def fullWork (m n k : Nat) : Nat := 2 * m * n * k
def quotientWork (r s k : Nat) : Nat := 2 * r * s * k

theorem exactWorkRatio16 :
    fullWork 1024 1024 1024 =
      16 * quotientWork 256 256 1024 := by
  decide

theorem strictWorkReduction :
    quotientWork 256 256 1024 <
      fullWork 1024 1024 1024 := by
  decide

end ChronoFold
