/-
  Quarantine dispositions for profile speedup claims.

  These theorems execute the PCSS publication predicate on the recorded
  gate vectors. They do not invent missing measurements.
  A false or unknown gate keeps the claim out of VERIFIED.
  Core lane: no Mathlib, zero sorry.
-/

namespace PCSS.Quarantine

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

theorem missing_lean_blocks (g : Gates) (h : g.leanCert = false) :
    Not (publishable g) := by
  intro hp
  have hl : g.leanCert = true := hp.2.2.2.2.2.2
  rw [h] at hl
  cases hl

theorem missing_performance_blocks (g : Gates) (h : g.performance = false) :
    Not (publishable g) := by
  intro hp
  have hx : g.performance = true := hp.2.2.2.2.2.1
  rw [h] at hx
  cases hx

theorem missing_quotient_blocks (g : Gates) (h : g.quotientForward = false) :
    Not (publishable g) := by
  intro hp
  have hq : g.quotientForward = true := hp.2.2.1
  rw [h] at hq
  cases hq

/-- cocoex bbob dim10 budget1000 20260910: 0/360 Q, slower. -/
def cocoex20260910 : Gates :=
  { integrity := true
    reproducibility := true
    quotientForward := false
    reconstructionReverse := true
    invariants := true
    performance := false
    leanCert := false }

theorem cocoex20260910_not_publishable : Not (publishable cocoex20260910) :=
  missing_quotient_blocks cocoex20260910 rfl

/-- SIM2XR 20260908: local sector, lean flag false on the certificate. -/
def sim2xr20260908 : Gates :=
  { integrity := true
    reproducibility := true
    quotientForward := true
    reconstructionReverse := true
    invariants := true
    performance := true
    leanCert := false }

theorem sim2xr20260908_not_publishable : Not (publishable sim2xr20260908) :=
  missing_lean_blocks sim2xr20260908 rfl

/-- S6/S7/S8 unofficial coco-equivalent 20260515. -/
def s6s7s8_20260515 : Gates :=
  { integrity := false
    reproducibility := false
    quotientForward := false
    reconstructionReverse := false
    invariants := false
    performance := false
    leanCert := false }

theorem s6s7s8_not_publishable : Not (publishable s6s7s8_20260515) :=
  missing_lean_blocks s6s7s8_20260515 rfl

/-- vault canonical decider 1.021: X not established. -/
def vaultDecider20260531 : Gates :=
  { integrity := false
    reproducibility := false
    quotientForward := false
    reconstructionReverse := false
    invariants := false
    performance := false
    leanCert := false }

theorem vault_decider_not_publishable : Not (publishable vaultDecider20260531) :=
  missing_performance_blocks vaultDecider20260531 rfl

/-- iqvf-coco: empty or stale official suite. -/
def iqvfCoco : Gates :=
  { integrity := false
    reproducibility := false
    quotientForward := false
    reconstructionReverse := false
    invariants := false
    performance := false
    leanCert := false }

theorem iqvf_coco_not_publishable : Not (publishable iqvfCoco) :=
  missing_quotient_blocks iqvfCoco rfl

/-- SNAP 9/24 vs CMA is not a speedup certificate. -/
def snap24 : Gates :=
  { integrity := false
    reproducibility := false
    quotientForward := false
    reconstructionReverse := false
    invariants := false
    performance := false
    leanCert := false }

theorem snap24_not_publishable : Not (publishable snap24) :=
  missing_performance_blocks snap24 rfl

/-- Ledger ratios are source-reported, not PCSS-published. -/
def ledgerReported : Gates :=
  { integrity := false
    reproducibility := false
    quotientForward := false
    reconstructionReverse := false
    invariants := false
    performance := false
    leanCert := false }

theorem ledger_not_publishable : Not (publishable ledgerReported) :=
  missing_performance_blocks ledgerReported rfl

/-- Graph500 reference is a baseline, not a candidate win. -/
def graph500Baseline : Gates :=
  { integrity := true
    reproducibility := false
    quotientForward := false
    reconstructionReverse := false
    invariants := false
    performance := false
    leanCert := false }

theorem graph500_not_publishable : Not (publishable graph500Baseline) :=
  missing_performance_blocks graph500Baseline rfl

end PCSS.Quarantine
