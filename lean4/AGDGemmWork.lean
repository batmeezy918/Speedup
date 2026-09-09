/-
  AGD-GEMM Work Model
  -------------------
  Arithmetic work-reduction layer only.

  Proves:
    * full GEMM work = 2mnk
    * quotient GEMM work = 2rsk
    * outer reduction of both dimensions by q yields exactly q² work
    * the canonical 1024→256 instance is exactly 16×

  Does NOT prove:
    * semantic equivalence of any particular projection
    * reconstruction correctness
    * measured wall-clock speedup (15.96× is evidence, not a theorem)
    * hardware superiority
-/

namespace AGDGemmWork

/-- Full GEMM arithmetic work: 2mnk scalar operations. -/
def fullWork (m n k : Nat) : Nat :=
  2 * m * n * k

/-- Quotient GEMM arithmetic work: 2rsk scalar operations. -/
def quotientWork (r s k : Nat) : Nat :=
  2 * r * s * k

/-- Square GEMM work on outer dimension `d`. -/
def squareWork (d k : Nat) : Nat :=
  fullWork d d k

/-- Exact modeled work ratio when the denominator divides the numerator. -/
def workRatio (full reduced : Nat) : Nat :=
  full / reduced

/-! ## Generic algebraic identities -/

/-- Reducing both outer dimensions by factor `q` multiplies work by `q²`. -/
theorem outer_factorization (q r s k : Nat) :
    fullWork (q * r) (q * s) k = q * q * quotientWork r s k := by
  unfold fullWork quotientWork
  simp [Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm]

/-- Square case of the same identity. -/
theorem square_reduction (q r k : Nat) :
    squareWork (q * r) k = q * q * squareWork r k := by
  unfold squareWork
  simpa [Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm] using
    outer_factorization q r r k

theorem quotientWork_ne_zero
    {r s k : Nat} (hr : r ≠ 0) (hs : s ≠ 0) (hk : k ≠ 0) :
    quotientWork r s k ≠ 0 := by
  unfold quotientWork
  exact Nat.mul_ne_zero
    (Nat.mul_ne_zero (Nat.mul_ne_zero (Nat.succ_ne_zero 1) hr) hs) hk

/-- When the reduced work is nonzero, the modeled ratio is exactly `q²`. -/
theorem workRatio_outer
    (q r s k : Nat)
    (hr : r ≠ 0) (hs : s ≠ 0) (hk : k ≠ 0) :
    workRatio (fullWork (q * r) (q * s) k) (quotientWork r s k) = q * q := by
  unfold workRatio
  rw [outer_factorization]
  exact Nat.mul_div_right (q * q) (quotientWork_ne_zero hr hs hk)

theorem workRatio_square
    (q r k : Nat)
    (hr : r ≠ 0) (hk : k ≠ 0) :
    workRatio (squareWork (q * r) k) (squareWork r k) = q * q := by
  unfold squareWork
  exact workRatio_outer q r r k hr hr hk

/-! ## Canonical 1024 → 256 instance (q = 4) -/

theorem fullWork_1024 :
    fullWork 1024 1024 1024 = 2147483648 := by
  native_decide

theorem quotientWork_256 :
    quotientWork 256 256 1024 = 134217728 := by
  native_decide

/-- The canonical quotient reduces modeled work by exactly 16×. -/
theorem canonical_ratio :
    fullWork 1024 1024 1024 = 16 * quotientWork 256 256 1024 := by
  native_decide

theorem strict_work_reduction :
    quotientWork 256 256 1024 < fullWork 1024 1024 1024 := by
  native_decide

/-- 1024 = 4 × 256, hence reducing both outer dimensions by 4 gives 4² = 16. -/
theorem factor_four_gives_sixteen :
    squareWork 1024 1024 = 16 * squareWork 256 1024 := by
  native_decide

theorem four_sq : (4 : Nat) * 4 = 16 := by
  native_decide

theorem dim_factorization : (1024 : Nat) = 4 * 256 := by
  native_decide

/-- Canonical modeled work ratio is 16. -/
theorem canonical_workRatio :
    workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 := by
  native_decide

/-- The 16× result is exactly the generic `q²` theorem at `q = 4`. -/
theorem canonical_is_instance_of_q_square :
    workRatio (fullWork (4 * 256) (4 * 256) 1024) (quotientWork 256 256 1024)
      = 4 * 4 :=
  workRatio_outer 4 256 256 1024 (by native_decide) (by native_decide) (by native_decide)

theorem canonical_q_square_equals_sixteen :
    workRatio (fullWork (4 * 256) (4 * 256) 1024) (quotientWork 256 256 1024) = 16 := by
  rw [canonical_is_instance_of_q_square, four_sq]

/-! ## Packaged work-model closure -/

theorem work_model_closure :
    fullWork 1024 1024 1024 = 2147483648 ∧
    quotientWork 256 256 1024 = 134217728 ∧
    fullWork 1024 1024 1024 = 16 * quotientWork 256 256 1024 ∧
    quotientWork 256 256 1024 < fullWork 1024 1024 1024 ∧
    squareWork 1024 1024 = 16 * squareWork 256 1024 ∧
    workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 ∧
    workRatio (fullWork (4 * 256) (4 * 256) 1024) (quotientWork 256 256 1024) = 4 * 4 :=
  ⟨fullWork_1024, quotientWork_256, canonical_ratio,
   strict_work_reduction, factor_four_gives_sixteen, canonical_workRatio,
   canonical_is_instance_of_q_square⟩

end AGDGemmWork
