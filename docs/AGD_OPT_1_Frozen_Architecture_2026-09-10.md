# AGD-OPT-1 — Frozen Proof-Bound Optimizer Architecture

**Silicon Speedup / AGD — Architecture Freeze — 2026-09-10**

## Status and Freeze

AGD-OPT-1 is frozen as the first proof-bound AGD optimizer architecture. The freeze records the strongest defensible consequences of the closed quotient/operator/reconstruction machinery and the termination boundary recovered from prior formal work. It does not promote physical speedup, universal optimization dominance, or arbitrary numerical accuracy to theorem status.

## Evidence Discipline

**CLAIM STRENGTH ≤ EVIDENCE STRENGTH.**

Proof pipeline: GREEN theorem → formal consequence → derived operational theorem/run → concrete instantiation.

A benchmark observation is never retroactively used as a proof.

## Literal Failure That Triggered the Reconstruction

The failed literal BBOB implementation applied a conventional update and then projected the resulting state. Its effective form was `x_(k+1)^Q = Π(x_k^Q + s_k)`, rather than a quotient-native transition `q_(k+1) = F̄(q_k)`. The run preserved its selected invariants and reconstruction checks across 360 problems, but literal objective equivalence failed for 360/360 cases and aggregate wall-clock speed was 0.8465×.

Architectural consequence: projection must not be a post-hoc repair operation. The optimizer must be constructed on the admissible quotient and its transition must itself descend.

## Closed Mathematical Foundation

Let `X` be the realization/state space. Let `Ω` and `C` denote declared constitutional observables/laws. Define `x ~ y` when the declared acceptance-relevant observables agree. The quotient is `Q = X/~` with projection `π : X → Q`.

A quotient computation is legitimate only when the transition respects the equivalence relation: `x ~ y ⇒ T(x) ~ T(y)`. This yields a descended operator `T̄` satisfying `π ∘ T = T̄ ∘ π` and therefore `π ∘ T^n = T̄^n ∘ π`.

With a reconstruction/section `ρ` satisfying `π ∘ ρ = id_Q` on the certified sector, quotient execution has a controlled realization boundary.

## Admissible Computational Domain

Define `X_A = {x ∈ X : A(x) = 1}` and `Q_A = π(X_A)`. The optimizer state is `q_k ∈ Q_A`. The candidate generator `G_θ` must satisfy `G_θ(Q_A) ⊆ Q_A`. Admissibility is constructed into the transition rather than repaired afterward.

## Objective Descent Requirement

A quotient optimizer requires a descended objective `f̄ : Q_A → ℝ` such that `f̄(πx) = f(x)` on the certified domain, equivalently `x ~ y ⇒ f(x) = f(y)`. If the objective does not descend, AGD must refuse to claim quotient-equivalent optimization for that objective.

## Optimizer Descent / Intertwining

For an underlying full transition `F`, the required bridge is `π ∘ F = F̄ ∘ π`. Iteration then gives `π ∘ F^n = F̄^n ∘ π`. This is the missing semantic condition in the failed projected BBOB construction.

The optimizer therefore operates on `Q_A` directly: `q_(k+1) = F̄(q_k)`, not `F` followed by projection.

## AGD-OPT-1 Core Algorithm

1. Initialize `x_0 ∈ X_A` and construct `q_0 = π(x_0)`.
2. Generate an admissible candidate `q'_k = G_(θ_k)(q_k)`.
3. Evaluate the descended objective `v_k = f̄(q_k)`, `v'_k = f̄(q'_k)`.
4. Accept only through the constitutional acceptance relation.
5. Record a proof-carrying witness containing state, invariants, constitutional status, objective values, progress certificate, and acceptance decision.
6. Terminate semantically only when the certified terminal predicate is reached.
7. Reconstruct `x* = ρ(q*)` on the certified reconstruction sector.
8. Run the literal/external verifier before promoting the result to a literal solution.

## Termination Guarantee

The prior closed correct-by-construction search theorem supplies the termination pattern: for a nonterminal transition, a natural-valued defect/rank `D` must strictly decrease, `D(q′) < D(q)`. Because `<` on `ℕ` is well-founded, an execution beginning with `D(q_0) = D_0` has at most `D_0` strict-progress transitions before reaching a terminal state, assuming every nonterminal state admits a certified progress step.

Admissibility/closure alone is not a termination proof; identity/cyclic admissible operators are explicit counterexamples. Therefore AGD-OPT-1 freezes semantic termination around a well-founded decreasing measure, not a time/evaluation budget.

## Literal Target-Accuracy Contract

The existing formal corpus does not justify a universal floating-point target such as `|f(x) − f*| < 10^-9`. The correct contract is target-predicate based.

Let `P(q)` be the declared target predicate. The terminal correctness obligation is `terminal(q) ⇒ P(q)`, followed by reconstruction and the corresponding literal verifier. For numerical optimization one may declare `P_ε(q) := f̄(q) − f* ≤ ε`, but the terminal-to-ε theorem must be proven for the particular problem class before it is called a guarantee.

For exact/discrete domains, literal accuracy can be an exact verifier predicate. Candidate validity and target reachability remain separate obligations.

## Missing Piece — Progress–Target Coupling

The remaining central theorem is to construct, for a concrete optimization class, a well-founded target defect `D_P : Q_A → ℕ` such that failure of the target implies a certified transition with `D_P` strictly decreasing. The desired coupling is:

`target → defect/rank → strict decrease → well-foundedness → finite termination → target → reconstruction → literal verification`.

This is the bridge that turns the generic closed termination machinery into an actual optimizer termination-and-target theorem.

## Three Accuracy Layers

- **Structural accuracy:** declared invariants/constitutional observables are preserved by the quotient and reconstruction.
- **Optimization accuracy:** the terminal quotient state satisfies the declared optimization predicate or ε-target, when the required theorem is closed.
- **Literal accuracy:** the reconstructed result passes the declared external/literal verifier.

## Cost and Speedup Boundary

The total cost is `C_AGD = C_π + C_F̄ + C_ρ`. Structural state reduction is not itself work reduction, and work reduction is not itself wall-clock reduction. A performance claim requires a bound or measurement of the full common boundary, including projection/class construction, reduced execution, reconstruction, verification, and a strong baseline.

The previously derived finite model `C_D(d,T)=Td` and `C_R(d,r,T)=2d+Tr` yields `C_R<C_D` iff `T > 2d/(d−r)`, under the stated model. This is a conditional complexity-model theorem, not a universal hardware speedup theorem.

## Frozen Refusal Rules

- No quotient-equivalence claim without objective descent/factorization where required.
- No optimizer trajectory-equivalence claim without transition intertwining/descent.
- No termination guarantee without a well-founded strict-progress measure.
- No numerical accuracy guarantee without a proven terminal-to-target bridge.
- No physical speedup claim without a common measured/bounded cost boundary.
- No universal speedup, optimizer dominance, or SOTA claim without independent evidence satisfying the project publication gates.

## Frozen Architectural Statement

AGD-OPT-1 is a representation-aware, proof-bound optimizer that searches an admissible quotient domain, applies constitution-preserving descended transitions, accepts only certified progress, terminates through a well-founded target-linked measure, reconstructs through a certified boundary, and requires literal verification before promoting a result.

This is a formal/architectural freeze. It is not a claim that the implementation is already universally optimal, universally faster, or SOTA.

## Next Formal Closure

The next theorem to construct is the concrete Progress–Target Coupling for a selected optimization class. The implementation should be generated from that theorem rather than retrofitting a conventional optimizer with a projection operator.
