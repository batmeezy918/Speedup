universe u v

namespace AGD

/-- Concrete tensor-product state restricted to the block-constant invariant sector.
    A full state has outer index R and repeated identity-fiber index M. -/
def TensorState (R M : Type u) (α : Type v) := R → M → α

/-- The admissible invariant sector: every M-fiber is constant. -/
def InvariantState (R M : Type u) (α : Type v) [Inhabited M] :=
  {x : TensorState R M α // ∀ b i j, x b i = x b j}

variable {R M : Type u} {α : Type v} [Inhabited M]

/-- Projection chooses the canonical value of each repeated identity fiber. -/
def project (x : InvariantState R M α) : R → α :=
  fun b => x.1 b default

/-- Reconstruction replicates each quotient value across the identity fiber. -/
def reconstruct (q : R → α) : TensorState R M α :=
  fun b _ => q b

/-- The tensor-separable full operator: the same quotient transition acts
    independently on every identity-fiber coordinate. -/
def fullStep (red : (R → α) → (R → α)) (x : InvariantState R M α) :
    InvariantState R M α :=
  ⟨fun b _ => red (fun c => x.1 c default) b,
   by intro b i j; rfl⟩

/-- Quotient transition. -/
def quotientStep (red : (R → α) → (R → α)) : (R → α) → (R → α) :=
  fun q => red q

/-- Concrete Lean instantiation of exact reconstruction on the invariant orbit. -/
theorem exact_reconstruction_on_invariant_orbit
    (red : (R → α) → (R → α))
    (x : InvariantState R M α) :
    ∀ (b : R) (i : M),
      reconstruct (R := R) (M := M) (quotientStep red (project x)) b i =
        (fullStep red x).1 b i := by
  intro b i
  rfl

/-- Forward refinement / commutation: project after the full step equals
    the quotient step after project. -/
theorem forward_refinement
    (red : (R → α) → (R → α))
    (x : InvariantState R M α) :
    ∀ (b : R), project (fullStep red x) b = quotientStep red (project x) b := by
  intro b
  rfl

/-- Boundary reconstruction is exact for every quotient state. -/
theorem reconstruction_exact
    (q : R → α) :
    ∀ (b : R) (i : M), reconstruct (R := R) (M := M) q b i = q b := by
  intro b i
  rfl

/-- Finite iteration of an operator. The state is advanced once per recursive
    call; no projection or reconstruction is inserted between steps. -/
def iterate {X : Type u} (f : X → X) : Nat → X → X
  | 0, x => x
  | n + 1, x => iterate f n (f x)

/-- The projection commutes with every finite recursive trajectory. This is the
    explicit recursive closure of the one-step forward-refinement theorem. -/
theorem recursive_forward_refinement
    (red : (R → α) → (R → α)) :
    ∀ (n : Nat) (x : InvariantState R M α) (b : R),
      project (iterate (fullStep red) n x) b =
        iterate (quotientStep red) n (project x) b := by
  intro n
  induction n with
  | zero =>
      intro x b
      rfl
  | succ n ih =>
      intro x b
      change project (iterate (fullStep red) n (fullStep red x)) b =
        iterate (quotientStep red) n (project (fullStep red x)) b
      exact ih (fullStep red x) b

/-- One initial projection, recursive quotient execution, and one final
    reconstruction exactly reproduce every finite full-state trajectory on
    the declared block-constant invariant sector. -/
theorem recursive_exact_reconstruction
    (red : (R → α) → (R → α))
    (x : InvariantState R M α) :
    ∀ (n : Nat) (b : R) (i : M),
      reconstruct (R := R) (M := M)
        (iterate (quotientStep red) n (project x)) b i =
      (iterate (fullStep red) n x).1 b i := by
  intro n b i
  calc
    reconstruct (R := R) (M := M)
        (iterate (quotientStep red) n (project x)) b i =
        iterate (quotientStep red) n (project x) b := rfl
    _ = (iterate (fullStep red) n x).1 b default :=
      (recursive_forward_refinement red n x b).symm
    _ = (iterate (fullStep red) n x).1 b i :=
      (iterate (fullStep red) n x).2 b default i

#print axioms recursive_forward_refinement
#print axioms recursive_exact_reconstruction
#print axioms exact_reconstruction_on_invariant_orbit
#print axioms forward_refinement
#print axioms reconstruction_exact

end AGD
