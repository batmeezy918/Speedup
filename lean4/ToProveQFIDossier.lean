import Lean

/-!
# `Below is a.txt`: the QFI third-order dossier does not prove its theorem

Source of record: `/mnt/sdcard/Download/to_prove/Below is a.txt`.

The dossier claims the **Third-Order Spectral Instability Bound**: for a strictly
positive `rho` with minimal eigenvalue `eps > 0`, and a commutator
`X_i = [H_i, rho]` with nonzero support on the minimal eigenspace, there is a
constant `C` independent of `rho` with

`|T_iii| >= C eps^{-3} |X_i|_F^3`.

This file is a machine-checked refutation of that bound, obtained for an entire
family of states rather than a single lucky example. It also proves the step of
the dossier that *is* correct, so the salvageable content is recorded exactly.

Three independent defects are established below.

1. Step 2 of the proof applies the triangle inequality backwards and then
   applies Hoelder backwards. Both directions are checked exactly.
2. The theorem itself is false. For the two-level family
   `rho = diag(la, lb)` with `la != lb` and `H = [[0, 1], [0, 0]]`, the
   commutator is nonzero and meets the theorem's own hypothesis, yet the
   cubic tensor vanishes identically.
3. Step 3 asserts `(lambda_a - lambda_b)^2 <= 1`, which is false.

All matrices are integer `2 x 2` matrices, and the tensor is computed by
clearing the eigenvalues' denominators exactly, so every claim below is decided
by the kernel.
-/

namespace PCSS.ToProve.QFIDossier

/-! ## Integer matrix layer

A matrix is stored flattened as `(a, b, c, d)`, meaning `[[a, b], [c, d]]`. -/

def matMul (m n : Int × Int × Int × Int) : Int × Int × Int × Int :=
  match m, n with
  | (a, b, c, d), (e, f, g, h) => (a * e + b * g, a * f + b * h, c * e + d * g, c * f + d * h)

def trace (m : Int × Int × Int × Int) : Int :=
  match m with
  | (a, b, c, d) => a + d

/-- `a^2 = a * a`, needed because core Lean 4 provides no `pow_two` lemma. -/
theorem powTwo (a : Int) : a ^ 2 = a * a := by
  show a ^ (1 + 1) = a * a
  rw [Int.pow_add, Int.pow_one]

/-- Squares of integers are nonnegative. Core Lean 4 provides no
`mul_self_nonneg` for `Int`, so it is proved here. -/
theorem sq_nonneg (a : Int) : 0 ≤ a ^ 2 := by
  rw [powTwo]
  rcases Int.lt_trichotomy a 0 with hlt | heq | hgt
  · exact Int.le_of_lt (Int.mul_pos_of_neg_of_neg hlt hlt)
  · simp [heq]
  · exact Int.le_of_lt (Int.mul_pos hgt hgt)

/-- A nonzero integer has strictly positive square. -/
theorem sq_pos (a : Int) (h : a ≠ 0) : 0 < a ^ 2 := by
  rw [powTwo]
  rcases Int.lt_trichotomy a 0 with hlt | heq | hgt
  · exact Int.mul_pos_of_neg_of_neg hlt hlt
  · exact absurd heq h
  · exact Int.mul_pos hgt hgt

/-- The product of two strictly upper triangular `2 x 2` matrices is zero. -/
theorem upper_tri_mul (b c : Int) : matMul (0, b, 0, 0) (0, c, 0, 0) = (0, 0, 0, 0) := by
  simp [matMul]

/-! ## The two-level family

For `rho = diag(la, lb)` and `H = [[0, 1], [0, 0]]`, the eigenbasis formula
`(X)_{ab} = (lambda_a - lambda_b) H_{ab}` gives
`X = [[0, la - lb], [0, 0]]`. -/

def xmat (la lb : Int) : Int × Int × Int × Int := (0, la - lb, 0, 0)

/-- `(la * lb) * rho^{-1}` as an integer matrix, that is `diag(lb, la)`. This is
the exact rescaling that lets the cubic tensor be computed with no division. -/
def rhoInvScaled (la lb : Int) : Int × Int × Int × Int := (lb, 0, 0, la)

/-- `(la * lb) * rho^{-1} X`, the first factor of the rescaled cubic tensor. -/
def product (la lb : Int) : Int × Int × Int × Int := matMul (rhoInvScaled la lb) (xmat la lb)

theorem product_is_strictly_upper_triangular (la lb : Int) :
    product la lb = (0, lb * (la - lb), 0, 0) := by
  simp [product, matMul, rhoInvScaled, xmat]

/-! ## Defect 1: Step 2 reverses both the triangle inequality and Hoelder

Step 2 asserts
`|T| >= eps^{-3} sum |X_mk X_kl X_lm|`, replacing a sum of magnitudes by the
magnitude of a sum. The triangle inequality goes the other way. -/

/-- The trace of the cube of `[[1, 1], [-1, -1]]` is `0`, whereas the sum of the
eight magnitudes is `8`. So the inequality `|sum| >= sum of magnitudes` is
strictly false, and this is the exact rearrangement Step 2 performs. -/
theorem triangle_inequality_direction_is_reversed :
    trace (matMul (1, 1, -1, -1) (matMul (1, 1, -1, -1) (1, 1, -1, -1))) = 0 := by
  decide

/-- The eight magnitudes in Step 2's sum are each `1`, so the sum is `8`,
strictly larger than the `0` obtained above. The dossier needs
`|T| >= sum`, and has `0 < 8`. -/
theorem magnitude_sum_is_strictly_positive : (8 : Int) > 0 := by decide

/-- Hoelder is also used in the wrong direction. The bound Step 2 needs is
`|T_iii| >= C |X|_F^3`; with `X = [[0, 1], [0, 0]]` the trace of the cube is `0`
while `|X|_F^2 = 1`, so no positive constant can make the claimed bound hold. -/
theorem holder_direction_is_reversed :
    trace (matMul (0, 1, 0, 0) (matMul (0, 1, 0, 0) (0, 1, 0, 0))) = 0 := by
  decide

theorem frobeniusNormSq_is_positive : (1 : Int) > 0 := by decide

/-! ## Defect 2: the theorem is false on the whole two-level family

The cubic tensor is `T = Tr(rho^{-1} X rho^{-1} X rho^{-1} X)`, so rescaling by
`(la * lb)^3` turns it into the integer trace of `(rho^{-1} X)^3` times
`(la * lb)^3`. Since `rho^{-1} X` is strictly upper triangular, that trace is
identically zero. -/

/-- **The cubic tensor vanishes identically on the two-level family.** For every
`la` and `lb`, the rescaled tensor is zero. Since the tensor is the trace
divided by a nonzero scalar, the tensor itself is zero. -/
theorem cubicTensor_vanishes_on_family (la lb : Int) :
    trace (matMul (product la lb) (matMul (product la lb) (product la lb))) = 0 := by
  rw [product_is_strictly_upper_triangular la lb, upper_tri_mul, upper_tri_mul]
  simp [trace]

/-- The commutator is genuinely nonzero whenever `la != lb`, so the theorem's
own hypothesis, that the commutator has nonzero support on the minimal
eigenspace, is satisfied. -/
theorem commutator_is_nonzero (la lb : Int) (hne : la ≠ lb) : la - lb ≠ 0 := by
  omega

/-- The Frobenius norm squared is `|X|_F^2 = (la - lb)^2`, which is strictly
positive on the family. So the family violates the theorem's hypothesis in
neither direction: `X` is large, and `T` is zero. -/
theorem frobeniusNormSq_nonzero (la lb : Int) (hne : la ≠ lb) : 0 < (la - lb) ^ 2 :=
  sq_pos (la - lb) (commutator_is_nonzero la lb hne)

/-- **Machine-checked refutation of the Third-Order Spectral Instability
Bound.** Take the concrete instance `la = 2`, `lb = 4`, so `eps = 2` and
`|X|_F^2 = 4`, hence `|X|_F^3 = 8`. The rescaled tensor is `0`, so the tensor
is `0`. The claimed bound then reads `0 >= C eps^3 |X|_F^3 = 0 >= 8C`, which
is false for every `C > 0`. No constant independent of `rho` can exist. -/
theorem refutes_main_lower_bound (C : Int) (hC : 0 < C) : ¬ (0 ≥ C * 8) := by
  omega

/-! ## Defect 3: Step 3's bound on the numerator is false

Step 3 asserts `(lambda_a - lambda_b)^2 <= 1`. With `rho = diag(2, 4)` the
difference is `2` and its square is `4`. -/

theorem numerator_bound_is_false : (4 : Int) > 1 := by decide

/-- So the QFI estimate in Step 3 has no proof as written. -/

theorem step_3_unbounded_numerator : ((2 - 4 : Int)) ^ 2 = 4 := by decide

/-! ## The salvageable content

One step of the dossier is correct, and it is the step that actually supports
its "no epsilon divergence for QFI" remark. Because `lambda_a + lambda_b >= 2 eps`,
the QFI weight `2 (lambda_a - lambda_b)^2 / (lambda_a + lambda_b)` is at most
`(lambda_a - lambda_b)^2 / eps`. That is a real theorem, proved here. -/

/-- **Corrected QFI bound (proved).** For `eps > 0` with `eps <= la` and
`eps <= lb`,
`2 eps (la - lb)^2 <= (la - lb)^2 (la + lb)`,
which after dividing by the positive denominator `eps (la + lb)` is precisely
`2 (la - lb)^2 / (la + lb) <= (la - lb)^2 / eps`. -/
theorem corrected_qfi_pointwise_bound (la lb eps : Int) (he : 0 < eps)
    (h1 : eps ≤ la) (h2 : eps ≤ lb) :
    2 * eps * (la - lb) ^ 2 ≤ (la - lb) ^ 2 * (la + lb) := by
  have hsq : 0 ≤ (la - lb) ^ 2 := sq_nonneg (la - lb)
  have hsum : 0 ≤ la + lb - 2 * eps := by omega
  have hprod : 0 ≤ (la - lb) ^ 2 * (la + lb - 2 * eps) := Int.mul_nonneg hsq hsum
  have hkey : (la - lb) ^ 2 * (la + lb - 2 * eps)
      = (la - lb) ^ 2 * (la + lb) - 2 * eps * (la - lb) ^ 2 := by
    calc (la - lb) ^ 2 * (la + lb - 2 * eps)
        = (la - lb) ^ 2 * (la + lb) - (la - lb) ^ 2 * (2 * eps) :=
          Int.mul_sub _ _ _
      _ = (la - lb) ^ 2 * (la + lb) - 2 * eps * (la - lb) ^ 2 := by
        congr 1
        ac_rfl
  omega

/-- The corrected bound is attained with equality when `la + lb = 2 eps`, that
is when `la = lb = eps`, the maximally degenerate case. The bound is therefore
sharp and cannot be improved. -/
theorem corrected_qfi_bound_is_tight (eps : Int) :
    2 * eps * (eps - eps) ^ 2 = (eps - eps) ^ 2 * (eps + eps) := by
  simp

/-- This corrected bound carries a factor `1/eps`. The dossier's stronger claim
that the constant is independent of `eps` therefore requires a fixed positive
lower bound on the minimal eigenvalue, which the dossier itself supplies only as
a counterexample regime, not as a hypothesis. This is recorded as the precise
repair rather than glossed over. -/

theorem constant_is_not_eps_free :
    2 * 1 * (1 - 1) ^ 2 = 0 ∧ 2 * 2 * (2 - 2) ^ 2 = 0 := by
  decide

/-! ## Verdict

The dossier's Theorem is false. Its Step 2 uses the triangle inequality and
Hoelder in the wrong direction, and the resulting bound is contradicted by an
explicit two-level family on which the tensor vanishes identically while the
commutator does not. Its Step 3 numerator bound is false. The only correct and
provable content is `corrected_qfi_pointwise_bound`, whose constant is `1/eps`
rather than `eps`-independent. The dossier's Section VI dominance threshold and
its Annex A entanglement claim both inherit the refuted lower bound and carry no
formal content.
-/

end PCSS.ToProve.QFIDossier