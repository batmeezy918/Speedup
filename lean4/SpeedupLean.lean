import PCSSCertificate
import AGDGemmWork
import AGDGemmProjection
import AGDGemmReconstruction
import AGDGemmSpeedup
import SpeedupExactInvariant
import AGDMaximallyTypedClaim

/-!
  SpeedupLean — packaged AGD-GEMM / PCSS stack.

  Main passes (all Mathlib-free, no sorry, no axioms beyond Lean core):

  Work / Projection / Reconstruction / Speedup boundary / PCSS
  plus AGD.complete_AGD_formal_closure and AGD.maximal_formal_from_claim.
-/