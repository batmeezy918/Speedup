/- AGD refinement kernel — quotient descent as an ORDER-PRESERVING contraction.

   WHY THIS FILE EXISTS (the gap it closes).

   AGDTensorSeparableInstantiation proves the quotient descent at the level of
   FUNCTIONS: `fullStep U (lift q) = lift (quotientStep U q)` holds by `rfl`,
   because both sides are definitionally the same. That is a theorem about the
   abstract model over `Rat`. It does NOT say anything about the ORDER in which
   the floating-point implementation accumulates, which is precisely the thing
   that decides whether the native C is bit-for-bit the model.

   This file closes that gap by proving the refinement at the level of the
   CONTRACTION FOLD ITSELF, parameterised over an ARBITRARY `add`, `mul`, `zero`.
   No arithmetic law is used — only congruence of the fold. Therefore the theorem
   is valid for IEEE-754 `Float` exactly as for `Rat`: both paths perform the same
   operations, on the same values, in the same index order, so the rounding is
   identical on both sides and cannot create a discrepancy.

   RESIDUAL OBLIGATION (named, not hidden).

   What remains after this file is a SINGLE finite claim: that the C compiler
   lowers `acc += row[c]*src[c*m]` (ascending `c`, starting at 0.0) to the same
   sequence of binary64 `add`/`mul` that `dot` models. That is a checkable
   statement about one loop, not a vague "we hope it matches". Until it is
   discharged the certificate stays FORMAL_PARTIAL; this file makes the remaining
   obligation precise and small.

   This file declares no axiom, opaque, sorry, admit, or native_decide.
-/
import AGDDescentCore

namespace AGDRefinement

open AGDDescent

/- ## The contraction fold, over an abstract numeric carrier -/

/-- Ordered contraction over `Fin r`, left fold, index order `0,1,…,r-1`.

    `mul` and `add` are LEFT ABSTRACT on purpose: the proof below never inspects
    them, so it is simultaneously a proof about `Rat`, about `Float`, and about a
    verified-float model. `zero` is the initial accumulator. -/
def dot {F : Type} {r : Nat} (mul add : F → F → F) (zero : F)
    (a b : Fin r → F) : F :=
  (List.finRange r).foldl (fun acc c => add acc (mul (a c) (b c))) zero

/-- **THE REFINEMENT WORKHORSE.** Contractions with pointwise-equal operands are
    EQUAL for any `mul`, `add`, `zero`. This uses only congruence of `foldl`;
    it assumes no associativity, distributivity, or any floating-point-friendly
    law. That is exactly why it survives IEEE-754. -/
theorem dot_congr {F : Type} {r : Nat} (mul add : F → F → F) (zero : F)
    {a₁ a₂ b₁ b₂ : Fin r → F} (ha : a₁ = a₂) (hb : b₁ = b₂) :
    dot mul add zero a₁ b₁ = dot mul add zero a₂ b₂ := by
  rw [ha, hb]

/- ## The tensor-separable operator, at the coordinate (= fold) level -/

/-- Full-state coordinate of one tensor-separable step: the ordered contraction
    of row `b` of `U` against the `j`-th fiber of `x`. This mirrors the C loop
    `for c: acc += U[b][c] * x[c][j]` with `c` ascending. -/
def fullCoord {F : Type} {r m : Nat} (mul add : F → F → F) (zero : F)
    (U : Fin r → Fin r → F) (x : Fin r → Fin m → F) (b : Fin r) (j : Fin m) : F :=
  dot mul add zero (U b) (fun c => x c j)

/-- Quotient coordinate: the SAME ordered contraction against the representative
    fiber `j0`. Mirrors `for c: acc += U[b][c] * q[c]`. -/
def quotCoord {F : Type} {r m : Nat} (mul add : F → F → F) (zero : F)
    (U : Fin r → Fin r → F) (x : Fin r → Fin m → F) (j0 : Fin m) (b : Fin r) : F :=
  dot mul add zero (U b) (fun c => x c j0)

/-- Block-constancy across fibers — the invariant sector, as an equality. -/
def BlockConstant {F : Type} {r m : Nat} (x : Fin r → Fin m → F) : Prop :=
  ∀ i j k, x i j = x i k

/-- Full-state step on states, defined through the contraction. -/
def fstep {F : Type} {r m : Nat} (mul add : F → F → F) (zero : F)
    (U : Fin r → Fin r → F) (x : Fin r → Fin m → F) : Fin r → Fin m → F :=
  fun b j => fullCoord mul add zero U x b j

/-- Reduced step on the quotient vector. -/
def qstep {F : Type} {r : Nat} (mul add : F → F → F) (zero : F)
    (U : Fin r → Fin r → F) (q : Fin r → F) : Fin r → F :=
  fun b => dot mul add zero (U b) q

/-- The invariant sector is preserved by the tensor-separable step. -/
theorem fstep_blockConstant {F : Type} {r m : Nat} (mul add : F → F → F) (zero : F)
    (U : Fin r → Fin r → F) (x : Fin r → Fin m → F) (h : BlockConstant x) :
    BlockConstant (fstep mul add zero U x) := by
  intro i j k
  unfold fstep fullCoord
  exact dot_congr mul add zero rfl (funext fun c => h c j k)

/-- **SINGLE-STEP REFINEMENT (bit-level).**
    On the block-constant sector, the full-state coordinate equals the quotient
    coordinate, for ARBITRARY `mul`/`add`/`zero`. Both sides fold the same terms
    in the same order, so the real implementation's rounding is identical on both
    paths. -/
theorem fullCoord_eq_quotCoord_of_blockConstant {F : Type} {r m : Nat}
    (mul add : F → F → F) (zero : F) (U : Fin r → Fin r → F)
    (x : Fin r → Fin m → F) (j0 : Fin m) (h : BlockConstant x)
    (b : Fin r) (j : Fin m) :
    fullCoord mul add zero U x b j = quotCoord mul add zero U x j0 b := by
  unfold fullCoord quotCoord
  exact dot_congr mul add zero rfl (funext fun c => h c j j0)

/-- Single-step lemma phrased over `fstep`/`qstep`, so it rewrites syntactically
    in the iterate proof. -/
theorem fstep_eq_qstep_coord {F : Type} {r m : Nat} (mul add : F → F → F) (zero : F)
    (U : Fin r → Fin r → F) (x : Fin r → Fin m → F) (j0 : Fin m)
    (h : BlockConstant x) (b : Fin r) (j : Fin m) :
    fstep mul add zero U x b j = qstep mul add zero U (fun i => x i j0) b := by
  unfold fstep qstep fullCoord
  exact dot_congr mul add zero rfl (funext fun c => h c j j0)

/-- The invariant sector is preserved along the whole full-state iterate. -/
theorem iter_blockConstant {F : Type} {r m : Nat} (mul add : F → F → F) (zero : F)
    (U : Fin r → Fin r → F) (x : Fin r → Fin m → F) (h : BlockConstant x) (n : Nat) :
    BlockConstant (iter (fstep mul add zero U) n x) := by
  induction n with
  | zero => exact h
  | succ n ih =>
    rw [iter_succ]
    exact fstep_blockConstant mul add zero U _ ih

/-- **ALL-ITERATE REFINEMENT (bit-level).**
    For every natural `n`, on a block-constant initial state the full-state
    iterate agrees coordinatewise with the reduced iterate. Proved by induction;
    the induction hypothesis is maintained by `iter_blockConstant`. -/
theorem iter_refines {F : Type} {r m : Nat} (mul add : F → F → F) (zero : F)
    (U : Fin r → Fin r → F) (x : Fin r → Fin m → F) (j0 : Fin m)
    (h : BlockConstant x) (n : Nat) (b : Fin r) (j : Fin m) :
    iter (fstep mul add zero U) n x b j
      = iter (qstep mul add zero U) n (fun i => x i j0) b := by
  induction n generalizing b j with
  | zero =>
    simp only [iter_zero]
    exact h b j j0
  | succ n ih =>
    have hbc : BlockConstant (iter (fstep mul add zero U) n x) :=
      iter_blockConstant mul add zero U x h n
    simp only [iter_succ]
    rw [fstep_eq_qstep_coord mul add zero U (iter (fstep mul add zero U) n x) j0 hbc b j]
    unfold qstep
    exact dot_congr mul add zero rfl (funext fun c => ih c j0)

/- ## IEEE-754 instantiation -/

/-- Binary64 instantiation: the refinement holds for `Float` with the standard
    `(· + ·)` and `(· * ·)`, because the proof assumes no arithmetic law. -/
example {r m : Nat} (U : Fin r → Fin r → Float) (x : Fin r → Fin m → Float)
    (j0 : Fin m) (h : BlockConstant x) (b : Fin r) (j : Fin m) :
    fullCoord (fun a b => a * b) (fun a b => a + b) 0.0 U x b j
      = quotCoord (fun a b => a * b) (fun a b => a + b) 0.0 U x j0 b :=
  fullCoord_eq_quotCoord_of_blockConstant _ _ _ U x j0 h b j

/-- Binary64 all-iterate instantiation, stated as a named theorem so its axiom
    footprint is machine-visible. -/
theorem float_iter_refines {r m : Nat} (U : Fin r → Fin r → Float)
    (x : Fin r → Fin m → Float) (j0 : Fin m) (h : BlockConstant x)
    (n : Nat) (b : Fin r) (j : Fin m) :
    iter (fstep (fun a b => a * b) (fun a b => a + b) 0.0 U) n x b j
      = iter (qstep (fun a b => a * b) (fun a b => a + b) 0.0 U) n
          (fun i => x i j0) b :=
  iter_refines _ _ _ U x j0 h n b j

#print axioms AGDRefinement.fullCoord_eq_quotCoord_of_blockConstant
#print axioms AGDRefinement.iter_refines
#print axioms AGDRefinement.float_iter_refines

end AGDRefinement
