/- AGD formal gap, ZERO-IZATION KERNEL — Mathlib-free (Lean 4 core) proof.

   Same statement as /root/AGDFormalGap.lean `AGDFormalGap.divisible_and_small_zero`.

   Why this file exists: /root/AGDFormalGap.lean line 1 is `import Mathlib`, and
   Mathlib is NOT built in this checkout — `lean /root/AGDFormalGap.lean` fails
   with "unknown module prefix 'Mathlib'". The original therefore cannot be
   machine-checked on this host. The lemma is elementary, so it is re-proved in
   Lean 4 core (Lean 4.29.0) so that it IS kernel-checked.

   Nothing in /root is modified. This is a derived artifact. -/

import Std

namespace AGDFormalGapCore

/-- Auxiliary: a nonzero integer has natAbs at least 1. -/
theorem natAbs_ge_one_of_ne_zero {k : Int} (hk0 : k ≠ 0) : 1 ≤ k.natAbs :=
  Nat.succ_le_of_lt (Int.natAbs_pos.mpr hk0)

/-- Auxiliary: for N > 0, |N·k| ≥ |N| whenever k ≠ 0. -/
theorem natAbs_mul_ge (N k : Int) (hN : 0 < N) (hk0 : k ≠ 0) :
    N.natAbs ≤ (N * k).natAbs := by
  rw [Int.natAbs_mul]
  calc N.natAbs ≤ k.natAbs * N.natAbs :=
        Nat.le_mul_of_pos_left N.natAbs (natAbs_ge_one_of_ne_zero hk0)
    _ = N.natAbs * k.natAbs := Nat.mul_comm _ _

/-- The arithmetic zeroization gate (formal gap G3).
    Divisibility by N alone does NOT force vanishing; a size certificate must be
    supplied in addition. This is precisely the Howgrave-Graham / Coppersmith
    gate that the RSA relation-lattice construction needs. -/
theorem divisible_and_small_zero (N y : Int) (hN : 0 < N)
    (hd : N ∣ y) (hb : y.natAbs < N.natAbs) : y = 0 := by
  rcases hd with ⟨k, hk⟩
  by_cases hk0 : k = 0
  · rw [hk, hk0, Int.mul_zero]
  · have key : N.natAbs ≤ y.natAbs := by
      calc N.natAbs ≤ (N * k).natAbs := natAbs_mul_ge N k hN hk0
        _ = y.natAbs := by rw [hk]
    exact (Nat.not_lt_of_ge key hb).elim

/-- G3 as a conditional: divisibility hands you only the implication, never the
    vanishing. -/
theorem divisibility_alone_insufficient (N y : Int) (hN : 0 < N) (hd : N ∣ y) :
    (y.natAbs < N.natAbs → y = 0) :=
  fun hb => divisible_and_small_zero N y hN hd hb

/-- The converse that closes the gap: a genuine multiple of N that is large does
    NOT vanish. This refutes any inference of the form "divisible by N ⇒ zero". -/
theorem large_multiple_does_not_vanish (N y : Int) (hN : 0 < N)
    (hd : N ∣ y) (hne : y ≠ 0) : N.natAbs ≤ y.natAbs := by
  rcases hd with ⟨k, hk⟩
  by_cases hk0 : k = 0
  · exfalso
    exact hne (by rw [hk, hk0, Int.mul_zero])
  · calc N.natAbs ≤ (N * k).natAbs := natAbs_mul_ge N k hN hk0
      _ = y.natAbs := by rw [hk]

end AGDFormalGapCore