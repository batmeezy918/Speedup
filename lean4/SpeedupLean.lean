import PCSSCertificate
import AGDGemmWork
import AGDGemmProjection
import AGDGemmReconstruction
import AGDGemmSpeedup
import SpeedupExactInvariant
import AGDMaximallyTypedClaim
import GODSQuotientClosure

/-!
  SpeedupLean — packaged AGD-GEMM / PCSS stack.

  Main passes (all Mathlib-free, no sorry, no axioms beyond Lean core):

  Work
    AGDGemmWork.outer_factorization
    AGDGemmWork.workRatio_outer
    AGDGemmWork.canonical_workRatio
    AGDGemmWork.canonical_is_instance_of_q_square
    AGDGemmWork.work_model_closure

  Projection
    AGDGemmProjection.projection_iterate
    AGDGemmProjection.intertwines_wellDefined
    AGDGemmProjection.induced_operator_unique
    AGDGemmProjection.quotient_observable_correct
    AGDGemmProjection.projection_closure

  Reconstruction
    AGDGemmReconstruction.reconstructed_operator
    AGDGemmReconstruction.reconstructed_iterate
    AGDGemmReconstruction.observe_via_section
    AGDGemmReconstruction.reconstruction_closure

  Speedup boundary
    AGDGemmSpeedup.modeled_speedup_valid
    AGDGemmSpeedup.semantic_and_work_closure
    AGDGemmSpeedup.measured_hundredths_neq_work_ratio_times_100
    AGDGemmSpeedup.speedup_stack_closure

  PCSS
    PCSS.publish_requires_all_gates
    PCSS.lean_false_not_publishable

  GODS quotient closure (len-3 kernel, no Mathlib)
    GODS.gods_descend
    GODS.gods_recursive_descent
    GODS.gods_bidirectional_closure
    GODS.gods_len3_certified
    GODS.gods_maximal_operational_claim
    GODS.reverse_respects
-/
