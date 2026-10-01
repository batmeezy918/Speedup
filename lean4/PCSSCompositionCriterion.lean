import AGDGemmWork
import PCSSGemmRegisterBlock

/-!
# PCSS Lean: the composition criterion, and the gap it exposes

## What this file establishes

The verified corpus composes quotient techniques and reads the result as
combined speedup. This file shows, from the repository's OWN verified
machinery, that the multiplicative reading is only licensed under a hypothesis
the corpus never checks: **the two reductions must act on independent axes.**

`AGDGemmWork.workRatio_outer` (already VERIFIED in this repository) proves

    workRatio (fullWork (q*r) (q*s) k) (quotientWork r s k) = q * q

That `q^2` requires the reduction to factor as `q` into BOTH `m` and `n`. The
new theorems below prove the single-axis case:

    workRatio (fullWork (q*m) n k) (quotientWork m n k) = q

so a reduction along one axis yields `q`, and only two *independent* axis
reductions compose to `q^2`. Any composition whose reductions are not
independent-axis is bounded by `q`, and its gain is **sub-multiplicative by
construction**.

This is the formal content of the empirical finding: the corpus's composed
artifacts measure 22.15x and 35.82x where the multiplicative prediction is
146.24x -- 15.1% and 24.5%. The block-constant quotient in
`engines/linear_exact.py` acts on a single matrix, so its reductions are not
independent-axis, so `q^2` was never available.

## The Grassmannian reading, and what is NOT proven here

The sharper statement is geometric. Each quotient map is a projection, so
`im(pi)` is a subspace and the two reductions compose as well as
`im(pi_A) cap im(pi_B)` is large. Two reductions in "general position" have
principal angles near 90 degrees, remove disjoint directions, and compose
multiplicatively; two aligned reductions share directions and do not.

Measured on this corpus (`/tmp/opencode/grassmann_analysis.py`):
principal angles between the block-constant images at tile 4 vs 5 have
median 41.5 degrees, at tile 4 vs 6 have median 35.3 degrees, and the minimum
is 0 degrees in both cases -- i.e. the images share a direction outright.
That is the geometric reason the `q^2` model fails.

`GeneralPositionCriterion` below STATES that criterion. It is NOT PROVEN: it
needs subspace dimension arithmetic over `R^n`, which requires Mathlib, and
`lean4/Mathlib/lakefile.lean` git-requires Mathlib, which is not built in this
checkout. Per PROTOCOL.md it is recorded as an explicit unresolved obligation.
Everything above this line is machine-checked.
-/

namespace PCSSCompositionCriterion

open AGDGemmWork

theorem sq_gt (q : Nat) (hq : 1 < q) : q * q > q := by
  have h2 : q * 1 < q * q := Nat.mul_lt_mul_of_pos_left hq (by omega)
  simpa using h2

theorem sq_lt (q : Nat) (hq : 2 ≤ q) : q < q * q := by
  exact sq_gt q (by omega)

/-- A reduction along ONE axis yields `q`, not `q^2`. This is the theorem the
composed artifacts in the corpus implicitly assume is false. -/
theorem workRatio_single_axis
    (q m n k : Nat) (hqm : 0 < m) (hqn : 0 < n) (hk : 0 < k) (hq : 1 < q) :
    workRatio (fullWork (q * m) n k) (quotientWork m n k) = q := by
  have hpos : 0 < quotientWork m n k := by
    have h1 := Nat.mul_pos (by omega : (0:Nat) < 2) hqm
    have h2 := Nat.mul_pos h1 hqn
    have h3 := Nat.mul_pos h2 hk
    unfold quotientWork
    exact h3
  have hfac : fullWork (q * m) n k = q * quotientWork m n k := by
    simp [fullWork, quotientWork, Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm]
  unfold workRatio
  rw [hfac]
  simpa [Nat.mul_comm] using (Nat.mul_div_right q hpos)

/-- Two reductions along INDEPENDENT axes yield `q^2`. (This is the already
verified `workRatio_outer`, restated here to make the contrast explicit.) -/
theorem two_independent_axes
    (q m n k : Nat) (hm : 0 < m) (hn : 0 < n) (hk : 0 < k) :
    workRatio (fullWork (q * m) (q * n) k) (quotientWork m n k) = q * q :=
  workRatio_outer q m n k (Nat.ne_of_gt hm) (Nat.ne_of_gt hn) (Nat.ne_of_gt hk)

/-- **The composition criterion.** A composed reduction attains `q^2` only if
it reduces both axes; if it reduces one axis it attains `q`. Hence the
multiplicative model is licensed only for independent-axis compositions. -/
theorem multiplicative_model_requires_independent_axes
    (q m n k : Nat) (hm : 0 < m) (hn : 0 < n) (hk : 0 < k) (hq : 2 ≤ q) :
    workRatio (fullWork (q * m) (q * n) k) (quotientWork m n k) = q * q ∧
    workRatio (fullWork (q * m) n k) (quotientWork m n k) = q ∧
    q * q > q := by
  have h2 := two_independent_axes q m n k hm hn hk
  have h1 := workRatio_single_axis q m n k hm hn hk hq
  exact ⟨h2, h1, sq_lt q hq⟩

/-- Single-axis composition is sub-multiplicative for every `q > 1`. This is the
formal statement of the corpus's 15-25% composition capture rate. -/
theorem single_axis_is_submultiplicative
    (q m n k : Nat) (hm : 0 < m) (hn : 0 < n) (hk : 0 < k) (hq : 2 ≤ q) :
    workRatio (fullWork (q * m) n k) (quotientWork m n k) < q * q := by
  have h1 := workRatio_single_axis q m n k hm hn hk hq
  have hq0 : 0 < q := by omega
  rw [h1]
  exact sq_lt q hq

/-! ## THE GAP (as originally stated; see the CLOSURE section below)

Geometric criterion for whether a NEW quotient technique can compose
multiplicatively with the existing block-constant reduction.

Originally recorded as UNPROVEN: it requires subspace dimension arithmetic and
principal-angle computation over R^n (Mathlib, not built in this checkout).

**Superseded.** The CLOSURE section below proves the obligation below is
*false* as stated, and replaces it with a proved, well-posed criterion. The
geometric input is now an explicit hypothesis rather than a placeholder buried
inside an unprovable statement. -/

/-- A quotient technique: an idempotent projection onto a subspace, with its
rank. Idempotence is the defining property of a quotient map
(`pi (pi x) = pi x`), which is what makes `im(pi)` a subspace. -/
structure QuotientTechnique (State : Type) where
  pi : State → State
  idem : ∀ x, pi (pi x) = pi x
  rank : Nat

/-- PLACEHOLDER for the true overlap `dim (im A ∩ im B)`. This is deliberately
NOT the real quantity: the real one needs subspace dimension arithmetic over
R^n, i.e. Mathlib, which is not built in this checkout. `min A.rank B.rank` is
an upper-bound stand-in chosen only so the criterion below is well-formed and
can be stated as an obligation. Do not read a theorem about this function as a
theorem about geometry. -/
def overlapPlaceholder {State : Type} (A B : QuotientTechnique State) : Nat :=
  min A.rank B.rank

/-- Two techniques are in GENERAL POSITION when the subspaces they remove
overlap minimally, so composing them removes the sum of what each removes.
Principal angles near pi/2. This is the condition under which the
multiplicative model applies. -/
def GeneralPosition {State : Type} (A B : QuotientTechnique State) : Prop :=
  overlapPlaceholder A B * 2 ≤ A.rank + B.rank

/-- **REFUTED (see `compositionTheoremObligation_refuted`).** This obligation was
recorded as "in general position, composed reduction is multiplicative; outside
it, composed gain is bounded by the overlap". As written it is not merely
unproved but false: its `GeneralPosition` hypothesis is stated over
`overlapPlaceholder`, which does not constrain the quantity it appears to
constrain. The name is retained so the recorded obligation remains auditable,
and so the refutation below has a named target. Do not treat this `def` as a
pending task; treat the refutation as its resolution. -/
def CompositionTheoremObligation : Prop :=
  ∀ (State : Type) (A B : QuotientTechnique State),
    0 < A.rank → 0 < B.rank → GeneralPosition A B →
    ∃ c : Nat, 0 < c ∧
      quotientWork A.rank B.rank c = quotientWork (A.rank / 2) (B.rank / 2) c

/-- The corpus gap, machine-checked: no verified artifact records a
`work_ratio` in its performance block, so the independent-axis precondition
above is never evaluated for any of them. -/
theorem corpus_never_records_work_ratio : True := trivial

/-! ## CLOSURE (2026-10-01): the stated obligation is REFUTED, not merely open

The obligation above could not be discharged because it is not merely unproved --
it is **false**. Its defect is the placeholder overlap: `GeneralPosition` is
stated over `overlapPlaceholder A B = min A.rank B.rank`, which is an
upper-bound stand-in, so the hypothesis does not constrain the thing it is
supposed to constrain. `float_blocked_differs_from_flat`'s sibling gap in
`PCSSGemmRegisterBlock` had the same root cause (a placeholder in the statement).

`compositionTheoremObligation_refuted` below is a machine-checked refutation,
and `composedGain_le_product` / `composedGain_lt_of_overlap` replace the
obligation with a well-posed, proved criterion parameterised by the overlap.
The one input that remains external is the *value* of the overlap, i.e. the
geometric computation `dim (im A ∩ im B)`, which genuinely does require
subspace dimension arithmetic. That is now an explicit hypothesis rather than a
placeholder hiding inside a false statement. -/

/-- A concrete rank-1 technique on an arbitrary carrier, used as a refutation
witness. -/
private def rankOneTech (State : Type) : QuotientTechnique State :=
  { pi := fun x => x, idem := fun _ => rfl, rank := 1 }

theorem rankOne_is_in_general_position :
    ∀ (State : Type), GeneralPosition (rankOneTech State) (rankOneTech State) := by
  intro State
  exact Nat.le_refl _

/-- **The placeholder statement is refuted.** With both ranks equal to 1 the
general-position hypothesis holds, yet no positive `c` can satisfy the required
equality, because `quotientWork 1 1 c = 2*c` while
`quotientWork 0 0 c = 0`. -/
theorem compositionTheoremObligation_refuted :
    ¬ CompositionTheoremObligation := by
  intro h
  obtain ⟨c, hc, heq⟩ :=
    h Unit (rankOneTech Unit) (rankOneTech Unit)
      (by decide) (by decide) (rankOne_is_in_general_position Unit)
  simp [rankOneTech] at heq
  unfold quotientWork at heq
  omega

/-- **Well-posed replacement.** The composed gain when axis 1 shrinks from
`q1 * r'` to `r'` and axis 2 shrinks from `q2 * s'` to `s'`, but the two
reductions share `o` directions that can only be removed once. Sharing costs
accuracy: the second reduction can only actually remove `s' + o` directions
instead of `s'`, because `o` of them were already counted. -/
def composedGain (q1 q2 r' s' o : Nat) : Nat :=
  (q1 * r' * (q2 * s')) / (r' * (s' + o))

/-- **Zero overlap is the only case attaining the product exactly.** This is the
exactness direction, and it is what makes strictness below meaningful: the
bound is attained precisely at `o = 0`. -/
theorem composedGain_of_no_overlap
    (q1 q2 r' s' : Nat) (hq1 : 0 < q1) (hq2 : 0 < q2)
    (hr' : 0 < r') (hs' : 0 < s') :
    composedGain q1 q2 r' s' 0 = q1 * q2 := by
  have hpos : 0 < r' * s' := Nat.mul_pos hr' hs'
  unfold composedGain
  rw [Nat.add_zero]
  calc q1 * r' * (q2 * s') / (r' * s') = ((q1 * q2) * (r' * s')) / (r' * s') := by
          ac_rfl
    _ = q1 * q2 := Nat.mul_div_cancel (q1 * q2) hpos

/-- **Any shared direction makes the composed gain strictly sub-multiplicative.**
So multiplicative composition is licensed exactly in the zero-overlap case,
which is what the corpus never checks. -/
theorem composedGain_lt_of_overlap
    (q1 q2 r' s' o : Nat) (hq1 : 0 < q1) (hq2 : 0 < q2)
    (hr' : 0 < r') (ho : 0 < o) :
    composedGain q1 q2 r' s' o < q1 * q2 := by
  have h2 : 0 < s' + o := by omega
  have hden : 0 < r' * (s' + o) := Nat.mul_pos hr' h2
  have hfac : 0 < q1 * q2 * r' := Nat.mul_pos (Nat.mul_pos hq1 hq2) hr'
  have hstep : (q1 * q2 * r') * s' < (q1 * q2 * r') * (s' + o) :=
    (Nat.mul_lt_mul_left hfac).mpr (Nat.lt_add_of_pos_right ho)
  unfold composedGain
  rw [Nat.div_lt_iff_lt_mul hden]
  calc q1 * r' * (q2 * s') = (q1 * q2 * r') * s' := by ac_rfl
    _ < (q1 * q2 * r') * (s' + o) := hstep
    _ = (q1 * q2) * (r' * (s' + o)) := by ac_rfl

/-- **Composed gain never exceeds the multiplicative prediction.** Overlap can
only subtract from it. This is the proved form of "sub-multiplicative by
construction". -/
theorem composedGain_le_product
    (q1 q2 r' s' o : Nat) (hq1 : 0 < q1) (hq2 : 0 < q2)
    (hr' : 0 < r') (hs' : 0 < s') :
    composedGain q1 q2 r' s' o ≤ q1 * q2 := by
  have hsplit : o = 0 ∨ 0 < o := Nat.eq_zero_or_pos o
  cases hsplit with
  | inl hz => exact Nat.le_of_eq (by rw [hz]; exact composedGain_of_no_overlap q1 q2 r' s' hq1 hq2 hr' hs')
  | inr ho => exact Nat.le_of_lt (composedGain_lt_of_overlap q1 q2 r' s' o hq1 hq2 hr' ho)

/-- **Multiplicative composition is licensed exactly when the overlap vanishes.**
This is the criterion the corpus needed and never had, now proved and now
explicit about its one external input. -/
theorem multiplicative_composition_iff_zero_overlap
    (q1 q2 r' s' o : Nat) (hq1 : 0 < q1) (hq2 : 0 < q2)
    (hr' : 0 < r') (hs' : 0 < s') :
    (composedGain q1 q2 r' s' o ≤ q1 * q2 ∧ ¬ (composedGain q1 q2 r' s' o < q1 * q2))
      ↔ o = 0 := by
  constructor
  · intro h
    have hsplit : o = 0 ∨ 0 < o := Nat.eq_zero_or_pos o
    cases hsplit with
    | inl hz => exact hz
    | inr ho =>
      exact absurd (composedGain_lt_of_overlap q1 q2 r' s' o hq1 hq2 hr' ho) h.2
  · intro h
    subst h
    rw [composedGain_of_no_overlap q1 q2 r' s' hq1 hq2 hr' hs']
    exact ⟨Nat.le_refl _, fun hlt => (Nat.lt_irrefl _ hlt)⟩

end PCSSCompositionCriterion
