/-
  ClaimRegistry — claim classes as data.

  This module does not prove any run was fast.
  It proves that VERIFIED is not a folder name:
  a claim may be marked Verified only if every PCSS gate is true,
  and a certificate with lean = false is not publishable.

  Mathlib-free. No sorry. No axioms beyond Lean core.
-/

import PCSSCertificate

namespace Claims

inductive ClaimClass where
  | quarantined
  | candidate
  | measuredBaseline
  | strongLocal
  | negative
  | theoreticalOrSimulated
  | formalPartial
  | verified
  deriving DecidableEq, Repr

/-- Public posture of one named packet. -/
structure Claim where
  id : String
  klass : ClaimClass
  integrity : Bool := false
  reproducibility : Bool := false
  quotientForward : Bool := false
  reconstructionReverse : Bool := false
  invariants : Bool := false
  performance : Bool := false
  lean : Bool := false
  deriving Repr

def Claim.allGates (c : Claim) : Bool :=
  c.integrity && c.reproducibility && c.quotientForward &&
  c.reconstructionReverse && c.invariants && c.performance && c.lean

/-- Elevation rule: Verified is exactly the seven-gate conjunction. -/
def Claim.wellClassified (c : Claim) : Prop :=
  (c.klass = ClaimClass.verified) ↔ (c.allGates = true)

theorem verified_iff_all_gates (c : Claim) :
    c.wellClassified ↔ ((c.klass = ClaimClass.verified) ↔ (c.allGates = true)) :=
  Iff.rfl

theorem lean_false_not_all_gates (c : Claim) (h : c.lean = false) :
    c.allGates = false := by
  unfold Claim.allGates
  rw [h]
  simp

theorem lean_false_not_verified
    (c : Claim) (hw : c.wellClassified) (hlean : c.lean = false) :
    c.klass ≠ ClaimClass.verified := by
  intro hv
  have hall : c.allGates = true := hw.mp hv
  have hfalse : c.allGates = false := lean_false_not_all_gates c hlean
  have contra : true = false := by
    rw [← hall]
    exact hfalse
  cases contra

/-- A PCSS certificate may be viewed as a claim skeleton.
    Class is not inferred from a path. -/
def ofCertificate (id : String) (klass : ClaimClass)
    (cert : PCSS.EvidenceCertificate) : Claim :=
  { id := id
    klass := klass
    integrity := cert.integrity
    reproducibility := cert.reproducibility
    quotientForward := cert.quotientForward
    reconstructionReverse := cert.reconstructionReverse
    invariants := cert.invariants
    performance := cert.performance
    lean := cert.lean }

theorem ofCertificate_lean_false_not_verified
    (id : String) (klass : ClaimClass) (cert : PCSS.EvidenceCertificate)
    (hw : (ofCertificate id klass cert).wellClassified)
    (hlean : cert.lean = false) :
    (ofCertificate id klass cert).klass ≠ ClaimClass.verified := by
  have hclaim : (ofCertificate id klass cert).lean = false := by
    unfold ofCertificate
    exact hlean
  exact lean_false_not_verified (ofCertificate id klass cert) hw hclaim

/-- STRONG_LOCAL is the honest class when every empirical gate holds
    and the Lean identity obligation does not. -/
def Claim.strongLocalShape (c : Claim) : Prop :=
  c.integrity = true ∧ c.reproducibility = true ∧ c.quotientForward = true ∧
  c.reconstructionReverse = true ∧ c.invariants = true ∧
  c.performance = true ∧ c.lean = false

theorem sim2xr_shape_is_not_verified
    (c : Claim) (hw : c.wellClassified) (h : c.strongLocalShape) :
    c.klass ≠ ClaimClass.verified :=
  lean_false_not_verified c hw h.2.2.2.2.2.2

/-- Work-ratio identity is a formal-partial fact. It does not
    authorize the Verified class by itself. -/
theorem formal_partial_not_auto_verified
    (c : Claim) (hw : c.wellClassified)
    (hklass : c.klass = ClaimClass.formalPartial) :
    c.klass ≠ ClaimClass.verified := by
  intro hv
  rw [hklass] at hv
  cases hv

end Claims
