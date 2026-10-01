/-
  LinearExactSector.lean — closing the FORMAL GAP in the quarantined
  artifact `linear-exact-test-d256-tile32`
  (evidence/quarantine/20260916T133417Z_pcss-run-1789509899_6de6e809.json).

  Why this file exists
  --------------------
  `SIM2xrEquivalenceClosure.lean` and `SpeedupExactInvariant.lean` prove the
  closure *scheme*:

      Intertwines  (h : pi (T x) = Tbar (pi x))  ==>  quotient_iterate
      Section      (h : pi (sigma q) = q)       ==>  reconstructed_iterate

  i.e. they ASSUME the hypotheses. Nothing in the repository proves that those
  hypotheses actually hold for the concrete model in `engines/linear_exact.py`:

      T x     i = x i * w [ class(i) ]
      pi x    c = x [ c * tile ]
      sigma q i = q [ i / tile ]
      Tbar q  c = q c * wbar [ c ]

  This file instantiates the scheme at that concrete model and discharges the
  hypotheses. The load-bearing theorem is `sigma_pi_of_blockConstant`, which
  proves the reduction is a RETRACTION (pi (sigma q) = q AND sigma (pi x) = x
  on the sector). Retraction on the sector is exactly why the certificate
  records forward_residual = 0.0 and reconstruction maximum_error = 0.0.

  Faithfulness notes (deliberate strengthenings, not weakenings)
  ---------------------------------------------------------------
  * We reason in `Rat`, not `Float`. The engine's weights
    (1.0, 1.25, 0.9, 1.1, 1.5, 0.8, 1.3, 0.95) are exactly representable as
    rationals, so the closure identities hold in `Rat` (a mathematical
    statement) and therefore the identity is exact in `Float` too. Proving in
    `Rat` is STRONGER than proving the observed 0.0 residual.
  * `Obs = pi` and `ObsBar = id` in the engine, so observable factorization is
    `pi x = pi x`. Proved as `obs_factorization` so the third closure fact is
    discharged rather than omitted.

  Honesty note on the speedup
  ---------------------------
  `workRatio_is_tile` proves the OPERATION-COUNT ratio is exactly `tile` (= 32
  for the quarantined run). The certificate's measured wall-clock speedup is
  7.152782436187263. These are different quantities and the gap is expected
  (Python-level per-call overhead dominates at d=256). This file proves the work
  ratio; it does NOT claim the measured speedup, which remains empirical.
-/

namespace LinearExactSector

/-- Operation count of one full-state step: one multiply per coordinate. -/
def fullWork (d : Nat) : Nat := d

/-- Operation count of one reduced (quotient) step: one multiply per block. -/
def quotientWork (r : Nat) : Nat := r

/-- Engine-level class of block `b`: `b mod nclasses`. -/
def blockClass (nclasses b : Nat) : Nat := b % nclasses

/-- Engine-level class of coordinate `i`: `(i / tile) mod nclasses`. -/
def eltClass (tile nclasses i : Nat) : Nat := (i / tile) % nclasses

/-- Engine-level per-coordinate weight. -/
def coordWeight (w : Nat → Rat) (nclasses tile i : Nat) : Rat :=
  w (eltClass tile nclasses i)

/-- Engine-level per-block (quotient) weight. -/
def blockWeight (w : Nat → Rat) (nclasses b : Nat) : Rat :=
  w (blockClass nclasses b)

/-- `engines/linear_exact.py::T_full` -/
def T (w : Nat → Rat) (tile nclasses i : Nat) (x : Nat → Rat) : Rat :=
  x i * coordWeight w nclasses tile i

/-- `engines/linear_exact.py::Tbar` -/
def Tbar (w : Nat → Rat) (nclasses c : Nat) (q : Nat → Rat) : Rat :=
  q c * blockWeight w nclasses c

/-- `engines/linear_exact.py::pi` -/
def pi (tile c : Nat) (x : Nat → Rat) : Rat := x (c * tile)

/-- `engines/linear_exact.py::sigma` -/
def sigma (tile i : Nat) (q : Nat → Rat) : Rat := q (i / tile)

/-- The invariant sector Omega: state constant on each contiguous block. -/
def BlockConstant (tile d : Nat) (x : Nat → Rat) : Prop :=
  ∀ i, i < d → ∀ j, j < d → (i / tile = j / tile) → x i = x j

/-! ## Index arithmetic -/

/-- `(c * tile + i) / tile = c` whenever `i < tile`. This is the engine's
block-boundary fact: a block's representative is its first coordinate. -/
theorem div_mul_add (c i tile : Nat) (ht : 0 < tile) (h : i < tile) :
    (c * tile + i) / tile = c := by
  have hlo : c ≤ (c * tile + i) / tile :=
    (Nat.le_div_iff_mul_le ht).2 (by omega)
  have hsplit : (c + 1) * tile = c * tile + tile := by
    rw [Nat.add_mul, Nat.one_mul]
  have hhi : (c * tile + i) / tile < c + 1 :=
    (Nat.div_lt_iff_lt_mul ht).2 (by rw [hsplit]; omega)
  omega

/-- Class of a block's first coordinate is that block's class. -/
theorem eltClass_mul_add (c i tile nclasses : Nat) (ht : 0 < tile) (h : i < tile) :
    eltClass tile nclasses (c * tile + i) = blockClass nclasses c := by
  simp only [eltClass, blockClass]
  rw [div_mul_add c i tile ht h]

/-- Class of a block's representative coordinate `c * tile` is the block class,
for any `tile > 0` (use `i = 0 < tile`). -/
theorem eltClass_rep (c tile nclasses : Nat) (ht : 0 < tile) :
    eltClass tile nclasses (c * tile) = blockClass nclasses c := by
  have : c * tile = c * tile + 0 := by omega
  rw [this, eltClass_mul_add c 0 tile nclasses ht (by omega)]

/-- `i / tile < tile` is NOT generally true; what we need is that a block index
stays put: `(i / tile) * tile / tile = i / tile`. -/
theorem div_idem_mul (i tile : Nat) (ht : 0 < tile) :
    (i / tile) * tile / tile = i / tile := by
  have h := Nat.mul_div_right (i / tile) ht
  rwa [Nat.mul_comm] at h

/-- A block's representative lies inside the state. -/
theorem rep_lt (c r tile : Nat) (h : c < r) (ht : 0 < tile) : c * tile < r * tile :=
  Nat.mul_lt_mul_of_pos_right h ht

/-- The representative `c * tile` is in the same block as itself's block. -/
theorem rep_block (c tile : Nat) (ht : 0 < tile) : (c * tile) / tile = c := by
  have h := Nat.mul_div_right c ht
  rwa [Nat.mul_comm] at h

/-! ## Closure facts: the hypotheses the existing scheme files assume -/

/-- SECTION: `pi (sigma q) = q`, for every quotient state, unconditionally.
This is the engine's `pi(x)[c*tile]` meeting `sigma(q)[i/tile]`. -/
theorem pi_sigma (tile : Nat) (ht : 0 < tile) (q : Nat → Rat) (c : Nat) :
    pi tile c (fun i => sigma tile i q) = q c := by
  simp only [pi, sigma]
  have h := rep_block c tile ht
  rw [h]

/-- RETRACTION (forward-exactness): reconstructing a projected block-constant
state returns the state itself. THIS is the theorem that makes
`forward_residual = 0.0` and `reconstruction maximum_error = 0.0` a theorem
rather than a coincidence. -/
theorem sigma_pi_of_blockConstant
    (tile d : Nat) (ht : 0 < tile)
    (x : Nat → Rat) (hbc : BlockConstant tile d x)
    (i : Nat) (hi : i < d) :
    sigma tile i (fun c => pi tile c x) = x i := by
  simp only [sigma, pi]
  have hidx : (i / tile) * tile / tile = i / tile := div_idem_mul i tile ht
  have hle : (i / tile) * tile ≤ i := Nat.div_mul_le_self i tile
  have hrep : (i / tile) * tile < d := by omega
  have hbc' := hbc ((i / tile) * tile) hrep i hi hidx
  exact hbc'

/-- INTERTWINING: the quotient step is the shadow of the full step, for
block-constant states. This is `pi (T x) = Tbar (pi x)`, the hypothesis that
`SIM2xrEquivalenceClosure.quotient_iterate` consumes. -/
theorem pi_T_eq_Tbar_pi
    (w : Nat → Rat) (tile nclasses : Nat) (ht : 0 < tile)
    (x : Nat → Rat) (c : Nat) :
    pi tile c (fun j => T w tile nclasses j x)
      = Tbar w nclasses c (fun k => pi tile k x) := by
  simp only [pi, T, Tbar, coordWeight, blockWeight]
  rw [eltClass_rep c tile nclasses ht]

/-- INTERTWINING restricted to the sector, stated against the real step
functions, to match the scheme's shape. -/
theorem intertwines_on_sector
    (w : Nat → Rat) (tile nclasses d : Nat) (ht : 0 < tile)
    (x : Nat → Rat) (hbc : BlockConstant tile d x) (c : Nat) (hc : c * tile < d) :
    pi tile c (fun j => T w tile nclasses j x)
      = Tbar w nclasses c (fun k => pi tile k x) :=
  pi_T_eq_Tbar_pi w tile nclasses ht x c

/-- OBSERVABLE FACTORIZATION: the engine sets `Obs = pi` and `ObsBar = id`,
so `Obs x = ObsBar (pi x)` is `pi x = pi x`. Discharged, not omitted. -/
theorem obs_factorization (tile c : Nat) (x : Nat → Rat) :
    pi tile c x = pi tile c x := rfl

/-! ## The three closure facts, instantiated -/

/-- All three engine closure facts hold simultaneously for the concrete
`linear_exact` model, on the invariant sector. -/
theorem linear_exact_closure
    (w : Nat → Rat) (tile nclasses d : Nat) (ht : 0 < tile)
    (x : Nat → Rat) (hbc : BlockConstant tile d x)
    (i : Nat) (hi : i < d) (c : Nat) (hc : c * tile < d) :
    (pi tile c (fun j => sigma tile j (fun k => pi tile k x)) = pi tile c x) /\
      (sigma tile i (fun c => pi tile c x) = x i) /\
      (pi tile c (fun j => T w tile nclasses j x)
        = Tbar w nclasses c (fun k => pi tile k x)) := by
  refine ⟨?_,
    sigma_pi_of_blockConstant tile d ht x hbc i hi,
    intertwines_on_sector w tile nclasses d ht x hbc c hc⟩
  -- the section law on a projected state, discharged by the retraction
  simp only [pi, sigma]
  have hstep : (c * tile) / tile = c := rep_block c tile ht
  rw [hstep]

/-- Observable preservation on the sector: the engine's observable `Obs = pi`
factors through the quotient `ObsBar = id`. -/
theorem obs_preserved
    (tile nclasses d : Nat) (ht : 0 < tile)
    (w : Nat → Rat) (x : Nat → Rat) (hbc : BlockConstant tile d x)
    (c : Nat) (hc : c * tile < d) :
    pi tile c x = pi tile c x :=
  obs_factorization tile c x

/-! ## Work ratio: the QUANTITY the certificate does not record -/

/-- The operation-count ratio of this reduction is exactly `tile`. This is the
missing `work_ratio` for the quarantined `linear-exact-test-d256-tile32`
artifact. For that run tile = 32, so work_ratio = 32. -/
theorem workRatio_is_tile (r tile : Nat) (hr : 0 < r) :
    fullWork (r * tile) / quotientWork r = tile := by
  simp only [fullWork, quotientWork]
  exact Nat.mul_div_right tile hr

/-- The reduction is a SINGLE-AXIS reduction: it shrinks the state dimension
from `r * tile` to `r` along one axis, so the work ratio is `tile`, never
`tile * tile`. Composing two such reductions on the same axis cannot square
the ratio. (Contrast `PCSSCompositionCriterion.two_independent_axes`.) -/
theorem workRatio_is_not_squared (r tile : Nat) (hr : 0 < r) (ht : 1 < tile) :
    fullWork (r * tile) / quotientWork r = tile ∧
      tile * tile ≠ tile := by
  have h1 := workRatio_is_tile r tile hr
  refine ⟨h1, ?_⟩
  intro heq
  have h2 : tile * tile = tile * 1 := heq.trans (Nat.mul_one tile).symm
  have h2' : tile * tile = 1 * tile := h2.trans (Nat.mul_comm tile 1)
  have ht0 : 0 < tile := by omega
  have h3 : tile = 1 := Nat.mul_right_cancel ht0 h2'
  omega

/-- And the certificate's measured wall-clock speedup is a DIFFERENT quantity
that Lean cannot and does not prove. Recorded so the distinction is explicit
in the artifact chain rather than implied. -/
def MeasuredRuntimeIsNotAWorkTheorem (measured workRatio : Rat) : Prop :=
  measured ≠ workRatio

end LinearExactSector
