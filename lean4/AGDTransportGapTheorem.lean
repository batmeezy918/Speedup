import Std

/-!
AGD transport-gap theorem: a concrete, independently kernel-checkable witness.

This theorem is deliberately bounded. It formalizes the 4-state / 2-state
quotient example used by the SIM2XR formal-gap bridge. It does NOT claim a
universal theorem for arbitrary operators or silicon implementations.

The key result is that the transport defect vanishes exactly on the
pairwise-constant admissible sector. The defect is globally nonzero, so
admissibility is a load-bearing gate rather than a cosmetic check.
-/

namespace AGDTransportGapTheorem

structure State4 where
  x0 : Int
  x1 : Int
  x2 : Int
  x3 : Int
  deriving DecidableEq, Repr

structure Quot2 where
  a : Int
  b : Int
  deriving DecidableEq, Repr

def full (x : State4) : State4 :=
  { x0 := 2 * x.x0 + x.x1
    x1 := x.x0 + 2 * x.x1
    x2 := 3 * x.x2 + x.x3
    x3 := x.x2 + 3 * x.x3 }

def project (x : State4) : Quot2 :=
  { a := x.x0, b := x.x2 }

def lift (q : Quot2) : State4 :=
  { x0 := q.a, x1 := q.a, x2 := q.b, x3 := q.b }

def reduced (q : Quot2) : Quot2 :=
  { a := 3 * q.a, b := 4 * q.b }

/-- Literal defect D(x) = P(Ax) - B(Px). -/
def gap (x : State4) : Quot2 :=
  let pAx := project (full x)
  let bPx := reduced (project x)
  { a := pAx.a - bPx.a, b := pAx.b - bPx.b }

/-- The invariant/admissible sector: each two-coordinate fiber is constant. -/
def admissible (x : State4) : Prop :=
  x.x0 = x.x1 ∧ x.x2 = x.x3

/-- Exact transport for this model: P(Ax) = B(Px). -/
def transportExact (x : State4) : Prop :=
  project (full x) = reduced (project x)

/-- Expand the literal operator defect into its two residual coordinates. -/
theorem gap_coordinates (x : State4) :
    gap x = { a := x.x1 - x.x0, b := x.x3 - x.x2 } := by
  cases x with
  | mk x0 x1 x2 x3 =>
    simp [gap, project, reduced, full]
    omega

/-- Main theorem: zero formal gap iff the state is admissible. -/
theorem gap_zero_iff_admissible (x : State4) :
    gap x = ({ a := 0, b := 0 } : Quot2) ↔ admissible x := by
  rw [gap_coordinates]
  cases x with
  | mk x0 x1 x2 x3 =>
    simp [admissible]
    omega

/-- The gap criterion is exactly the forward intertwining/transport equation. -/
theorem gap_zero_iff_transport_exact (x : State4) :
    gap x = ({ a := 0, b := 0 } : Quot2) ↔ transportExact x := by
  rw [gap_coordinates]
  cases x with
  | mk x0 x1 x2 x3 =>
    simp [transportExact, project, reduced, full]
    omega

/-- Quotient followed by lift is identity on quotient coordinates. -/
theorem project_lift (q : Quot2) : project (lift q) = q := by
  cases q
  rfl

/-- The defect annihilates every lifted quotient state: D(Sq)=0. -/
theorem gap_lift_zero (q : Quot2) :
    gap (lift q) = ({ a := 0, b := 0 } : Quot2) := by
  rw [gap_zero_iff_admissible]
  exact ⟨rfl, rfl⟩

/-- Reconstruction is exact on the admissible sector: S(Px)=x. -/
theorem lift_project_of_admissible (x : State4) (h : admissible x) :
    lift (project x) = x := by
  cases x with
  | mk x0 x1 x2 x3 =>
    change x0 = x1 ∧ x2 = x3 at h
    rcases h with ⟨h01, h23⟩
    simp [lift, project, h01, h23]

/-- The full operator preserves the admissible sector. -/
theorem full_preserves_admissible (x : State4) (h : admissible x) :
    admissible (full x) := by
  cases x with
  | mk x0 x1 x2 x3 =>
    change x0 = x1 ∧ x2 = x3 at h
    rcases h with ⟨h01, h23⟩
    simp [admissible, full, h01, h23]
    omega

/-- A concrete inadmissible state has a nonzero gap; the gate is necessary. -/
theorem inadmissible_counterexample_has_gap :
    gap ({ x0 := 1, x1 := 0, x2 := 0, x3 := 0 } : State4)
      ≠ ({ a := 0, b := 0 } : Quot2) := by
  decide

/-- Consequence: on the admissible sector, full and reduced steps intertwine. -/
theorem transport_on_admissible (x : State4) (h : admissible x) :
    transportExact x := by
  apply (gap_zero_iff_transport_exact x).mp
  exact (gap_zero_iff_admissible x).2 h

/-- Repeated full execution, with the initial state at iteration zero. -/
def iterateFull : Nat → State4 → State4
  | 0, x => x
  | n + 1, x => full (iterateFull n x)

/-- Repeated reduced execution, with the quotient state at iteration zero. -/
def iterateReduced : Nat → Quot2 → Quot2
  | 0, q => q
  | n + 1, q => reduced (iterateReduced n q)

/-- The invariant is preserved at every full-trajectory step. -/
theorem iterateFull_preserves_admissible (n : Nat) (x : State4)
    (h : admissible x) : admissible (iterateFull n x) := by
  induction n with
  | zero => exact h
  | succ n ih =>
    exact full_preserves_admissible (iterateFull n x) ih

/-- Multi-step consequence: for every iteration count, projection of the full
    trajectory equals the reduced trajectory, provided the initial state is
    admissible. This is a bounded-model transport theorem, not a runtime claim. -/
theorem iterated_transport (n : Nat) (x : State4) (h : admissible x) :
    project (iterateFull n x) = iterateReduced n (project x) := by
  induction n generalizing x with
  | zero => rfl
  | succ n ih =>
    change project (full (iterateFull n x)) =
      reduced (iterateReduced n (project x))
    have hiter := iterateFull_preserves_admissible n x h
    rw [transport_on_admissible (iterateFull n x) hiter]
    exact congrArg reduced (ih x h)

#print axioms AGDTransportGapTheorem.gap_zero_iff_admissible
#print axioms AGDTransportGapTheorem.gap_zero_iff_transport_exact
#print axioms AGDTransportGapTheorem.lift_project_of_admissible
#print axioms AGDTransportGapTheorem.full_preserves_admissible
#print axioms AGDTransportGapTheorem.inadmissible_counterexample_has_gap
#print axioms AGDTransportGapTheorem.transport_on_admissible
#print axioms AGDTransportGapTheorem.iterated_transport

end AGDTransportGapTheorem
