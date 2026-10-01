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
to zero to a fixed number of fractional bits. Denote that model by `fadd`, and
let `p = 8` be the scale for the 3-bit model.

Each individual rounding introduces an error of strictly less than one unit in
the last place. A chain of `t` roundings therefore accumulates an error bounded
by the sum of the per-step ulps, which for this model is bounded by `t/8` in the
scaled-integer representation -- i.e. `t/2^3` in the real-valued
interpretation. That is the standard forward-error shape `|fl(x) - x| <= t*u`,
specialised to a representable-integer model so it is fully checkable.

`Int`/`Rat` is the right instrument here: `Rat` exists in core Lean 4.29, so no
Mathlib is needed, and every bound below is a decidable rational inequality.

## What is NOT claimed

* No claim that the two associations agree, in any regime.
* No claim about the shipped C kernel's rounding mode; this models one specific
  truncation scheme, chosen because `PCSSGemmRegisterBlock` already fixes it.
  Matching the real `float` behaviour is a separate, unproved obligation.
* No wall-clock consequence whatsoever.
-/

import PCSSGemmRegisterBlock

namespace PCSSErrorBound

open PCSSGemmRegisterBlock
open PCSSGemmRegisterBlock.FloatModel

/-- Scale of the model in `PCSSGemmRegisterBlock.FloatModel`: rounding keeps
`p` fractional bits, so the model works with significands scaled by `2^p`. -/
def scale : Nat := 3

/-- The integer scale factor `2^scale`, i.e. the ulp denominator. -/
def ulpDen : Nat := 2 ^ scale

/-- The exact real value represented by a scaled model integer `x`. -/
def exact (x : Int) : Rat := x / ulpDen

/-- One rounding step in exact rational terms: `fadd` rounds toward zero to
`ulpDen` units, so the represented exact value differs from the exact sum by
strictly less than one ulp. -/
theorem fadd_error_lt_one_ulp (x y : Int) :
    |(exact (fadd x y)) - (exact x + exact y)| < 1 := by
  unfold exact fadd ulpDen
  -- Rounding toward zero of `x + y` to a multiple of 8 leaves a remainder of
  -- magnitude strictly below 8, i.e. strictly below one unit after rescaling.
  simp only [round]
  constructor <;> norm_num [Int.ediv_lt_iff_lt_mul, Int.ediv_le_iff_le_mul]

end PCSSErrorBound