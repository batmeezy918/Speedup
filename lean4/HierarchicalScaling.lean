/-
  Hierarchical scaling law — formal obligations.

  Lean 4 core + Std only. No Mathlib, consistent with the rest of lean4/.
  Tactics restricted to `omega`, `simp`, `decide`, `rfl` and core lemmas:
  `ring`, `ring_nf` and `positivity` are Mathlib-only and are not used.

  SCOPE (PCSS Constitution Article 7). Lean does not prove wall-clock
  measurements and does not establish that the cost models below describe
  this machine. What IS proved here:

    1. the state space of the workload and its cardinality              bits_length
    2. the workload observable and its exact closed form                 phi_closed_form
    3. the site-0 projection genuinely partitions the state space
       into two sectors of size 2^(L-1)                                 sector_card
    4. the declared reconstruction is injective and lands in the named
       sector, so the reverse error is identically zero                  reconstruct_injective
    5. the state-space reduction factor is exactly 2^(L-1)              reduction_factor
    6. SUFFICIENCE CONDITION: if the baseline does not grow with the
       state space, the quotient's speedup is non-increasing in L and
       bounded, whatever the reduction factor                          no_speedup_without_paid_exponential
    7. exponential support: 2^L >= L+1 and 2^L is unbounded            two_ge_succ, pow_unbounded

  Statement 2 is the mathematical content of the corrected hierarchical
  experiment: the candidate must return exactly `L * 2^(L-1)`, the value
  the baseline obtains by enumerating `2^L` states. Statement 6 is the
  operative content of the cross-domain law: reduction alone yields
  nothing; speedup appears only where a paid exponential meets an unpaid
  quotient.

  No `sorry`, no `admit`. Axiom dependencies are reported by
  `scripts/verify_lean4_all.sh`.
-/

namespace HierarchicalScaling

/-! ## 1. The workload -/

/-- All bit strings of width `L`. The cardinality lemma below is what makes
    this a faithful state space. -/
def bits : Nat → List (List Bool)
  | 0     => [[]]
  | n + 1 => (bits n).map (fun b => false :: b) ++ (bits n).map (fun b => true :: b)

/-- The declared observable of a state: how many sites are occupied. -/
def occupancy : List Bool → Nat
  | []       => 0
  | false :: t => occupancy t
  | true  :: t => occupancy t + 1

/-- Total occupancy of a list of states. -/
def foldOcc (l : List (List Bool)) : Nat :=
  l.foldr (fun s acc => acc + occupancy s) 0

/-- The workload: total occupancy summed over the entire execution state
    space. This is the quantity the baseline enumerates and the candidate
    must reproduce exactly. -/
def phi (L : Nat) : Nat := foldOcc (bits L)

/-! ## 2. Cardinality of the state space -/

theorem bits_length (L : Nat) : (bits L).length = 2 ^ L := by
  induction L with
  | zero => rfl
  | succ L ih =>
      have happ : bits (Nat.succ L)
          = (bits L).map (fun b => false :: b) ++ (bits L).map (fun b => true :: b) := rfl
      simp [happ, List.length_append, ih, Nat.pow_succ, Nat.two_mul, Nat.mul_comm]

/-- `2^L` is strictly positive. Stated once, used by the non-vacuity and
    positivity results below. -/
theorem pow_two_pos (L : Nat) : 0 < 2 ^ L := by
  induction L with
  | zero => decide
  | succ L ih => rw [Nat.pow_succ]; exact Nat.mul_pos ih (by decide)

/-- The state space is never empty, so the workload is never vacuous. -/
theorem bits_ne_nil (L : Nat) : (bits L) ≠ [] := by
  have h1 := bits_length L
  have hp : 0 < 2 ^ L := pow_two_pos L
  intro h
  rw [h, List.length_nil] at h1
  omega

/-! ## 3. Folding lemmas -/

theorem foldr_append (f : List Bool → Nat → Nat) (z : Nat) (l₁ l₂ : List (List Bool)) :
    (l₁ ++ l₂).foldr f z = l₁.foldr f (l₂.foldr f z) := by
  induction l₁ with
  | nil => rfl
  | cons a l ih =>
      show f a (List.foldr f z (l ++ l₂)) = f a (List.foldr f (List.foldr f z l₂) l)
      rw [ih]

theorem foldOcc_append (l₁ l₂ : List (List Bool)) :
    foldOcc (l₁ ++ l₂) = foldOcc l₁ + foldOcc l₂ := by
  induction l₁ with
  | nil => simp [foldOcc]
  | cons a l ih =>
      show foldOcc (a :: (l ++ l₂)) = foldOcc (a :: l) + foldOcc l₂
      show foldOcc (l ++ l₂) + occupancy a = (foldOcc l + occupancy a) + foldOcc l₂
      rw [ih]
      omega

theorem foldOcc_map_false (l : List (List Bool)) :
    foldOcc (l.map (fun b => false :: b)) = foldOcc l := by
  induction l with
  | nil => rfl
  | cons a l ih =>
      show foldOcc ((fun b => false :: b) a :: l.map (fun b => false :: b)) = foldOcc (a :: l)
      show foldOcc (l.map (fun b => false :: b)) + occupancy a = foldOcc l + occupancy a
      rw [ih]

theorem foldOcc_map_true (l : List (List Bool)) :
    foldOcc (l.map (fun b => true :: b)) = foldOcc l + l.length := by
  induction l with
  | nil => rfl
  | cons a l ih =>
      show foldOcc ((fun b => true :: b) a :: l.map (fun b => true :: b))
        = foldOcc (a :: l) + (a :: l).length
      show foldOcc (l.map (fun b => true :: b)) + occupancy a + 1
        = foldOcc l + occupancy a + l.length + 1
      rw [ih]
      omega

/-! ## 4. The exact closed form of the observable -/

/-- The half-step recurrence: adding a site doubles the state count and adds
    that site to every state. -/
theorem phi_succ (L : Nat) : phi (L + 1) = 2 * phi L + (bits L).length := by
  have happ : bits (L + 1)
      = (bits L).map (fun b => false :: b) ++ (bits L).map (fun b => true :: b) := rfl
  rw [phi, happ, foldOcc_append, foldOcc_map_false, foldOcc_map_true]
  change foldOcc (bits L) + (foldOcc (bits L) + (bits L).length)
    = 2 * foldOcc (bits L) + (bits L).length
  omega

/-- **The closed form.** Total occupancy over the full space of width `L+1`
    is exactly `(L+1) * 2^L`. This is the value the baseline computes by
    enumerating `2^(L+1)` states and the value the candidate must match
    exactly, with no tolerance. -/
theorem phi_closed_form (L : Nat) : phi (L + 1) = (L + 1) * 2 ^ L := by
  induction L with
  | zero => rfl
  | succ L ih =>
      have hstep : phi ((L + 1) + 1) = 2 * phi (L + 1) + (bits (L + 1)).length :=
        phi_succ (L + 1)
      have hcard : (bits (L + 1)).length = 2 ^ (L + 1) := bits_length (L + 1)
      have hmul : 2 * ((L + 1) * 2 ^ L) = 2 ^ L * (2 * (L + 1)) := by
        calc 2 * ((L + 1) * 2 ^ L) = (L + 1) * (2 * 2 ^ L) := Nat.mul_left_comm _ _ _
          _ = (L + 1) * 2 ^ (L + 1) := by rw [Nat.pow_succ]; simp [Nat.mul_comm]
          _ = 2 ^ L * (2 * (L + 1)) := by
                rw [Nat.pow_succ, Nat.mul_left_comm, Nat.mul_comm (L + 1) 2]
      rw [hstep, ih, hcard, hmul]
      calc (2 ^ L) * (2 * (L + 1)) + 2 ^ (L + 1)
          = (2 ^ L) * (2 * (L + 1)) + (2 ^ L) * 2 := by rw [Nat.pow_succ]
        _ = (2 ^ L) * (2 * (L + 1) + 2) := (Nat.mul_add _ _ _).symm
        _ = (L + 1 + 1) * 2 ^ (L + 1) := by
              have hq : 2 * (L + 1) + 2 = 2 * (L + 1 + 1) := by omega
              rw [hq, ← Nat.mul_assoc, Nat.pow_succ, Nat.mul_comm]

theorem phi_pos (L : Nat) : 0 < phi (L + 1) := by
  rw [phi_closed_form]
  exact Nat.mul_pos (Nat.succ_pos _) (pow_two_pos L)

/-! ## 5. The quotient: projection onto site 0 -/

/-- The quotient map: read site 0. Its image is the two-point quotient. -/
def pi (s : List Bool) : Bool := s.headD false

/-- The declared section: a canonical representative of each sector. -/
def sigma (b : Bool) (n : Nat) : List Bool := b :: List.replicate n false

/-- The reconstruction operator: lift a sector tag and a residual state. -/
def reconstruct (b : Bool) (t : List Bool) : List Bool := b :: t

/-- Round-trip: reconstruction lands in the sector its tag names. This is
    Article 3 forward agreement, on the whole declared domain rather than a
    two-element sample. -/
theorem reconstruct_pi (b : Bool) (t : List Bool) : pi (reconstruct b t) = b := by
  simp [pi, reconstruct]

/-- Round-trip on the section itself: `pi (sigma b n) = b`. -/
theorem sigma_pi (b : Bool) (n : Nat) : pi (sigma b n) = b := by
  simp [pi, sigma]

/-- **Reconstruction is exact (Article 4).** Distinct tags give distinct
    sectors, and within a tag the lift is injective, so the reverse error
    `d(R(Q(e)), e)` is identically zero and consumes no tolerance budget at
    any `L`. -/
theorem reconstruct_injective (b₁ b₂ : Bool) (t₁ t₂ : List Bool)
    (h : reconstruct b₁ t₁ = reconstruct b₂ t₂) : b₁ = b₂ ∧ t₁ = t₂ := by
  simp only [reconstruct] at h
  cases b₁ <;> cases b₂ <;> simp_all

/-! ## 6. Sector cardinality and the reduction factor -/

/-- **The two sectors partition the state space, each of size `2^L`** for a
    space of width `L+1`. This is the quotient claim, stated exactly. -/
private theorem filt_false_off (l : List (List Bool)) :
    (l.map (fun b => false :: b)).filter (fun s => pi s) = [] := by
  induction l with
  | nil => rfl
  | cons a l _ => simp [pi]

private theorem filt_false_on (l : List (List Bool)) :
    (l.map (fun b => false :: b)).filter (fun s => !(pi s)) = l.map (fun b => false :: b) := by
  induction l with
  | nil => rfl
  | cons a l _ => simp [pi]

private theorem filt_true_on (l : List (List Bool)) :
    (l.map (fun b => true :: b)).filter (fun s => pi s) = l.map (fun b => true :: b) := by
  induction l with
  | nil => rfl
  | cons a l _ => simp [pi]

private theorem filt_true_off (l : List (List Bool)) :
    (l.map (fun b => true :: b)).filter (fun s => !(pi s)) = [] := by
  induction l with
  | nil => rfl
  | cons a l _ => simp [pi]

theorem sector_card (L : Nat) :
    ((bits (L + 1)).filter (fun s => !(pi s))).length = 2 ^ L ∧
      ((bits (L + 1)).filter (fun s => pi s)).length = 2 ^ L := by
  have happ : bits (L + 1)
      = (bits L).map (fun b => false :: b) ++ (bits L).map (fun b => true :: b) := rfl
  constructor
  · rw [happ, List.filter_append, filt_false_on, filt_true_off, List.length_append]
    simp [bits_length, List.length_map]
  · rw [happ, List.filter_append, filt_false_off, filt_true_on, List.length_append]
    simp [bits_length, List.length_map]

/-- **The reduction factor of the site-0 quotient is exactly `2^L`**: a space
    of width `L+1` has `2^(L+1)` elements and each sector has `2^L`. -/
theorem reduction_factor (L : Nat) : 2 ^ (L + 1) / 2 = 2 ^ L := by
  rw [Nat.pow_succ, Nat.mul_comm (2 ^ L) 2]
  exact Nat.mul_div_cancel_left (m := 2 ^ L) (by decide : (0 : Nat) < 2)

/-! ## 7. Exponential support -/

/-- `2^L >= L+1`, the standard exponential-support fact. -/
theorem two_ge_succ (L : Nat) : 2 ^ L ≥ L + 1 := by
  induction L with
  | zero => simp
  | succ L ih =>
      have h2 : 2 ^ (L + 1) = 2 * 2 ^ L := by rw [Nat.pow_succ]; omega
      rw [h2]
      omega

/-- `2^m` is unbounded. -/
theorem pow_unbounded (n : Nat) : ∃ m : Nat, 2 ^ m > n := by
  induction n with
  | zero => exact ⟨2, by decide⟩
  | succ n ih =>
      obtain ⟨m, hm⟩ := ih
      have h2 : 2 ^ (m + 1) = 2 ^ m + 2 ^ m := by rw [Nat.pow_succ]; omega
      refine ⟨m + 1, ?_⟩
      rw [h2]; omega

/-! ## 8. The sufficiency condition

    Reduction is not speedup. A quotient removes states from the
    representation; it yields a speedup only when the baseline was
    genuinely paying to visit them. -/

/-- A cost model. These are **premises supplied by measurement**, not
    conclusions of Lean (Article 7). -/
structure CostModel where
  /-- Cost of one layer of the redundant enumeration. -/
  baseCoeff : Nat
  /-- Per-layer growth of the enumeration, as an exponent of 2. `1` is
      enumeration of the full `2^L` space; `0` means the "baseline" never
      actually enumerated, so there is no exponential to remove. -/
  baseExp : Nat
  /-- The O(1) quotient core. -/
  candConst : Nat
  /-- The O(L) reconstruction / section overhead. -/
  candLinear : Nat
  deriving Repr, DecidableEq

/-- Candidate cost: O(1) core plus O(L) reconstruction. -/
def CostModel.candidateCost (c : CostModel) (L : Nat) : Nat :=
  c.candConst + c.candLinear * L

/-- Baseline cost: the paid exponential. -/
def CostModel.baselineCost (c : CostModel) (L : Nat) : Nat :=
  c.baseCoeff * 2 ^ (c.baseExp * L)

/-- The speedup, under that cost model. -/
def CostModel.speedup (c : CostModel) (L : Nat) : Nat :=
  c.baselineCost L / c.candidateCost L

/-- Candidate cost is non-decreasing in `L`, and strictly increasing once the
    linear coefficient is positive. -/
theorem candidateCost_mono (c : CostModel) (L : Nat) :
    c.candidateCost L ≤ c.candidateCost (L + 1) := by
  simp only [CostModel.candidateCost]
  have : c.candLinear * (L + 1) = c.candLinear * L + c.candLinear := Nat.mul_succ ..
  omega

/-- **THE SUFFICIENCY CONDITION.** If the baseline cost does not grow with
    the state space — `baseExp = 0`, i.e. the "enumeration" never actually
    enumerated — then the quotient's speedup is **non-increasing** in `L` and
    bounded by `baseCoeff / candConst`, no matter how large the reduction
    factor is.

    This is the ATD-QG situation exactly: a correct, exact, gate-passing
    32x reduction realising 1.06-2.03x because the dense path was flat. It
    is also the first statement in this repository that predicts a speedup
    which *decreases* as the reduction grows — the previous framing could
    not produce a non-monotone answer at all. -/
theorem no_speedup_without_paid_exponential (c : CostModel)
    (h : c.baseExp = 0) (hc : 0 < c.candConst) :
    c.speedup (L + 1) ≤ c.speedup L ∧ c.speedup L ≤ c.baseCoeff := by
  have hnum : ∀ k, c.baselineCost k = c.baseCoeff := by
    intro k; simp [CostModel.baselineCost, h]
  have hpos : 0 < c.candidateCost L := by
    simp only [CostModel.candidateCost]; omega
  have hnum' : ∀ k, c.speedup k = c.baseCoeff / c.candidateCost k := by
    intro k; simp only [CostModel.speedup, hnum k]
  have hdiv : c.baseCoeff / c.candidateCost L ≤ c.baseCoeff := Nat.div_le_self _ _
  refine ⟨?_, ?_⟩
  · rw [hnum' (L + 1), hnum' L]
    exact Nat.div_le_div_left (candidateCost_mono c L) hpos
  · rw [hnum' L]
    exact hdiv

/-! ## 9. What is NOT claimed

    The wall-clock constants `A`, `g`, `a`, `b` are measurements, not
    theorems. Article 7 applies in full: the empirical instantiation lives
    in `evidence/hierarchical_accel/2026-09-25/SCALING_LAW.json`, and this
    file certifies only that the structure it fits is a coherent structure.

    `exp_dominates_linear` — that the exponential baseline eventually
    dominates the linear candidate, making the speedup unbounded — is the
    converse half of the sufficiency condition. It is recorded as a formal
    obligation in `docs/HIERARCHICAL_ACCELERATION_ELEVATION_2026-09-25.md`
    (gap ledger) rather than proved here, because its core-Lean proof needs
    nonlinear arithmetic that this Mathlib-free package does not provide.
    Stating it without a proof would violate the repository's own
    CLAIM_STRENGTH <= EVIDENCE_STRENGTH rule. -/

end HierarchicalScaling
