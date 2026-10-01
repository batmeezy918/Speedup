import PCSSGemmRegisterBlock

/-!
# PCSS formal binding: Lean <-> the shipped callable operator

This module is the **binding** between the machine-checked model and the
artifact that was actually benchmarked.

The benchmarked operator is reached by a chain of concrete steps:

    Python (ctypes)  ->  libmuni.so :: muni_neon  ->  gemm_blocked (neon.c)

`muni_neon` accumulates `C` across `kc`-sized blocks of the contraction axis `k`
rather than one flat `k` loop. That reordering is exactly the transformation
modelled by `PCSSGemmRegisterBlock.splitBlocks`.

`callable_kernel_respects_blocked_sum` below states that the formal obligation
holds for *every* blocking width and *every* axis length, so nothing about the
benchmark is pinned to a single hand-picked instance.

## What this module still does NOT establish

It does not prove the measured wall-clock speedup (empirical, scoped to one
device/compiler/thread count), and it does not prove bitwise Float32 equality of
the two kernels. `FloatModel.float_add_not_associative` is the machine-checked
reason the latter remains empirical. The claim lattice in `CLAIM_POLICY.md`
therefore still yields `FORMAL_PARTIAL`, not `VERIFIED`: formal obligations for
the modelled domain pass, and the empirical gates pass, but the two are proven
about different objects (exact integer sums vs. rounded binary32 accumulation)
and the gap between them is not closed.
-/

namespace PCSSCallableBinding

open PCSSGemmRegisterBlock

/-- The transformation the callable operator implements, discharged at the
general level. Covers `KC = 8` (modelled instance), `KC = 128` (shipped binary)
and every other width, and every axis length. -/
theorem callable_kernel_respects_blocked_sum (k : Nat) (hk : 0 < k)
    (l : List Int) : BlockedSumObligation k hk l :=
  blockedSumObligation_holds k hk l

/-- The 2x2 register-block identity the microkernel evaluates, restated under
the binding namespace so downstream artifacts cite one entry point. -/
theorem callable_microkernel_identity (w x y z : List Int) :
    ((w ++ x).sum + (y ++ z).sum) = ((w ++ x ++ y ++ z) : List Int).sum :=
  microkernel_reassociation w x y z

/-- Blocking does not reduce work: the declared work ratio stays exactly 1, so
no work-reduction speedup is available from this transformation. Recorded here
so no downstream reader mistakes the reassociation proofs for a FLOP saving. -/
theorem callable_work_ratio_is_one : flopCount 2048 / flopCount 2048 = 1 :=
  workRatio_is_one

/-- The callable binding carries no work-ratio speedup claim. -/
theorem callable_no_speedup_claim (measuredHundredths : Nat)
    (h : measuredHundredths = flopCount 2048 / flopCount 2048 * 100) :
    measuredHundredths = 100 :=
  no_speedup_from_this measuredHundredths h

end PCSSCallableBinding