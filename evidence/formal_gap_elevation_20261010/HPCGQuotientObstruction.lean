universe u

/-- A transition descends through a setoid quotient only if it preserves
    the equivalence relation. This is a necessary condition for quotienting. -/
def Respects {α : Type u} (T : α → α) (r : α → α → Prop) : Prop :=
  ∀ a b, r a b → r (T a) (T b)

theorem quotient_transition_requires_respects
    {α : Type u} (s : Setoid α) (T : α → α)
    (F : Quotient s → Quotient s)
    (spec : ∀ x, F (Quotient.mk s x) = Quotient.mk s (T x)) :
    Respects T s.r := by
  intro a b hab
  apply Quotient.exact
  calc
    Quotient.mk s (T a) = F (Quotient.mk s a) := (spec a).symm
    _ = F (Quotient.mk s b) := congrArg F (Quotient.sound hab)
    _ = Quotient.mk s (T b) := spec b

/-- A two-coordinate toy transition exposes the same obstruction pattern:
    the inputs are equivalent under coordinate swap, but their outputs are not.
    This is a logical witness, not a claim about HPCG's kernel. -/
def swapPair (x : Nat × Nat) : Nat × Nat := (x.2, x.1)
def toyTransition (x : Nat × Nat) : Nat × Nat := (x.1, x.1 + x.2)
def swapOrbitRelation (a b : Nat × Nat) : Prop := b = a ∨ b = swapPair a

theorem toy_transition_breaks_swap_invariance :
    ¬ Respects toyTransition swapOrbitRelation := by
  intro h
  have hab : swapOrbitRelation (0, 1) (1, 0) := by
    right
    rfl
  have hout := h (0, 1) (1, 0) hab
  have hbad : ¬ swapOrbitRelation (toyTransition (0, 1)) (toyTransition (1, 0)) := by
    simp [swapOrbitRelation, toyTransition, swapPair]
  exact hbad hout

#print axioms quotient_transition_requires_respects
#print axioms toy_transition_breaks_swap_invariance
