/-
  Exact invariant-sector semantics, Mathlib-free.
  Re-stated on the AGD-GEMM iterate/projection vocabulary.
-/

import AGDGemmProjection
import AGDGemmReconstruction

namespace Speedup

open AGDGemmProjection
open AGDGemmReconstruction

universe u v

def Descends {S : Type u} {Q : Type v} (π : S → Q) (T : S → S) (Tbar : Q → Q) : Prop :=
  Intertwines T Tbar π

theorem finite_descent
    {S : Type u} {Q : Type v} (π : S → Q) (T : S → S) (Tbar : Q → Q)
    (h : Descends π T Tbar) :
    ∀ n s, π (iterate T n s) = iterate Tbar n (π s) :=
  projection_iterate T Tbar π h

theorem bidirectional
    {S : Type u} {Q : Type v} (π : S → Q) (r : Q → S)
    (T : S → S) (Tbar : Q → Q)
    (hreconstruct : Section π r)
    (hdescend : Descends π T Tbar) :
    (∀ q, π (r q) = q) ∧ (∀ s, π (T s) = Tbar (π s)) :=
  ⟨hreconstruct, hdescend⟩

theorem exact_sector_semantics
    {S : Type u} {Q : Type v} (π : S → Q) (r : Q → S)
    (T : S → S) (Tbar : Q → Q)
    (hreconstruct : Section π r)
    (hintertwine : ∀ s, π (T s) = Tbar (π s)) :
    (∀ n s, π (iterate T n s) = iterate Tbar n (π s)) ∧
      (∀ q, π (r q) = q) :=
  ⟨projection_iterate T Tbar π hintertwine, hreconstruct⟩

end Speedup
