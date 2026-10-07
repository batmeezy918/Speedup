import Lean

/-!
# `THREAD LOCK.txt`: exact verification of the reported global invariants

Source of record: `/mnt/sdcard/Download/to_prove/THREAD LOCK.txt`.

That document reports three "global invariants" as sums over the seven
iteration states `i = 0 .. 6`:

* `Omega_total = 3.57`
* `Xi_total = 2.50`
* `RIF_total = 2.64`

Every per-iteration metric in the document is stated to exactly two decimal
places. Encoding each value as an exact integer count of hundredths therefore
removes all floating-point ambiguity, and each reported total becomes an
integer sum that the Lean kernel evaluates and checks exactly.

This is the decisive feature of the encoding: it is not a choice of mine, it is
forced by the source. `Omega_total` and `RIF_total` both come out exactly right
under the hundredths encoding, which certifies that the encoding is the one the
document's author used. The third sum then also comes out exactly, and it
**disagrees with the reported value**. A discrepancy that survives the encoding
validated by two independent totals is a defect in the document, not an artifact
of my reading.

Outcome of this file:

* `omega_total_holds`, `rif_total_holds`: two reported invariants confirmed.
* `xi_total_true`, `xi_total_claim_is_false`: one reported invariant refuted,
  with the exact correction and the exact size of the error certified.
-/

namespace PCSS.ToProve.ThreadLock

/-- Per-iteration `Omega` values for `i = 0 .. 6`, in hundredths:
`0.18, 0.26, 0.39, 0.52, 0.60, 0.78, 0.84`. -/
def omegaSteps : List Int := [18, 26, 39, 52, 60, 78, 84]

/-- Per-iteration `Xi` values for `i = 0 .. 6`, in hundredths:
`0.12, 0.20, 0.33, 0.61, 0.55, 0.63, 0.66`. -/
def xiSteps : List Int := [12, 20, 33, 61, 55, 63, 66]

/-- Per-iteration `RIF` values for `i = 0 .. 6`, in hundredths:
`0.00, 0.08, 0.15, 0.34, 0.48, 0.71, 0.88`. -/
def rifSteps : List Int := [0, 8, 15, 34, 48, 71, 88]

/-- `Omega_total` exactly as reported, in hundredths (`3.57`). -/
def omegaClaim : Int := 357

/-- `Xi_total` exactly as reported, in hundredths (`2.50`). -/
def xiClaim : Int := 250

/-- `RIF_total` exactly as reported, in hundredths (`2.64`). -/
def rifClaim : Int := 264

/-! ### Shape of the data

Each table has exactly one entry per iteration state, so each reported total is
a sum over the whole table with no entries dropped or duplicated. -/

theorem omegaSteps_card : omegaSteps.length = 7 := by decide

theorem xiSteps_card : xiSteps.length = 7 := by decide

theorem rifSteps_card : rifSteps.length = 7 := by decide

/-! ### Confirmed invariants

`Omega_total = 3.57` and `RIF_total = 2.64` are both confirmed exactly. -/

theorem omega_total_holds : omegaSteps.sum = omegaClaim := by decide

theorem rif_total_holds : rifSteps.sum = rifClaim := by decide

/-! ### Refuted invariant

The same arithmetic applied to `Xi` does not reproduce the reported total. -/

/-- The exact value of the `Xi` sum over the seven listed iteration states:
`0.12 + 0.20 + 0.33 + 0.61 + 0.55 + 0.63 + 0.66 = 3.10`. -/
theorem xi_total_true : xiSteps.sum = 310 := by decide

/-- **Machine-checked refutation.** The claim `Xi_total = 2.50` does not hold
for the per-iteration `Xi` values given in the same document. -/
theorem xi_total_claim_is_false : xiSteps.sum ≠ xiClaim := by decide

/-- The size of the discrepancy, to the same exact precision as the source: the
listed values exceed the reported total by exactly `0.60`. -/
theorem xi_total_overstatement : xiSteps.sum - xiClaim = 60 := by decide

/-! ### Why the refutation is not an artifact of the encoding

The encoding is fixed by the source document, not chosen to produce a
contradiction. Two of the three reported totals are reproduced *exactly* under
it. Had the hundredths reading been wrong, at least one of those two would
have failed too. The `Xi` failure is therefore a genuine internal inconsistency
in `THREAD LOCK.txt`, and the supported value of `Xi_total` is `3.10`. -/

theorem encoding_is_validated_by_two_independent_totals :
    omegaSteps.sum = omegaClaim ∧ rifSteps.sum = rifClaim := ⟨omega_total_holds, rif_total_holds⟩

end PCSS.ToProve.ThreadLock