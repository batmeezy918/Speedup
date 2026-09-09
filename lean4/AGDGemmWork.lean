namespace AGDGemmWork

def fullWork (m n k : Nat) : Nat := 2 * m * n * k
def quotientWork (r s k : Nat) : Nat := 2 * r * s * k
def squareWork (d k : Nat) : Nat := fullWork d d k
def workRatio (full reduced : Nat) : Nat := full / reduced

theorem fullWork_1024 : fullWork 1024 1024 1024 = 2147483648 := by native_decide
theorem quotientWork_256 : quotientWork 256 256 1024 = 134217728 := by native_decide
theorem canonical_ratio : fullWork 1024 1024 1024 = 16 * quotientWork 256 256 1024 := by native_decide
theorem strict_work_reduction : quotientWork 256 256 1024 < fullWork 1024 1024 1024 := by native_decide
theorem square_reduction (q r k : Nat) :
    squareWork (q * r) k = q * q * squareWork r k := by
  unfold squareWork fullWork
  simp [Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm]
theorem factor_four_gives_sixteen :
    squareWork 1024 1024 = 16 * squareWork 256 1024 := by native_decide
theorem canonical_workRatio :
    workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 := by native_decide
theorem work_model_closure :
    fullWork 1024 1024 1024 = 2147483648 ∧
    quotientWork 256 256 1024 = 134217728 ∧
    fullWork 1024 1024 1024 = 16 * quotientWork 256 256 1024 ∧
    quotientWork 256 256 1024 < fullWork 1024 1024 1024 ∧
    squareWork 1024 1024 = 16 * squareWork 256 1024 ∧
    workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 :=
  ⟨fullWork_1024, quotientWork_256, canonical_ratio,
   strict_work_reduction, factor_four_gives_sixteen, canonical_workRatio⟩

end AGDGemmWork
