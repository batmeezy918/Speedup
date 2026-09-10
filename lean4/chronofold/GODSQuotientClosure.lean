/-
  ChronoFold lane — GODS Quotient Closure (Quot kernel).

  Lean core only. No Mathlib. No unfinished-proof markers.

  Len-3 kernel:
    1. gods_descend
    2. gods_recursive_descent
    3. gods_bidirectional_closure
-/

namespace ChronoFold.GODS

set_option autoImplicit false

universe u v

variable {X : Type u} {Y : Type v}

def UniqueExists {alpha : Sort u} (p : alpha → Prop) : Prop :=
  ∃ x, p x ∧ ∀ y, p y → y = x

def GODSEquiv (O : X → Y) (x y : X) : Prop :=
  O x = O y

def Respects (O : X → Y) (T : X → X) : Prop :=
  ∀ x y : X, GODSEquiv O x y → GODSEquiv O (T x) (T y)

def Q (O : X → Y) := Quot (GODSEquiv O)

def mkG (O : X → Y) (x : X) : Q O :=
  Quot.mk (GODSEquiv O) x

theorem mkG_sound (O : X → Y) {x y : X}
    (h : GODSEquiv O x y) :
    mkG O x = mkG O y :=
  Quot.sound h

def inducedObs (O : X → Y) : Q O → Y :=
  Quot.lift O (fun _x _y h => h)

theorem mkG_exact (O : X → Y) {x y : X}
    (h : mkG O x = mkG O y) :
    GODSEquiv O x y := by
  change inducedObs O (mkG O x) = inducedObs O (mkG O y)
  rw [h]

theorem mkG_surjective (O : X → Y) :
    Function.Surjective (mkG O) := by
  intro q
  refine Quot.inductionOn q ?_
  intro x
  exact ⟨x, rfl⟩

def descendOp (O : X → Y) (T : X → X) (hR : Respects O T) :
    Q O → Q O :=
  Quot.lift
    (fun x => mkG O (T x))
    (fun x y h => mkG_sound O (hR x y h))

theorem gods_one_step (O : X → Y) (T : X → X) (hR : Respects O T) :
    mkG O ∘ T = descendOp O T hR ∘ mkG O :=
  rfl

theorem gods_descend (O : X → Y) (T : X → X) (hR : Respects O T) :
    UniqueExists fun (T_bar : Q O → Q O) =>
      mkG O ∘ T = T_bar ∘ mkG O := by
  refine ⟨descendOp O T hR, gods_one_step O T hR, ?uniq⟩
  intro g hg
  funext q
  refine Quot.inductionOn q ?_
  intro x
  calc
    g (mkG O x)
        = (g ∘ mkG O) x :=
      rfl
    _ = (mkG O ∘ T) x := by
      rw [← hg]
    _ = descendOp O T hR (mkG O x) :=
      rfl

def iterate {alpha : Type u} (step : alpha → alpha) : Nat → alpha → alpha
  | 0,     x => x
  | n + 1, x => step (iterate step n x)

theorem respects_iterate (O : X → Y) (T : X → X) (hR : Respects O T) :
    ∀ n, Respects O (fun x => iterate T n x) := by
  intro n
  induction n with
  | zero =>
      intro x y h
      exact h
  | succ n ih =>
      intro x y h
      exact hR (iterate T n x) (iterate T n y) (ih x y h)

theorem gods_recursive_descent
    (O : X → Y) (T : X → X) (_hR : Respects O T)
    (T_bar : Q O → Q O)
    (hcomm : mkG O ∘ T = T_bar ∘ mkG O) :
    ∀ n, mkG O ∘ (fun x => iterate T n x) =
      (fun q => iterate T_bar n q) ∘ mkG O := by
  intro n
  induction n with
  | zero =>
      funext x
      rfl
  | succ n ih =>
      funext x
      have hstep : mkG O (T (iterate T n x)) =
          T_bar (mkG O (iterate T n x)) :=
        congrFun hcomm (iterate T n x)
      have hih : mkG O (iterate T n x) = iterate T_bar n (mkG O x) :=
        congrFun ih x
      calc
        mkG O (iterate T (n + 1) x)
            = mkG O (T (iterate T n x)) :=
          rfl
        _ = T_bar (mkG O (iterate T n x)) :=
          hstep
        _ = T_bar (iterate T_bar n (mkG O x)) := by
          rw [hih]
        _ = iterate T_bar (n + 1) (mkG O x) :=
          rfl

def SectionOf (O : X → Y) (R : Q O → X) : Prop :=
  mkG O ∘ R = id

theorem gods_bidirectional_closure
    (O : X → Y) (T : X → X) (hR : Respects O T)
    (T_bar : Q O → Q O)
    (hcomm : mkG O ∘ T = T_bar ∘ mkG O)
    (R : Q O → X) (hR_sec : mkG O ∘ R = id) :
    ∀ n, mkG O ∘ (fun x => iterate T n x) ∘ R =
      fun q => iterate T_bar n q := by
  intro n
  funext q
  have hrec :=
    congrFun (gods_recursive_descent O T hR T_bar hcomm n) (R q)
  have hsec : mkG O (R q) = q :=
    congrFun hR_sec q
  calc
    (mkG O ∘ (fun x => iterate T n x) ∘ R) q
        = mkG O (iterate T n (R q)) :=
      rfl
    _ = iterate T_bar n (mkG O (R q)) :=
      hrec
    _ = iterate T_bar n q := by
      rw [hsec]

theorem reverse_respects
    (O : X → Y) (T : X → X)
    (T_bar : Q O → Q O)
    (hcomm : mkG O ∘ T = T_bar ∘ mkG O) :
    Respects O T := by
  intro x y hxy
  have hpi : mkG O x = mkG O y :=
    mkG_sound O hxy
  have hT : mkG O (T x) = mkG O (T y) := by
    calc
      mkG O (T x)
          = T_bar (mkG O x) :=
        congrFun hcomm x
      _ = T_bar (mkG O y) := by
        rw [hpi]
      _ = mkG O (T y) :=
        (congrFun hcomm y).symm
  exact mkG_exact O hT

structure Len3Kernel (O : X → Y) (T : X → X) (hR : Respects O T) : Prop where
  descend :
    UniqueExists fun (T_bar : Q O → Q O) =>
      mkG O ∘ T = T_bar ∘ mkG O
  recursive :
    ∀ (T_bar : Q O → Q O)
      (_hcomm : mkG O ∘ T = T_bar ∘ mkG O) (n : Nat),
      mkG O ∘ (fun x => iterate T n x) =
        (fun q => iterate T_bar n q) ∘ mkG O
  bidirectional :
    ∀ (T_bar : Q O → Q O)
      (_hcomm : mkG O ∘ T = T_bar ∘ mkG O)
      (R : Q O → X) (_hR_sec : mkG O ∘ R = id) (n : Nat),
      mkG O ∘ (fun x => iterate T n x) ∘ R =
        fun q => iterate T_bar n q

theorem gods_len3_certified
    (O : X → Y) (T : X → X) (hR : Respects O T) :
    Len3Kernel O T hR where
  descend := gods_descend O T hR
  recursive := fun T_bar hcomm n =>
    gods_recursive_descent O T hR T_bar hcomm n
  bidirectional := fun T_bar hcomm R hR_sec n =>
    gods_bidirectional_closure O T hR T_bar hcomm R hR_sec n

structure GODSHypotheses (O : X → Y) (T : X → X) where
  respects : Respects O T
  reconstruct : Q O → X
  reconstructs : SectionOf O reconstruct

def MaximalOperational
    (O : X → Y) (T : X → X) (H : GODSHypotheses O T) : Prop :=
  let T_bar := descendOp O T H.respects
  (mkG O ∘ T = T_bar ∘ mkG O) ∧
  (∀ n, mkG O ∘ (fun x => iterate T n x) =
    (fun q => iterate T_bar n q) ∘ mkG O) ∧
  (∀ n, mkG O ∘ (fun x => iterate T n x) ∘ H.reconstruct =
    fun q => iterate T_bar n q) ∧
  Function.Surjective (mkG O) ∧
  Respects O T

theorem gods_maximal_operational_claim
    (O : X → Y) (T : X → X) (H : GODSHypotheses O T) :
    MaximalOperational O T H :=
  let T_bar := descendOp O T H.respects
  And.intro (gods_one_step O T H.respects)
    (And.intro
      (gods_recursive_descent O T H.respects T_bar (gods_one_step O T H.respects))
      (And.intro
        (gods_bidirectional_closure O T H.respects T_bar
          (gods_one_step O T H.respects) H.reconstruct H.reconstructs)
        (And.intro (mkG_surjective O) H.respects)))

theorem gods_stack_closure
    (O : X → Y) (T : X → X) (hR : Respects O T) :
    Len3Kernel O T hR ∧
    (mkG O ∘ T = descendOp O T hR ∘ mkG O) ∧
    Function.Surjective (mkG O) :=
  And.intro (gods_len3_certified O T hR)
    (And.intro (gods_one_step O T hR) (mkG_surjective O))

end ChronoFold.GODS
