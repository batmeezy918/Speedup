/-
  Reusable PCSS certificate skeleton.
  Instantiate numbers per RUN_ID. Do not hard-code a specimen speedup here.
  No Mathlib. Zero sorry.
-/

namespace PCSS.Template

structure Gates where
  integrity : Bool
  reproducibility : Bool
  quotientForward : Bool
  reconstructionReverse : Bool
  invariants : Bool
  performance : Bool
  leanCert : Bool

def publishable (g : Gates) : Prop :=
  g.integrity = true /\
  g.reproducibility = true /\
  g.quotientForward = true /\
  g.reconstructionReverse = true /\
  g.invariants = true /\
  g.performance = true /\
  g.leanCert = true

theorem unknown_lean_blocks (g : Gates) (h : g.leanCert = false) :
    Not (publishable g) := by
  intro hp
  have hl : g.leanCert = true := hp.2.2.2.2.2.2
  rw [h] at hl
  cases hl

/-- Ratio above 1x, stored as numerator/denominator in Nat. -/
theorem ratio_gt_one (num den : Nat) (h : den < num) (hd : 0 < den) :
    den < num := h

end PCSS.Template
