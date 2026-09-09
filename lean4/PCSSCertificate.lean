/-
  PCSS certificate predicates.
  Lean 4 core only. No Mathlib. Fail-closed publication.
-/

namespace PCSS

structure EvidenceCertificate where
  scenarioHash : String
  sourceHash : String
  inputHash : String
  environmentHash : String
  traceHash : String
  quotientHash : String
  reverseHash : String
  integrity : Bool
  reproducibility : Bool
  quotientForward : Bool
  reconstructionReverse : Bool
  invariants : Bool
  performance : Bool
  lean : Bool := false
  deriving Repr

inductive ClaimStrength where
  | candidate
  | strongLocal
  | formalPartial
  | verified
  deriving Repr, DecidableEq

inductive ResultClass where
  | candidate
  | strongLocal
  | formalPartial
  | verified
  | regression
  | drift
  | nonEquivalent
  | reconstructionFailure
  | leanFailure
  | quarantined
  deriving Repr, DecidableEq

structure QuotientWitness where
  forward : String
  reverse : String
  equivalent : Bool
  deriving Repr

structure InvariantWitness where
  name : String
  baseline : String
  candidate : String
  preserved : Bool
  deriving Repr

structure PerformanceWitness where
  metric : String
  baseline : Float
  candidate : Float
  repetitions : Nat
  deriving Repr

def publishable (c : EvidenceCertificate) : Prop :=
  c.integrity = true ∧
  c.reproducibility = true ∧
  c.quotientForward = true ∧
  c.reconstructionReverse = true ∧
  c.invariants = true ∧
  c.performance = true ∧
  c.lean = true

theorem publish_requires_all_gates
    (c : EvidenceCertificate)
    (h : publishable c) :
    c.integrity = true ∧
    c.reproducibility = true ∧
    c.quotientForward = true ∧
    c.reconstructionReverse = true ∧
    c.invariants = true ∧
    c.performance = true ∧
    c.lean = true :=
  h

/-- A certificate with lean=false is not publishable. -/
theorem lean_false_not_publishable
    (c : EvidenceCertificate)
    (h : c.lean = false) :
    ¬ publishable c := by
  intro hp
  have : c.lean = true := hp.2.2.2.2.2.2
  rw [h] at this
  cases this

def bidirectionalQuotientPass (w : QuotientWitness) : Prop :=
  w.equivalent = true

def verifiedResult (c : EvidenceCertificate) : Prop :=
  publishable c

/-- Formal-partial is the strongest label this stack may assign
    without a bound official cocoex Observer reconstruction. -/
def strongestUnverified : ClaimStrength :=
  ClaimStrength.formalPartial

end PCSS
