namespace AGDGemmProjection

universe u v w

def iterate {State : Type _} (T : State → State) : Nat → State → State
  | 0, x => x
  | n + 1, x => T (iterate T n x)

def Intertwines {State : Type u} {Reduced : Type v}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced) : Prop :=
  ∀ x, π (T x) = Tbar (π x)

def ObservablePreserved {State : Type u} {Reduced : Type v} {Obs : Type w}
    (π : State → Reduced) (observe : State → Obs) (observeReduced : Reduced → Obs) : Prop :=
  ∀ x, observe x = observeReduced (π x)

theorem projection_step {State : Type u} {Reduced : Type v}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced)
    (h : Intertwines T Tbar π) :
    ∀ x, π (T x) = Tbar (π x) :=
  h

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

theorem projection_closure {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (hI : Intertwines T Tbar π)
    (hO : ObservablePreserved π observe observeReduced) :
    (∀ x, π (T x) = Tbar (π x)) ∧
    (∀ n x, π (iterate T n x) = iterate Tbar n (π x)) ∧
    (∀ n x, observe (iterate T n x) = observeReduced (iterate Tbar n (π x))) :=
  ⟨projection_step T Tbar π hI,
   projection_iterate T Tbar π hI,
   quotient_observable_correct T Tbar π observe observeReduced hI hO⟩

end AGDGemmProjection
