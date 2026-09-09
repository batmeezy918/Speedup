namespace PCSSScaffold

def Quotient (State Observable : Type) := State → Observable

def ForwardEquivalent {State Observable : Type}
    (Q : Quotient State Observable) (a b : State) : Prop := Q a = Q b

def ReverseBound {State Observable Dist : Type}
    (Q : Quotient State Observable)
    (R : Observable → State)
    (d : State → State → Dist) (le : Dist → Dist → Prop) (ε : Dist) (s : State) : Prop :=
  le (d (R (Q s)) s) ε

def InvariantPreserved {State Invariant : Type}
    (Ω : State → Invariant) (a b : State) : Prop := Ω a = Ω b

theorem forward_equivalence_refl {State Observable : Type}
    (Q : Quotient State Observable) (s : State) : ForwardEquivalent Q s s :=
  rfl

end PCSSScaffold
