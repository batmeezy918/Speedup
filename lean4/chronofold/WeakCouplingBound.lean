namespace SiliconSpeedup

def iterNat : Nat → (Nat → Nat) → Nat → Nat
  | 0, _, x => x
  | n + 1, f, x => f (iterNat n f x)

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
          have hstep : e 1 ≤ eps * C * z 0 := by
            calc
              e 1 ≤ M * e 0 + eps * C * z 0 := he 0
              _ = eps * C * z 0 := by simp [he0]
          have hz0 : z 0 ≤ z0 := by simpa [iterNat] using hz 0
          have hstep' : e 1 ≤ eps * C * z0 :=
            Nat.le_trans hstep (Nat.mul_le_mul_left (eps * C) hz0)
          simpa [iterNat] using hstep'
      | succ n ih =>
          have hstep := he (n + 1)
          have hz' := hz (n + 1)
          have hbounde : e (n + 1) ≤
              eps * (n + 1) * C * iterNat n (fun v => G * v) z0 := by
            simpa [Nat.add_sub_cancel] using ih
          have hboundz : z (n + 1) ≤
              G * iterNat n (fun v => G * v) z0 := by
            simpa [iterNat] using hz'
          have hstep' : e (n + 2) ≤
              M * (eps * (n + 1) * C * iterNat n (fun v => G * v) z0) +
              eps * C * (G * iterNat n (fun v => G * v) z0) := by
            exact Nat.le_trans hstep (Nat.add_le_add
              (Nat.mul_le_mul_left M hbounde)
              (Nat.mul_le_mul_left (eps * C) hboundz))
          have hcoef := Nat.mul_le_mul_right
            (eps * C * iterNat n (fun v => G * v) z0) (hGdom n)
          have harith :
              M * (eps * (n + 1) * C * iterNat n (fun v => G * v) z0) +
              eps * C * (G * iterNat n (fun v => G * v) z0)
              ≤ eps * (n + 2) * C * iterNat (n + 1) (fun v => G * v) z0 := by
            simpa [iterNat, Nat.mul_add, Nat.add_mul, Nat.mul_assoc,
              Nat.mul_left_comm, Nat.mul_comm] using hcoef
          exact Nat.le_trans hstep' harith

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
      exact Nat.le_trans (he n) (Nat.mul_le_mul_left M ih)

end SiliconSpeedup
