# PCSS Constitution v1.0

## Article 1 — Evidence supremacy

`CLAIM_STRENGTH <= EVIDENCE_STRENGTH` is invariant. No scheduler, benchmark, language model, or publication step may increase claim strength without a corresponding evidentiary transition.

## Article 2 — Deterministic scenario identity

Every experiment has a canonical scenario manifest containing workload, implementation identifiers, parameters, environment, command, repetitions, warm-up policy, timing source, random seeds, and expected observables.

The manifest is hashed before execution. Derived artifacts retain the manifest hash.

## Article 3 — Observable quotient

Let `E` be the execution state space and `Q : E -> O` the declared acceptance-relevant observable quotient. Candidate and baseline are equivalent only relative to the declared `Q` and invariant set `Ω`.

Required forward condition:

`Q(E_candidate) = Q(E_baseline)`

or the explicitly declared tolerance relation when the domain is numerical.

## Article 4 — Reverse reconstruction

Forward agreement alone is insufficient. The verifier must test a declared reconstruction operator `R` and record reconstruction error:

`d(R(Q(e)), e) <= ε`

for every tested state or an explicitly bounded sampled domain.

## Article 5 — Invariants

All declared acceptance invariants must be preserved. For operator transition `e' = O(e)`, the verifier records the relevant invariant signature `Ω(e')` and checks the declared relation to `Ω(e)`.

## Article 6 — Performance

Performance claims must specify metric, baseline, candidate, sample count, aggregation rule, confidence/uncertainty treatment, and environment. A ratio is evidence only within that scope.

## Article 7 — Formal gate

Lean is used to verify mathematical obligations instantiated from the experiment certificate. Lean does not magically prove wall-clock measurements. Empirical observations remain empirical artifacts; formal proofs establish the stated mathematical relations.

## Article 8 — Quarantine

Any failed, incomplete, contradictory, stale, or unverifiable artifact is retained under quarantine and excluded from verified indexes.

## Article 9 — Publication

The only automatic publication transition is:

`PUBLISH <=> I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L`

If any predicate is false or unknown: `QUARANTINE`.

## Article 10 — Novelty discipline

A design may be described as newly constructed in this repository. Scientific novelty is a separate claim requiring prior-art analysis and cannot be inferred from architecture alone.
