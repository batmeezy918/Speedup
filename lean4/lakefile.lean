import Lake
open Lake DSL

package «speedup_lean» where
  version := v!"0.1.0"

lean_lib «SpeedupLean» where
  srcDir := "."
  roots := #[`PCSSCertificate, `AGDGemmWork, `AGDGemmProjection, `AGDGemmReconstruction, `AGDGemmSpeedup, `LeanSpeedup]
