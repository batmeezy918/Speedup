/-
  ProvenAgd.CorrectByConstructionSearch
  ======================================

  Ported from unmerged config: batmeezy918/chronofold PR #13
  (branch head: src/Chronofold/CorrectByConstructionSearch.lean
   "Formalize Correct-by-Construction Search in Lean 4").
  The PR was closed without merge. The master theorem it pushed:

    given  S, an equivalence `~`, an invariant `Ω : S → Q`,
    an admissible `T : S → S` compatible with `~`, a section `σ : Q → S`,
    a ranking `D : Q → Nat` that strictly decreases along T-bar for
    non-terminal quotients, then a Correct-by-Construction search exists:
      1. sound_execution      : preserved equivalence under T
      2. finite_termination   : well-founded step relation on the quotient
      3. correct_reconstruction : terminal quotients reconstruct via σ to a valid state

  Core-only adaptations (no Mathlib):
    - The quotient space is represented by the reduced type `Q` with the
      repo's congruence `AGD.Equivalent π` (`π x = π y`), which is the
      `x ~ y ↔ Ω x = Ω y` identification of the PR.
    - Reconstruction uses the repo's `AGD.Section π σ` (`π ∘ σ = id`)
      instead of `Quotient.out`/`Quotient.out_eq` (Mathlib-only).
    - `finite_termination` is proved by strong induction on the measure
      `D q` (core `Acc`/`Nat.strongRecOn`) instead of Mathlib's
      `Subrelation.wf`/`InvImage.wf`/`Finite`.

  Lean 4 core only. Self-contained modulo AGDMaximallyTypedClaim.
  No `sorry`.
-/

import AGDMaximallyTypedClaim

namespace Chronofold.CorrectByConstruction

open AGD

universe u v

set_option linter.unusedVariables false

/-- Strong induction on Nat built from core `Nat.strongRecOn` (Mathlib-free),
    matching the pattern used elsewhere in this repo. -/
theorem StrongInductionOn {p : Nat → Prop} (n : Nat)
    (h : ∀ n, (∀ m, m < n → p m) → p n) : p n :=
  Nat.strongRecOn n h

-- 2. Quotient space represented by `Q`; congruence `Equivalent π` is the PR's quotient relation.
-- 3. Invariant projection.
def Invariant {S : Type u} {Q : Type v} (π : S → Q) := π

-- 4. `x ~ y ↔ Ω x = Ω y` holds definitionally in this idiom.
theorem equiv_iff_invariant_eq {S : Type u} {Q : Type v}
    (π : S → Q) (x y : S) :
    Equivalent π x y ↔ π x = π y := by
  rfl

-- 5. Admissible transition and induced transition.
def Admissible {S : Type u} {Q : Type v}
    (T : S → S) (Tbar : Q → Q) (π : S → Q) : Prop :=
  Intertwines T Tbar π

-- 6. Section.
def Reconstruction {S : Type u} {Q : Type v}
    (π : S → Q) (σ : Q → S) : Prop :=
  Section π σ

/-- Sound execution: `T` respects the congruence (the PR's `sound_execution`). -/
theorem sound_execution
    {S : Type u} {Q : Type v}
    (T : S → S) (Tbar : Q → Q) (π : S → Q)
    (h : Admissible T Tbar π) :
    ∀ x y : S, π x = π y → π (T x) = π (T y) :=
  intertwining_implies_wellDefined T Tbar π h

/-- A single admissible step on the quotient: from a non-terminal `q` via T-bar. -/
def RankStep {Q : Type v} (Tbar : Q → Q) (terminal : Q → Prop) (q' q : Q) : Prop :=
  ¬ terminal q ∧ q' = Tbar q

/-- Finite termination: the step relation is well founded because D strictly
    decreases along non-terminal T-bar steps (strong induction on `D q`). -/
theorem finite_termination
    {Q : Type v}
    (Tbar : Q → Q) (terminal : Q → Prop)
    (D : Q → Nat)
    (h_decr : ∀ q, ¬ terminal q → D (Tbar q) < D q) :
    WellFounded (RankStep Tbar terminal) := by
  apply WellFounded.intro
  intro q
  have h_all : ∀ n (q : Q), D q = n → Acc (RankStep Tbar terminal) q := by
    intro n
    induction n using StrongInductionOn with
    | h n ih =>
        intro q hq
        apply Acc.intro
        intro y hy
        rcases hy with ⟨hnt, hyeq⟩
        subst hyeq
        have hlt : D (Tbar q) < D q := h_decr q hnt
        exact ih (D (Tbar q)) (Nat.lt_of_lt_of_eq hlt hq) (Tbar q) rfl
  exact h_all (D q) q rfl

/-- Correct reconstruction of a terminal quotient via the section. -/
def ValidConcrete {S : Type u} {Q : Type v}
    (π : S → Q) (σ : Q → S) (q : Q) (s : S) : Prop :=
  π s = q

theorem terminal_reconstructs_valid
    {S : Type u} {Q : Type v}
    (π : S → Q) (σ : Q → S) (terminal : Q → Prop)
    (hS : Reconstruction π σ)
    (q : Q) (_h : terminal q) :
    ValidConcrete π σ q (σ q) :=
  hS q

/-- The master Correct-by-Construction search certificate bundling the three
    pushed properties. -/
structure CorrectByConstructionSearch
    {S : Type u} {Q : Type v}
    (π : S → Q) (T : S → S) (Tbar : Q → Q) (σ : Q → S)
    (terminal : Q → Prop) : Prop where
  sound_execution : ∀ x y : S, π x = π y → π (T x) = π (T y)
  finite_termination : WellFounded (RankStep Tbar terminal)
  correct_reconstruction : ∀ q : Q, terminal q → ValidConcrete π σ q (σ q)

/-- The main Correct-by-Construction Search theorem. -/
theorem correctByConstructionSearch
    {S : Type u} {Q : Type v}
    (π : S → Q) (σ : Q → S)
    (T : S → S) (Tbar : Q → Q)
    (terminal : Q → Prop) (D : Q → Nat)
    (hI : Admissible T Tbar π)
    (hS : Reconstruction π σ)
    (h_decr : ∀ q, ¬ terminal q → D (Tbar q) < D q) :
    CorrectByConstructionSearch π T Tbar σ terminal := {
  sound_execution := sound_execution T Tbar π hI
  finite_termination := finite_termination Tbar terminal D h_decr
  correct_reconstruction := terminal_reconstructs_valid π σ terminal hS
}

end Chronofold.CorrectByConstruction