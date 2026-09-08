# Proof-Carrying Speedup Scheduler (PCSS) — Hard Specification v1.0

**Target repository:** `batmeezy918/Speedup`
**Status:** normative engineering specification

## 0. Purpose

PCSS is a fail-closed execution, measurement, quotient-validation, Lean 4 formalization, and publication system for reproducible speedup experiments executed through an authorized remote host and Termux environment.

The system distinguishes empirical evidence from formal proof and never upgrades a claim without a corresponding evidence transition.

## 1. Constitutional invariant

`CLAIM_STRENGTH <= EVIDENCE_STRENGTH`

Unknown, missing, contradictory, stale, or unverifiable evidence is not publishable.

## 2. Canonical execution object

Each run is represented by:

`Run = (Scenario, Source, Environment, Inputs, Trace, Measurements, Quotient, Reconstruction, Invariants, Proof, Publication)`

Every component receives a deterministic content hash where applicable.

## 3. Scenario identity

A scenario MUST specify:

- source/script identity and SHA-256
- exact command
- input identity and SHA-256
- parameters
- repetitions and warmups
- random seed policy
- timing source
- expected observables
- baseline/candidate relationship
- environment fingerprint policy

The scenario manifest is hashed before execution and its hash propagates into all downstream artifacts.

## 4. Remote execution boundary

The remote host is an execution substrate, not a proof authority.

The executor MUST capture, where authorized:

- wall-clock duration
- process CPU time
- exit status
- stdout/stderr
- filesystem mutations
- process/resource observations
- environment fingerprint
- command metadata
- trace sequence

Termux MUST be treated as part of the measured environment whenever the workload executes there.

## 5. Performance protocol

A speedup claim MUST specify:

`metric, baseline, candidate, sample count, warmup, aggregation, uncertainty treatment, environment`

Required summary statistics should include median, p95, p99, minimum, maximum, and dispersion where enough samples exist.

A ratio alone is never sufficient to establish a general performance theorem.

## 6. Forward quotient

Let `E` be the execution-state space and:

`Q : E -> O`

be the explicitly declared acceptance-relevant observable quotient.

Candidate/baseline equivalence means:

`Q(E_candidate) = Q(E_baseline)`

or the formally declared tolerance relation for numerical observations.

Implementation identity is not required for quotient equivalence.

## 7. Reverse reconstruction

Forward agreement MUST be paired with a reverse path. Let `R` reconstruct an observable execution representation from the certificate/quotient artifact.

The verifier records:

`d(R(Q(e)), e) <= epsilon`

for the declared domain or bounded test sample.

The required bidirectional condition is:

`Q_forward(run) = Q_reverse(certificate)`

subject to the declared tolerance model.

## 8. Invariants

Each experiment declares its invariant signature.

Where appropriate, the invariant transition is expressed as:

`Omega(O psi) = Omega(psi)`

or by an explicitly specified admissible relation.

Canonical operator algebra may include:

`A = <S, Delta, Omega, Xi, ...>`

with execution derivations represented by compositions of declared operators.

## 9. Formalization boundary

Lean 4 proves formal propositions generated from the evidence contract. It does not transform a stopwatch reading into a mathematical theorem by itself.

The evidence-to-Lean compiler MUST bind certificate identities, assumptions, quotient relations, invariant relations, and declared numerical propositions into Lean obligations.

A proof is not accepted if unresolved obligations or `sorry` placeholders remain in the required verification surface.

## 10. Proof state model

Where the derivation is mathematical, reason over `psi in H` and represent transitions as:

`psi_(k+1) = O psi_k`

with:

`O_total = O_n o ... o O_2 o O_1`

and final state:

`psi_final = O_total psi_initial`

The derivation artifact MUST preserve the operator chain and relevant invariants.

## 11. Evidence state machine

`DISCOVERED -> SCENARIO_LOCKED -> EXECUTED -> CAPTURED -> NORMALIZED -> QUOTIENTED -> RECONSTRUCTED -> INVARIANTS_CHECKED -> PERFORMANCE_CHECKED -> LEAN_GENERATED -> LEAN_VERIFIED -> PUBLISHABLE`

Failure at any mandatory stage transitions to `QUARANTINED`.

## 12. Publication gate

Automatic publication is permitted if and only if:

`PUBLISH <=> I and R and Q and Q^-1 and Omega and X and L`

where:

- `I` = integrity verified
- `R` = reproducibility verified
- `Q` = forward quotient verified
- `Q^-1` = reverse reconstruction verified
- `Omega` = invariants verified
- `X` = performance evidence verified
- `L` = Lean obligations verified

Any false or unknown predicate means quarantine.

## 13. Repository roles

`batmeezy918/Speedup` is the designated speedup evidence, execution, quotient, certificate, and orchestration repository.

`batmeezy918/chronoflow-proof` remains the formal Lean proof corpus. Cross-repository linkage MUST use immutable commit/certificate/proof hashes.

## 14. Auto-push policy

The publisher MAY push verified artifacts only after the complete publication gate passes.

On failure it MUST preserve the artifact under quarantine and MUST NOT label it verified.

The publisher MUST record:

- source hash
- environment hash
- scenario hash
- trace hash
- certificate hash
- proof hash when available
- destination repository/ref
- publication decision

## 15. GitHub CI role

GitHub Actions is an independent verification layer. CI SHOULD re-check certificate integrity, execute Lean verification, and validate the publication manifest.

Local/remote verification and CI verification are distinct evidence events.

## 16. Scheduler role

A scheduler invocation is an orchestration event, not proof. It selects a deterministic scenario and requests execution.

High-frequency execution belongs on the authorized remote/Termux scheduler. ChatGPT scheduling is an orchestration layer and should not be treated as a sub-hour real-time scheduler.

## 17. Novelty discipline

Architecture novelty, implementation novelty, mathematical novelty, and scientific novelty are separate claims.

PCSS MAY document a newly constructed system design. It MUST NOT infer scientific novelty solely from the fact that the architecture is unusual.

## 18. Required artifact set

Each publishable run should contain, as applicable:

`scenario.json`
`environment.json`
`trace.jsonl`
`performance.json`
`quotient.json`
`reconstruction.json`
`invariants.json`
`certificate.json`
`derivation.json`
`Lean source/scaffold`
`proof result`
`publication manifest`

## 19. Security and authorization boundary

Commands are restricted to the designated workspace and authorized machine context. No scheduler rule grants implicit authorization for arbitrary filesystem or network operations.

Secrets, tokens, and credentials MUST NOT be written into evidence artifacts.

## 20. Canonical result classes

- `VERIFIED`: all mandatory gates pass.
- `FORMAL_PARTIAL`: formal obligations verified only for the declared scope.
- `STRONG_LOCAL`: strong local empirical evidence without complete formal closure.
- `CANDIDATE`: plausible result requiring further verification.
- `REGRESSION`: semantics preserved but performance objective failed.
- `DRIFT`: environment or execution substrate changed materially.
- `NON_EQUIVALENT`: quotient obligation failed.
- `RECONSTRUCTION_FAILURE`: reverse path failed.
- `LEAN_FAILURE`: formal gate failed.
- `QUARANTINED`: any invalid/unknown/contradictory state.
