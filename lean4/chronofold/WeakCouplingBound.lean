namespace SiliconSpeedup

/-- Discrete nonnegative recurrence abstraction of weakly coupled dynamics. -/
def iterNat : Nat → (Nat → Nat) → Nat → Nat
  | 0, _, x => x
  | n + 1, f, x => f (iterNat n f x)

/-- Zero coupling collapses the recurrence error to zero. -/
theorem weak_coupling_zero
    (M : Nat)
    (e : Nat → Nat)
    (he0 : e 0 = 0)
    (he : ∀ n, e (n + 1) ≤ M * e n) :
    ∀ N, e N = 0 := by
  intro N
  induction N with
  | zero => exact he0
  | succ n ih =>
      have hstep : e (n + 1) ≤ M * e n := he n
      have hmul : M * e n = 0 := by
        rw [ih]
        simp
      have hle : e (n + 1) ≤ 0 := by
        rw [← hmul]
        exact hstep
      exact Nat.eq_zero_of_le_zero hle

/-- Finite-horizon bound under an explicit coefficient hypothesis.
    The coefficient inequality is an assumption, not a silent arithmetic axiom.
    No wall-clock claim is made. -/
theorem weak_coupling_bound
    (eps C z0 : Nat)
    (e : Nat → Nat)
    (step : Nat → Nat)
    (he0 : e 0 = 0)
    (hstep0 : e 1 ≤ eps * C * z0)
    (hrec : ∀ n, e (n + 2) ≤ eps * (n + 2) * C * step n)
    (hstep : ∀ n, step n = iterNat (n + 1) (fun v => v) z0) :
    ∀ N, 1 ≤ N → e N ≤ eps * N * C * iterNat (N - 1) (fun v => v) z0 := by
  intro N hN
  cases N with
  | zero => exact False.elim (Nat.not_succ_le_zero 0 hN)
  | succ n =>
      cases n with
      | zero =>
          simpa [iterNat, he0] using hstep0
      | succ n =>
          have h := hrec n
          have hs := hstep n
          simpa [hs, Nat.add_assoc] using h

end SiliconSpeedup
