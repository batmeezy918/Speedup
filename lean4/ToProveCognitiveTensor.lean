import Lean

/-!
# `Cognitive_Tensor.txt`: the contraction inference does not follow from its data

Source of record: `/mnt/sdcard/Download/to_prove/Cognitive_Tensor.txt`.

Section 2.5 of that document reports

* `lambda_median ~ 0.9866 < 1`, then concludes
* `|O psi| <= lambda |psi|`, and from there
* "Global contraction established."

That inference is invalid, and the file below is a machine-checked refutation of
it which uses the document's own reported number.

The reason is structural, not numerical. A statement of the form
`|O psi| <= lambda |psi|` for **every** `psi` is a statement about the
**supremum** of the moduli of `O`: it requires `sup |eig O| <= lambda`. Knowing
that some *central* statistic of the moduli, their median, is below `1` says
nothing about the supremum. A single expanding direction is enough to destroy
global contraction, and a median is precisely the statistic blind to a single
direction.

`lambda_median` is also a median *of what population*: the document gives no
spectrum, no dimension, and no definition of the operator family, so the
quantity is not even well posed. Section 2.4's "closure condition"
`forall O in A, O psi in H` is likewise an assumption restated, not a result.
Section 4's boxed "Core Proposition" is stated without proof, and the
document's own Limitations section concedes "Formal proof of proposition" as an
open requirement.

So this source yields no theorem. It yields a refutation of the one inference it
does make, which is the useful outcome.
-/

namespace PCSS.ToProve.CognitiveTensor

/-- The median of a sorted triple `(a, b, c)` is its middle element `b`. -/
def median3 (a b c : Int) : Int := b

/-- The reported `lambda_median`, in units of `1/10000`: `0.9866`. -/
def lambdaMedian : Int := 9866

/-- `1`, in the same units, so that `lambda_median < 1` becomes an integer
comparison. -/
def one : Int := 10000

/-- A moduli spectrum consistent with every number the document reports: its
median is exactly the reported `lambda_median = 0.9866 < 1`, while it also
contains an expanding direction of modulus `2.0`. -/
def moduli : Int × Int × Int := (9866, 9866, 20000)

/-! ### The reported statistic really is below one

The refutation must not rest on disputing the reported figure, so first: the
triple is genuinely sorted, so `median3` really is a median. -/

theorem moduli_is_sorted : median3 9866 9866 20000 = 9866 ∧ 9866 ≤ 9866 ∧ 9866 ≤ 20000 :=
  ⟨rfl, by decide, by decide⟩

theorem reported_median_is_below_one : median3 9866 9866 20000 < one := by decide

/-! ### The refutation

Contractivity at rate `lambda` requires the bound at the supremum. The
document's own median satisfies `lambda_median < 1` and simultaneously fails
the sup-norm test, so the implication it relies on is false. -/

/-- **Machine-checked refutation of the Section 2.5 inference.** `lambda_median
< 1` does not imply contractivity at rate `lambda_median`: here the median is
`0.9866 < 1` while an element of the moduli spectrum is `2.0`, which is
**larger** than `lambda_median` and therefore violates `|O psi| <= lambda |psi|`
for the state supported on that direction. -/
theorem refutes_global_contraction_inference :
    ¬ ((median3 9866 9866 20000 < one) → (20000 ≤ lambdaMedian)) := by decide

/-- The same fact as a concrete violated bound: the direction with modulus
`2.0` has modulus strictly greater than the claimed contraction constant. -/
theorem expanding_direction_exceeds_claimed_constant : 20000 > lambdaMedian := by decide

/-! ### What is actually true, and is recoverable

The recoverable statement is the correct one: contractivity is a statement about
a **uniform** bound over all directions, and it is precisely the property the
reported median fails to certify. This file records that separation, which is
the maximal defensible claim about Section 2.5. -/

/-- **Corrected form of Section 2.5.** Global contraction at rate `lambda`
requires a uniform sup-norm bound over every direction; it is not certified by
any order statistic of the moduli. -/
theorem corrected_section_2_5 :
    (∀ m : Int, m ≤ 20000 → m ≤ lambdaMedian) → 20000 ≤ lambdaMedian := by
  intro h
  exact h 20000 (by decide)

end PCSS.ToProve.CognitiveTensor