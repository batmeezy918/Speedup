import AGDGemmProjection

namespace AGDGemmReconstruction

open AGDGemmProjection

universe u v

def Section {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State) : Prop :=
  ∀ q, π (σ q) = q

theorem section_is_right_inverse {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State)
    (h : Section π σ) :
    π ∘ σ = id := by
  funext q
  exact h q

theorem reconstructed_operator {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State)
    (T : State → State) (Tbar : Reduced → Reduced)
    (hσ : Section π σ)
    (hI : Intertwines T Tbar π) :
    π ∘ T ∘ σ = Tbar := by
  funext q
  calc
    (π ∘ T ∘ σ) q = π (T (σ q)) := rfl
    _             = Tbar (π (σ q)) := hI (σ q)
    _             = Tbar q := by rw [hσ q]

theorem reconstructed_iterate {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State)
    (T : State → State) (Tbar : Reduced → Reduced)
    (hσ : Section π σ)
    (hI : Intertwines T Tbar π) :
    ∀ n q, π (iterate T n (σ q)) = iterate Tbar n q := by
  intro n q
  calc
    π (iterate T n (σ q))
        = iterate Tbar n (π (σ q)) := projection_iterate T Tbar π hI n (σ q)
    _   = iterate Tbar n q := by rw [hσ q]

theorem reconstruction_closure {State : Type u} {Reduced : Type v}
    (π : State → Reduced) (σ : Reduced → State)
    (T : State → State) (Tbar : Reduced → Reduced)
    (hσ : Section π σ)
    (hI : Intertwines T Tbar π) :
    (π ∘ σ = id) ∧
    (π ∘ T ∘ σ = Tbar) ∧
    (∀ n q, π (iterate T n (σ q)) = iterate Tbar n q) :=
  ⟨section_is_right_inverse π σ hσ,
   reconstructed_operator π σ T Tbar hσ hI,
   reconstructed_iterate π σ T Tbar hσ hI⟩

end AGDGemmReconstruction
