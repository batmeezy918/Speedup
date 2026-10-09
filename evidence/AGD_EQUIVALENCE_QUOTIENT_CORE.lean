universe u v

namespace AGD.QuotientCore

/-- Finite iteration. -/
def iterate {X : Type u} (f : X → X) : Nat → X → X
  | 0, x => x
  | n + 1, x => iterate f n (f x)

/-- The one-step commuting square is sufficient to propagate projection
    equivalence through every finite trajectory. No domain-specific structure
    is assumed about S, Q, F, G, or p. -/
theorem iterate_projection_commutes
    {S : Type u} {Q : Type v}
    (full : S → S) (quotient : Q → Q) (project : S → Q)
    (commutes : ∀ x, project (full x) = quotient (project x)) :
    ∀ n x, project (iterate full n x) =
      iterate quotient n (project x) := by
  intro n
  induction n with
  | zero =>
      intro x
      rfl
  | succ n ih =>
      intro x
      calc
        project (iterate full n (full x)) =
            iterate quotient n (project (full x)) := ih (full x)
        _ = iterate quotient n (quotient (project x)) := by
          rw [commutes x]

/-- Exact reconstruction on the covered state space. The section law
    decode(project x)=x plus one-step commutation yields exact reconstruction
    after any finite number of quotient steps. -/
theorem iterate_reconstruction_exact
    {S : Type u} {Q : Type v}
    (full : S → S) (quotient : Q → Q)
    (project : S → Q) (decode : Q → S)
    (commutes : ∀ x, project (full x) = quotient (project x))
    (section_law : ∀ x, decode (project x) = x) :
    ∀ n x, decode (iterate quotient n (project x)) =
      iterate full n x := by
  intro n
  induction n with
  | zero =>
      intro x
      simpa [iterate] using section_law x
  | succ n ih =>
      intro x
      change decode (iterate quotient n (quotient (project x))) =
        iterate full n (full x)
      rw [← commutes x]
      exact ih (full x)

/-- Invariant propagation is an independent obligation: if I is preserved
    by the full transition, every finite iterate remains in I. -/
theorem iterate_preserves_invariant
    {S : Type u} (full : S → S) (I : S → Prop)
    (preserved : ∀ x, I x → I (full x)) :
    ∀ n x, I x → I (iterate full n x) := by
  intro n
  induction n with
  | zero =>
      intro x hx
      exact hx
  | succ n ih =>
      intro x hx
      exact ih (full x) (preserved x hx)

-- Quotient-core theorem inventory.
#print axioms iterate_projection_commutes
#print axioms iterate_reconstruction_exact
#print axioms iterate_preserves_invariant

end AGD.QuotientCore