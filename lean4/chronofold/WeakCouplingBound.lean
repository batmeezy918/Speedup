namespace SiliconSpeedup

/-- Discrete nonnegative recurrence abstraction of weakly coupled dynamics. -/
def iterNat : Nat → (Nat → Nat) → Nat → Nat
  | 0, _, x => x
  | n + 1, f, x => f (iterNat n f x)

/-- Finite-horizon weak-coupling bound at the algebraic recurrence boundary.
Normed-space instantiations supply the recurrence inequalities separately. -/
theorem weak_coupling_bound
    (M L C eps z0 : Nat)
    (e z : Nat → Nat)
    (G : Nat)
    (hG : G = M + eps * L)
    (hGdom : ∀ n, M * (n + 1) + G ≤ (n + 2) * G)
    (he0 : e 0 = 0)
    (hz : ∀ n, z n ≤ iterNat n (fun v => G * v) z0)
    (he : ∀ n, e (n + 1) ≤ M * e n + eps * C * z n) :
    ∀ N, 1 ≤ N →
      e N ≤ eps * N * C * iterNat (N - 1) (fun v => G * v) z0 := by
  intro N hN
  cases N with
  | zero => exact False.elim (Nat.not_succ_le_zero 0 hN)
  | succ n =>
      induction n with
      | zero =>
          simpa [he0, iterNat] using he 0
      | succ n ih =>
          have hstep := he (n + 1)
          have hz' := hz (n + 1)
          have hbounde : e (n + 1) ≤ eps * (n + 1) * C * iterNat n (fun v => G * v) z0 := ih
          have hboundz : z (n + 1) ≤ G * iterNat n (fun v => G * v) z0 := by
            simpa [iterNat] using hz'
          have hstep' : e (n + 2) ≤
              M * (eps * (n + 1) * C * iterNat n (fun v => G * v) z0) +
              eps * C * (G * iterNat n (fun v => G * v) z0) := by
            exact le_trans hstep (Nat.add_le_add
              (Nat.mul_le_mul_left hbounde M)
              (Nat.mul_le_mul_left hboundz (eps * C)))
          have hcoef := Nat.mul_le_mul_right
            (hGdom n) (eps * C * iterNat n (fun v => G * v) z0)
          have harith :
              M * (eps * (n + 1) * C * iterNat n (fun v => G * v) z0) +
              eps * C * (G * iterNat n (fun v => G * v) z0)
              ≤ eps * (n + 2) * C * iterNat (n + 1) (fun v => G * v) z0 := by
            simpa [iterNat, Nat.mul_add, Nat.add_mul, Nat.mul_assoc,
              Nat.mul_left_comm, Nat.mul_comm] using hcoef
          exact le_trans hstep' harith

/-- Zero coupling collapses the recurrence error to zero. -/
theorem weak_coupling_zero
    (M C : Nat)
    (e : Nat → Nat)
    (he0 : e 0 = 0)
    (he : ∀ n, e (n + 1) ≤ M * e n) :
    ∀ N, e N ≤ 0 := by
  intro N
  induction N with
  | zero => simp [he0]
  | succ n ih =>
      exact le_trans (he n) (Nat.mul_le_mul_left ih M)

end SiliconSpeedup
