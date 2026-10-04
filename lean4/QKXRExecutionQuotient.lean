namespace SiliconSpeedup

universe u q a

variable {X : Type u} {Q : Type q} {A : Type a}

def ExecutionPreserving (π : X → Q) (exec : X → A) : Prop :=
  ∀ ⦃x y : X⦄, π x = π y → exec x = exec y

def RefinedQuotient (π : X → Q) (exec : X → A) : X → Q × A :=
  fun x => (π x, exec x)

theorem execution_preserved_by_refinement
    (π : X → Q) (exec : X → A) :
    ∀ ⦃x y : X⦄,
      RefinedQuotient π exec x = RefinedQuotient π exec y →
      exec x = exec y := by
  intro x y h
  exact congrArg Prod.snd h

theorem coarse_execution_collision_rejects
    (π : X → Q) (exec : X → A)
    (hnot : ¬ ExecutionPreserving π exec) :
    ∃ x y, π x = π y ∧ exec x ≠ exec y := by
  classical
  apply Classical.byContradiction
  intro h
  apply hnot
  intro x y hxy
  apply Classical.byContradiction
  intro hne
  apply h
  exact ⟨x, y, hxy, hne⟩

theorem execution_preserving_class
    (π : X → Q) (exec : X → A)
    (h : ExecutionPreserving π exec) :
    ∀ ⦃x y : X⦄, π x = π y → exec x = exec y := by
  exact h

end SiliconSpeedup
