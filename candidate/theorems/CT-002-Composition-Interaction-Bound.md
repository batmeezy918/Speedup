# CT-002 — Composition Interaction Bound

**Status:** CANDIDATE / DERIVED TARGET  
**Scope:** sequential composition of independently measured speedup primitives  
**Evidence class:** CANDIDATE  

## Requirement

Separate a directly measured composed speedup from the product of isolated speedup ratios, and provide a rigorous interaction diagnostic.

## Definitions

Let a canonical baseline have execution time `T0`. Let primitive `P1` and `P2` be independently instantiated in the same declared workload family. Let their isolated measured times be `T1` and `T2`, and let the fully composed implementation have directly measured time `T12`.

Define

`S1 = T0/T1`,

`S2 = T0/T2`,

and

`S12 = T0/T12`.

Define the interaction/composability diagnostic

`K12 = S12/(S1*S2)`

whenever `S1*S2 != 0`.

## Candidate theorem

The directly measured composed speedup satisfies the identity

`S12 = K12 * S1 * S2`.

Consequently, multiplicative composition is exact **if and only if** `K12 = 1`.

For arbitrary real positive measured times, `K12` is a descriptive statistic of the realized composition; it is not a predictive law.

## Proof

By definition,

`K12 = S12/(S1*S2)`.

Multiplication by `S1*S2` gives

`S12 = K12*S1*S2`.

If `K12=1`, then `S12=S1*S2`. Conversely, if `S12=S1*S2`, division by the nonzero denominator gives `K12=1`.

No assumption about independence, additivity, or hardware behavior is required for this identity.

## Recursive protocol consequence

The identity does **not** authorize predicting `S12` from `S1` and `S2`. The protocol must measure `T12` directly. The same rule applies recursively to `P1 o P2 o ... o Pn`.

The canonical cumulative quantity remains

`S_cumulative = T_canonical_baseline / T_fully_composed`.

## Attribution obligation

A valid composition record must separately identify `SavedWork_1`, `SavedWork_2`, overlap, new overhead, interaction, and net saved work. A favorable `K12` does not prove causal attribution.

## Proof boundary

This is a mathematical bookkeeping theorem about measured positive execution times. It proves no universal speedup, no optimality, no hardware mechanism, and no performance guarantee.

## Required evidence closure

- common scenario identity;
- independent measurements of `T0`, `T1`, `T2`, and `T12`;
- uncertainty treatment;
- direct cumulative measurement;
- interaction-factor calculation;
- attribution evidence;
- source/environment hashes;
- equivalence and reconstruction evidence;
- formal verification where promotion requires it.

## Speedup boundary

No speedup is promoted to `VERIFIED` by this theorem. `S1`, `S2`, `S12`, and `K12` remain scenario-scoped measurements until their independent evidence gates close.
