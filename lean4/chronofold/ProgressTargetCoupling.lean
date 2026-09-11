/-!
Progress–Target Coupling bridge for the ChronoFold/Speedup formal layer.

This file is deliberately narrow: it closes the mathematical gap between a
Nat-valued strict-progress measure and eventual target reachability, then
binds that quotient result to the existing literal reconstruction/intertwining
layer.

Evidence status:
* Theorems in this file are NEW constructions until CI compiles them in the
  repository's canonical Lean environment.
* No empirical speedup is asserted here.
* No universal optimizer or wall-clock claim is asserted here.
-/
namespace ChronoFold

universe u v

variable {X : Type u} {Q : Type v}

/-- A quotient-space target reached by an iterated transition. -/
def Reaches (Target : Q → Prop) (Tbar : Q → Q) (q : Q) : Prop :=
  ∃ n, Target (iter n Tbar q)

/--
Progress–Target Coupling:
if every non-target state strictly decreases a Nat-valued defect, and zero
is target, then every initial quotient state reaches the target in finitely
many iterations.
-/
theorem progress_target_coupling
    (D : Q → Nat)
    (Target : Q → Prop)
    (Tbar : Q → Q)
    (h_zero : ∀ q, D q = 0 → Target q)
    (h_dec : ∀ q, ¬ Target q → D (Tbar q) < D q) :
    ∀ q, Reaches Target Tbar q := by
  intro q
  induction h : D q using Nat.strong_induction_on with
  | h d ih =>
      by_cases ht : Target q
      · exact ⟨0, by simpa [iter] using ht⟩
      · have hlt : D (Tbar q) < d := by
          simpa [h] using h_dec q ht
        obtain ⟨n, hn⟩ := ih (D (Tbar q)) hlt (Tbar q) rfl
        exact ⟨n + 1, by simpa [iter] using hn⟩

/-- Zero-defect characterization is sufficient to turn termination into the target. -/
theorem zero_defect_is_target
    (D : Q → Nat)
    (Target : Q → Prop)
    (h_zero : ∀ q, D q = 0 → Target q) :
    ∀ q, D q = 0 → Target q := by
  intro q hq
  exact h_zero q hq

/--
Literal target transfer through the existing intertwining theorem.
If the quotient trajectory reaches `Target`, the corresponding literal
trajectory reaches the same quotient target.
-/
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
    rw [forward_iterate π T Tbar hT]
    exact hn
  ⟩

/--
Reconstructed literal execution from a certified quotient representative.
The section law preserves the quotient target at every finite iterate.
-/
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
    have hrec := reconstructed_iterate π T Tbar hσ hT n q
    rw [hrec]
    exact hn
  ⟩

/--
Master closure for the first concrete gap:
Progress–Target Coupling + intertwining + section gives literal target
reachability from every reconstructed quotient state.
-/
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
  apply reconstructed_target_transfer π T Tbar σ Target hσ hT q
  exact progress_target_coupling D Target Tbar h_zero h_dec q

end ChronoFold
