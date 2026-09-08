# PCSS Implementation Specification v1.0

## A. Pipeline

```text
Scheduler
  -> scenario lock
  -> remote execution
  -> Termux execution
  -> trace capture
  -> normalization
  -> forward quotient
  -> reverse reconstruction
  -> invariant checks
  -> performance statistics
  -> evidence certificate
  -> Lean obligation generation
  -> Lean verification
  -> publication gate
  -> GitHub push
```

## B. Directory contract

```text
speedup/
  scenarios/        deterministic experiment manifests
  runners/          local/remote execution adapters
  capture/          trace and resource capture
  quotient/         observable quotient implementation
  reconstruction/   reverse certificate-to-observable logic
  invariants/       invariant evaluators
  benchmarks/       benchmark protocols and summaries
  evidence/         immutable certificates and manifests
  derivation/       operator chains and derivation metadata
  lean4/            generated obligations and verified propositions
  publisher/        fail-closed release logic
  quarantine/       invalid or incomplete evidence
```

## C. Hash chain

For run `r`, calculate:

`H_s = SHA256(canonical(source))`
`H_i = SHA256(canonical(input))`
`H_e = SHA256(canonical(environment))`
`H_t = SHA256(canonical(trace))`
`H_q = SHA256(canonical(quotient))`
`H_c = SHA256(canonical(certificate))`

The publication manifest records all hashes and their dependency ordering.

## D. Bidirectional quotient contract

Forward:

`candidate_trace -> Q -> candidate_observable`

`baseline_trace -> Q -> baseline_observable`

Required relation:

`Equivalent(candidate_observable, baseline_observable)`

Reverse:

`certificate -> reconstruct -> reconstructed_observable -> Q`

Required relation:

`Equivalent(forward_quotient, reverse_quotient)`

For numerical observables, `Equivalent` MUST reference an explicit tolerance or statistically specified acceptance relation.

## E. Performance contract

Default measurements:

- cold-start wall time
- warm-start wall time
- process CPU time
- peak resident memory where available
- I/O counters where available
- network timing only when materially part of workload
- median, p95, p99
- sample count and dispersion

Baseline and candidate MUST use the same scenario protocol unless the experiment explicitly defines a controlled difference.

## F. Lean obligation generation

The evidence compiler creates theorem obligations from a certificate. Example conceptual surface:

```lean
structure EvidenceCertificate where
  scenarioHash : String
  sourceHash : String
  inputHash : String
  environmentHash : String
  traceHash : String
  quotientHash : String
  reverseHash : String
  integrityOK : Bool
  reproducibilityOK : Bool
  quotientForwardOK : Bool
  reconstructionReverseOK : Bool
  invariantsOK : Bool
  performanceOK : Bool

structure FormalCertificate extends EvidenceCertificate where
  leanTheorems : List String
```

The Lean layer proves the mathematical relations claimed by the certificate. The runtime evidence remains separately recorded and hashed.

## G. No-sorry gate

The formal pipeline MUST reject required proofs containing `sorry`, unresolved goals, or failed imports/builds. Generated scaffolding may contain placeholders only before the formal gate and MUST NEVER receive a verified status while placeholders remain.

## H. Cross-repository linkage

`batmeezy918/Speedup` stores execution/evidence artifacts.

`batmeezy918/chronoflow-proof` stores formal Lean proof corpus.

A cross-link manifest MUST identify:

`speedup_run_id`
`speedup_commit`
`certificate_hash`
`lean_commit`
`lean_proof_hash`
`theorem_identifiers`
`verification_timestamp`

## I. Failure behavior

Any failure is explicit and retained. Never silently retry into a passing result without recording all attempts.

Failure codes:

`HASH_MISMATCH`
`SCENARIO_DRIFT`
`ENVIRONMENT_DRIFT`
`TRACE_NONDETERMINISM`
`QUOTIENT_MISMATCH`
`RECONSTRUCTION_FAILURE`
`INVARIANT_FAILURE`
`PERFORMANCE_REGRESSION`
`LEAN_BUILD_FAILURE`
`LEAN_OBLIGATION_FAILURE`
`CERTIFICATE_INVALID`

## J. Publication semantics

The publisher may create a verified publication only after all mandatory booleans are true.

```text
verified = integrity
        && reproducibility
        && quotient_forward
        && reconstruction_reverse
        && invariants
        && performance
        && lean
```

Otherwise:

```text
verified = false
publication = quarantine
```

## K. Scheduler extension point

ChatGPT scheduling is used for orchestration. The remote host/Termux runner handles execution and any cadence requiring sub-hour repetition.

A scheduler run should request a single deterministic evaluation and receive a terminal state:

`PUBLISHABLE | QUARANTINED | DRIFT | REGRESSION | NON_EQUIVALENT | LEAN_FAILURE`

## L. Operator representation

Derivations SHOULD record:

`O_total = O_publish o O_lean o O_certificate o O_quotient o O_measure o O_execute o O_scenario`

and, when mathematical state is used:

`psi_final = O_total psi_initial`

Relevant invariants SHOULD be emitted at every admissible transformation boundary.
