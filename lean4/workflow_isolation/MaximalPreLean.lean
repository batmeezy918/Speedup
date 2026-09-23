namespace SpeedupWorkflow

universe u v w

variable {X : Type u} {Q : Type v} {Y : Type w}

structure QuotientModel (X : Type u) (Q : Type v) (Y : Type w) where
  π : X → Q
  T : X → X
  Tbar : Q → Q
  σ : Q → X
  obs : X → Y
  obsBar : Q → Y

class Intertwining {X : Type u} {Q : Type v} {Y : Type w}
    (M : QuotientModel X Q Y) : Prop where
  step : ∀ x, M.π (M.T x) = M.Tbar (M.π x)

class Reconstruction {X : Type u} {Q : Type v} {Y : Type w}
    (M : QuotientModel X Q Y) : Prop where
  section_ : ∀ q, M.π (M.σ q) = q

class Observable {X : Type u} {Q : Type v} {Y : Type w}
    (M : QuotientModel X Q Y) : Prop where
  preserved : ∀ x, M.obs x = M.obsBar (M.π x)

def Iterate {α : Type u} (f : α → α) : Nat → α → α
  | 0, x => x
  | n + 1, x => f (Iterate f n x)

theorem finite_descent
    {X : Type u} {Q : Type v} {Y : Type w}
    (M : QuotientModel X Q Y)
    [h : Intertwining M] :
    ∀ n x, M.π (Iterate M.T n x) = Iterate M.Tbar n (M.π x) := by
  intro n
  induction n with
  | zero => intro x; rfl
  | succ n ih =>
      intro x
      change M.π (M.T (Iterate M.T n x)) =
        M.Tbar (Iterate M.Tbar n (M.π x))
      rw [h.step, ih x]

theorem reconstruction
    {X : Type u} {Q : Type v} {Y : Type w}
    (M : QuotientModel X Q Y)
    [h : Reconstruction M] :
    ∀ q, M.π (M.σ q) = q := h.section_

theorem observable_preservation
    {X : Type u} {Q : Type v} {Y : Type w}
    (M : QuotientModel X Q Y)
    [h : Observable M] :
    ∀ x, M.obs x = M.obsBar (M.π x) := h.preserved

def fullWork (m n k : Nat) := 2 * m * n * k
def reducedWork (r s k : Nat) := 2 * r * s * k

theorem work_16x :
    fullWork 1024 1024 1024 =
      16 * reducedWork 256 256 1024 := by
  decide

theorem reduced_is_strictly_smaller :
    reducedWork 256 256 1024 <
      fullWork 1024 1024 1024 := by
  decide

structure RuntimeBinding where
  baselineNs : Nat
  candidateNs : Nat
  candidatePositive : 0 < candidateNs
  artifactHash : String
  sourceId : String
  reproducible : Bool

def RuntimeBindingValid (e : RuntimeBinding) : Prop :=
  e.artifactHash ≠ "" ∧ e.sourceId ≠ "" ∧ e.reproducible = true

end SpeedupWorkflow
