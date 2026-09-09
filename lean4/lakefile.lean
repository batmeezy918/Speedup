import Lake
open Lake DSL

package «speedup_lean» where
  version := v!"0.1.0"

/-- Default target so `lake build` actually compiles the stack.
    Previous configuration completed with 0 jobs and never typechecked. -/
@[default_target]
lean_lib «SpeedupLean» where
  srcDir := "."
  roots := #[`SpeedupLean]
