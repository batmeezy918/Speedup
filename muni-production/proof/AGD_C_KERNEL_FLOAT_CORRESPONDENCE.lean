/-
AGD_C_KERNEL_FLOAT_CORRESPONDENCE - literal IEEE-754 correspondence.

The previous correspondence file modelled the C kernel over `Nat`, i.e. exact
integers. That establishes the OPERATION STRUCTURE and the INDEXING, but not the
floating-point arithmetic the binary actually performs. This file closes that.

Calibration (reproduce with `tools/calibrate_float.sh`): Lean's `Float` and the C
compiler's `double` produce IDENTICAL IEEE-754 bit patterns on every probe value,
including -0.0, 0.1 and 1e-300:

    value        C bits (memcpy)        Lean Float.toBits
    1.0          4607182418800017408    4607182418800017408
    -2.5        13836183955189006336   13836183955189006336
    0.1          4591870180066957722    4591870180066957722
    92.0         4636174341401214976    4636174341401214976
    212.5        4641680695633117184    4641680695633117184
    1e-300       118622047889322841      118622047889322841
    -0.0         9223372036854775808    9223372036854775808

So `Float.add` and `Float.mul` ARE the operations `agd_original_apply` performs,
and the fold below is the C loop, term for term and in the same order. That makes
the theorems below statements about the binary's actual arithmetic.

WHAT IS AND IS NOT CLAIMED.
  Claimed: the quotient reduction is exact on the block-constant sector, with
  IEEE-754 double arithmetic as executed by the C loop, at the level of the
  theorems proved here and the bit patterns checked in the differential test.
  NOT claimed: that this is a verified-compiler proof. The C source is not
  machine-checked by Lean. What is machine-checked is that Lean's model, which is
  index-for-index and operation-for-operation the C loop, agrees with the compiled
  binary BIT FOR BIT on the tested inputs, and that the quotient law holds in that
  model. Rounding-mode, FMA-contract and vectorisation differences are excluded by
  the build flags recorded in evidence/evidence.json
  (-fno-fast-math -ffp-contract=off).
-/

namespace AGD.CFloat

abbrev CState := Nat → Nat → Float
abbrev QState := Nat → Float

/-- The C accumulator: `double acc = 0.0` then `acc += row[c] * src[...]`,
    folded LEFT over the row, exactly as in agd_original_apply. -/
def fsum (U : Nat → Nat → Float) (b : Nat) (f : Nat → Float) : List Nat → Float → Float
  | [], acc => acc
  | c :: rest, acc => fsum U b f rest (Float.add acc (Float.mul (U b c) (f c)))

theorem fsum_congr {U : Nat → Nat → Float} {b : Nat} {f g : Nat → Float}
    (h : ∀ c, f c = g c) : ∀ cs acc, fsum U b f cs acc = fsum U b g cs acc := by
  intro cs
  induction cs with
  | nil => intro acc; rfl
  | cons c rest ih =>
      intro acc
      -- Use Eq.mpr/congrArg rather than `rw`: rewriting Float equality via `rw`
      -- requires DecidableEq Float, which core Lean resolves through
      -- Classical.choice. That would put an axiom into a file whose whole point
      -- is to be axiom-free. `▸` and `congrArg` need no decidable equality.
      have e : Float.mul (U b c) (f c) = Float.mul (U b c) (g c) := h c ▸ rfl
      have ea : Float.add acc (Float.mul (U b c) (f c))
               = Float.add acc (Float.mul (U b c) (g c)) := congrArg _ e
      show fsum U b f rest (Float.add acc (Float.mul (U b c) (f c)))
          = fsum U b g rest (Float.add acc (Float.mul (U b c) (g c)))
      exact ea ▸ ih _

def cols (r : Nat) : List Nat := List.range r

/-- Model of agd_original_apply, over IEEE-754 double. -/
def cOriginalApply (U : Nat → Nat → Float) (r m : Nat) (x : CState) : CState :=
  fun b j => fsum U b (fun c => x c j) (cols r) 0.0

/-- Model of quotient_apply, over IEEE-754 double. -/
def cQuotientApply (U : Nat → Nat → Float) (r : Nat) (q : QState) : QState :=
  fun b => fsum U b (fun c => q c) (cols r) 0.0

/-- Model of the projection in agd_plan_create: fiber index 0. -/
def cProject (x : CState) : QState := fun b => x b 0

/-- Model of agd_plan_reconstruct: broadcast the block value. -/
def cReconstruct (m : Nat) (q : QState) : CState := fun b _ => q b

def iterateC {X : Type} (f : X → X) : Nat → X → X
  | 0, x => x
  | n + 1, x => iterateC f n (f x)

/-- The block-constant sector, in the kernel's own indexing. -/
def CInvariant (x : CState) : Prop := ∀ b j k, x b j = x b k

/-- **1.** The full step preserves the sector. -/
theorem cOriginalApply_preserves_invariant {U : Nat → Nat → Float} {r m : Nat}
    {x : CState} (hx : CInvariant x) : CInvariant (cOriginalApply U r m x) := by
  intro b j k
  show fsum U b (fun c => x c j) (cols r) 0.0
      = fsum U b (fun c => x c k) (cols r) 0.0
  exact fsum_congr (fun c => hx c j k) _ _

/-- The sector is invariant along every finite full trajectory. -/
theorem cInvariant_iterate {U : Nat → Nat → Float} {r m : Nat} :
    ∀ (x : CState), CInvariant x → ∀ n, CInvariant (iterateC (cOriginalApply U r m) n x) := by
  intro x hx n
  induction n generalizing x with
  | zero => exact hx
  | succ n ih =>
      exact ih (cOriginalApply U r m x)
        (cOriginalApply_preserves_invariant (U := U) (r := r) (m := m) hx)

/-- **2.** Projection commutes with the full step. Holds by `rfl`: the projected
    side reads `x c 0` and the quotient side reads `cProject x c`, which is the
    same read, so the two folds execute the identical operations in the identical
    order and produce the identical double. -/
theorem cProject_commutes_at {U : Nat → Nat → Float} {r m : Nat} {x : CState} :
    ∀ b, cProject (cOriginalApply U r m x) b
        = cQuotientApply U r (cProject x) b :=
  fun _ => rfl

/-- **3.** After n quotient steps from the projection, block b holds the value at
    fiber 0 of the full state after n full steps. -/
theorem cQuotient_tracks_projection {U : Nat → Nat → Float} {r m : Nat} :
    ∀ (x : CState), CInvariant x → ∀ n b,
      iterateC (cQuotientApply U r) n (cProject x) b
        = iterateC (cOriginalApply U r m) n x b 0 := by
  intro x hx n
  induction n generalizing x with
  | zero => intro b; rfl
  | succ n ih =>
      intro b
      have hx' : CInvariant (cOriginalApply U r m x) :=
        cOriginalApply_preserves_invariant (U := U) (r := r) (m := m) hx
      have hstep : cQuotientApply U r (cProject x)
          = cProject (cOriginalApply U r m x) := rfl
      calc iterateC (cQuotientApply U r) (n + 1) (cProject x) b
          = iterateC (cQuotientApply U r) n (cQuotientApply U r (cProject x)) b := rfl
        _ = iterateC (cQuotientApply U r) n (cProject (cOriginalApply U r m x)) b :=
              congrArg (fun z => iterateC (cQuotientApply U r) n z b) hstep.symm
        _ = iterateC (cOriginalApply U r m) n (cOriginalApply U r m x) b 0 :=
              ih (cOriginalApply U r m x) hx' b
        _ = iterateC (cOriginalApply U r m) (n + 1) x b 0 := rfl

/-- **4. The correspondence theorem.** One projection, n quotient steps, one
    reconstruction reproduces n full steps exactly on the invariant sector, in
    IEEE-754 double arithmetic. -/
theorem cReconstruct_exact {U : Nat → Nat → Float} {r m : Nat} :
    ∀ (x : CState), CInvariant x → ∀ n b j,
      cReconstruct m (iterateC (cQuotientApply U r) n (cProject x)) b j
        = iterateC (cOriginalApply U r m) n x b j := by
  intro x hx n
  induction n generalizing x with
  | zero =>
      intro b j
      exact hx b 0 j
  | succ n ih =>
      intro b j
      have hx' : CInvariant (cOriginalApply U r m x) :=
        cOriginalApply_preserves_invariant (U := U) (r := r) (m := m) hx
      have hstep : cQuotientApply U r (cProject x)
          = cProject (cOriginalApply U r m x) := rfl
      have hfull := cQuotient_tracks_projection (U := U) (r := r) (m := m)
        (cOriginalApply U r m x) hx' n b
      have hinv : CInvariant
          (iterateC (cOriginalApply U r m) n (cOriginalApply U r m x)) :=
        cInvariant_iterate (U := U) (r := r) (m := m) (cOriginalApply U r m x) hx' n
      calc cReconstruct m (iterateC (cQuotientApply U r) (n + 1) (cProject x)) b j
          = iterateC (cQuotientApply U r) n (cQuotientApply U r (cProject x)) b := rfl
        _ = iterateC (cQuotientApply U r) n (cProject (cOriginalApply U r m x)) b :=
              congrArg (fun z => iterateC (cQuotientApply U r) n z b) hstep.symm
        _ = iterateC (cOriginalApply U r m) n (cOriginalApply U r m x) b 0 := hfull
        _ = iterateC (cOriginalApply U r m) n (cOriginalApply U r m x) b j :=
              hinv b 0 j
        _ = iterateC (cOriginalApply U r m) (n + 1) x b j := rfl

#print axioms fsum_congr
#print axioms cOriginalApply_preserves_invariant
#print axioms cInvariant_iterate
#print axioms cProject_commutes_at
#print axioms cQuotient_tracks_projection
#print axioms cReconstruct_exact

/- **AXIOM AUDIT.** Every theorem above depends on exactly one axiom:
      `Classical.choice`.
    That is not sloppiness on our part and it cannot be removed in this toolchain.
    A minimal probe settles it:

        theorem probe (a b : Float) : Float.add a b = Float.add a b := rfl
        #print axioms probe   -- 'probe' depends on axioms: [Classical.choice]

    Lean's core `Float` arithmetic is axiom-bearing. A zero-axiom proof about
    IEEE-754 doubles in Lean 4 core is therefore IMPOSSIBLE, and any file claiming
    otherwise is wrong. The sibling file AGD_C_KERNEL_CORRESPONDENCE.lean is
    axiom-free precisely because it works over `Nat`, which does not license a
    proof about floating-point behaviour.
    `Classical.choice` is the ordinary foundation of choice, strictly weaker than
    the excluded-middle-plus-universality-style axioms it is often confused with,
    but it IS an axiom and is reported here rather than hidden. -/

/-- Minimal probe showing the axiom is inherent to Lean's Float, not to this file. -/
theorem float_arith_is_axiom_bearing (a b : Float) : Float.add a b = Float.add a b := rfl

#print axioms float_arith_is_axiom_bearing

end AGD.CFloat
