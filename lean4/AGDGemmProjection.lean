/-
  AGD-GEMM Projection Correctness
  -------------------------------
  Abstract SIM2XR/AGD descent layer.

  Proves, from the intertwining hypothesis πT = T̄π:
    * one-step commutation
    * finite-iterate commutation πTⁿ = T̄ⁿπ
    * iterate additivity
    * well-definedness on fibres
    * uniqueness of the induced quotient operator when π is surjective
    * observable preservation across every finite execution

  Does NOT prove that any particular GEMM projection satisfies Intertwines.
  That remains a concrete obligation: actual_projection_intertwines.
-/

namespace AGDGemmProjection

universe u v w

/-- Explicit iteration, independent of Mathlib `Function.iterate`. -/
def iterate {State : Type _} (T : State → State) : Nat → State → State
  | 0,     x => x
  | n + 1, x => T (iterate T n x)

theorem iterate_zero {State : Type _} (T : State → State) (x : State) :
    iterate T 0 x = x :=
  rfl

theorem iterate_succ {State : Type _} (T : State → State) (n : Nat) (x : State) :
    iterate T (n + 1) x = T (iterate T n x) :=
  rfl

theorem iterate_one {State : Type _} (T : State → State) (x : State) :
    iterate T 1 x = T x :=
  rfl

theorem iterate_add {State : Type _} (T : State → State) :
    ∀ (m n : Nat) (x : State),
      iterate T (m + n) x = iterate T m (iterate T n x) := by
  intro m
  induction m with
  | zero =>
      intro n x
      rfl
  | succ m ih =>
      intro n x
      have hsucc : Nat.succ m + n = Nat.succ (m + n) := Nat.succ_add m n
      rw [hsucc]
      change T (iterate T (m + n) x) = T (iterate T m (iterate T n x))
      exact congrArg T (ih n x)

/-- Operational fibre: two states are equivalent when they share a class. -/
def Equivalent {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (x y : State) : Prop :=
  π x = π y

/-- One-step quotient intertwining: πT = T̄π. -/
def Intertwines {State : Type u} {Reduced : Type v}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced) : Prop :=
  ∀ x, π (T x) = Tbar (π x)

/-- The hidden operator is well-defined on fibres of π. -/
def WellDefined {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (T : State → State) : Prop :=
  ∀ x y, π x = π y → π (T x) = π (T y)

/-- Observable extracted from full and reduced states agrees. -/
def ObservablePreserved {State : Type u} {Reduced : Type v} {Obs : Type w}
    (π : State → Reduced) (observe : State → Obs) (observeReduced : Reduced → Obs) : Prop :=
  ∀ x, observe x = observeReduced (π x)

/-- Fibre-constancy of an observable. -/
def Respects {State : Type u} {Reduced : Type v} {Obs : Type w}
    (π : State → Reduced) (f : State → Obs) : Prop :=
  ∀ x y, π x = π y → f x = f y

theorem projection_step {State : Type u} {Reduced : Type v}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced)
    (h : Intertwines T Tbar π) :
    ∀ x, π (T x) = Tbar (π x) :=
  h

/-- Intertwining implies the hidden operator cannot leave its class. -/
theorem intertwines_wellDefined {State : Type u} {Reduced : Type v}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced)
    (h : Intertwines T Tbar π) :
    WellDefined π T := by
  intro x y hxy
  calc
    π (T x) = Tbar (π x) := h x
    _       = Tbar (π y) := by rw [hxy]
    _       = π (T y) := (h y).symm

/-- Observable preservation implies fibre-constancy of the full observable. -/
theorem observable_respects {State : Type u} {Reduced : Type v} {Obs : Type w}
    (π : State → Reduced) (observe : State → Obs) (observeReduced : Reduced → Obs)
    (h : ObservablePreserved π observe observeReduced) :
    Respects π observe := by
  intro x y hxy
  calc
    observe x = observeReduced (π x) := h x
    _         = observeReduced (π y) := by rw [hxy]
    _         = observe y := (h y).symm

/-- Projection commutes with every finite execution. -/
theorem projection_iterate {State : Type u} {Reduced : Type v}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced)
    (h : Intertwines T Tbar π) :
    ∀ n x, π (iterate T n x) = iterate Tbar n (π x) := by
  intro n
  induction n with
  | zero =>
      intro x
      rfl
  | succ n ih =>
      intro x
      calc
        π (iterate T (n + 1) x)
            = π (T (iterate T n x)) := rfl
        _   = Tbar (π (iterate T n x)) := h (iterate T n x)
        _   = Tbar (iterate Tbar n (π x)) := by rw [ih x]
        _   = iterate Tbar (n + 1) (π x) := rfl

/-- If π is surjective, at most one quotient operator intertwines with T. -/
theorem induced_operator_unique {State : Type u} {Reduced : Type v}
    (T : State → State) (Tbar Tbar' : Reduced → Reduced) (π : State → Reduced)
    (hπ : Function.Surjective π)
    (h1 : Intertwines T Tbar π)
    (h2 : Intertwines T Tbar' π) :
    Tbar = Tbar' := by
  funext q
  obtain ⟨x, hx⟩ := hπ q
  calc
    Tbar q = Tbar (π x) := by rw [hx]
    _      = π (T x) := (h1 x).symm
    _      = Tbar' (π x) := h2 x
    _      = Tbar' q := by rw [hx]

/-- Quotient execution preserves the same observable for every finite run. -/
theorem quotient_observable_correct {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (hI : Intertwines T Tbar π)
    (hO : ObservablePreserved π observe observeReduced) :
    ∀ n x, observe (iterate T n x) = observeReduced (iterate Tbar n (π x)) := by
  intro n x
  calc
    observe (iterate T n x)
        = observeReduced (π (iterate T n x)) := hO (iterate T n x)
    _   = observeReduced (iterate Tbar n (π x)) := by
            rw [projection_iterate T Tbar π hI n x]

/-- Packaged projection closure. -/
theorem projection_closure {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (hI : Intertwines T Tbar π)
    (hO : ObservablePreserved π observe observeReduced) :
    WellDefined π T ∧
    (∀ x, π (T x) = Tbar (π x)) ∧
    (∀ n x, π (iterate T n x) = iterate Tbar n (π x)) ∧
    (∀ n x, observe (iterate T n x) = observeReduced (iterate Tbar n (π x))) ∧
    Respects π observe :=
  ⟨intertwines_wellDefined T Tbar π hI,
   projection_step T Tbar π hI,
   projection_iterate T Tbar π hI,
   quotient_observable_correct T Tbar π observe observeReduced hI hO,
   observable_respects π observe observeReduced hO⟩

end AGDGemmProjection
