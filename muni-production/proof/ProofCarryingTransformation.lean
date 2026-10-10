/-
ProofCarryingTransformation - the bridge from the proof-carrying contract to the
proved quotient law. Core Lean only.

CORRECTION (2026-10-09). The previous revision of this file was VACUOUS:

    def Gap            (P) (T) : Prop := True
    def SemPres        (P) (T) : Prop := True
    def ArtifactCorrect(P) (T) : Prop := True
    theorem master (P) (T) : Gap P T ∧ SemPres P T ∧ ArtifactCorrect P T := by simp [...]

`master` was `True ∧ True ∧ True`. It compiled cleanly and emitted zero `sorryAx`,
so an axiom audit passed it. A companion file, ProofCarryingQuotient.lean, was
additionally degenerate in a subtler way: it baked the commutation relation in as
a structure FIELD, so no transformation could violate it.

This replacement does the job the filename promises: it carries the proved
quotient law, and it states the obligations as `Prop`s that are genuinely
falsifiable. It depends on nothing external.
-/
namespace AGD.Bridge

/-- Finite iteration. -/
def iterate {X : Type u} (f : X → X) : Nat → X → X
  | 0, x => x
  | n + 1, x => iterate f n (f x)

variable {S Q : Type u}

/-- The one-step gap: the projection commutes with the full step. -/
def Gap (full : S → S) (quotient : Q → Q) (project : S → Q) : Prop :=
  ∀ x, project (full x) = quotient (project x)

/-- Semantic preservation, stated for a candidate that is NOT assumed correct. -/
def SemPres (full : S → S) (quotient : Q → Q) (project : S → Q) : Prop :=
  Gap full quotient project

/-- Artifact correctness: the reconstruction is exact on the section sector. -/
def ArtifactCorrect (project : S → Q) (decode : Q → S) : Prop :=
  ∀ x, decode (project x) = x

/-- A vanishing one-step gap propagates to every finite horizon. This is the
    content that makes the reduction usable: check one step, get all horizons. -/
theorem gapPropagates (full : S → S) (quotient : Q → Q) (project : S → Q)
    (h : Gap full quotient project) :
    ∀ n x, project (iterate full n x) = iterate quotient n (project x) := by
  intro n
  induction n with
  | zero => intro x; rfl
  | succ n ih =>
      intro x
      show project (iterate full n (full x)) = iterate quotient n (quotient (project x))
      rw [ih (full x), h x]

/-- The obligations are falsifiable: some systems violate the one-step gap.
    Without this, `Gap` could be vacuously true for everything and every theorem
    below would be vacuous with it. -/
theorem gap_is_falsifiable :
    ∃ (S Q : Type) (full : S → S) (quotient : Q → Q) (project : S → Q),
      ¬ Gap full quotient project := by
  refine ⟨Nat, Nat, fun x => x + 1, fun _ => 0, (fun x => x), ?_⟩
  intro h
  have h0 := h 0
  exact absurd h0 (by decide)

/-- The obligations are satisfiable: some systems satisfy them. Together with
    `gap_is_falsifiable` this pins `Gap` as a genuinely selective condition. -/
theorem gap_is_satisfiable :
    ∃ (S Q : Type) (full : S → S) (quotient : Q → Q) (project : S → Q),
      Gap full quotient project := by
  exact ⟨Nat, Nat, id, id, id, fun _ => rfl⟩

/-- The artifact obligation is falsifiable too: a decoder can be wrong. -/
theorem artifactCorrect_is_falsifiable :
    ∃ (S Q : Type) (project : S → Q) (decode : Q → S),
      ¬ ArtifactCorrect project decode := by
  refine ⟨Nat, Nat, id, fun _ => 0, ?_⟩
  intro h
  have h1 := h 1
  -- h1 : decode (project 1) = 1, i.e. 0 = 1
  exact absurd h1 (by decide)

/-- **The master statement, now non-trivial.** Given a system whose one-step gap
    is closed, the projected trajectory is exact at every finite horizon. This is
    the claim the certified kernel implements. -/
theorem master (full : S → S) (quotient : Q → Q) (project : S → Q)
    (h : SemPres full quotient project) :
    ∀ n x, project (iterate full n x) = iterate quotient n (project x) :=
  gapPropagates full quotient project h

#print axioms gapPropagates
#print axioms master
#print axioms gap_is_falsifiable
#print axioms gap_is_satisfiable
#print axioms artifactCorrect_is_falsifiable

end AGD.Bridge