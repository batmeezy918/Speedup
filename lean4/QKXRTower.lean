namespace QKXR

variable {X S I E : Type}

def FactorsThrough {Q B : Type} (π : X → Q) (inv : X → B) : Prop :=
  ∃ f : Q → B, ∀ x, inv x = f (π x)

structure Signature (S I E : Type) where
  spread : S
  imbalance : I
  execution : E

def DerivedSignature (spread : X → S) (imbalance : X → I) (exec : X → E) (x : X) :
    Signature S I E :=
  { spread := spread x, imbalance := imbalance x, execution := exec x }

def TowerQuotient (spread : X → S) (imbalance : X → I) (exec : X → E) :
    X → Signature S I E :=
  DerivedSignature spread imbalance exec

theorem spread_descends
    (spread : X → S) (imbalance : X → I) (exec : X → E) :
    FactorsThrough (TowerQuotient spread imbalance exec) spread := by
  refine ⟨fun q => q.spread, ?_⟩
  intro x
  rfl

theorem imbalance_descends
    (spread : X → S) (imbalance : X → I) (exec : X → E) :
    FactorsThrough (TowerQuotient spread imbalance exec) imbalance := by
  refine ⟨fun q => q.imbalance, ?_⟩
  intro x
  rfl

theorem execution_descends
    (spread : X → S) (imbalance : X → I) (exec : X → E) :
    FactorsThrough (TowerQuotient spread imbalance exec) exec := by
  refine ⟨fun q => q.execution, ?_⟩
  intro x
  rfl

theorem tower_components_are_recoverable
    (spread : X → S) (imbalance : X → I) (exec : X → E) (x : X) :
    (TowerQuotient spread imbalance exec x).spread = spread x ∧
    (TowerQuotient spread imbalance exec x).imbalance = imbalance x ∧
    (TowerQuotient spread imbalance exec x).execution = exec x := by
  exact ⟨rfl, rfl, rfl⟩

theorem tower_execution_preserved
    (spread : X → S) (imbalance : X → I) (exec : X → E)
    {x y : X}
    (h : TowerQuotient spread imbalance exec x =
         TowerQuotient spread imbalance exec y) :
    exec x = exec y := by
  exact congrArg Signature.execution h

def Section (π : X → Signature S I E) (σ : Signature S I E → X) : Prop :=
  ∀ q, π (σ q) = q

theorem reconstructed_execution_preserved
    (spread : X → S) (imbalance : X → I) (exec : X → E)
    (σ : Signature S I E → X)
    (hsec : Section (TowerQuotient spread imbalance exec) σ) :
    ∀ x, exec (σ (TowerQuotient spread imbalance exec x)) = exec x := by
  intro x
  have h := hsec (TowerQuotient spread imbalance exec x)
  exact congrArg Signature.execution h

end QKXR
