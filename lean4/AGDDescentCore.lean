/- AGD certified computational descent — Lean 4 CORE lane (no Mathlib).

Covers Levels 1-4 and 7 of the Certified Computational Descent Calculus:

    L1 ALGEBRA      quotient / equivalence
    L2 DYNAMICS     Descent => unique Tbar with Tbar.pi = pi.T, and for all n,
                    iter Tbar n . pi = pi . iter T n
    L3 OBSERVATION  observable constant on classes factors through, uniquely
    L4 EXECUTION    EXACT reconstruction on the invariant orbit
    L7 HIERARCHY    certified descents compose; intertwining carries to iterates

WHY THIS IS IN THE CORE LANE

The abstraction needs only `Quot`, `Quot.sound`, `Quot.lift`, `Quot.ind` and
function extensionality — all Lean 4 CORE. Mathlib is required for the
`Submodule` / `LinearMap` / `mkQ` / `liftQ` dressing only, NOT for the
mathematics. So the substantive theorem is machine-checked in this lane, and the
module dressing is a separate file built in CI
(lean4/Mathlib/AGDDescentMathlib.lean).

PORTABILITY NOTES. This core has neither `Function.iterate` nor the `∃!`
notation, so `iter` is defined locally and unique-existence is written explicitly
as `∃ x, P x ∧ ∀ y, P y → y = x`. Both are strictly more explicit than the
notations they replace.

PRIOR ART — stated plainly.

"Descent => exists unique descended operator with Tbar.pi = pi.T" is STANDARD
quotient algebra; Mathlib supplies the `Submodule` form via `Submodule.mapQ` and
`LinearMap.liftQ`. This file is NOT a novel theorem. It is the dependency-free
core-lane statement plus the two consequences the AGD programme actually needed
formalised: the all-`n` iterate theorem (L2) and exact reconstruction on the
invariant orbit (L4).

NO TIMING CLAIM. Nothing here asserts anything about wall-clock time.
-/

import Std

namespace AGDDescent

variable {α : Type u} {β : Type v} {r : α → α → Prop}

/- ## Iteration, defined locally (no `Function.iterate` in this core) -/

def iter {γ : Type w} (f : γ → γ) : Nat → γ → γ
  | 0, a => a
  | n + 1, a => f (iter f n a)

@[simp] theorem iter_zero (f : γ → γ) (a : γ) : iter f 0 a = a := rfl

theorem iter_succ (f : γ → γ) (n : Nat) (a : γ) : iter f (n + 1) a = f (iter f n a) := rfl

/- ## The three predicates -/

/-- `T` is well defined on `r`-classes. -/
def Descends (T : α → α) (r : α → α → Prop) : Prop := ∀ a b, r a b → r (T a) (T b)

/-- The descended map intertwines: `Tbar ∘ pi = pi ∘ T`. -/
def Intertwines (T : α → α) (r : α → α → Prop) (Tbar : Quot r → Quot r) : Prop :=
  ∀ x, Tbar (Quot.mk r x) = Quot.mk r (T x)

/-- An observable constant on classes factors through the quotient. -/
def QuotientObservable (r : α → α → Prop) (O : α → β) : Prop := ∀ a b, r a b → O a = O b

/- ## The canonical descents (by lifting) -/

/-- The descended operator, built by lifting `x ↦ [T x]`. -/
def descended (T : α → α) (r : α → α → Prop) (hT : Descends T r) : Quot r → Quot r :=
  Quot.lift (fun x => Quot.mk r (T x)) (fun a b hab => Quot.sound (hT a b hab))

@[simp] theorem descends_apply (T : α → α) (r : α → α → Prop) (hT : Descends T r) (x : α) :
    descended T r hT (Quot.mk r x) = Quot.mk r (T x) := rfl

/-- The descended observable, built by lifting `O`. -/
def descendedObservable (O : α → β) (r : α → α → Prop) (hO : QuotientObservable r O) :
    Quot r → β := Quot.lift O (fun a b hab => hO a b hab)

@[simp] theorem descendsObservable_apply (O : α → β) (r : α → α → Prop)
    (hO : QuotientObservable r O) (x : α) :
    descendedObservable O r hO (Quot.mk r x) = O x := rfl

/- ## L2 : existence and uniqueness of the descended operator -/

/-- **DESCENT EXISTS AND IS UNIQUE.**
`∃!` is unavailable in this core, so unique-existence is written explicitly. -/
theorem exists_unique_descent (T : α → α) (r : α → α → Prop) (hT : Descends T r) :
    ∃ Tbar : Quot r → Quot r,
      Intertwines T r Tbar
      ∧ ∀ Tbar' : Quot r → Quot r, Intertwines T r Tbar' → Tbar' = Tbar := by
  refine ⟨descended T r hT, fun _ => rfl, fun Tbar' h => ?_⟩
  funext z
  have key : ∀ a : α, Tbar' (Quot.mk r a) = descended T r hT (Quot.mk r a) := fun a => h a
  exact Quot.ind (β := fun w => Tbar' w = descended T r hT w) key z

/-- **THE ITERATE INTERTWINING THEOREM (L2).**
`iter Tbar n ∘ pi = pi ∘ iter T n` for every natural `n`. -/
theorem descent_iterate (T : α → α) (r : α → α → Prop) (hT : Descends T r) (n : Nat) (x : α) :
    iter (descended T r hT) n (Quot.mk r x) = Quot.mk r (iter T n x) := by
  induction n with
  | zero => rfl
  | succ n ih =>
    show descended T r hT (iter (descended T r hT) n (Quot.mk r x))
        = Quot.mk r (iter T (n + 1) x)
    rw [iter_succ, ih]
    rfl

/- ## L3 : observable factorization -/

theorem exists_unique_observable (O : α → β) (r : α → α → Prop)
    (hO : QuotientObservable r O) :
    ∃ Obar : Quot r → β,
      (∀ x, Obar (Quot.mk r x) = O x)
      ∧ ∀ Obar' : Quot r → β, (∀ x, Obar' (Quot.mk r x) = O x) → Obar' = Obar := by
  refine ⟨descendedObservable O r hO, fun _ => rfl, fun Obar' h => ?_⟩
  funext z
  have key : ∀ a : α, Obar' (Quot.mk r a) = descendedObservable O r hO (Quot.mk r a) :=
    fun a => h a
  exact Quot.ind (β := fun w => Obar' w = descendedObservable O r hO w) key z

/-- **THE MASTER SEMANTIC THEOREM (L2 + L3).**
`O (T^[n] x) = Obar (Tbar^[n] (pi x))` — exact observable equivalence along the
whole orbit, not merely at a single step. -/
theorem observed_orbit (T : α → α) (r : α → α → Prop) (hT : Descends T r)
    (O : α → β) (hO : QuotientObservable r O) (n : Nat) (x : α) :
    O (iter T n x) = descendedObservable O r hO (iter (descended T r hT) n (Quot.mk r x)) := by
  rw [descent_iterate T r hT n x]
  rfl

/- ## L4 : invariant sector and EXACT reconstruction on the orbit -/

def Invariant (S : α → Prop) (T : α → α) : Prop := ∀ x, S x → S (T x)

/-- Reconstruction is exact ON the sector — the strong form, not a numeric bound. -/
def ReconstructsOn (ρ : Quot r → α) (S : α → Prop) : Prop := ∀ x, S x → ρ (Quot.mk r x) = x

theorem invariant_iterate (S : α → Prop) (T : α → α) (hS : Invariant S T) (n : Nat) :
    ∀ x, S x → S (iter T n x) := by
  induction n with
  | zero => intro _ hx; exact hx
  | succ n ih =>
    intro x hx
    show S (iter T (n + 1) x)
    rw [iter_succ]
    exact hS (iter T n x) (ih x hx)

/-- **THE EXACT-RECONSTRUCTION-ON-THE-INVARIANT-ORBIT THEOREM (L4).**

Not "reconstruction is numerically close": for every point of the sector and every
iterate, `rho (iter Tbar n (pi x)) = iter T n x` as an EQUALITY. -/
theorem exact_reconstruction_on_invariant_orbit (T : α → α) (r : α → α → Prop)
    (hT : Descends T r) (ρ : Quot r → α) (S : α → Prop)
    (hS : Invariant S T) (hR : ReconstructsOn ρ S) (n : Nat) (x : α) (hx : S x) :
    ρ (iter (descended T r hT) n (Quot.mk r x)) = iter T n x := by
  rw [descent_iterate T r hT n x]
  exact hR (iter T n x) (invariant_iterate S T hS n x hx)

/- ## L7 : compositionality -/

def RespectsRel (p0 : α → β) (r0 : α → α → Prop) (r1 : β → β → Prop) : Prop :=
  ∀ a b, r0 a b → r1 (p0 a) (p0 b)

/-- The map induced on the source classes. -/
def induced (p0 : α → β) (r0 : α → α → Prop) (r1 : β → β → Prop) (hp0 : RespectsRel p0 r0 r1) :
    Quot r0 → Quot r1 :=
  Quot.lift (fun x => Quot.mk r1 (p0 x)) (fun a b hab => Quot.sound (hp0 a b hab))

/-- The composed operator on the target classes. -/
def composedOp (T0 : α → α) (r0 : α → α → Prop) (hT0 : Descends T0 r0)
    (p0 : α → β) (r1 : β → β → Prop) (hp0 : RespectsRel p0 r0 r1) :
    Quot r0 → Quot r1 :=
  Quot.lift (fun x => Quot.mk r1 (p0 (T0 x)))
    (fun a b hab => Quot.sound (hp0 (T0 a) (T0 b) (hT0 a b hab)))

/-- **COMPOSITIONALITY (L7).**
A certified descent at level 0, composed with a relation-respecting map, yields a
unique certified descent at level 1. Formal content of "individually certified
state-space descents compose into one certified descended execution". -/
theorem compose_two_descents (T0 : α → α) (r0 : α → α → Prop) (hT0 : Descends T0 r0)
    (p0 : α → β) (r1 : β → β → Prop) (hp0 : RespectsRel p0 r0 r1) :
    ∃ F : Quot r0 → Quot r1,
      (∀ x, F (Quot.mk r0 x) = Quot.mk r1 (p0 (T0 x)))
      ∧ ∀ F' : Quot r0 → Quot r1, (∀ x, F' (Quot.mk r0 x) = Quot.mk r1 (p0 (T0 x))) → F' = F := by
  refine ⟨composedOp T0 r0 hT0 p0 r1 hp0, fun _ => rfl, fun F' h => ?_⟩
  funext z
  have key : ∀ a : α, F' (Quot.mk r0 a)
      = composedOp T0 r0 hT0 p0 r1 hp0 (Quot.mk r0 a) := fun a => h a
  exact Quot.ind (β := fun w => F' w = composedOp T0 r0 hT0 p0 r1 hp0 w) key z

/-- **LEVEL-0 INTERTWINING CARRIES THROUGH ITERATES.**
If the level-0 descent already intertwines (`Pi T0 = T1 Pi`), so does every
iterate.

CORRECTION ON RECORD: the first draft of this file omitted this hypothesis and the
proof silently assumed `T1` commutes with `p0`, which made `composed_intertwine`
FALSE. The hypothesis is now explicit. -/
theorem compose_iterate (T0 : α → α) (p0 : α → β) (T1 : β → β)
    (hp : ∀ x, T1 (p0 x) = p0 (T0 x)) (n : Nat) (x : α) :
    iter T1 n (p0 x) = p0 (iter T0 n x) := by
  induction n with
  | zero => rfl
  | succ n ih =>
    show iter T1 (n + 1) (p0 x) = p0 (iter T0 (n + 1) x)
    rw [iter_succ, iter_succ, ih, hp]

/-- **HIERARCHICAL INTERTWINING (L7), all `n`.**
`Pi . T0^n = T1^n . Pi` for a chain of certified descents. -/
theorem composed_intertwine (T0 : α → α) (r0 : α → α → Prop) (hT0 : Descends T0 r0)
    (p0 : α → β) (T1 : β → β) (r1 : β → β → Prop)
    (hp0 : RespectsRel p0 r0 r1) (hT1 : Descends T1 r1)
    (hp : ∀ x, T1 (p0 x) = p0 (T0 x)) (n : Nat) (x : α) :
    iter (descended T1 r1 hT1) n (induced p0 r0 r1 hp0 (Quot.mk r0 x))
      = Quot.mk r1 (p0 (iter T0 n x)) := by
  show iter (descended T1 r1 hT1) n (Quot.mk r1 (p0 x)) = Quot.mk r1 (p0 (iter T0 n x))
  rw [descent_iterate T1 r1 hT1 n, compose_iterate T0 p0 T1 hp n x]

end AGDDescent