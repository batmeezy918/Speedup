/-
  AGD-GEMM Reconstruction
  -----------------------
  Reverse direction: a section σ of π recovers the quotient operator
  and every finite reduced trajectory.

  Proves:
    * π ∘ σ = id
    * T̄ = π ∘ T ∘ σ
    * π(Tⁿ(σ q)) = T̄ⁿ q
    * observables on the reduced state are the full observables of the section

  Does NOT prove that a particular GEMM embedding is a section.
  That remains the obligation: actual_reconstruction_section.
-/

import AGDGemmProjection

namespace AGDGemmReconstruction

open AGDGemmProjection

universe u v w

/-- A section of π reconstructs one representative of each class. -/
def Section {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State) : Prop :=
  ∀ q, π (σ q) = q

theorem section_is_right_inverse {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State)
    (h : Section π σ) :
    π ∘ σ = id := by
  funext q
  exact h q

/-- A section is necessarily injective. -/
theorem section_injective {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State)
    (h : Section π σ) :
    Function.Injective σ := by
  intro q q' hσ
  calc
    q = π (σ q) := (h q).symm
    _ = π (σ q') := by rw [hσ]
    _ = q' := h q'

/-- Existence of a section implies π is surjective. -/
theorem section_implies_surjective {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State)
    (h : Section π σ) :
    Function.Surjective π :=
  fun q => ⟨σ q, h q⟩

/-- The unique recovered quotient operator. -/
theorem reconstructed_operator {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State)
    (T : State → State) (Tbar : Reduced → Reduced)
    (hσ : Section π σ)
    (hI : Intertwines T Tbar π) :
    π ∘ T ∘ σ = Tbar := by
  funext q
  calc
    (π ∘ T ∘ σ) q = π (T (σ q)) := rfl
    _             = Tbar (π (σ q)) := hI (σ q)
    _             = Tbar q := by rw [hσ q]

/-- Every finite reduced trajectory is the projection of the reconstructed run. -/
theorem reconstructed_iterate {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State)
    (T : State → State) (Tbar : Reduced → Reduced)
    (hσ : Section π σ)
    (hI : Intertwines T Tbar π) :
    ∀ n q, π (iterate T n (σ q)) = iterate Tbar n q := by
  intro n q
  calc
    π (iterate T n (σ q))
        = iterate Tbar n (π (σ q)) := projection_iterate T Tbar π hI n (σ q)
    _   = iterate Tbar n q := by rw [hσ q]

/-- Reduced observables are full observables of reconstructed representatives. -/
theorem observe_via_section {State : Type u} {Reduced : Type v} {Obs : Type w}
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (hσ : Section π σ)
    (hO : ObservablePreserved π observe observeReduced) :
    ∀ q, observeReduced q = observe (σ q) := by
  intro q
  calc
    observeReduced q = observeReduced (π (σ q)) := by rw [hσ q]
    _                = observe (σ q) := (hO (σ q)).symm

/-- Combined reconstruction + observable recovery for finite runs. -/
theorem reconstructed_observable {State : Type u} {Reduced : Type v} {Obs : Type w}
    (π : State → Reduced) (σ : Reduced → State)
    (T : State → State) (Tbar : Reduced → Reduced)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (hσ : Section π σ)
    (hI : Intertwines T Tbar π)
    (hO : ObservablePreserved π observe observeReduced) :
    ∀ n q,
      observeReduced (iterate Tbar n q) =
        observe (iterate T n (σ q)) := by
  intro n q
  calc
    observeReduced (iterate Tbar n q)
        = observeReduced (π (iterate T n (σ q))) := by
            rw [reconstructed_iterate π σ T Tbar hσ hI n q]
    _   = observe (iterate T n (σ q)) := (hO (iterate T n (σ q))).symm

/-- Packaged reconstruction closure. -/
theorem reconstruction_closure {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State)
    (T : State → State) (Tbar : Reduced → Reduced)
    (hσ : Section π σ)
    (hI : Intertwines T Tbar π) :
    (π ∘ σ = id) ∧
    Function.Injective σ ∧
    Function.Surjective π ∧
    (π ∘ T ∘ σ = Tbar) ∧
    (∀ n q, π (iterate T n (σ q)) = iterate Tbar n q) :=
  ⟨section_is_right_inverse π σ hσ,
   section_injective π σ hσ,
   section_implies_surjective π σ hσ,
   reconstructed_operator π σ T Tbar hσ hI,
   reconstructed_iterate π σ T Tbar hσ hI⟩

end AGDGemmReconstruction
