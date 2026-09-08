import Std

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

/-- The publication predicate is deliberately explicit and fail-closed. --/
def publishable (c : EvidenceCertificate) : Prop :=
  c.integrity = true ∧
  c.reproducibility = true ∧
  c.quotientForward = true ∧
  c.reconstructionReverse = true ∧
  c.invariants = true ∧
  c.performance = true ∧
  c.lean = true

/-- Evidence cannot be upgraded unless every publication predicate is established. --/
theorem publish_requires_all_gates
    (c : EvidenceCertificate)
    (h : publishable c) :
    c.integrity = true ∧
    c.reproducibility = true ∧
    c.quotientForward = true ∧
    c.reconstructionReverse = true ∧
    c.invariants = true ∧
    c.performance = true ∧
    c.lean = true := by
  exact h

/-- Forward and reverse quotient witnesses must agree before publication. --/
def bidirectionalQuotientPass (w : QuotientWitness) : Prop :=
  w.equivalent = true

/-- A certificate that is not fully proven is not a verified certificate. --/
def verifiedResult (c : EvidenceCertificate) : Prop :=
  publishable c

end PCSS
