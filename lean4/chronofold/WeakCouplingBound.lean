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
  have aux : ∀ k, e (k + 1) ≤ eps * (k + 1) * C * iterNat k (fun v => G * v) z0 := by
    intro k
    induction k with
    | zero =>
        have h1 : e (0 + 1) ≤ eps * C * z 0 := by
          calc
            e (0 + 1) ≤ M * e 0 + eps * C * z 0 := he 0
            _ = eps * C * z 0 := by simp [he0]
        have hz0b : z 0 ≤ z0 := by simpa [iterNat] using hz 0
        simpa [iterNat] using (Nat.le_trans h1 (Nat.mul_le_mul_left (eps * C) hz0b))
    | succ k ih =>
        have hstep := he (k + 1)
        have hz' := hz (k + 1)
        have hboundz : z (k + 1) ≤ G * iterNat k (fun v => G * v) z0 := by
          simpa [iterNat] using hz'
        have hstep' : e (k + 2) ≤
            M * (eps * (k + 1) * C * iterNat k (fun v => G * v) z0) +
            eps * C * (G * iterNat k (fun v => G * v) z0) := by
          exact Nat.le_trans hstep (Nat.add_le_add
            (Nat.mul_le_mul_left M ih)
            (Nat.mul_le_mul_left (eps * C) hboundz))
        have hcoef := Nat.mul_le_mul_right
            (eps * C * iterNat k (fun v => G * v) z0) (hGdom k)
        have harith :
            M * (eps * (k + 1) * C * iterNat k (fun v => G * v) z0) +
            eps * C * (G * iterNat k (fun v => G * v) z0)
            ≤ eps * (k + 2) * C * iterNat (k + 1) (fun v => G * v) z0 := by
          simpa [iterNat, Nat.mul_add, Nat.add_mul, Nat.mul_assoc,
            Nat.mul_left_comm, Nat.mul_comm] using hcoef
        exact Nat.le_trans hstep' harith
  have hNarg : N - 1 + 1 = N := Nat.sub_add_cancel hN
  rw [← hNarg]
  exact aux (N - 1)

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
      exact Nat.le_trans (he n) (by simpa using Nat.mul_le_mul_left M ih)

end SiliconSpeedup