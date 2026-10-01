/-
  Frozen empirical certificate PCSS_NEON_GEMM_N512_20261001T052954Z.

  Lean proves the logical consequences of the supplied record.
  Lean does not measure Android wall-clock.
  Core lane: no Mathlib, zero sorry.
-/

namespace PCSS.NEON512

def runId : String := "PCSS_NEON_GEMM_N512_20261001T052954Z"
def benchmarkSha256 : String :=
  "b6d1187d5d6e7b2189bf5ed3b0298b764227babcd1dae71143efe78697195fca"
def arch : String := "aarch64"
def kernel : String := "4x4 NEON FMA"
def precision : String := "FP32"
def n : Nat := 512

/-- Speedups stored as millionths so 11.294605 = 11294605 / 1000000. -/
def scale : Nat := 1000000
def run0 : Nat := 11294605
def run1 : Nat := 9562833
def run2 : Nat := 11691331
def canonical : Nat := 11294605
def minimum : Nat := 9562833
def maximum : Nat := 11691331

/-- Wall times in nanoseconds, as supplied. -/
def scalarMedianNs : Nat := 319142604
def neonMedianNs : Nat := 27621615

def correctness : Bool := true
def semanticReproducibility : Bool := true
def performancePass : Bool := true
def independentRunsAboveOne : Nat := 3

theorem run0_gt_one : run0 > scale := by decide
theorem run1_gt_one : run1 > scale := by decide
theorem run2_gt_one : run2 > scale := by decide
theorem canonical_gt_one : canonical > scale := by decide
theorem minimum_gt_one : minimum > scale := by decide

theorem run1_le_run0 : run1 <= run0 := by decide
theorem run0_le_run2 : run0 <= run2 := by decide
theorem minimum_is_run1 : minimum = run1 := rfl
theorem maximum_is_run2 : maximum = run2 := rfl
theorem canonical_is_run0 : canonical = run0 := rfl

theorem scalar_slower_than_neon : neonMedianNs < scalarMedianNs := by decide
theorem three_of_three : independentRunsAboveOne = 3 := rfl

theorem correctness_pass : correctness = true := rfl
theorem semantic_reproducibility_pass : semanticReproducibility = true := rfl
theorem performance_gate_pass : performancePass = true := rfl

theorem empirical_certificate :
    run0 > scale /\
    run1 > scale /\
    run2 > scale /\
    correctness = true /\
    semanticReproducibility = true /\
    performancePass = true := by
  refine And.intro run0_gt_one ?_
  refine And.intro run1_gt_one ?_
  refine And.intro run2_gt_one ?_
  refine And.intro correctness_pass ?_
  refine And.intro semantic_reproducibility_pass performance_gate_pass

/-- Supplied record does not contain Q, Qinv, or Omega witnesses. -/
structure SuppliedGates where
  integrity : Bool
  reproducibility : Bool
  quotientForward : Bool
  reconstructionReverse : Bool
  invariants : Bool
  performance : Bool
  leanCert : Bool

def supplied : SuppliedGates :=
  { integrity := true
    reproducibility := true
    quotientForward := false
    reconstructionReverse := false
    invariants := false
    performance := true
    leanCert := true }

def publishable (g : SuppliedGates) : Prop :=
  g.integrity = true /\
  g.reproducibility = true /\
  g.quotientForward = true /\
  g.reconstructionReverse = true /\
  g.invariants = true /\
  g.performance = true /\
  g.leanCert = true

theorem neon_not_publishable : Not (publishable supplied) := by
  intro h
  have hq : supplied.quotientForward = true := h.2.2.1
  simp [supplied] at hq

end PCSS.NEON512
