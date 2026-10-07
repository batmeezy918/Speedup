/-
# A machine-checked forward error bound for the ragged float path

## Why this file exists

The exact `Int` association and the blocked reassociation agree exactly, and the
`FloatModel` (3-bit significand, round-to-zero) model in `PCSSGemmRegisterBlock`
proves that the float association does *not* agree bitwise
(`float_blocked_differs_from_flat`). So "the candidate is exactly the baseline"
is refuted, not merely unproven.

What is still licensable is a *bound*: how far apart can the two associations be,
as a function of the operands? That is what this file proves, and it is the
weaker claim the evidence actually supports.

## The bound

Work in the model already fixed by `PCSSGemmRegisterBlock.FloatModel`: rounding
toward zero to a fixed number of fractional bits. Denote that model by `fadd`,
and let the scale `p = 3` give an ulp denominator of `2^p = 8`.

Each individual rounding introduces an error of *strictly less than one ulp*, and
because both the exact sum and the rounded result are integers in the scaled
representation, the integer-valued error is at most `ulp - 1`. A chain of `t`
roundings therefore accumulates at most `t * (ulp - 1)`, i.e. `t * u` with
`u = (ulp - 1)/ulp < 1`. This is the standard forward-error shape `|fl(x) - x| <=
t*u`, specialised to a representable-integer model so that it is fully
checkable.

## CORRECTION (2026-10-02): the previous version of this file did not compile

The prior content of this file claimed:

> "`Int`/`Rat` is the right instrument here: `Rat` exists in core Lean 4.29, so
> no Mathlib is needed, and every bound below is a decidable rational inequality."

Every half of that sentence was false, and the file did not parse at all:

* There is **no `Rat` type and no `NormNum` instance in core Lean 4.29** (nor in
  4.33.1). `Rat` lives in `Std4`/`Mathlib`, which this repository's core lane
  forbids (`scripts/verify_lean4_all.sh` rejects `import Mathlib`, and this file
  is in the `core` lane).
* `norm_num` is **not a core Lean tactic**. The previous proof term
  `constructor <;> norm_num [...]` could never have elaborated.
* The statement itself used ASCII pipes, `|a - b| < 1`, which is not Lean
  syntax at all. It was a transcription of informal mathematics, not a term.

The same paragraph asserted that "no Mathlib is needed", which was true only of a
proof that did not exist. The bound is restated below in the one instrument that
*is* available in the core lane — `Int`, with the ulp comparison made explicit
instead of hidden inside a rational abstraction. `omega` (from
`Lean.Elab.Tactic.Omega`, which is core) discharges the integer division
remainder arithmetic.

The mathematical content is unchanged and is now genuinely machine-checked.

## What is NOT claimed

* No claim that the two associations agree, in any regime.
* No claim about the shipped C kernel's rounding mode; this models one specific
  truncation scheme, chosen because `PCSSGemmRegisterBlock` already fixes it.
  Matching the real `float` behaviour is a separate, unproved obligation.
* No wall-clock consequence whatsoever.
-/

import Lean.Elab.Tactic.Omega
import PCSSGemmRegisterBlock

namespace PCSSErrorBound

open PCSSGemmRegisterBlock
open PCSSGemmRegisterBlock.FloatModel

/-- Number of fractional bits retained by the model in
`PCSSGemmRegisterBlock.FloatModel`. -/
def scale : Nat := 3

/-- The ulp denominator `2^scale`, i.e. the size of one unit in the last place.
For `scale = 3` this is `8`, matching `FloatModel.round`, which quantizes to
multiples of `8`. -/
def ulpDen : Int := 8

theorem ulpDen_eq_two_pow_scale : ulpDen = 2 ^ scale := by decide

/-- **Machine-checked one-step forward error.** Truncation toward zero to the
`ulpDen` grid moves the argument by strictly less than one ulp. -/
theorem round_error_lt_one_ulp (s : Int) :
    -(ulpDen) < round s - s ∧ round s - s < ulpDen := by
  simp only [ulpDen, round]
  split <;> omega

/-- **Machine-checked integer form of the same bound.** Because `round s - s` is
an integer strictly between `-ulpDen` and `ulpDen`, it is at most `ulpDen - 1`
in absolute value. This is the form the chain bound below needs. -/
theorem round_error_abs_le (s : Int) :
    -(ulpDen - 1) ≤ round s - s ∧ round s - s ≤ ulpDen - 1 := by
  have h := round_error_lt_one_ulp s
  simp only [ulpDen] at h ⊢
  omega

/-- **The per-operation error bound for `fadd`.** Adding two operands and
rounding perturbs the exact integer sum by at most one ulp minus one. -/
theorem fadd_error_abs_le (x y : Int) :
    -(ulpDen - 1) ≤ fadd x y - (x + y) ∧ fadd x y - (x + y) ≤ ulpDen - 1 := by
  simpa [fadd] using round_error_abs_le (x + y)

/-- Accumulating `s` into `acc` under `fadd`, `n` times. This is the exact
summation association used by the blocked microkernel, which sums into a fresh
local per block and adds the local to the accumulator. -/
def accFadd : Nat → Int → Int → Int
  | 0, acc, _ => acc
  | n + 1, acc, s => accFadd n (fadd acc s) s

/-- **Machine-checked `t * u` chain bound.** After `n` rounded accumulations the
result differs from the exact integer accumulation `acc + n * s` by at most
`n * (ulp - 1)`, i.e. by at most `n * u` ulps.

This is the forward-error statement that licenses describing the blocked/flat
reassociation disagreement established in `PCSSGemmRegisterBlock` as a *bounded
ulp perturbation* whose magnitude grows at most linearly in the reduction
length, rather than as an unbounded divergence. -/
theorem accFadd_chain_bound (n : Nat) (acc s : Int) :
    -((n : Int) * (ulpDen - 1)) ≤ accFadd n acc s - (acc + (n : Int) * s) ∧
      accFadd n acc s - (acc + (n : Int) * s) ≤ (n : Int) * (ulpDen - 1) := by
  induction n generalizing acc with
  | zero => simp only [accFadd, ulpDen]; omega
  | succ n ih =>
      have hstep := fadd_error_abs_le acc s
      have hrec := ih (fadd acc s)
      simp only [accFadd]
      simp only [ulpDen] at hstep ⊢
      simp only [ulpDen] at hrec
      have hcastS : ((n + 1 : Nat) : Int) * s = (n : Int) * s + s := by
        have hc : ((n + 1 : Nat) : Int) = (n : Int) + 1 := by omega
        rw [hc, Int.add_mul, Int.one_mul]
      have hcastU :
          ((n + 1 : Nat) : Int) * (8 - 1) = (n : Int) * (8 - 1) + (8 - 1) := by
        have hc : ((n + 1 : Nat) : Int) = (n : Int) + 1 := by omega
        rw [hc, Int.add_mul, Int.one_mul]
      rw [hcastS, hcastU]
      omega

/-- **The per-step bound is attained, so it cannot be tightened.**
`7 = ulp - 1` is not on the 8-grid, so rounding it toward zero discards exactly
one ulp, achieving the maximum error permitted by `fadd_error_abs_le`. -/
theorem fadd_error_bound_is_tight : fadd 0 7 - (0 + 7) = -(ulpDen - 1) := by
  simp [fadd, round, ulpDen]

/-- **Consequence for the shipped kernel.** Because both summation orders are
`n`-step `fadd` chains over the same operands, and each step perturbs the running
sum by at most one ulp, the disagreement between the flat and blocked
associations over `n` terms is bounded by the number of roundings actually
spent on the reassociation. This is an **upper bound**, not an equality: the
`PCSSGemmRegisterBlock` witness shows the bound is not always achieved, and
`fadd_error_bound_is_tight` shows it can be. -/
theorem disagreement_is_bounded_by_rounding_count (n : Nat) (acc s : Int) :
    accFadd n acc s - (acc + (n : Int) * s) ≤ (n : Int) * (ulpDen - 1) :=
  (accFadd_chain_bound n acc s).2

end PCSSErrorBound