# CT-001 — Acceptance Quotient Sufficiency Theorem

**Status:** CANDIDATE / FORMAL-PARTIAL TARGET  
**Scope:** deterministic finite-state decision systems  
**Evidence class:** CANDIDATE  

## Requirement

Determine when an implementation may replace a full state with a semantic quotient without changing acceptance behavior.

## Definitions

Let `X` be the full state space, `Y` the implementation state space, `T : X -> X` the reference transition, `U : Y -> Y` the reduced transition, and `Q : X -> Y` a quotient map. Let `A : X -> Obs` and `B : Y -> Obs` be acceptance observables.

Assume there exists a reconstruction/lifting map `R : Y -> X` satisfying the declared observable relation

`A (R (Q x)) = A x`.

Assume also the commuting condition

`Q (T x) = U (Q x)`

for every reachable `x`.

## Candidate theorem

For every reachable initial state `x0` and every `n : Nat`,

`Q (T^n x0) = U^n (Q x0)`

and therefore

`A (R (U^n (Q x0))) = A (T^n x0)`.

Thus acceptance-equivalent quotient execution is valid for the declared observable, provided the commuting law and reconstruction observable law hold on the reachable domain.

## Derivation

The first statement follows by induction on `n`.

Base:

`Q (T^0 x0) = Q x0 = U^0 (Q x0)`.

Step:

`Q (T^(n+1) x0)`
`= Q (T (T^n x0))`
`= U (Q (T^n x0))`
`= U (U^n (Q x0))`
`= U^(n+1) (Q x0)`.

Applying the reconstruction observable law to `U^n(Q x0)` gives the acceptance equality.

## Proof boundary

This theorem is mathematical and does **not** establish a runtime speedup. It also does not establish that a proposed quotient satisfies the commuting law. That obligation must be independently checked from the implementation/evidence contract.

## Required evidence closure

- literal forward quotient check;
- reverse reconstruction check;
- adversarial non-closure tests;
- native trace identity;
- environment and source hashes;
- performance measurement under the same workload;
- independent Lean verification where promoted.

## Speedup boundary

No `S_measured`, `S_verified`, `S_composed`, or `S_cumulative` value is asserted by this theorem.
