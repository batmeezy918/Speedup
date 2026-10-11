/- AGD recursive formal-gap derivation for the quotient-descent claim.

   WHAT A "GAP" IS HERE.

   The quotient claim is: on the block-constant sector, running the reduced
   operator and re-broadcasting reproduces the full operator EXACTLY (bit for
   bit in the native implementation). The GAP is the coordinate difference
   between the two reconstructions. This file does three things:

   1. SUFFICIENCY. The chosen invariant (`BlockConstant`) forces the gap to be
      zero. This is the licence MUNI's fast path actually relies on.
   2. NECESSITY IS REAL. The invariant is not vacuous: there is an explicit
      non-block-constant state and certified operator on which the gap is
      NONzero. Therefore the admissibility gate is load-bearing, and a missing
      gate is a genuine (not cosmetic) gap. This is what makes the recursion
      below terminate against real holes rather than tautologies.
   3. THE OBLIGATION SET. The five obligations the claim depends on, named, so
      the runtime gap ledger (`agd_gap_ledger`) can recurse over exactly these
      and refuse closure until each carries evidence.

   No axiom, opaque, sorry, admit, or native_decide is declared here.
-/
import AGDRefinement

namespace AGDGapDerivation

open AGDRefinement

/-- The gap is zero: full and reduced reconstructions agree at every coordinate.
    This is the exact-soundness predicate the certificate must back. -/
def GapFree {F : Type} {r m : Nat} (mul add : F → F → F) (zero : F)
    (U : Fin r → Fin r → F) (x : Fin r → Fin m → F) (j0 : Fin m) : Prop :=
  ∀ b j, fullCoord mul add zero U x b j = quotCoord mul add zero U x j0 b

/-- **SUFFICIENCY.** Block-constancy discharges the gap obligation at every
    coordinate, for any arithmetic. -/
theorem blockConstant_implies_gapFree {F : Type} {r m : Nat}
    (mul add : F → F → F) (zero : F) (U : Fin r → Fin r → F)
    (x : Fin r → Fin m → F) (j0 : Fin m) (h : BlockConstant x) :
    GapFree mul add zero U x j0 :=
  fun b j => fullCoord_eq_quotCoord_of_blockConstant mul add zero U x j0 h b j

/- ## The five obligations of the claim -/

/-- The obligations the quotient-descent claim (exact + faster) depends on.
    o1 structure   : the operator is the certified tensor-separable `U ⊗ I_m`.
    o2 admissibility: the state is block-constant to tolerance.
    o3 certificate : the certificate authorises the optimised path (fail-closed).
    o4 refinement  : native `add`/`mul` and accumulation ORDER match the model.
    o5 exactness   : reconstruction re-broadcasts the reduced state exactly. -/
inductive Obligation
  | structure | admissibility | certificate | refinement | exactness
  deriving DecidableEq, Repr

/-- The full obligation set, in the order a recursion attacks them. -/
def obligations : List Obligation :=
  [.structure, .admissibility, .certificate, .refinement, .exactness]

/-- Recursion step: the next still-open obligation (or `none` when closed). The
    runtime ledger supplies the evidence vector; this is its formal skeleton. -/
def nextOpen (discharged : Obligation → Bool) : Option Obligation :=
  obligations.find? (fun o => !discharged o)

/- ## Necessity: an explicit gap witness over ℤ (the gate is load-bearing) -/

/-- A non-block-constant 2×2 state: fibers differ. -/
def xce : Fin 2 → Fin 2 → Int :=
  fun i j => if j = 0 then (if i = 0 then 1 else 0) else (if i = 0 then 2 else 0)

/-- The identity quotient operator. -/
def Uce : Fin 2 → Fin 2 → Int := fun b c => if b = c then 1 else 0

theorem ce_not_blockConstant : ¬ BlockConstant xce := by
  intro h
  have h01 : xce (0 : Fin 2) 0 = xce (0 : Fin 2) 1 := h 0 0 1
  exact absurd h01 (by decide)

/-- On the witness the gap is genuinely nonzero: the admissibility obligation is
    necessary, not cosmetic. -/
theorem ce_has_gap : ¬ GapFree (· * ·) (· + ·) (0 : Int) Uce xce 0 := by
  intro h
  have h01 : fullCoord (· * ·) (· + ·) (0 : Int) Uce xce 0 1
      = quotCoord (· * ·) (· + ·) (0 : Int) Uce xce 0 0 := h 0 1
  exact absurd h01 (by decide)

/-- **THE GATE IS EXACT.** The chosen invariant is sufficient AND its failure
    admits a real gap. Therefore the admissibility gate can neither be dropped
    (necessity) nor replaced by a weaker check without a proof (sufficiency). -/
theorem invariant_is_sufficient_and_necessary :
    (∀ x : Fin 2 → Fin 2 → Int, BlockConstant x →
        GapFree (· * ·) (· + ·) (0 : Int) Uce x 0)
    ∧ (∃ (x : Fin 2 → Fin 2 → Int) (U : Fin 2 → Fin 2 → Int) (j0 : Fin 2),
        ¬ BlockConstant x ∧ ¬ GapFree (· * ·) (· + ·) (0 : Int) U x j0) :=
  ⟨fun x hx => blockConstant_implies_gapFree (· * ·) (· + ·) (0 : Int) Uce x 0 hx,
   ⟨xce, Uce, 0, ce_not_blockConstant, ce_has_gap⟩⟩

#print axioms AGDGapDerivation.blockConstant_implies_gapFree
#print axioms AGDGapDerivation.ce_has_gap
#print axioms AGDGapDerivation.invariant_is_sufficient_and_necessary

end AGDGapDerivation
