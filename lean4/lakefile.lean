import Lake
open Lake DSL

package «speedup_lean» where
  version := v!"0.1.0"

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
    `SpeedupLean
  ]
