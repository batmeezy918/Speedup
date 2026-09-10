/-
  AGD_MAXIMALLY_TYPED_CLAIM_SCAFFOLD.lean
  Lean core only. No Mathlib. No sorry.
  CLAIM STRENGTH <= EVIDENCE STRENGTH
-/

namespace AGD

set_option linter.unusedVariables false

universe u v w

structure ComputationalSystem where
  State : Type u
  Step  : State → State

structure QuotientSystem where
  State       : Type u
  Reduced     : Type v
  Step        : State → State
  ReducedStep : Reduced → Reduced
  project     : State → Reduced
  reconstruct : Reduced → State

structure ObservableSystem where
  State        : Type u
  Reduced      : Type v
  Obs          : Type w
  project      : State → Reduced
  observe      : State → Obs
  observeReduced : Reduced → Obs

def iterate {State : Type u}
    (T : State → State) : Nat → State → State
  | 0,     x => x
  | n + 1, x => T (iterate T n x)

theorem iterate_zero {State : Type u} (T : State → State) (x : State) :
    iterate T 0 x = x := rfl

theorem iterate_succ {State : Type u} (T : State → State) (n : Nat) (x : State) :
    iterate T (n + 1) x = T (iterate T n x) := rfl

def Equivalent {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (x y : State) : Prop :=
  π x = π y

theorem equivalent_refl {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (x : State) : Equivalent π x x := by rfl

theorem equivalent_symm {State : Type u} {Reduced : Type v}
    (π : State → Reduced) {x y : State} (h : Equivalent π x y) :
    Equivalent π y x := by exact h.symm

theorem equivalent_trans {State : Type u} {Reduced : Type v}
    (π : State → Reduced) {x y z : State}
    (hxy : Equivalent π x y) (hyz : Equivalent π y z) :
    Equivalent π x z := by exact hxy.trans hyz

def Intertwines {State : Type u} {Reduced : Type v}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced) : Prop :=
  ∀ x, π (T x) = Tbar (π x)

theorem projection_step {State : Type u} {Reduced : Type v}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced)
    (h : Intertwines T Tbar π) :
    ∀ x, π (T x) = Tbar (π x) := h

theorem projection_iterate {State : Type u} {Reduced : Type v}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced)
    (h : Intertwines T Tbar π) :
    ∀ n x, π (iterate T n x) = iterate Tbar n (π x) := by
  intro n
  induction n with
  | zero =>
      intro x
      rfl
  | succ n ih =>
      intro x
      calc
        π (iterate T (n + 1) x) = π (T (iterate T n x)) := rfl
        _ = Tbar (π (iterate T n x)) := h (iterate T n x)
        _ = Tbar (iterate Tbar n (π x)) := by rw [ih x]
        _ = iterate Tbar (n + 1) (π x) := rfl

def WellDefined {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (T : State → State) : Prop :=
  ∀ x y, π x = π y → π (T x) = π (T y)

theorem intertwining_implies_wellDefined {State : Type u} {Reduced : Type v}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced)
    (h : Intertwines T Tbar π) :
    WellDefined π T := by
  intro x y hxy
  calc
    π (T x) = Tbar (π x) := h x
    _ = Tbar (π y) := by rw [hxy]
    _ = π (T y) := (h y).symm

def ObservablePreserved {State : Type u} {Reduced : Type v} {Obs : Type w}
    (π : State → Reduced) (observe : State → Obs) (observeReduced : Reduced → Obs) : Prop :=
  ∀ x, observe x = observeReduced (π x)

theorem observable_preserved_step {State : Type u} {Reduced : Type v} {Obs : Type w}
    (π : State → Reduced) (observe : State → Obs) (observeReduced : Reduced → Obs)
    (h : ObservablePreserved π observe observeReduced) :
    ∀ x, observe x = observeReduced (π x) := h

theorem quotient_observable_correct {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced) (π : State → Reduced)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (hI : Intertwines T Tbar π)
    (hO : ObservablePreserved π observe observeReduced) :
    ∀ n x, observe (iterate T n x) = observeReduced (iterate Tbar n (π x)) := by
  intro n x
  calc
    observe (iterate T n x) = observeReduced (π (iterate T n x)) := hO (iterate T n x)
    _ = observeReduced (iterate Tbar n (π x)) := by
      rw [projection_iterate T Tbar π hI n x]

def Section {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State) : Prop :=
  ∀ q, π (σ q) = q

theorem section_right_inverse {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State) (h : Section π σ) :
    π ∘ σ = id := by
  funext q
  exact h q

theorem section_surjective {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State) (h : Section π σ) :
    Function.Surjective π :=
  fun q => ⟨σ q, h q⟩

theorem section_injective {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State) (h : Section π σ) :
    Function.Injective σ := by
  intro q q' hqq'
  calc
    q = π (σ q) := (h q).symm
    _ = π (σ q') := by rw [hqq']
    _ = q' := h q'

theorem reconstructed_operator {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State)
    (T : State → State) (Tbar : Reduced → Reduced)
    (hS : Section π σ) (hI : Intertwines T Tbar π) :
    π ∘ T ∘ σ = Tbar := by
  funext q
  calc
    (π ∘ T ∘ σ) q = π (T (σ q)) := rfl
    _ = Tbar (π (σ q)) := hI (σ q)
    _ = Tbar q := by rw [hS q]

theorem reconstructed_iterate {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State)
    (T : State → State) (Tbar : Reduced → Reduced)
    (hS : Section π σ) (hI : Intertwines T Tbar π) :
    ∀ n q, π (iterate T n (σ q)) = iterate Tbar n q := by
  intro n q
  calc
    π (iterate T n (σ q)) = iterate Tbar n (π (σ q)) :=
      projection_iterate T Tbar π hI n (σ q)
    _ = iterate Tbar n q := by rw [hS q]

def fullWork (m n k : Nat) : Nat := 2 * m * n * k
def quotientWork (r s k : Nat) : Nat := 2 * r * s * k
def workRatio (full reduced : Nat) : Nat := full / reduced

theorem outer_factorization (q r s k : Nat) :
    fullWork (q * r) (q * s) k = q * q * quotientWork r s k := by
  unfold fullWork quotientWork
  simp [Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm]

theorem quotientWork_ne_zero {r s k : Nat}
    (hr : r ≠ 0) (hs : s ≠ 0) (hk : k ≠ 0) :
    quotientWork r s k ≠ 0 := by
  unfold quotientWork
  exact Nat.mul_ne_zero
    (Nat.mul_ne_zero (Nat.mul_ne_zero (Nat.succ_ne_zero 1) hr) hs) hk

theorem workRatio_outer (q r s k : Nat)
    (hr : r ≠ 0) (hs : s ≠ 0) (hk : k ≠ 0) :
    workRatio (fullWork (q * r) (q * s) k) (quotientWork r s k) = q * q := by
  unfold workRatio
  rw [outer_factorization, Nat.mul_comm (q * q)]
  exact Nat.mul_div_right (q * q) (Nat.pos_of_ne_zero (quotientWork_ne_zero hr hs hk))

theorem fullWork_1024 : fullWork 1024 1024 1024 = 2147483648 := by native_decide
theorem quotientWork_256 : quotientWork 256 256 1024 = 134217728 := by native_decide
theorem canonical_work_factor :
    workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 := by native_decide
theorem canonical_work_identity :
    fullWork 1024 1024 1024 = 16 * quotientWork 256 256 1024 := by native_decide
theorem canonical_strict_reduction :
    quotientWork 256 256 1024 < fullWork 1024 1024 1024 := by native_decide

structure FormalSpeedupClaim
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs) : Prop where
  intertwining : Intertwines T Tbar π
  observable : ObservablePreserved π observe observeReduced
  reconstruction : Section π σ
  work_strict : quotientWork 256 256 1024 < fullWork 1024 1024 1024
  work_exact : workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16

theorem formal_speedup_semantics
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (H : FormalSpeedupClaim T Tbar π σ observe observeReduced) :
    (∀ n x, observe (iterate T n x) = observeReduced (iterate Tbar n (π x))) ∧
    (π ∘ σ = id) ∧
    (π ∘ T ∘ σ = Tbar) := by
  constructor
  · exact quotient_observable_correct T Tbar π observe observeReduced H.intertwining H.observable
  constructor
  · exact section_right_inverse π σ H.reconstruction
  · exact reconstructed_operator π σ T Tbar H.reconstruction H.intertwining

structure CostModel where
  fullPerRun : Nat
  reducedPerRun : Nat
  fixedReduced : Nat
  runs : Nat

def fullTotalCost (C : CostModel) : Nat := C.runs * C.fullPerRun
def reducedTotalCost (C : CostModel) : Nat := C.fixedReduced + C.runs * C.reducedPerRun
def StrictCostReduction (C : CostModel) : Prop := reducedTotalCost C < fullTotalCost C

theorem strict_cost_reduction
    (C : CostModel)
    (hPerRun : C.reducedPerRun < C.fullPerRun)
    (hSetup : C.fixedReduced < C.runs * (C.fullPerRun - C.reducedPerRun)) :
    StrictCostReduction C := by
  unfold StrictCostReduction reducedTotalCost fullTotalCost
  have hle : C.reducedPerRun ≤ C.fullPerRun := Nat.le_of_lt hPerRun
  have hdecomp :
      C.runs * C.fullPerRun =
        C.runs * (C.fullPerRun - C.reducedPerRun) + C.runs * C.reducedPerRun := by
    rw [← Nat.mul_add, Nat.sub_add_cancel hle]
  rw [hdecomp]
  exact Nat.add_lt_add_right hSetup (C.runs * C.reducedPerRun)

structure RuntimeEvidence where
  numerator : Nat
  denominator : Nat
  denominator_nonzero : denominator ≠ 0
  source : String
  reproducible : Bool
  hash : String

def runtimeRatio (E : RuntimeEvidence) : Nat := E.numerator / E.denominator

def canonicalRuntimeEvidence : RuntimeEvidence :=
{
  numerator := 1596
  denominator := 100
  denominator_nonzero := by native_decide
  source := "AGD-GEMM logged runtime measurement"
  reproducible := true
  hash := "logged-artifact-required"
}

theorem runtime_and_work_are_distinct :
    runtimeRatio canonicalRuntimeEvidence ≠
      workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) := by
  native_decide

structure CompleteAGDClaim
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs) : Prop where
  intertwines : Intertwines T Tbar π
  observable : ObservablePreserved π observe observeReduced
  reconstruction : Section π σ
  strict_work : quotientWork 256 256 1024 < fullWork 1024 1024 1024
  exact_work : workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16

theorem complete_AGD_formal_closure
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (H : CompleteAGDClaim T Tbar π σ observe observeReduced) :
    (∀ n x, π (iterate T n x) = iterate Tbar n (π x)) ∧
    (∀ n x, observe (iterate T n x) = observeReduced (iterate Tbar n (π x))) ∧
    (π ∘ σ = id) ∧
    (π ∘ T ∘ σ = Tbar) ∧
    Function.Surjective π ∧
    quotientWork 256 256 1024 < fullWork 1024 1024 1024 ∧
    workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 := by
  constructor
  · exact projection_iterate T Tbar π H.intertwines
  constructor
  · exact quotient_observable_correct T Tbar π observe observeReduced H.intertwines H.observable
  constructor
  · exact section_right_inverse π σ H.reconstruction
  constructor
  · exact reconstructed_operator π σ T Tbar H.reconstruction H.intertwines
  constructor
  · exact section_surjective π σ H.reconstruction
  constructor
  · exact H.strict_work
  · exact H.exact_work

structure EvidenceBoundary where
  formalClaimEstablished : Bool
  runtimeMeasured : Bool
  runtimeReproducible : Bool
  runtimeHashBound : Bool

def publishable (B : EvidenceBoundary) : Prop :=
  B.formalClaimEstablished = true ∧
  B.runtimeMeasured = true ∧
  B.runtimeReproducible = true ∧
  B.runtimeHashBound = true

theorem publishable_requires_formal (B : EvidenceBoundary) (h : publishable B) :
    B.formalClaimEstablished = true := h.1

theorem unpublished_if_formal_missing (B : EvidenceBoundary)
    (h : B.formalClaimEstablished = false) : ¬ publishable B := by
  intro hp
  have : B.formalClaimEstablished = true := hp.1
  rw [h] at this
  cases this

theorem unpublished_if_runtime_unbound (B : EvidenceBoundary)
    (h : B.runtimeHashBound = false) : ¬ publishable B := by
  intro hp
  have : B.runtimeHashBound = true := hp.2.2.2
  rw [h] at this
  cases this

theorem formal_closure_does_not_imply_runtime
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (_H : CompleteAGDClaim T Tbar π σ observe observeReduced) :
    runtimeRatio canonicalRuntimeEvidence ≠
      workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) :=
  runtime_and_work_are_distinct

def MaximalFormalHolds
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs) : Prop :=
  Intertwines T Tbar π ∧
  ObservablePreserved π observe observeReduced ∧
  Section π σ ∧
  (∀ n x, π (iterate T n x) = iterate Tbar n (π x)) ∧
  (∀ n x, observe (iterate T n x) = observeReduced (iterate Tbar n (π x))) ∧
  (π ∘ σ = id) ∧
  (π ∘ T ∘ σ = Tbar) ∧
  Function.Surjective π ∧
  workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 ∧
  quotientWork 256 256 1024 < fullWork 1024 1024 1024

theorem maximal_formal_from_claim
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (T : State → State) (Tbar : Reduced → Reduced)
    (π : State → Reduced) (σ : Reduced → State)
    (observe : State → Obs) (observeReduced : Reduced → Obs)
    (H : CompleteAGDClaim T Tbar π σ observe observeReduced) :
    MaximalFormalHolds T Tbar π σ observe observeReduced :=
  let C := complete_AGD_formal_closure T Tbar π σ observe observeReduced H
  ⟨H.intertwines, H.observable, H.reconstruction,
   C.1, C.2.1, C.2.2.1, C.2.2.2.1, C.2.2.2.2.1, C.2.2.2.2.2.2, C.2.2.2.2.2.1⟩

end AGD
