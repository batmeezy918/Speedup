namespace AGDGemmWork

def fullWork (m n k : Nat) : Nat :=
  2 * m * n * k

def quotientWork (r s k : Nat) : Nat :=
  2 * r * s * k

def squareWork (d k : Nat) : Nat :=
  fullWork d d k

def workRatio (full reduced : Nat) : Nat :=
  full / reduced

theorem outer_factorization (q r s k : Nat) :
    fullWork (q * r) (q * s) k = q * q * quotientWork r s k := by
  unfold fullWork quotientWork
  simp [Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm]

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

theorem workRatio_outer
    (q r s k : Nat)
    (hr : r ≠ 0) (hs : s ≠ 0) (hk : k ≠ 0) :
    workRatio (fullWork (q * r) (q * s) k) (quotientWork r s k) = q * q := by
  unfold workRatio
  rw [outer_factorization, Nat.mul_comm (q * q)]
  exact Nat.mul_div_right (q * q)
    (Nat.pos_of_ne_zero (quotientWork_ne_zero hr hs hk))

theorem workRatio_square
    (q r k : Nat)
    (hr : r ≠ 0) (hk : k ≠ 0) :
    workRatio (squareWork (q * r) k) (squareWork r k) = q * q := by
  unfold squareWork
  exact workRatio_outer q r r k hr hr hk

theorem fullWork_1024 :
    fullWork 1024 1024 1024 = 2147483648 := by
  native_decide

theorem quotientWork_256 :
    quotientWork 256 256 1024 = 134217728 := by
  native_decide

theorem canonical_ratio :
    fullWork 1024 1024 1024 = 16 * quotientWork 256 256 1024 := by
  native_decide

theorem strict_work_reduction :
    quotientWork 256 256 1024 < fullWork 1024 1024 1024 := by
  native_decide

theorem factor_four_gives_sixteen :
    squareWork 1024 1024 = 16 * squareWork 256 1024 := by
  native_decide

theorem four_sq : (4 : Nat) * 4 = 16 := by
  native_decide

theorem dim_factorization : (1024 : Nat) = 4 * 256 := by
  native_decide

theorem canonical_workRatio :
    workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 := by
  native_decide

theorem canonical_is_instance_of_q_square :
    workRatio (fullWork (4 * 256) (4 * 256) 1024) (quotientWork 256 256 1024)
      = 4 * 4 :=
  workRatio_outer 4 256 256 1024 (by native_decide) (by native_decide) (by native_decide)

theorem canonical_q_square_equals_sixteen :
    workRatio (fullWork (4 * 256) (4 * 256) 1024) (quotientWork 256 256 1024) = 16 := by
  rw [canonical_is_instance_of_q_square, four_sq]

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
