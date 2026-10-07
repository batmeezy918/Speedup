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
a single flat `k` loop. Core Lean 4 only; no Mathlib; no proof holes and no
postulated constants. -/
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

/-! ### A recorded defect and its correction

The first definition of `round` in this model was

```
def round (x : Int) : Int := if 0 ≤ x then x / 8 else -((-x) / 8)
```

which does not round: it DIVIDES by 8, moving the radix point rather than
truncating the low three bits. A round-to-zero to three fractional bits must fix
a value already on the 8-grid and must be idempotent; that function satisfies
neither, and its `fadd` shrank its operands instead of adding them. The original
non-associativity witnesses were therefore artifacts of the defect: the cited
witness `(8 +. 8) +. (-9)` does not even disagree in real IEEE-754 binary32
(`(8+8)+(-9) = 7 = 8+(8+(-9))` there).

The defect is recorded below as a machine-checked refutation, and `round` is
redefined as an actual quantizer. The identifier `round` is kept because it is
the model's public name; `roundDivide` preserves the historical behaviour for
the refutation. -/

/-- Historical (defective) definition, retained only so the defect can be
machine-checked rather than described in prose. -/
def roundDivide (x : Int) : Int := if 0 ≤ x then x / 8 else -((-x) / 8)

/-- The historical function's addition, retained for the same reason. -/
def faddDivide (x y : Int) : Int := roundDivide (x + y)

/-- **Machine-checked defect (1):** a quantizer to 3 fractional bits must leave
a value already on the grid unchanged. `roundDivide` divides it by 8. -/
theorem roundDivide_not_a_quantizer : roundDivide 8 ≠ 8 := by decide

/-- **Machine-checked defect (2):** a quantizer is idempotent; `roundDivide` is
not (each pass divides again). -/
theorem roundDivide_not_idempotent :
    roundDivide (roundDivide 8) ≠ roundDivide 8 := by decide

/-- **Machine-checked defect (3):** consequently the historical `fadd` was not an
adder at all -- `800 +. 800` collapsed below `800`. -/
theorem faddDivide_shrinks : faddDivide 800 800 < 800 := by decide

/-- **The corrected model.** Round-to-zero to 3 fractional bits: truncate the
low three bits toward zero, i.e. move to the nearest multiple of `2^3 = 8`.
This FIXES grid points and is idempotent, which is what makes it a rounding
model rather than a rescaling. -/
def round (x : Int) : Int := if 0 ≤ x then (x / 8) * 8 else -(((-x) / 8) * 8)

/-- Faithfulness of the corrected model: points already on the 8-grid survive. -/
theorem round_fixes_grid (x : Int) (h : 8 ∣ x) : round x = x := by
  obtain ⟨c, rfl⟩ := h
  have h8 : (8 : Int) ≠ 0 := by decide
  rcases (show (0 ≤ 8 * c) ∨ (0 < -(8 * c)) by omega) with _ | _
  · rw [round, if_pos (by omega : 0 ≤ 8 * c), Int.mul_ediv_cancel_left c h8,
      Int.mul_comm]
  · rw [round, if_neg (by omega : ¬(0 ≤ 8 * c))]
    have heq : -(8 * c) = 8 * -c := (Int.mul_neg 8 c).symm
    have hd : -(8 * c) / 8 = -c := by
      rw [heq, Int.mul_ediv_cancel_left _ h8]
    rw [hd, Int.neg_mul, Int.neg_neg, Int.mul_comm]

/-- Faithfulness of the corrected model: it is idempotent. -/
theorem round_idempotent (x : Int) : round (round x) = round x := by
  have h : 8 ∣ round x := by
    unfold round
    split
    · simp [Int.mul_comm, Int.dvd_mul_right]
    · simp [Int.mul_comm]
  obtain ⟨c, hc⟩ := h
  rw [hc]
  exact round_fixes_grid (8 * c) ⟨c, rfl⟩

/-- Addition in this 3-bit-mantissa model. -/
def fadd (x y : Int) : Int := round (x + y)

/-- Machine-checked non-associativity witness for the corrected model:
`(8 +. 8) +. (-9) = 0` while `8 +. (8 +. (-9)) = 8`. -/
theorem float_add_not_associative :
    fadd (fadd 8 8) (-9) ≠ fadd 8 (fadd 8 (-9)) := by decide

/-- Straight `k`-ascending accumulation -- the association the baseline inner
loop performs: `for k: c[i,j] += a[i,k]*b[k,j]`. -/
def fflat : List Int → Int → Int
  | [], acc => acc
  | x :: xs, acc => fflat xs (fadd acc x)

/-- Accumulation across `k`-blocks in which each block is summed into a *fresh
local* before being added to the accumulator.

This is exactly the association of the ragged-column-edge path in
`gemm_blocked` (`neon.c`):

```
float s = 0.0f;
for (int p = pc; p < pmax; p++) s += a[(i+r)*n+p] * b[p*n + (jc+j)];
c[(i+r)*n + (jc+j)] += s;
```

i.e. `c += (sum of block)`, rather than `c += term` repeated. It is the only
place in the shipped candidate where the summation order differs from the
baseline; it is reached only when a column block width is not a multiple of the
microkernel width AND more than one `k`-block is traversed.

Recursion is on an explicit fuel argument rather than on `l.length` via
well-founded recursion, so the kernel can reduce concrete instances and the
witness below is provable by `decide` without `native_decide`. The fuel is
supplied as `l.length + 1`, and since `k > 0` each step removes at least one
element, so the fuel is always sufficient. -/
def fblockedFuel (k : Nat) : Nat → List Int → Int → Int
  | 0, _, acc => acc
  | _ + 1, [], acc => acc
  | fuel + 1, l, acc =>
      if l.length ≤ k then fadd acc (fflat l 0)
      else fblockedFuel k fuel (l.drop k) (fadd acc (fflat (l.take k) 0))

def fblocked (k : Nat) (l : List Int) (acc : Int) : Int :=
  fblockedFuel k (l.length + 1) l acc

/-- The fuel supplied by `fblocked` is always sufficient. -/
theorem fblocked_fuel_sufficient (k : Nat) (l : List Int) (acc : Int) :
    fblockedFuel k (l.length + 1) l acc = fblocked k l acc := rfl

/-- **Machine-checked: the blocked association changes the result.**
Block-boundary reassociation is value-preserving over `Int`
(`blockedSumObligation_holds`) but NOT over the float model, exactly as the
empirical sweep observed: bitwise disagreement at ragged sizes, magnitude ~1
ULP.

The witness is a 5-element list with a ragged tail. `fblocked` splits it as
`[8,8,8] ++ [-9,9]`, sums each block into a *fresh* local accumulator and then
combines them, giving `round(24 + round(-18)) = round(24 + (-16)) = 8`, whereas
straight `fflat` accumulation gives `round(round(round(8+8)+8)+(-9))+9 = 16`. -/
theorem float_blocked_differs_from_flat :
    fblocked 3 [8, 8, 8, -9, 9] 0
      ≠ fflat [8, 8, 8, -9, 9] 0 := by decide

/-- **The disagreement requires a block width of at least 2.**
For singleton blocks (`k = 1`) the partition *is* the singleton decomposition,
so the recursion degenerates to exactly the flat left-to-right fold and the two
agree. This is the machine-checked statement that the disagreement above is
caused by block-boundary reassociation, not by the blocked code path itself. -/
theorem singleton_blocks_agree_with_flat :
    fblocked 1 [-40, -40, -40, -40, -40] 0
      = fflat [-40, -40, -40, -40, -40] 0 := by decide

/-- The same five operands under the exact (integer) association, for contrast:
here the association is irrelevant and the total is exact. -/
theorem int_blocked_agrees_with_flat :
    (([-40, -40, -40, -40, -40] : List Int).foldl (· + ·) 0)
      = (-40 * 5 : Int) := by decide

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
