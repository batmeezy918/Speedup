# T2 — AGD Controlled Quotient Refinement and Safe Policy Lifting

## 1. Problem

Extend the existing uncontrolled quotient intertwining framework (T1) to controlled transitions
and establish formal guarantees for policy lifting from quotient space to concrete space.

## 2. Existing T1 Result

The existing formalization establishes:
- **Intertwining**: `π ∘ T = T̄ ∘ π` for uncontrolled transitions `T : X → X`, `T̄ : Q → Q`
- **Section**: `π ∘ σ = id` for reconstruction `σ : Q → X`
- **Finite-horizon projection**: `π (Tⁿ x) = T̄ⁿ (π x)` for all `n : ℕ`
- **Observable preservation**: `obs (Tⁿ x) = obs̄ (T̄ⁿ (π x))`

These results are in `ChronoFold.GODS`, `ChronoFold.LinearQuotient`, `AGDGemmProjection`, and `AGDGemmReconstruction`.

## 3. New T2 Result

This module formalizes the controlled extension:

### Controlled Transitions
- `T : X → U → X` — concrete controlled transition
- `quotientStep : Q → U → Q` — quotient controlled transition
- **Controlled Intertwining**: `∀ x u, π (T x u) = quotientStep (π x) u`

### Policy Lifting
- `κ̄ : Q → U` — quotient policy
- `κ : X → U` defined by `κ x = κ̄ (π x)` — lifted concrete policy

### Core Theorems

1. **Single-step Commutation** (`closed_loop_quotient_commutes`):
   ```
   π (T x (κ x)) = quotientStep (π x) (κ̄ (π x))
   ```

2. **Finite-Horizon Trace Projection** (`closed_loop_trace_projection`):
   If `xₖ₊₁ = T xₖ (κ xₖ)` and `qₖ₊₁ = quotientStep qₖ (κ̄ qₖ)`,
   then `π xₖ = qₖ` for all `k : ℕ`.

3. **Policy Well-Definedness** (`policy_lift_respects_equiv`):
   If `π x = π y` then `κ x = κ y`.

4. **Invariant Preservation** (`closed_loop_invariant_preservation`):
   If `Pquotient` is a quotient invariant and `Pquotient (π x) → Pconcrete x`,
   then `Pconcrete` holds on all concrete trajectory states.

5. **Commuting Square** (`commuting_square`):
   ```
   π ∘ T_κ = T̄_κ̄ ∘ π
   ```
   where `T_κ x = T x (κ x)` and `T̄_κ̄ q = quotientStep q (κ̄ q)`.

## 4. Exact Assumptions

- `ControlledIntertwines T Tbar π` — the controlled intertwining law holds
- `h_inv : ∀ x, Pquotient (π x) → Pconcrete x` — concrete safety implied by quotient safety
- `hq : QuotientInvariant Tbar κbar Pquotient` — quotient invariant preserved by quotient closed-loop
- `hx₀ : Pquotient (π x₀)` — initial quotient state satisfies invariant

## 5. Exact Conclusions

- Single-step commutation holds by direct application of intertwining
- Finite-horizon projection by induction on `n`
- Policy well-definedness by definition of `κ = κ̄ ∘ π`
- Invariant preservation by combining quotient invariant with lifting implication
- Commuting square as function equality from single-step commutation

## 6. Relationship to Quotient Dynamics

The quotient transition `quotientStep` is the unique map making the diagram commute.
The lifted policy `κ = κ̄ ∘ π` is the unique policy making the closed-loop commute.

## 7. Relationship to Policy Lifting

Policy lifting is purely definitional: `κ x = κ̄ (π x)`.
No choice or axiom is involved.
Well-definedness follows immediately from function composition.

## 8. What Is Formally Established

- Controlled intertwining extends uncontrolled intertwining to control inputs
- Policy lifting preserves equivalence classes
- Closed-loop commutation holds for single step and finite horizons
- Quotient invariants lift to concrete invariants under the implication hypothesis
- The refinement square commutes exactly

## 9. What Remains Empirical

- Existence of `quotientStep` for a given concrete system (requires `Respects` condition)
- Existence of section `σ` for reconstruction
- Validity of specific quotient invariants for concrete systems
- Wall-clock performance of any implementation
- Hardware-specific behavior or thermal/RF characteristics

## 10. Future BFS/Reachability Theorem (T3)

**T3 — AGD Quotient Reachability / Safety Refinement**

Target concept:
```
reachable concrete state  ↔  reachable quotient state
```
under the lifted policy, with appropriate hypotheses.

BFS should eventually operate over `Q` rather than raw `X`.
This will require:
- Formal definition of reachability sets in both spaces
- Proof that `π` maps concrete reachable set into quotient reachable set
- Proof that section `σ` maps quotient reachable set into concrete reachable set
- Conditions under which the inclusion becomes equality