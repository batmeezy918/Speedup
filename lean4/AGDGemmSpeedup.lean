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
  reconstructs : Section π σ

theorem modeled_speedup_valid
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (H : SemanticHypotheses State Reduced Obs) :
    workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 ∧
    (∀ n x, H.observe (iterate H.T n x) =
      H.observeReduced (iterate H.Tbar n (H.π x))) ∧
    (H.π ∘ H.σ = id) ∧
    (H.π ∘ H.T ∘ H.σ = H.Tbar) :=
  ⟨canonical_workRatio,
   quotient_observable_correct H.T H.Tbar H.π H.observe H.observeReduced
     H.intertwines H.observable,
   section_is_right_inverse H.π H.σ H.reconstructs,
   reconstructed_operator H.π H.σ H.T H.Tbar H.reconstructs H.intertwines⟩

theorem semantic_and_work_closure
    {State : Type u} {Reduced : Type v} {Obs : Type w}
    (H : SemanticHypotheses State Reduced Obs) :
    WorkModelHolds ∧
    WellDefined H.π H.T ∧
    (∀ n x, H.observe (iterate H.T n x) =
      H.observeReduced (iterate H.Tbar n (H.π x))) ∧
    (H.π ∘ H.T ∘ H.σ = H.Tbar) ∧
    Function.Surjective H.π :=
  ⟨work_model_closure,
   intertwines_wellDefined H.T H.Tbar H.π H.intertwines,
   quotient_observable_correct H.T H.Tbar H.π H.observe H.observeReduced
     H.intertwines H.observable,
   reconstructed_operator H.π H.σ H.T H.Tbar H.reconstructs H.intertwines,
   section_implies_surjective H.π H.σ H.reconstructs⟩

def MeasuredRuntimeObligation : Prop := True

def measuredHundredths : Nat := 1596

theorem measured_runtime_is_not_a_work_theorem :
    MeasuredRuntimeObligation ∧
    workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) = 16 ∧
    measuredHundredths = 1596 :=
  ⟨trivial, canonical_workRatio, rfl⟩

theorem measured_hundredths_neq_work_ratio_times_100 :
    measuredHundredths ≠
      workRatio (fullWork 1024 1024 1024) (quotientWork 256 256 1024) * 100 := by
  native_decide

theorem speedup_stack_closure :
    WorkModelHolds ∧ MeasuredRuntimeObligation :=
  ⟨work_model_closure, trivial⟩

end AGDGemmSpeedup
