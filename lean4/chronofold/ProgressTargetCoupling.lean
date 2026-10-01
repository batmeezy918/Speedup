/-!
Progress–Target Coupling bridge for the ChronoFold/Speedup formal layer.

Self-contained core-lane file. No empirical speedup is asserted here.
-/
namespace ChronoFold

universe u v

def iter {α : Type u} : Nat → (α → α) → α → α
  | 0, _, x => x
  | n + 1, f, x => f (iter n f x)

variable {X : Type u} {Q : Type v}

def Intertwines (π : X → Q) (T : X → X) (Tbar : Q → Q) : Prop :=
  ∀ x, π (T x) = Tbar (π x)

def Section (π : X → Q) (σ : Q → X) : Prop :=
  ∀ q, π (σ q) = q

theorem forward_iterate
    (π : X → Q) (T : X → X) (Tbar : Q → Q)
    (hT : Intertwines π T Tbar) :
    ∀ n x, π (iter n T x) = iter n Tbar (π x) := by
  intro n
  induction n with
  | zero => intro x; rfl
  | succ n ih =>
      intro x
      show π (T (iter n T x)) = Tbar (iter n Tbar (π x))
      rw [hT, ih]

theorem reconstructed_iterate
    (π : X → Q) (T : X → X) (Tbar : Q → Q) (σ : Q → X)
    (hσ : Section π σ) (hT : Intertwines π T Tbar) :
    ∀ n q, π (iter n T (σ q)) = iter n Tbar q := by
  intro n q
  have hfwd := forward_iterate π T Tbar hT n (σ q)
  calc
    π (iter n T (σ q)) = iter n Tbar (π (σ q)) := hfwd
    _ = iter n Tbar q := by rw [hσ q]

/-- A quotient-space target reached by an iterated transition. -/
def Reaches (Target : Q → Prop) (Tbar : Q → Q) (q : Q) : Prop :=
  ∃ n, Target (iter n Tbar q)

theorem iter_comm {α : Type u} (f : α → α) (n : Nat) (x : α) :
    iter n f (f x) = f (iter n f x) := by
  induction n with
  | zero => rfl
  | succ n ih =>
      show f (iter n f (f x)) = f (f (iter n f x))
      rw [ih]

theorem progress_target_coupling
    (D : Q → Nat)
    (Target : Q → Prop)
    (Tbar : Q → Q)
    (h_zero : ∀ q, D q = 0 → Target q)
    (h_dec : ∀ q, ¬ Target q → D (Tbar q) < D q) :
    ∀ q, Reaches Target Tbar q := by
  have wf : WellFounded (fun a b : Q => D a < D b) :=
    InvImage.wf D Nat.lt_wfRel.wf
  refine WellFounded.fix wf ?_
  intro q ih
  by_cases ht : Target q
  · exact ⟨0, ht⟩
  · have hlt : D (Tbar q) < D q := h_dec q ht
    obtain ⟨n, hn⟩ := ih (Tbar q) hlt
    refine ⟨n + 1, ?_⟩
    have hstep : iter (n + 1) Tbar q = iter n Tbar (Tbar q) := by
      show Tbar (iter n Tbar q) = iter n Tbar (Tbar q)
      exact (iter_comm Tbar n q).symm
    rw [hstep]
    exact hn

theorem zero_defect_is_target
    (D : Q → Nat)
    (Target : Q → Prop)
    (h_zero : ∀ q, D q = 0 → Target q) :
    ∀ q, D q = 0 → Target q := h_zero

theorem literal_target_transfer
    (π : X → Q)
    (T : X → X)
    (Tbar : Q → Q)
    (Target : Q → Prop)
    (hT : Intertwines π T Tbar)
    (x : X)
    (hreach : Reaches Target Tbar (π x)) :
    ∃ n, Target (π (iter n T x)) := by
  obtain ⟨n, hn⟩ := hreach
  exact ⟨n, by
    rw [forward_iterate π T Tbar hT n x]
    exact hn
  ⟩

theorem reconstructed_target_transfer
    (π : X → Q)
    (T : X → X)
    (Tbar : Q → Q)
    (σ : Q → X)
    (Target : Q → Prop)
    (hσ : Section π σ)
    (hT : Intertwines π T Tbar)
    (q : Q)
    (hreach : Reaches Target Tbar q) :
    ∃ n, Target (π (iter n T (σ q))) := by
  obtain ⟨n, hn⟩ := hreach
  exact ⟨n, by
    rw [reconstructed_iterate π T Tbar σ hσ hT n q]
    exact hn
  ⟩

theorem progress_target_literal_closure
    (π : X → Q)
    (T : X → X)
    (Tbar : Q → Q)
    (σ : Q → X)
    (D : Q → Nat)
    (Target : Q → Prop)
    (h_zero : ∀ q, D q = 0 → Target q)
    (h_dec : ∀ q, ¬ Target q → D (Tbar q) < D q)
    (hσ : Section π σ)
    (hT : Intertwines π T Tbar) :
    ∀ q, ∃ n, Target (π (iter n T (σ q))) := by
  intro q
  exact reconstructed_target_transfer π T Tbar σ Target hσ hT q
    (progress_target_coupling D Target Tbar h_zero h_dec q)

end ChronoFold
