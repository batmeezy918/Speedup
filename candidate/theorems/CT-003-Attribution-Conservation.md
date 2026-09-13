# CT-003 — Speedup Attribution Conservation Theorem

**Status:** CANDIDATE / FORMAL-PARTIAL TARGET  
**Scope:** sequential implementation transformations with explicit work attribution  
**Evidence class:** CANDIDATE  

## Requirement

Determine when the performance contribution attributed to individual primitives and their interactions accounts for the observed baseline-to-composed reduction without double counting.

## Definitions

Let `W0` be the canonical baseline work or measured time and `Wc` the fully composed implementation work or measured time. For primitives `P_i`, let `SavedWork_i` denote work removed by the primitive when evaluated under the declared attribution protocol. Let `Overlap_ij` denote work savings counted by both `P_i` and `P_j`, and let `NewOverhead_i` and `Interaction_ij` denote respectively primitive-specific and pairwise composition overheads under that same protocol.

Define

`NetSavedWork = sum_i SavedWork_i - sum_{i<j} Overlap_ij - sum_i NewOverhead_i - sum_{i<j} Interaction_ij`.

Let the observed reduction be

`ObservedSavedWork = W0 - Wc`.

## Candidate theorem

If the attribution protocol partitions every difference between the canonical baseline and fully composed implementation into the declared primitive savings, overlap corrections, primitive overheads, pairwise interaction terms, and no unclassified residual remains, then

`NetSavedWork = ObservedSavedWork`.

Consequently, any attribution claim that omits a nonzero residual, overlap, or interaction term is incomplete under the declared accounting model.

## Derivation

By the partition assumption, the baseline-to-composed difference is exactly the sum of all classified contributions with their declared signs. Substitution of the definitions gives

`W0 - Wc`
`= sum_i SavedWork_i - sum_{i<j} Overlap_ij`
`  - sum_i NewOverhead_i - sum_{i<j} Interaction_ij`
`= NetSavedWork`.

The equality is therefore an accounting consequence of exhaustive, non-overlapping attribution categories; it is not a causal inference from timing alone.

## Proof boundary

This theorem does **not** prove that a measured primitive caused its attributed saving. It requires an independently specified attribution protocol and evidence that the categories are exhaustive and consistently measured. Correlation with a timing change is insufficient.

## Required evidence closure

- locked canonical baseline and fully composed implementation;
- isolated primitive measurements under the declared protocol;
- explicit overlap measurements or justified zero-overlap evidence;
- explicit primitive and interaction overhead measurements;
- residual/error term reported rather than silently discarded;
- native trace sufficient to connect attribution categories to execution;
- uncertainty treatment for all measured contributions;
- independent formal verification where promoted.

## Speedup boundary

No `S_measured`, `S_verified`, `S_composed`, or `S_cumulative` value is asserted by this theorem. Attribution closure cannot promote a speedup primitive by itself.
