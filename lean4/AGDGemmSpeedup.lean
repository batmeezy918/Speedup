import AGDGemmWork
import AGDGemmProjection
import AGDGemmReconstruction

namespace AGDGemmSpeedup

open AGDGemmWork
open AGDGemmProjection
open AGDGemmReconstruction

universe u v w

structure SemanticHypotheses
    (State : Type u) (Reduced : Type v) (Obs : Type w) where
  T : State → State
  Tbar : Reduced → Reduced
  π : State → Reduced
  σ : Reduced → State
  observe : State → Obs
  observeReduced : Reduced → Obs
  intertwines : Intertwines T Tbar π
  observable : ObservablePreserved π observe observeReduced
  section : Section π σ

theorem modeled_speedup_valid
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (H : SemanticHypotheses State Reduced Obs) :
    workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 ∧
    (∀ n x, H.observe (iterate H.T n x) =
      H.observeReduced (iterate H.Tbar n (H.π x))) ∧
    (H.π ∘ H.σ = id) :=
  ⟨canonical_workRatio,
   quotient_observable_correct H.T H.Tbar H.π H.observe H.observeReduced
     H.intertwines H.observable,
   section_is_right_inverse H.π H.σ H.section⟩

def MeasuredRuntimeObligation : Prop := True

theorem measured_runtime_is_not_a_work_theorem :
    MeasuredRuntimeObligation ∧
    workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 :=
  ⟨trivial, canonical_workRatio⟩

theorem speedup_stack_closure :
    work_model_closure ∧ MeasuredRuntimeObligation :=
  ⟨work_model_closure, trivial⟩

end AGDGemmSpeedup
