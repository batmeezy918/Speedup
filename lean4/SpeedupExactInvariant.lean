import Mathlib

namespace Speedup

/-- A quotient map from concrete states to represented states. -/
def Descends {S Q : Type} (π : S → Q) (T : S → S) (Tbar : Q → Q) : Prop :=
  ∀ s, π (T s) = Tbar (π s)

/-- One-step descent implies descent for every finite iterate. -/
theorem finite_descent
    {S Q : Type} (π : S → Q) (T : S → S) (Tbar : Q → Q)
    (h : Descends π T Tbar) :
    ∀ n s, π (Function.iterate T n s) = Function.iterate Tbar n (π s) := by
  intro n
  induction n with
  | zero =>
      intro s
      rfl
  | succ n ih =>
      intro s
      rw [Function.iterate_succ_apply]
      rw [Function.iterate_succ_apply]
      rw [h]
      exact congrArg Tbar (ih s)

/-- Bidirectional semantic witness: reconstruction on represented states and
forward intertwining on concrete states. -/
theorem bidirectional
    {S Q : Type} (π : S → Q) (r : Q → S)
    (T : S → S) (Tbar : Q → Q)
    (hreconstruct : ∀ q, π (r q) = q)
    (hdescend : Descends π T Tbar) :
    (∀ q, π (r q) = q) ∧ (∀ s, π (T s) = Tbar (π s)) := by
  exact ⟨hreconstruct, hdescend⟩

/-- Exact coordinate-sector construction. For a selected invariant sector,
projection after the dense operator equals application of the reduced
operator after projection. The implementation witness supplies this relation
for the concrete diagonal operator and coordinate-selection map. -/
theorem exact_sector_semantics
    {S Q : Type} (π : S → Q) (r : Q → S)
    (T : S → S) (Tbar : Q → Q)
    (hreconstruct : ∀ q, π (r q) = q)
    (hintertwine : ∀ s, π (T s) = Tbar (π s)) :
    (∀ n s, π (Function.iterate T n s) = Function.iterate Tbar n (π s)) ∧
      (∀ q, π (r q) = q) := by
  constructor
  · exact finite_descent π T Tbar hintertwine
  · exact hreconstruct

end Speedup
