import Lake
open Lake DSL

package «speedup_lean» where
  version := v!"0.1.0"

/-- Default target so `lake build` actually compiles the stack. -/
@[default_target]
lean_lib «SpeedupLean» where
  srcDir := "."
  roots := #[
    `PCSSCertificate,
    `AGDGemmWork,
    `AGDGemmProjection,
    `AGDGemmReconstruction,
    `AGDGemmSpeedup,
    `SpeedupExactInvariant,
    `AGDMaximallyTypedClaim,
    `SpeedupLean
  ]
