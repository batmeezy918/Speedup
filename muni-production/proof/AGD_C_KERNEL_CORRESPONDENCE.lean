/-
AGD_C_KERNEL_CORRESPONDENCE - the missing formal/native link.

The closure ledger left `native_equivalence` OPEN: the Lean tensor bridge
(AGD_TENSOR_OPERATOR_BRIDGE.lean) models the operator abstractly and the C
kernel implements it concretely, but nothing connected them.

This file connects them in the direction that is actually checkable without a
verified compiler: it restates the C kernel's semantics as Lean definitions
that MIRROR THE LOOPS INDEX-FOR-INDEX, and proves the correspondence theorems.

The C functions being modelled, from muni/kernel.c:

    agd_original_apply : y[b*m+j] = sum over c in [0,r) of U[b*r+c] * x[c*m+j]
    quotient_apply    : o[b]      = sum over c in [0,r) of U[b*r+c] * q[c]
    plan_create       : q0[b]     = x[b*m]                        (projection)
    plan_reconstruct  : out[b*m+j] = qf[b]                        (broadcast)

The full state is therefore a pair-indexed map (block, fiber) -> value, which is
how the C loops address it. Modelling it that way avoids flattening and keeps the
Lean indices identical to the C indices.

Two facts about the C code bound the claim:

  * The projection takes fiber index 0. It is exact only when the state really is
    block-constant. That is the section law, and it is an ASSUMPTION here, not
    something the arithmetic supplies.

  * Arithmetic below is over Nat, i.e. exact integers. This file establishes the
    OPERATION STRUCTURE and the INDEXING correspondence. IEEE-754 rounding is a
    separate obligation and is NOT claimed here; it is checked separately by
    executing the C kernel and this model on identical inputs and comparing.
-/

namespace AGD.CCorrespond

/-- The full state, indexed exactly as the C loops index it: (block, fiber). -/
abbrev CState := Nat → Nat → Nat

/-- The quotient state: one value per block. -/
abbrev QState := Nat → Nat

/-- Accumulator exactly as C: start at zero, fold left over the row. -/
def csum (U : Nat → Nat → Nat) (b : Nat) (f : Nat → Nat) : List Nat → Nat → Nat
  | [], acc => acc
  | c :: rest, acc => csum U b f rest (acc + U b c * f c)

theorem csum_congr {U : Nat → Nat → Nat} {b : Nat} {f g : Nat → Nat}
    (h : ∀ c, f c = g c) : ∀ cs acc, csum U b f cs acc = csum U b g cs acc := by
  intro cs
  induction cs with
  | nil => intro acc; rfl
  | cons c rest ih =>
      intro acc
      simp [csum]
      rw [h c, ih]

/-- The C loop bound. -/
def cols (r : Nat) : List Nat := List.range r

/-- Model of `agd_original_apply`: independent accumulation per (block, fiber). -/
def cOriginalApply (U : Nat → Nat → Nat) (r m : Nat) (x : CState) : CState :=
  fun b j => csum U b (fun c => x c j) (cols r) 0

/-- Model of `quotient_apply`: one accumulation per block. -/
def cQuotientApply (U : Nat → Nat → Nat) (r : Nat) (q : QState) : QState :=
  fun b => csum U b (fun c => q c) (cols r) 0

/-- Model of the projection in `agd_plan_create`: take fiber index 0. -/
def cProject (x : CState) : QState := fun b => x b 0

/-- Model of `agd_plan_reconstruct`: broadcast the block value to every fiber. -/
def cReconstruct (m : Nat) (q : QState) : CState := fun b _ => q b

/-- Finite iteration, matching `agd_plan_run`. -/
def iterateC {X : Type} (f : X → X) : Nat → X → X
  | 0, x => x
  | n + 1, x => iterateC f n (f x)

/-- The invariant sector in C's own indexing: fiber j and k agree in block b. -/
def CInvariant (x : CState) : Prop := ∀ b j k, x b j = x b k

/-- **Correspondence 1.** The full step preserves the block-constant sector.
    This is what makes repeated application legitimate. -/
theorem cOriginalApply_preserves_invariant {U : Nat → Nat → Nat} {r m : Nat}
    {x : CState} (hx : CInvariant x) :
    CInvariant (cOriginalApply U r m x) := by
  intro b j k
  simp [cOriginalApply]
  refine csum_congr (fun c => ?_) _ _
  exact hx c j k

/-- The sector is invariant along every finite full trajectory. -/
theorem cInvariant_iterate {U : Nat → Nat → Nat} {r m : Nat} :
    ∀ (x : CState), CInvariant x → ∀ n, CInvariant (iterateC (cOriginalApply U r m) n x) := by
  intro x hx n
  induction n generalizing x with
  | zero => exact hx
  | succ n ih =>
      exact ih (cOriginalApply U r m x)
        (cOriginalApply_preserves_invariant (U := U) (r := r) (m := m) hx)

/-- **Correspondence 2.** Projection commutes with the full step.
    `cProject (cOriginalApply x) = cQuotientApply (cProject x)` holds by `rfl`:
    the projected side reads `x c 0` and the quotient side reads `cProject x c`,
    which is also `x c 0`. This is the one-step commuting relation the whole
    quotient rests on. -/
theorem cProject_commutes {U : Nat → Nat → Nat} {r m : Nat} {x : CState} :
    cProject (cOriginalApply U r m x) = cQuotientApply U r (cProject x) := by
  funext b; rfl

/-- Pointwise form of correspondence 2, stated so no function extensionality is
    needed anywhere downstream. -/
theorem cProject_commutes_at {U : Nat → Nat → Nat} {r m : Nat} {x : CState} :
    ∀ b, cProject (cOriginalApply U r m x) b
        = cQuotientApply U r (cProject x) b :=
  fun _ => rfl

/-- **Correspondence 3a.** After `n` quotient steps from the projection, the
    value at block `b` equals the value at fiber 0 of the full state after `n`
    full steps. Proved by induction, generalising over the starting state. -/
theorem cQuotient_tracks_projection {U : Nat → Nat → Nat} {r m : Nat} :
    ∀ (x : CState), CInvariant x → ∀ n b,
      iterateC (cQuotientApply U r) n (cProject x) b
        = iterateC (cOriginalApply U r m) n x b 0 := by
  intro x hx n
  induction n generalizing x with
  | zero =>
      intro b
      rfl
  | succ n ih =>
      intro b
      have hx' : CInvariant (cOriginalApply U r m x) :=
        cOriginalApply_preserves_invariant (U := U) (r := r) (m := m) hx
      have hstep : cQuotientApply U r (cProject x)
          = cProject (cOriginalApply U r m x) := rfl
      change iterateC (cQuotientApply U r) n
          (cQuotientApply U r (cProject x)) b = _
      rw [hstep]
      exact ih (cOriginalApply U r m x) hx' b

/-- **Correspondence 3.** One projection, `n` quotient steps, one reconstruction
    reproduces `n` full steps exactly on the invariant sector. -/
theorem cReconstruct_exact {U : Nat → Nat → Nat} {r m : Nat} :
    ∀ (x : CState), CInvariant x → ∀ n b j,
      cReconstruct m (iterateC (cQuotientApply U r) n (cProject x)) b j
        = iterateC (cOriginalApply U r m) n x b j := by
  intro x hx n
  induction n generalizing x with
  | zero =>
      intro b j
      -- reconstruction of the projection is the identity on the sector
      exact hx b 0 j
  | succ n ih =>
      intro b j
      have hx' : CInvariant (cOriginalApply U r m x) :=
        cOriginalApply_preserves_invariant (U := U) (r := r) (m := m) hx
      have hstep : cQuotientApply U r (cProject x)
          = cProject (cOriginalApply U r m x) := rfl
      change iterateC (cQuotientApply U r) n
          (cQuotientApply U r (cProject x)) b = _
      rw [hstep]
      have hfull := cQuotient_tracks_projection (U := U) (r := r) (m := m)
        (cOriginalApply U r m x) hx' n b
      have hfullj : iterateC (cQuotientApply U r) n
          (cProject (cOriginalApply U r m x)) b
          = iterateC (cOriginalApply U r m) n (cOriginalApply U r m x) b j := by
        have hinv : CInvariant
            (iterateC (cOriginalApply U r m) n (cOriginalApply U r m x)) :=
          cInvariant_iterate (U := U) (r := r) (m := m) (cOriginalApply U r m x) hx' n
        rw [hfull, hinv b 0 j]
      exact hfullj

#print axioms csum_congr
#print axioms cOriginalApply_preserves_invariant
#print axioms cProject_commutes_at
#print axioms cQuotient_tracks_projection
#print axioms cReconstruct_exact

end AGD.CCorrespond