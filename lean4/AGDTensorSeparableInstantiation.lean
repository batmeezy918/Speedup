import AGDDescentCore

/-!
AGD tensor-separable quotient instantiation (Lean 4 core lane).

The full state has r coordinates and m repeated fibers. The operator applies the
same reduced map independently to each fiber: fullStep U x i j = U (x · j) i.
The admissible sector is constant across the fiber index. This proves the exact
algebraic model, not the C floating-point implementation.
-/

namespace AGDTensorSeparable

variable {r m : Nat}
abbrev State (r m : Nat) := Fin r → Fin m → Rat

def lift (m : Nat) (q : Fin r → Rat) : State r m := fun i _ => q i

def project (j0 : Fin m) (x : State r m) : Fin r → Rat := fun i => x i j0

def BlockConstant (x : State r m) : Prop :=
  ∀ i j k, x i j = x i k

def fullStep (U : (Fin r → Rat) → Fin r → Rat) (x : State r m) : State r m :=
  fun i j => U (fun k => x k j) i

def quotientStep (U : (Fin r → Rat) → Fin r → Rat) (q : Fin r → Rat) : Fin r → Rat :=
  U q

theorem lift_project_of_blockConstant (j0 : Fin m) (x : State r m)
    (h : BlockConstant x) : lift m (project j0 x) = x := by
  funext i j
  exact h i j0 j

theorem fullStep_lift (U : (Fin r → Rat) → Fin r → Rat) (q : Fin r → Rat) :
    fullStep U (lift m q) = lift m (quotientStep U q) := by
  rfl

theorem project_fullStep (U : (Fin r → Rat) → Fin r → Rat)
    (j0 : Fin m) (x : State r m) :
    project j0 (fullStep U x) = quotientStep U (project j0 x) := by
  rfl

theorem blockConstant_fullStep (U : (Fin r → Rat) → Fin r → Rat)
    (x : State r m) (h : BlockConstant x) :
    BlockConstant (fullStep U x) := by
  intro i j k
  change U (fun a => x a j) i = U (fun a => x a k) i
  have hf : (fun a : Fin r => x a j) = (fun a => x a k) := by
    funext a
    exact h a j k
  rw [hf]

theorem iter_fullStep_lift (U : (Fin r → Rat) → Fin r → Rat)
    (n : Nat) (q : Fin r → Rat) :
    AGDDescent.iter (fullStep U) n (lift m q) =
      lift m (AGDDescent.iter (quotientStep U) n q) := by
  induction n with
  | zero => rfl
  | succ n ih => simp [AGDDescent.iter, ih, fullStep_lift]

/-- Exact reconstruction for every iterate, on the block-constant invariant sector. -/
theorem exact_reconstruction_on_blockConstant
    (U : (Fin r → Rat) → Fin r → Rat) (j0 : Fin m)
    (x : State r m) (h : BlockConstant x) (n : Nat) :
    lift m (AGDDescent.iter (quotientStep U) n (project j0 x)) =
      AGDDescent.iter (fullStep U) n x := by
  calc
    lift m (AGDDescent.iter (quotientStep U) n (project j0 x)) =
        AGDDescent.iter (fullStep U) n (lift m (project j0 x)) := by
          symm
          exact iter_fullStep_lift U n (project j0 x)
    _ = AGDDescent.iter (fullStep U) n x := by
          rw [lift_project_of_blockConstant j0 x h]

#print axioms exact_reconstruction_on_blockConstant
#print axioms blockConstant_fullStep

end AGDTensorSeparable
