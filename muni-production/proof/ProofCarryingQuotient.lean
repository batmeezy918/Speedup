/-
ProofCarryingQuotient - the proof-carrying contract, core Lean only.

CORRECTION (2026-10-09), two defects removed:

1. The file previously opened with `import Mathlib`. No Mathlib symbol was
   used anywhere in it, so the import was spurious and made the file
   uncompilable in the pinned toolchain (Lean 4.29.0 core-only). Removed.

2. `forward_closed` was a DATA FIELD of `structure Transformation`, so
   `∀ x, project (P.step x) = candidate_step (project x)` held for every
   inhabitant of the type by construction. `SemPres`, `GapClosed` and their
   theorems were therefore degenerate: it was impossible to build a
   `Transformation` that violated the commutation relation, so proving
   `GapClosed → SemPres` proved only that a field equals a projection of
   itself. This is a structural vacuity that a `def ... := True` check and an
   axiom audit both MISS.

   Fix: `Transformation` now carries only data. The obligations are separate
   `Prop`s that a caller may or may not discharge, and
   `semPres_is_falsifiable` now actually constructs a transformation that
   violates them.
-/
namespace AGD

/-- A program: a state space and one step. -/
structure Program where
  State : Type
  step : State → State

/-- A candidate transformation: data only. It carries no obligations.
    Whether it is *correct* is a separate question, stated below as a `Prop`. -/
structure Transformation (P : Program) where
  CandidateState : Type
  candidate_step : CandidateState → CandidateState
  project : P.State → CandidateState
  reconstruct : CandidateState → P.State
  /-- The sector on which reconstruction is claimed to be exact. -/
  observable : P.State → Prop

/-- Semantic preservation: the projection commutes with the step. This is a
    proposition a `Transformation` need NOT satisfy. -/
def SemPres {P : Program} (T : Transformation P) : Prop :=
  ∀ x, T.project (P.step x) = T.candidate_step (T.project x)

/-- The certified gap is closed exactly when the commutation relation holds. -/
def GapClosed {P : Program} (T : Transformation P) : Prop :=
  SemPres T

/-- Exact reconstruction on the observable sector. Also not automatic. -/
def ReconstructExact {P : Program} (T : Transformation P) : Prop :=
  ∀ x, T.observable x → T.reconstruct (T.project x) = x

/-- The observable sector is invariant under the step, so a finite horizon can
    be iterated while staying inside it. -/
def SectorInvariant {P : Program} (T : Transformation P) : Prop :=
  ∀ x, T.observable x → T.observable (P.step x)

/-- A transformation is admissible when it commutes with the step and its
    observable sector is preserved. -/
def Admissible {P : Program} (T : Transformation P) : Prop :=
  SemPres T ∧ SectorInvariant T

theorem gapClosed_iff_semPres {P : Program} (T : Transformation P) :
    GapClosed T ↔ SemPres T := Iff.rfl

theorem semPres_of_admissible {P : Program} (T : Transformation P) :
    Admissible T → SemPres T := fun h => h.1

/-- Reconstruction is exact on the observable sector, by assumption. -/
theorem reconstruct_exact_of {P : Program} (T : Transformation P)
    (hex : ReconstructExact T) :
    ∀ x, T.observable x → T.reconstruct (T.project x) = x := hex

/-- **Falsifiability.** The obligations are not vacuous: there is a program and a
    transformation for which the commutation relation FAILS. This is the check
    the previous revision could not even state, because its structure made a
    counterexample unrepresentable. -/
theorem semPres_is_falsifiable :
    ∃ (P : Program) (T : Transformation P), ¬ SemPres T := by
  refine ⟨Program.mk Nat (fun x => x + 1),
          Transformation.mk Nat (fun _ => 0) (fun x => x) (fun x => x) (fun _ => True),
          ?_⟩
  intro h
  have h0 := h 0
  -- h0 : project (step 0) = candidate_step (project 0), i.e. 0 + 1 = 0
  exact absurd h0 (by decide)

/-- Reconstruction exactness is likewise falsifiable. -/
theorem reconstruct_exact_of' {P : Program} (T : Transformation P) :
    ∀ x, T.observable x → T.reconstruct (T.project x) = x →
      T.reconstruct (T.project x) = x := fun _ _ h => h

theorem reconstructExact_is_falsifiable :
    ∃ (P : Program) (T : Transformation P), ¬ ReconstructExact T := by
  refine ⟨Program.mk Nat (fun x => x + 1),
          Transformation.mk Nat (fun x => x) (fun x => x) (fun x => 2 * x + 1) (fun _ => True),
          ?_⟩
  intro h
  have h0 := h 0 (by trivial)
  -- h0 : reconstruct (project 0) = 0, i.e. 0 + 1 = 0
  exact absurd h0 (by decide)

#print axioms gapClosed_iff_semPres
#print axioms semPres_of_admissible
#print axioms reconstruct_exact_of
#print axioms reconstruct_exact_of'
#print axioms semPres_is_falsifiable
#print axioms reconstructExact_is_falsifiable

end AGD
