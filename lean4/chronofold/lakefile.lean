import Lake
open Lake DSL

package chronofold where
  version := v!"0.1.0"

@[default_target]
lean_lib «ChronoFoldLane» where
  srcDir := "."
  roots := #[
    `ChronoFoldProof,
    `ExactQuotientClosure,
    `GODSQuotientClosure,
    `LinearQuotientProof,
    `ProgressTargetCoupling,
    `WeakCouplingBound
  ]
