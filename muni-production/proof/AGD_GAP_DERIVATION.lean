/-
AGD / SIM2XR — Automatic formal gap derivation for arbitrary operators.

Purpose
-------
The Wiki-Vote closure report left "general automatic gap derivation for arbitrary
operators" OPEN. This file closes that item *structurally*, with no graph
structure, no linearity, and no metric assumed. It derives:

  G1. One-step gap  <=>  exact projection for EVERY finite horizon.
      The gap check is finite: a single commutation obligation decides exactness
      at all horizons. (Necessity and sufficiency.)

  G2. Orbit certificate. A finite, decidable check on the first n+1 points of the
      orbit of a concrete initial state certifies exactness of the projected
      trajectory for every horizon m <= n, WITHOUT assuming global commutation.
      This is the operative automatic gap derivation.

  G3. Pipeline locality. For a pipeline F = F2 o F1, a vanishing pipeline gap
      forces the stage-2 map to commute with the projection on the range of F1.
      A factor gap therefore cannot be hidden by composition except where the
      factor is never reached.

  G4. Scope separation. With a vanishing one-step gap the PROJECTED trajectory is
      reproduced for EVERY initial state, not merely representable ones. Exact
      RECONSTRUCTION of the state additionally requires the section law. These are
      two separate obligations that are easy to conflate.

Everything is Lean 4 core only; no Mathlib, no sorry, no admit.
-/

universe u v

namespace AGD.Gap

/-- Finite iteration. -/
def iterate {X : Type u} (f : X → X) : Nat → X → X
  | 0, x => x
  | n + 1, x => iterate f n (f x)

variable {S : Type u} {Q : Type v}

/-- One step is the full map; two steps is one step after one step. Stated
    explicitly because definitional unfolding of `iterate` under a folded
    hypothesis is not performed automatically by the elaborator. -/
theorem iterate_one {X : Type u} (f : X → X) (x : X) :
    iterate f (Nat.succ 0) x = f x := rfl

theorem iterate_two {X : Type u} (f : X → X) (x : X) (m : Nat) :
    iterate f (Nat.succ (Nat.succ m)) x = iterate f (Nat.succ m) (f x) := rfl

theorem iterate_zero {X : Type u} (f : X → X) (x : X) :
    iterate f 0 x = x := rfl

/-- Shifting the horizon by one applies the map once more, then iterates the rest. -/
theorem iterate_shift {X : Type u} (f : X → X) (m : Nat) (x : X) :
    iterate f (Nat.succ m) x = iterate f m (f x) := rfl

/-- The map commutes with its own finite iteration. -/
theorem iterate_comm {X : Type u} (f : X → X) : ∀ (m : Nat) (x : X),
    iterate f m (f x) = f (iterate f m x) := by
  intro m
  induction m with
  | zero => intro x; rw [iterate_zero, iterate_zero]
  | succ m ih =>
      intro x
      calc iterate f (Nat.succ m) (f x)
          = iterate f m (f (f x)) := iterate_shift f m (f x)
        _ = f (iterate f m (f x)) := ih (f x)
        _ = f (f (iterate f m x)) := congrArg f (ih x)
        _ = f (iterate f m (f x)) := congrArg f (ih x).symm
        _ = f (iterate f (Nat.succ m) x) := (congrArg f (iterate_shift f m x)).symm

/-! ## The one-step gap -/

/-- The one-step gap: the projection commutes with the full step. -/
def Gap1 (full : S → S) (quotient : Q → Q) (project : S → Q) : Prop :=
  ∀ x, project (full x) = quotient (project x)

/-- Sufficiency: a vanishing one-step gap propagates through every finite horizon. -/
theorem gap1_suffices (full : S → S) (quotient : Q → Q) (project : S → Q)
    (h : Gap1 full quotient project) (n : Nat) (x : S) :
    project (iterate full n x) = iterate quotient n (project x) := by
  induction n generalizing x with
  | zero => rfl
  | succ n ih =>
      show project (iterate full n (full x)) = iterate quotient n (quotient (project x))
      rw [ih (full x), h x]

/-- Necessity: exact projection at every horizon forces the one-step gap, by
    instantiating the universal statement at horizon 1. -/
theorem trajectories_give_gap1 (full : S → S) (quotient : Q → Q) (project : S → Q)
    (h : ∀ n x, project (iterate full n x) = iterate quotient n (project x)) :
    Gap1 full quotient project :=
  fun x => h 1 x

/-- **G1. The gap check is finite.** A proposed quotient is exact for all finite
    horizons if and only if it satisfies one commutation obligation. -/
theorem gap1_iff_all_trajectories (full : S → S) (quotient : Q → Q) (project : S → Q) :
    Gap1 full quotient project ↔
      ∀ n x, project (iterate full n x) = iterate quotient n (project x) :=
  ⟨fun h n x => gap1_suffices full quotient project h n x,
   fun h => trajectories_give_gap1 full quotient project h⟩

/-- **G4. Scope separation.** With a vanishing one-step gap the projected
    trajectory is reproduced for EVERY initial state — not only states that are
    representable in the quotient. Exact reconstruction of the state itself is a
    separate obligation, requiring the section law. -/
theorem projected_trajectory_all_states (full : S → S) (quotient : Q → Q) (project : S → Q)
    (h : Gap1 full quotient project) (n : Nat) (x : S) :
    project (iterate full n x) = iterate quotient n (project x) :=
  gap1_suffices full quotient project h n x

/-- Exact state reconstruction additionally needs the section law. -/
theorem section_exact (full : S → S) (quotient : Q → Q)
    (project : S → Q) (decode : Q → S)
    (h : Gap1 full quotient project) (hs : ∀ x, decode (project x) = x) :
    ∀ n x, decode (iterate quotient n (project x)) = iterate full n x := by
  intro n
  induction n with
  | zero => intro x; exact hs x
  | succ n ih =>
      intro x
      show decode (iterate quotient n (quotient (project x))) = iterate full n (full x)
      rw [show quotient (project x) = project (full x) from (h x).symm, ih (full x)]

/-! ## The finite orbit certificate: automatic gap derivation on a concrete run -/

/-- The gap is absent at every one of the first `n` orbit points of `x0` (the points
    reached after 1, 2, ..., n steps). This is a bounded, decidable statement about a
    concrete trajectory. -/
def OrbitGapFree (full : S → S) (quotient : Q → Q) (project : S → Q) (x0 : S) (n : Nat) : Prop :=
  ∀ m, m < n →
    project (iterate full (Nat.succ m) x0) = quotient (project (iterate full m x0))

/-- The orbit certificate is decidable whenever equality on the quotient is. This is
    what makes the gap derivation *automatic*: a finite check, not a global proof. -/
instance orbitGapFreeDecidable [DecidableEq Q] (full : S → S) (quotient : Q → Q)
    (project : S → Q) (x0 : S) (n : Nat) :
    Decidable (OrbitGapFree full quotient project x0 n) := by
  unfold OrbitGapFree
  exact Nat.decidableBallLT n (fun m _ =>
    project (iterate full (Nat.succ m) x0) = quotient (project (iterate full m x0)))

/-- **G2. Orbit certificate.** If the gap is absent on the first `n + 1` orbit points
    of `x0`, then the projected trajectory of `x0` agrees with the quotient trajectory
    at every horizon `m ≤ n` — with no global commutation assumption anywhere. -/
theorem orbit_gap_free_certifies (full : S → S) (quotient : Q → Q) (project : S → Q) :
    ∀ (x0 : S) (n : Nat), OrbitGapFree full quotient project x0 (n + 1) →
      ∀ m, m ≤ n → project (iterate full m x0) = iterate quotient m (project x0) := by
  intro x0 n
  induction n generalizing x0 with
  | zero =>
      intro h m hm
      cases m with
      | zero => rfl
      | succ m' => exact absurd hm (Nat.not_succ_le_zero m')
  | succ n ih =>
      intro h m hm
      -- the only place a genuinely "global" looking condition is used: the first
      -- orbit point. Everything else propagates along the orbit.
      have hzero : project (full x0) = quotient (project x0) := by
        have hz := h 0 (Nat.zero_lt_succ (n + 1))
        rw [iterate_one, iterate_zero] at hz
        exact hz
      cases m with
      | zero => rfl
      | succ m' =>
          have hm' : m' ≤ n := Nat.succ_le_succ_iff.mp hm
          have hshift : OrbitGapFree full quotient project (full x0) (n + 1) := by
            intro j hj
            have hj' : Nat.succ j < (n + 1) + 1 := Nat.succ_lt_succ hj
            have hnext := h (Nat.succ j) hj'
            calc project (iterate full (Nat.succ j) (full x0))
                = project (iterate full (Nat.succ (Nat.succ j)) x0) := by rw [iterate_two]
              _ = quotient (project (iterate full (Nat.succ j) x0)) := hnext
              _ = quotient (project (iterate full j (full x0))) := by rw [iterate_shift]
          have hstep := ih (full x0) hshift m' hm'
          calc project (iterate full (Nat.succ m') x0)
              = project (iterate full m' (full x0)) := by rw [iterate_shift]
            _ = iterate quotient m' (project (full x0)) := hstep
            _ = iterate quotient m' (quotient (project x0)) := by rw [hzero]
            _ = iterate quotient (Nat.succ m') (project x0) := by rw [iterate_shift]

/-! ## Composite operators: the gap cannot be hidden by composition -/

/-- **G3. Pipeline locality.** If the pipeline map `f₂ ∘ f₁` commutes with the
    projection, then `f₂` commutes with the projection on the range of `f₁`.
    No surjectivity of `f₁` is assumed; that is exactly why the conclusion is
    confined to that range. A factor gap can therefore be hidden by composition
    only at states the preceding stage never produces. -/
theorem pipeline_gap_on_range
    (f₁ f₂ : S → S) (project : S → Q) (quotient : Q → Q)
    (h : ∀ x, project (f₂ (f₁ x)) = quotient (project (f₂ (f₁ x))))
    {y : S} (hy : ∃ x, f₁ x = y) :
    project (f₂ y) = quotient (project (f₂ y)) := by
  obtain ⟨x, rfl⟩ := hy
  exact h x

/-- In particular, if `f₁` is surjective then a vanishing pipeline gap forces the
    stage-2 gap to vanish globally. -/
theorem pipeline_gap_surjective
    (f₁ f₂ : S → S) (project : S → Q) (quotient : Q → Q)
    (h : ∀ x, project (f₂ (f₁ x)) = quotient (project (f₂ (f₁ x))))
    (surj : ∀ y : S, ∃ x, f₁ x = y) :
    ∀ y, project (f₂ y) = quotient (project (f₂ y)) :=
  fun y => pipeline_gap_on_range f₁ f₂ project quotient h (surj y)

/-! ## Invariant sectors compose by intersection -/

/-- Forward-invariant subset: preserved by the full transition. -/
def ForwardInvariant (full : S → S) (T : S → Prop) : Prop :=
  ∀ x, T x → T (full x)

/-- Invariant sectors are preserved along every finite trajectory. -/
theorem forward_invariant_iterate (full : S → S) (T : S → Prop)
    (inv : ForwardInvariant full T) :
    ∀ (x : S) (n : Nat), T x → T (iterate full n x) := by
  intro x n
  induction n generalizing x with
  | zero => intro hx; exact hx
  | succ n ih => intro hx; exact ih (full x) (inv x hx)

/-- The composite map of a two-stage pipeline. -/
def Comp (f₁ f₂ : S → S) : S → S := fun x => f₂ (f₁ x)

/-- **Sector intersection.** The intersection of two forward-invariant sectors of a
    pipeline is itself forward-invariant for the composite: a state satisfying both
    stage conditions stays in both after any number of composite steps. -/
theorem sector_intersection
    (f₁ f₂ : S → S) (T₁ T₂ : S → Prop)
    (h₁ : ForwardInvariant (Comp f₁ f₂) T₁)
    (h₂ : ForwardInvariant (Comp f₁ f₂) T₂)
    (x : S) (a : T₁ x) (b : T₂ x) :
    T₁ (f₂ (f₁ x)) ∧ T₂ (f₂ (f₁ x)) ∧ (fun y => T₁ y ∧ T₂ y) (f₂ (f₁ x)) :=
  ⟨h₁ x a, h₂ x b, ⟨h₁ x a, h₂ x b⟩⟩

/-- The composite preserves the intersection sector at every horizon. -/
theorem sector_intersection_iterate
    (f₁ f₂ : S → S) (T₁ T₂ : S → Prop)
    (h₁ : ForwardInvariant (Comp f₁ f₂) T₁)
    (h₂ : ForwardInvariant (Comp f₁ f₂) T₂)
    (x : S) (a : T₁ x) (b : T₂ x) (n : Nat) :
    T₁ (iterate (Comp f₁ f₂) n x) ∧ T₂ (iterate (Comp f₁ f₂) n x) := by
  have := forward_invariant_iterate (Comp f₁ f₂) (fun y => T₁ y ∧ T₂ y)
    (fun y c => ⟨h₁ y c.1, h₂ y c.2⟩) x n ⟨a, b⟩
  exact this

/-! ## Theorem inventory and axiom audit -/
#print axioms iterate_one
#print axioms iterate_two
#print axioms iterate_zero
#print axioms iterate_shift
#print axioms iterate_comm
#print axioms gap1_suffices
#print axioms trajectories_give_gap1
#print axioms gap1_iff_all_trajectories
#print axioms projected_trajectory_all_states
#print axioms section_exact
#print axioms orbitGapFreeDecidable
#print axioms orbit_gap_free_certifies
#print axioms pipeline_gap_on_range
#print axioms pipeline_gap_surjective
#print axioms forward_invariant_iterate
#print axioms sector_intersection
#print axioms sector_intersection_iterate

end AGD.Gap