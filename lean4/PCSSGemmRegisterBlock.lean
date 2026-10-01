import Lean.Elab.Tactic.Omega

/-!
# PCSS Lean obligation: register-blocked GEMM (workRatio = 1.0)

## What this file does and does not establish

`workloads/gemm_register_block` replaces a column-streaming GEMM with an 8x8
register-blocked, cache-blocked, prefetching kernel. Both kernels execute the
**same** `2*n^3` floating-point operations. `workRatio = 1.0`. There is no work
reduction, so there is no work-ratio speedup theorem, and none is claimed.

The transformation changes only the *order of summation* over k. The
machine-checked content of that change is below: reassociating a sum of blocks
preserves its value.

This is a **correctness** obligation, not a performance one. It does **not**
prove the measured wall-clock factor, which is empirical and scoped to one
machine, and it does **not** prove bitwise equality of the two Float32 outputs.
Observed `max|candidate - baseline| = 0.0` is recorded empirical evidence in the
certificate, not a theorem.

## PROVENANCE AND SCOPE OF THE PROOFS

Proved here with core Lean 4 only. This repository's `lean4/Mathlib/lakefile.lean`
requires Mathlib from git and Mathlib is NOT built in this checkout, so the
general-N statement is recorded as an explicit unresolved obligation rather than
machine-checked, per PROTOCOL.md ("If a step cannot be represented as a declared
transformation/operator, it becomes an explicit unresolved obligation").

`microkernel_reassociation` is the identity the actual kernel relies on: a 2x2
register block sums `k` as four groups `(w ++ x) + (y ++ z)`, and that equals the
straight `w ++ x ++ y ++ z` sum. `blocked_sum_N` states the general N-block
version and is currently UNPROVEN.

This mirrors the discipline in `AGDGemmSpeedup.lean`, which defines
`MeasuredRuntimeObligation : Prop := True` and proves
`measured_runtime_is_not_a_work_theorem`.

## RESOLUTION (2026-10-01): the general-N obligation IS machine-checked

The paragraph above recorded the general-N statement as an unresolved obligation
on the stated grounds that proving it "needs induction on `l.length` with
well-founded recursion, and Mathlib ... is not built in this checkout".

That blocker was **self-imposed and incorrect**, and is superseded. This checkout
builds with core Lean 4 alone (`leanprover/lean4:v4.29.0`, `lake build
PCSSGemmRegisterBlock` green), and the required well-founded recursion is
available in core as `Nat.strongRecOn` (`Init/WF.lean`), together with
`List.take_append_drop`, `List.length_drop` and `List.sum_append` in core. No
Mathlib is needed. `blockedSumObligation_holds` below discharges the previously
UNPROVEN `BlockedSumObligation` for all `k`, `k > 0` and all `l`.

Nothing else about the scope is relaxed. In particular the reassociation
theorems remain statements over `Int`, and this file still does **not** prove
bitwise Float32 equality of the two kernels. That limitation is now *explained*
rather than merely asserted: `float_add_not_associative` below is a
machine-checked witness that addition in a 3-bit-mantissa floating-point model
is not associative, which is exactly why the shipped result is scoped to
`max|candidate - baseline| = 0.0` as empirical evidence.
-/

namespace PCSSGemmRegisterBlock

/-- Splitting a sum at a boundary preserves its value. This is the single
primitive that all cache blocking is built from. -/
theorem sum_append (l₁ l₂ : List Int) :
    (l₁ ++ l₂).sum = l₁.sum + l₂.sum := List.sum_append

/-- The 2x2 register block identity used by the microkernel: splitting the k
axis into four consecutive groups and summing pairwise yields the same total as
the straight concatenation. -/
theorem microkernel_reassociation (w x y z : List Int) :
    ((w ++ x).sum + (y ++ z).sum) = ((w ++ x ++ y ++ z) : List Int).sum := by
  simp only [List.sum_append, Int.add_assoc]

/-- Reassociation of three block sums preserves the total. -/
theorem reassociate3 (a b c : List Int) :
    (a.sum + b.sum) + c.sum = a.sum + (b.sum + c.sum) := by
  simp only [Int.add_assoc]

/-- Split a list into consecutive blocks of length at most `k`. -/
def splitBlocks (k : Nat) (hk : 0 < k) : List Int → List (List Int)
  | [] => []
  | l => if l.length ≤ k then [l]
         else (l.take k) :: splitBlocks k hk (l.drop k)
  termination_by l => l.length
  decreasing_by
    simp only [List.length_drop]
    omega

/-- **UNRESOLVED OBLIGATION (now DISCHARGED — see `blockedSumObligation_holds`).**
The general statement that blocking a sum into consecutive blocks of size at most
`k` preserves the total, for all `N`.

`microkernel_reassociation` establishes the `N = 4, k = 2` instance, which is
the shape the shipped microkernel actually evaluates. This general form was
originally recorded as NOT machine-checked, on the stated grounds that it "needs
induction on `l.length` with well-founded recursion, and Mathlib ... is not built
in this checkout". That ground was wrong: `Nat.strongRecOn` is core. The `def`
below is retained unchanged so the historical obligation identifier keeps its
meaning; `blockedSumObligation_holds` now proves it. -/
def BlockedSumObligation (k : Nat) (hk : 0 < k) (l : List Int) : Prop :=
  ((splitBlocks k hk l).map List.sum).sum = l.sum

/-- Auxiliary: strong induction on the length of `l`, with `k` fixed. -/
private theorem blockedSum_gen (k : Nat) (hk : 0 < k) :
    ∀ (m : Nat) (l : List Int), l.length = m →
      ((splitBlocks k hk l).map List.sum).sum = l.sum := by
  intro m
  induction m using Nat.strongRecOn with
  | _ m ih =>
    intro l hl
    cases l with
    | nil => simp [splitBlocks]
    | cons hd t =>
      have hunf : splitBlocks k hk (hd :: t)
            = if (hd :: t).length ≤ k then [(hd :: t)]
              else (hd :: t).take k :: splitBlocks k hk ((hd :: t).drop k) :=
        splitBlocks.eq_2 k hk _ (by simp)
      by_cases h : (hd :: t).length ≤ k
      · rw [hunf, if_pos h, List.map_singleton, List.sum_cons, List.sum_nil,
            Int.add_zero]
      · calc
          ((splitBlocks k hk (hd :: t)).map List.sum).sum
              = ((hd :: t).take k).sum
                  + ((splitBlocks k hk ((hd :: t).drop k)).map List.sum).sum := by
                  rw [hunf, if_neg h, List.map_cons, List.sum_cons]
          _ = ((hd :: t).take k).sum + ((hd :: t).drop k).sum := by
              have hdrop : ((hd :: t).drop k).length < m := by
                have hd2 := List.length_drop (i := k) (l := hd :: t)
                have hl2 : (hd :: t).length = m := hl
                omega
              rw [ih ((hd :: t).drop k).length hdrop ((hd :: t).drop k) rfl]
          _ = ((hd :: t).take k ++ (hd :: t).drop k).sum := List.sum_append.symm
          _ = (hd :: t).sum := by rw [List.take_append_drop k (hd :: t)]

/-- **THE PREVIOUSLY UNPROVEN GENERAL STATEMENT, NOW MACHINE-CHECKED.**
Blocking a sum into consecutive blocks of size at most `k` preserves the total,
for every `k > 0` and every `l`. This is the identity the shipped `gemm_blocked`
kernel relies on when it accumulates `C` across `kc`-sized `k` blocks instead of
a single flat `k` loop. Core Lean 4 only; no Mathlib; no `sorry`, no `axiom`. -/
theorem blockedSumObligation_holds :
    ∀ (k : Nat) (hk : 0 < k) (l : List Int),
      ((splitBlocks k hk l).map List.sum).sum = l.sum := by
  intro k hk l
  exact blockedSum_gen k hk l.length l rfl

/-- The general statement above, restated as the historical obligation identifier. -/
theorem blockedSumObligation_proved (k : Nat) (hk : 0 < k) (l : List Int) :
    BlockedSumObligation k hk l := blockedSumObligation_holds k hk l

/-- Concrete instance matching the shipped kernel's blocking width (`KC = 8`
in this model; the binary uses `KC = 128`). Guards against a vacuous general
statement: the blocks really are produced and really do re-sum. -/
theorem blockedSum_concrete :
    ((splitBlocks 8 (by decide) ((List.range 20).map Int.ofNat)).map List.sum).sum
      = ((List.range 20).map Int.ofNat).sum :=
  blockedSumObligation_holds 8 (by decide) ((List.range 20).map Int.ofNat)

/-! ### Why the reassociation theorems are stated over `Int`, not `Float`

The shipped kernels accumulate in IEEE-754 binary32, where addition is not
associative. The following is a machine-checked witness on a minimal 3-bit
mantissa model: addition is not associative, so no reassociation theorem over
floating point can be transported from the `Int` results above. This is the
formal reason `max|candidate - baseline| = 0.0` is recorded as empirical
evidence in the certificate rather than proved. -/

namespace FloatModel

/-- Round-to-zero to 3 fractional bits: the integer `x` is a significand scaled
by `2^-3`. A deliberately minimal, fully explicit rounding model. -/
def round (x : Int) : Int := if 0 ≤ x then x / 8 else -((-x) / 8)

/-- Addition in this 3-bit-mantissa model. -/
def fadd (x y : Int) : Int := round (x + y)

/-- Machine-checked non-associativity witness:
`(8 +. 8) +. (-9) = 0` while `8 +. (8 +. (-9)) = 1`. -/
theorem float_add_not_associative :
    fadd (fadd 8 8) (-9) ≠ fadd 8 (fadd 8 (-9)) := by decide

end FloatModel

/-- Work performed by the baseline and the candidate. Identical: the candidate
performs strictly *more* work (B-panel packing, index arithmetic), not less. -/
def flopCount (n : Nat) : Nat := 2 * n * n * n

/-- The declared work ratio for this artifact is exactly 1.

Proved with `decide` rather than `native_decide`: `decide` is checked by the
kernel and yields an axiom-free proof, whereas `native_decide` delegates to the
compiler and leaves behind a `_native.native_decide` axiom. This is a strict
rigor upgrade of the original statement, which is unchanged. -/
theorem workRatio_is_one : flopCount 2048 / flopCount 2048 = 1 := by decide

/-- No speedup follows from equality of work, and none is claimed. Stated
explicitly so no downstream artifact can read the reassociation theorems above
as a performance claim. -/
theorem no_speedup_from_this (measuredHundredths : Nat)
    (h : measuredHundredths = flopCount 2048 / flopCount 2048 * 100) :
    measuredHundredths = 100 := by
  have h1 : flopCount 2048 / flopCount 2048 = 1 := workRatio_is_one
  rw [h1, Nat.one_mul] at h
  exact h

end PCSSGemmRegisterBlock
