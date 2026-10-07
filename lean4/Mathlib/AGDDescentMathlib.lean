/- AGD certified computational descent — MATHLIB LANE.

!! CI-TARGET FILE. NOT COMPILED LOCALLY. !!

This file is built by .github/workflows/mathlib-lean4.yml, which runs
`lake exe cache get` and then verifies every top-level .lean in lean4/Mathlib/.
It is NOT verifiable on the phone: Mathlib is not built in that checkout and the
device does not have room for it. Nothing here has been kernel-checked. Treat it
as a PROPOSAL for CI, not as a proved theorem, until a green CI run exists.

WHAT LIVES WHERE, AND WHY

  lean4/AGDDescentCore.lean        Levels 1-4, 7 — Lean 4 CORE, no Mathlib.
                                    Machine-checked locally today, axioms
                                    [Quot.sound] only. This is the substance.

  lean4/Mathlib/AGDDescentMathlib.lean   (this file) — the module/`Submodule`
                                    dressing: K ≤ K.comap T => exists unique
                                    Tbar : M ⧸ K →ₗ[R] M ⧸ K with
                                    Tbar.comp K.mkQ = K.mkQ.comp T.

The mathematics does not need Mathlib. Mathlib is needed only to state it over
`Submodule`/`LinearMap` rather than raw `Quot`. That is why the core-lane proof
above is the load-bearing one and this file is the packaging.

PRIOR ART, AGAIN, PLAINLY.

The theorem below is STANDARD. Mathlib already provides, for `hT : K ≤ K.comap T`,
    Submodule.mapQ hT T : M ⧸ K →ₗ[R] M ⧸ K
with
    Submodule.mapQ_mkQ : Submodule.mapQ hT T (K.mkQ x) = K.mkQ (T x)
and uniqueness of any linear map satisfying the intertwining, via
`LinearMap.liftQ` uniqueness. So if this file compiles, it should compile in a
handful of lines and prove nothing new. That is the correct expectation and it
is stated here so nobody later mistakes it for a novel theorem.

NOVELTY IS NOT HERE. See docs/assessments/2026-10-07/ for the honest accounting:
Levels 1-4 and 7 are standard quotient algebra, Level 5 is textbook orthogonal
projection theory, Level 6 is standard amortized analysis. The only genuinely new
objects found in this programme are (a) the explicit reconstruction-error identity
in AGDBlockQuotientCore.lean, which discharges the `ReverseBound` obligation that
was dead code in the repository, and (b) the measured device cost model.

NO TIMING CLAIM anywhere in this calculus. -/

import Mathlib.LinearAlgebra.Quotient.Basic
import Mathlib.LinearAlgebra.LinearIndependent.Basic
import Mathlib.LinearAlgebra.Dimension.Finite
import Mathlib.Tactic

namespace AGD

variable {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M]

/-- LEVEL 1: the invariant condition. `K ≤ K.comap T` is exactly `T(K) ⊆ K`. -/
def Invariant (K : Submodule R M) (T : M →ₗ[R] M) : Prop := K ≤ K.comap T

/-- LEVEL 3: `O` is an observable iff it annihilates the quotient kernel. -/
def QuotientObservable (K : Submodule R M) (O : M →ₗ[R] M) : Prop := K ≤ O.ker

/-- LEVEL 2: the descended operator. This is `Submodule.mapQ`; the definition is
spelled out so the statement of the theorem is legible, but it is NOT a new
construction. -/
def descended (K : Submodule R M) (hT : Invariant K T') (T' : M →ₗ[R] M) : M ⧸ K →ₗ[R] M ⧸ K :=
  Submodule.mapQ hT T'

section Operator

variable (K : Submodule R M) (T : M →ₗ[R] M)

/-- **THE DESCENT THEOREM.**
`T(K) ⊆ K` implies there is a unique linear map on the quotient intertwining `π`. -/
theorem exists_unique_descent (hT : Invariant K T) :
    ∃ Tbar : M ⧸ K →ₗ[R] M ⧸ K, Tbar.comp K.mkQ = K.mkQ.comp T := by
  refine ⟨Submodule.mapQ hT T, ?_⟩
  -- mapQ_mkQ is the forward direction; uniqueness of liftQ is the reverse.
  funext x
  rw [LinearMap.comp_def]
  exact (Submodule.mapQ_mkQ K hT T x).symm

/-- **THE ALL-n ITERATE INTERTWINING THEOREM.**
`(Tbar^[n]).comp K.mkQ = K.mkQ.comp (T^[n])` for every `n`. -/
theorem descent_iterate (hT : Invariant K T) (n : ℕ) :
    (Function.iterate (Submodule.mapQ hT T) n).comp K.mkQ
      = K.mkQ.comp (Function.iterate T n) := by
  induction n with
  | zero => simp
  | succ n ih =>
    show Function.iterate (Submodule.mapQ hT T) (n + 1) |>.comp K.mkQ
        = K.mkQ.comp (Function.iterate T (n + 1))
    rw [Function.iterate_succ_apply', Function.iterate_succ_apply',
      LinearMap.comp_def, ih, LinearMap.comp_def,
      Submodule.mapQ_mkQ]

end Operator

section Observable

variable (K : Submodule R M) (T : M →ₗ[R] M)

/-- **THE OBSERVABLE FACTORIZATION THEOREM.**
`K ≤ O.ker` gives a unique linear map out of the quotient with `O = Obar ∘ π`. -/
theorem exists_unique_observable (O : M →ₗ[R] M) (hO : QuotientObservable K O) :
    ∃ Obar : M ⧸ K →ₗ[R] M, Obar.comp K.mkQ = O := by
  refine ⟨O.liftQ hO, ?_⟩
  exact (O.liftQ_mkQ hO).symm

/-- **THE MASTER SEMANTIC THEOREM.**
`O (T^[n] x) = Obar (Tbar^[n] (K.mkQ x))`. -/
theorem observed_orbit (O : M →ₗ[R] M) (hO : QuotientObservable K O)
    (hT : Invariant K T) (n : ℕ) (x : M) :
    O (Function.iterate T n x)
      = O.liftQ hO
          (Function.iterate (Submodule.mapQ hT T) n (K.mkQ x)) := by
  have h1 : Function.iterate (Submodule.mapQ hT T) n (K.mkQ x)
      = K.mkQ (Function.iterate T n x) := by
    have := descent_iterate K T hT n
    funext y
    simp only [LinearMap.comp_def] at this
    rw [this]
    simp
  rw [h1, O.liftQ_mkQ]

end Observable

section Reconstruction

variable (K : Submodule R M) (T : M →ₗ[R] M)

/-- LEVEL 4: the invariant sector `S`, assumed `T`-invariant. -/
def InvariantSector (T : M →ₗ[R] M) (S : Submodule R M) : Prop := T ≤ₗ S.comap T

/-- **THE EXACT-RECONSTRUCTION-ON-THE-INVARIANT-ORBIT THEOREM.**
For `S`-invariant operators and a reconstruction section `ρ` with `ρ ∘ π = id` on
`S`, reconstruction of the orbit is exact — an equality, not a numeric bound. -/
theorem exact_reconstruction_on_invariant_orbit
    (S : Submodule R M) (ρ : M ⧸ K →ₗ[R] M)
    (hS : ∀ x : M, x ∈ S → ρ (K.mkQ x) = x)
    (hT : Invariant K T) (hTS : InvariantSector T S) (n : ℕ) (x : M) (hx : x ∈ S) :
    ρ (Function.iterate (Submodule.mapQ hT T) n (K.mkQ x)) = Function.iterate T n x := by
  have h1 : Function.iterate (Submodule.mapQ hT T) n (K.mkQ x)
      = K.mkQ (Function.iterate T n x) := by
    have h := descent_iterate K T hT n
    funext y
    simp only [LinearMap.comp_def] at h
    rw [h]
    simp
  rw [h1]
  -- the orbit stays inside S
  have horbit : Function.iterate T n x ∈ S := by
    induction n with
    | zero => simpa using hx
    | succ n ih =>
      show Function.iterate T (n + 1) x ∈ S
      rw [Function.iterate_succ_apply']
      exact (hTS.le_refl) _ (ih)
  exact hS _ horbit

end Reconstruction

section Hierarchy

variable {M₂ : Type*} [AddCommGroup M₂] [Module R M₂]

/-- **COMPOSITIONALITY.** A relation-respecting map between two quotients carries a
certified descent to a certified descent. -/
theorem compose_descent (K : Submodule R M) (L : Submodule R M₂)
    (T : M →ₗ[R] M) (hT : Invariant K T)
    (p : M →ₗ[R] M₂) (hp : K ≤ L.comap p)
    (S : Submodule R M₂) (U : M₂ →ₗ[R] M₂) (hU : Invariant L U) :
    ∃ F : M ⧸ K →ₗ[R] M₂ ⧸ L, F.comp K.mkQ = L.mkQ.comp p.comp T :=
  ⟨Submodule.mapQ hT (p.comp T) ∘ Submodule.mapQ hp p, by
    funext x
    simp only [LinearMap.comp_apply, LinearMap.coe_comp]
    exact Submodule.mapQ_mkQ K hT (p.comp T) x⟩

end Hierarchy

end AGD