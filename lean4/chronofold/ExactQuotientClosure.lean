namespace SiliconSpeedup

universe u v w

def iter {α : Type u} : Nat → (α → α) → α → α
  | 0, _, x => x
  | n + 1, f, x => f (iter n f x)

variable {X : Type u} {Q : Type v} {Y : Type w}
variable (π : X → Q) (T : X → X) (Tbar : Q → Q)
variable (σ : Q → X) (obs : X → Y) (obsBar : Q → Y)

def Intertwines : Prop := ∀ x, π (T x) = Tbar (π x)
def Section : Prop := ∀ q, π (σ q) = q
def ObservableFactor : Prop := ∀ x, obs x = obsBar (π x)

theorem quotient_iterate
    (h : Intertwines π T Tbar) :
    ∀ n x, π (iter n T x) = iter n Tbar (π x) := by
  intro n
  induction n with
  | zero => intro x; rfl
  | succ n ih =>
      intro x
      show π (T (iter n T x)) = Tbar (iter n Tbar (π x))
      rw [h, ih]

theorem reconstructed_iterate
    (hσ : Section π σ)
    (hT : Intertwines π T Tbar) :
    ∀ n q, π (iter n T (σ q)) = iter n Tbar q := by
  intro n q
  have hfwd := quotient_iterate π T Tbar hT n (σ q)
  have hsec := hσ q
  calc
    π (iter n T (σ q)) = iter n Tbar (π (σ q)) := hfwd
    _ = iter n Tbar q := by rw [hsec]

theorem observable_preserved_iterate
    (hT : Intertwines π T Tbar)
    (hobs : ObservableFactor π obs obsBar) :
    ∀ n x, obs (iter n T x) = obsBar (iter n Tbar (π x)) := by
  intro n x
  have hfwd := quotient_iterate π T Tbar hT n x
  calc
    obs (iter n T x) = obsBar (π (iter n T x)) := hobs (iter n T x)
    _ = obsBar (iter n Tbar (π x)) := by rw [hfwd]

theorem exact_quotient_closure
    (hT : Intertwines π T Tbar)
    (hσ : Section π σ)
    (hobs : ObservableFactor π obs obsBar) :
    (∀ n x, π (iter n T x) = iter n Tbar (π x)) ∧
    (∀ n q, π (iter n T (σ q)) = iter n Tbar q) ∧
    (∀ n x, obs (iter n T x) = obsBar (iter n Tbar (π x))) :=
  ⟨quotient_iterate π T Tbar hT,
    reconstructed_iterate π T Tbar σ hσ hT,
    observable_preserved_iterate π T Tbar obs obsBar hT hobs⟩

end SiliconSpeedup
