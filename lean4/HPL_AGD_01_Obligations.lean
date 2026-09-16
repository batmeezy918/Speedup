/-
HPL_AGD_01_Obligations.lean
-----------------------
Formal obligations for the HPL-AGD-01 structured instance.

Instance:
    B = [[2,1],[1,3]],  m = 4,  r = 2,  N = 8
    A = I_m (x) B  (block-diagonal, four equal 2x2 blocks)
    RHS b = tile((5,7), 4),  exact solution x = tile((8/5,9/5), 4)

Content:
  1. EXACT INSTANCE  : B * x0 = b0 with x0=(8/5,9/5), b0=(5,7)  (exact Rat arithmetic, native_decide)
                        plus the blockwise A * x = b identity     (native_decide)
  2. QUOTIENT ALGEBRA: concrete State (four blocks), Reduced (one block),
                        pi (first block), sigma (tile), T (per-block solve), Tbar (2x2 solve)
                        then bind the CORPUS theorems
                        (reconstruction_closure) to this instance
                        => pi∘sigma=id, injective/surjective, pi∘T∘sigma=Tbar,
                           recursive descent pi(iterate T n (sigma q)) = iterate Tbar n q.

No sorry, no admit, no axiom. Lean proves mathematics, not wall-clock timing.
-/
import AGDGemmProjection
import AGDGemmReconstruction

namespace HPLAGD01

open AGDGemmProjection
open AGDGemmReconstruction

abbrev Block := Rat × Rat                 -- one 2-vector
abbrev Reduced := Block                   -- quotient coordinate

structure State where
  b0 : Block
  b1 : Block
  b2 : Block
  b3 : Block
deriving DecidableEq, Repr

/-- Solve map of B on a reduced coordinate: B*(a,b) = (2a+b, a+3b). --/
def solveB (q : Reduced) : Reduced := (2 * q.1 + q.2, q.1 + 3 * q.2)

/-- Per-block descent operator T on the full state (independent per block). --/
def T (x : State) : State :=
  ⟨solveB x.b0, solveB x.b1, solveB x.b2, solveB x.b3⟩

/-- Descended operator on the quotient. --/
def Tbar (q : Reduced) : Reduced := solveB q

/-- Projection: extract the first block. --/
def pi (x : State) : Reduced := x.b0

/-- Reconstruction: tile the reduced coordinate m=4 times. --/
def sigma (q : Reduced) : State := ⟨q, q, q, q⟩

/-- RHS: block-equal b = tile((5,7),4). --/
def bFull : State := ⟨((5 : Rat), 7), (5, 7), (5, 7), (5, 7)⟩

/-- Exact reduced solution: B * (8/5,9/5) = (5,7). --/
theorem reduced_exact_solution :
    solveB (8 / 5, 9 / 5) = ((5 : Rat), 7) := by
  native_decide

/-- Exact full identity: with x = sigma(8/5,9/5), T x has scalar value bFull.
Since A is block diagonal with equal blocks B, (A*x)_i = B*x0 = b0 for each i. --/
theorem full_exact_solution :
    T (sigma (8 / 5, 9 / 5)) = bFull := by
  native_decide

/-- Section identity: pi ∘ sigma = id on the quotient coordinate. --/
theorem section_pi_sigma : Section pi sigma := by
  intro q
  change (sigma q).b0 = q
  cases q
  rfl

/-- Descent: pi (T x) = Tbar (pi x) for every full x. --/
theorem descent_intertwines : Intertwines T Tbar pi := by
  intro x
  change solveB (x.b0) = solveB x.b0
  rfl

/-- Bind the corpus closure theorem to this instance. Yields section right-inverse,
injectivity/surjectivity, pi∘T∘sigma=Tbar, and recursive descent for all n. --/
theorem hpl_agd_01_reconstruction_closure :
    (pi ∘ sigma = id) ∧
    Function.Injective sigma ∧
    Function.Surjective pi ∧
    (pi ∘ T ∘ sigma = Tbar) ∧
    (∀ n q, pi (iterate T n (sigma q)) = iterate Tbar n q) := by
  exact reconstruction_closure pi sigma T Tbar section_pi_sigma descent_intertwines

/-- The exact-instance solution claim, as an observable statement
   (the reduced observable holds for the reduced solution). --/
theorem reduced_solution_observable :
    let b0 := ((5 : Rat), 7)
    solveB (8 / 5, 9 / 5) = b0 := by
  native_decide

end HPLAGD01