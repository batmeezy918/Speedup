/-
# Silicon Speedup Proof — formal core

These are the framework's *discipline* laws, not its physics. Each theorem is a
statement the validators enforce at runtime, restated so that the Lean kernel
checks that the statement is well-formed and true.

Scope limits, stated because they matter:

* This file proves nothing about any kernel, device, or measurement. It proves
  statements about a discrete claim lattice and about arithmetic identities over
  concrete numbers.
* It is checked with Lean 4 core only. Mathlib is NOT available in this
  repository (`lean4/lake-manifest.json` has `"packages": []` and
  `import Mathlib` fails), so nothing here depends on it. Anything requiring
  Mathlib is recorded as a formal gap rather than asserted.
* A kernel-checked proof of a statement in this file does not upgrade any
  empirical or performance claim. See `references/evidence-model.md`.

Build:

    lean formal/SSProofCore.lean

Toolchain recorded at build time: leanprover/lean4:v4.29.0
-/

namespace SSProof

/-! ## The two ladders -/

/-- Evidence strength, weakest to strongest. The order is given by `rank`. -/
inductive Strength where
  | unevidenced | observed | executed | reproduced
  | correctness | mechanism | formal | scopedVerified
  deriving DecidableEq, Repr, BEq

/-- Claim strength, weakest to strongest. NONE is added at the bottom; the
remaining four match the repository's `speedup/const.py` CLAIM_LATTICE. -/
inductive Claim where
  | none | candidate | strongLocal | formalPartial | verified
  deriving DecidableEq, Repr, BEq

def Strength.rank : Strength → Nat
  | .unevidenced => 0
  | .observed => 1
  | .executed => 2
  | .reproduced => 3
  | .correctness => 4
  | .mechanism => 5
  | .formal => 6
  | .scopedVerified => 7

def Claim.rank : Claim → Nat
  | .none => 0
  | .candidate => 1
  | .strongLocal => 2
  | .formalPartial => 3
  | .verified => 4

/-- The kind of thing being claimed. A correctness pass is not a speedup. -/
inductive ClaimKind where
  | none | performance | implementation | hardwareMechanism
  | formal | composition | cumulative
  deriving DecidableEq, Repr, BEq

/-- Minimum evidence level required before a given (claim, kind) pair may be
recorded. Mirrors `MINIMUM_EVIDENCE` in `scripts/ssproof.py`. -/
def floor : Claim → ClaimKind → Strength
  | .none, _ => .unevidenced
  | .candidate, _ => .observed
  | .strongLocal, .none => .executed
  | .strongLocal, .performance => .reproduced
  | .strongLocal, .implementation => .correctness
  | .strongLocal, .hardwareMechanism => .mechanism
  | .strongLocal, .formal => .formal
  | .strongLocal, .composition => .correctness
  | .strongLocal, .cumulative => .correctness
  | .formalPartial, .none => .correctness
  | .formalPartial, .performance => .correctness
  | .formalPartial, .implementation => .correctness
  | .formalPartial, .hardwareMechanism => .mechanism
  | .formalPartial, .formal => .formal
  | .formalPartial, .composition => .correctness
  | .formalPartial, .cumulative => .correctness
  | .verified, _ => .scopedVerified

/-- Admissibility is the conjunction of two independent constraints:
`CLAIM_STRENGTH <= EVIDENCE_STRENGTH`, and `EVIDENCE_STRENGTH >= floor`. -/
def Acceptable (c : Claim) (k : ClaimKind) (e : Strength) : Prop :=
  c.rank ≤ e.rank ∧ e.rank ≥ (floor c k).rank

/-! ## The constitutional invariant -/

/-- `CLAIM_STRENGTH <= EVIDENCE_STRENGTH` is the first conjunct of
admissibility, by definition. -/
theorem claimRank_neverExceeds_evidence {c : Claim} {e : Strength}
    (h : Acceptable c .none e) : c.rank ≤ e.rank := h.1

/-- VERIFIED is unreachable on an observation, for every claim kind. -/
theorem verified_rejected_on_observation (k : ClaimKind) :
    ¬ Acceptable .verified k .observed := by
  intro h
  have hle : (4 : Nat) ≤ 1 := h.1
  omega

/-- A single measured run cannot support a STRONG_LOCAL performance claim. -/
theorem singleRunCannotBeStrongLocal :
    ¬ Acceptable .strongLocal .performance .executed := by
  intro h
  have hle : (3 : Nat) ≤ 2 := h.2
  omega

/-- A correctness certificate is not evidence for a hardware mechanism. -/
theorem mechanismNeedsMechanismEvidence :
    ¬ Acceptable .strongLocal .hardwareMechanism .correctness := by
  intro h
  have hle : (5 : Nat) ≤ 4 := h.2
  omega

/-- A formal claim needs a kernel-checked proof, not a correctness
certificate. -/
theorem formalClaimNeedsFormalEvidence :
    ¬ Acceptable .formalPartial .formal .correctness := by
  intro h
  have hle : (6 : Nat) ≤ 4 := h.2
  omega

/-- A composition claim needs its own correctness evidence, not just two
reproduced component runs. -/
theorem compositionNeedsCorrectnessEvidence :
    ¬ Acceptable .strongLocal .composition .reproduced := by
  intro h
  have hle : (4 : Nat) ≤ 3 := h.2
  omega

/-! ## Composition is not multiplication -/

def natSum : List Nat → Nat
  | [] => 0
  | a :: t => a + natSum t

/-- Measured end-to-end baseline total for the synthetic two-stage workload. -/
def stageBaselineTotal : Nat := 120
/-- Per-stage baseline totals; they must sum to `stageBaselineTotal`. -/
def stageBaselinePerStage : List Nat := [60, 60]
/-- Per-stage candidate totals under the ideal sequential model. -/
def stageCandidateIdealPerStage : List Nat := [20, 20]
def stageCandidateIdealTotal : Nat := 40
/-- Candidate total actually measured on the composed run: worse than ideal. -/
def stageCandidateMeasuredTotal : Nat := 200

/-- Each isolated stage ran 60/20 = 3, so the multiplicative reference is 9. -/
def sOne : Nat := 3
def multiplicativeReference : Nat := sOne * sOne

/-- The measured composed ratio (120/200) is not the multiplicative reference
(9/1). Cross-multiplied: `120 * 1 ≠ 200 * 9`. This is the theorem behind
`L-SPD-1`: isolated ratios may not be multiplied into a composed result. -/
theorem composed_is_not_the_product :
    stageBaselineTotal * 1 ≠ stageCandidateMeasuredTotal * multiplicativeReference := by
  decide

/-- The ideal sequential model is the ratio of sums, and the per-stage
totals are the ones it sums. -/
theorem ideal_model_sums_the_declared_stages :
    natSum stageBaselinePerStage = stageBaselineTotal ∧
      natSum stageCandidateIdealPerStage = stageCandidateIdealTotal := by
  decide

theorem ideal_model_is_ratio_of_sums :
    natSum stageBaselinePerStage * natSum stageCandidateIdealPerStage
      = stageBaselineTotal * stageCandidateIdealTotal := by
  decide

/-- Interaction factor. With a shared baseline total,
`eta = S_composed / S_ideal = (Tb/Tm) / (Tb/Ti) = Ti / Tm`, so `eta = 1`
exactly when the composed candidate total matches the ideal one. -/
theorem eta_one_iff_measured_equals_ideal (tb ti tm : Nat) (h : 0 < tb) :
    (ti * tb = tm * tb) ↔ (ti = tm) := by
  constructor
  · intro he
    exact Nat.mul_right_cancel h he
  · intro he
    simp [he]

/-- For this fixture the composed run is measurably worse than the ideal model
predicts, so interference is present and eta < 1. -/
theorem fixture_has_interference :
    stageCandidateMeasuredTotal > stageCandidateIdealTotal := by
  decide

theorem fixture_eta_is_not_one :
    stageBaselineTotal * 1 ≠ stageCandidateMeasuredTotal * stageCandidateIdealTotal := by
  decide

/-! ## Vacuous validation is not coverage -/

inductive Check where
  | vacuous | substantive
  deriving DecidableEq, Repr, BEq

def substantiveCount : List Check → Nat
  | [] => 0
  | .substantive :: t => 1 + substantiveCount t
  | .vacuous :: t => substantiveCount t

/-- Every entry of the batch is vacuous. -/
def everyVacuous : List Check → Prop
  | [] => True
  | c :: t => (c == .vacuous) ∧ everyVacuous t

/-- A vacuous batch is non-empty and contains only vacuous entries. The
non-emptiness condition is separate on purpose: "no validations" and "only
vacuous validations" are different conditions, and conflating them turns
missing coverage into apparent coverage. -/
def isVacuousBatch (cs : List Check) : Prop := cs ≠ [] ∧ everyVacuous cs

/-- An arbitrarily large batch of vacuous validations contributes zero
substantive coverage. This is the theorem behind "a high raw test count is not
evidence". -/
theorem vacuousBatch_has_no_coverage (n : Nat) :
    substantiveCount (List.replicate n .vacuous) = 0 := by
  induction n with
  | zero => rfl
  | succ n ih => simp [List.replicate, substantiveCount, ih]

theorem everyVacuous_replicate (n : Nat) :
    everyVacuous (List.replicate n Check.vacuous) := by
  induction n with
  | zero => trivial
  | succ n ih =>
      show everyVacuous (Check.vacuous :: List.replicate n Check.vacuous)
      exact ⟨rfl, ih⟩

/-- Any batch of one or more vacuous validations is detected as a vacuous
batch, for every batch length. -/
theorem isVacuousBatch_replicate (n : Nat) :
    isVacuousBatch (List.replicate (n + 1) Check.vacuous) :=
  ⟨by simp, everyVacuous_replicate (n + 1)⟩

/-- The empty batch is not a vacuous batch: zero validations must not be
reported as (vacuous) coverage. -/
theorem empty_batch_is_not_a_vacuousBatch :
    ¬ isVacuousBatch ([] : List Check) := fun h => h.1 rfl

/-- A batch containing one substantive check is not a vacuous batch, however
many vacuous checks surround it. -/
theorem everyVacuous_app_substantive_false (n : Nat) :
    ¬ everyVacuous (List.replicate n Check.vacuous ++ [Check.substantive]) := by
  induction n with
  | zero =>
      show ¬ everyVacuous ([Check.substantive] : List Check)
      intro h
      have hne : ¬ (Check.substantive == Check.vacuous) := by decide
      exact hne h.1
  | succ n ih =>
      show ¬ everyVacuous (Check.vacuous :: (List.replicate n Check.vacuous ++ [Check.substantive]))
      intro h
      exact ih h.2

theorem oneRealCheckEscapes (n : Nat) :
    ¬ isVacuousBatch (List.replicate n Check.vacuous ++ [Check.substantive]) :=
  fun h => everyVacuous_app_substantive_false n h.2

/-! ## Negative evidence survives a later success -/

inductive Status where
  | proposed | implemented | measured | reproduced | verified
  | regressed | blocked | superseded | quarantined
  deriving DecidableEq, Repr, BEq

def negative : Status → Bool
  | .regressed | .blocked | .quarantined => true
  | _ => false

/-- Appending a later successful status cannot remove an earlier negative
status from the history. This is the law `L-ST-2` enforces on the ledger: it
holds for every status, and in particular for `regressed`, `blocked` and
`quarantined`. -/
theorem negativeSurvivesAppend (hist : List Status) (s : Status) (h : s ∈ hist) :
    s ∈ hist ++ [Status.verified] := by
  simp [List.mem_append, h]

/-- The membership law that makes append-only preservation checkable. -/
theorem membership_is_append_only (hist extra : List Status) (s : Status) :
    s ∈ hist ++ extra ↔ s ∈ hist ∨ s ∈ extra := by
  exact List.mem_append

/-- A regression is recorded as a regression, not as a success. -/
theorem regressionIsNegative :
    negative Status.regressed = true := by
  rfl

theorem verifiedIsNotNegative :
    negative Status.verified = false := by
  rfl

/-! ## Conflicts and gaps bound the claim -/

/-- The claim strength a record may carry after a repeat run. -/
def afterConflict (ratiosAgree : Bool) : Claim :=
  if ratiosAgree then .verified else .candidate

/-- Contradictory repeat runs never yield VERIFIED. -/
theorem conflictBlocksVerified (disagree : ratiosAgree = false) :
    afterConflict ratiosAgree ≠ .verified := by
  simp [afterConflict, disagree]

/-- Agreeing repeat runs may reach VERIFIED (subject to every other gate). -/
theorem agreementCanReachVerified (agree : ratiosAgree = true) :
    afterConflict ratiosAgree = .verified := by
  simp [afterConflict, agree]

/-- The claim strength a record may carry while a promotion-blocking gap is
open. -/
def afterGaps (blocking : List Bool) (c : Claim) : Claim :=
  if blocking.any id then .candidate else c

theorem openGapBlocksVerified (blocking : List Bool)
    (h : blocking.any id = true) :
    afterGaps blocking .verified = .candidate := by
  unfold afterGaps
  rw [h]
  rfl

theorem closedGapsDoNotDowngrade (blocking : List Bool)
    (h : blocking.any id = false) :
    afterGaps blocking .verified = .verified := by
  unfold afterGaps
  rw [h]
  rfl

/-! ## A composition needs a run of its own -/

/-- True when the composition's own run id also appears among its components'
run ids, i.e. the composition was not re-run as one implementation. -/
def reusedComponentRun (own : String) (componentRuns : List String) : Bool :=
  componentRuns.any (fun r => decide (r == own))

theorem reusedRunIdIsNotFresh :
    reusedComponentRun "run-c2" ["run-c1", "run-c2"] = true := by
  decide

theorem distinctRunIdIsFresh :
    reusedComponentRun "run-comp" ["run-c1", "run-c2"] = false := by
  decide

end SSProof