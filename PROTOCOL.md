# PCSS Operational Protocol

## State machine

`PROPOSED -> SPECIFIED -> EXECUTED -> CAPTURED -> QUOTIENT_CHECKED -> RECONSTRUCTED -> INVARIANT_CHECKED -> BENCHMARKED -> FORMALIZED -> VERIFIED`

Failure from any mandatory gate transitions to `QUARANTINED`.

## Required artifact chain

1. Scenario manifest
2. Environment fingerprint
3. Baseline trace
4. Candidate trace
5. Forward quotient result
6. Reverse reconstruction result
7. Invariant certificate
8. Performance certificate
9. Evidence manifest with hashes
10. Lean obligation/scaffold
11. Lean build/test result
12. Publication decision

## Execution

The executor may launch authorized local/remote commands, including Termux workloads, but execution authority is external to the mathematical claim. Every command and result must be captured.

## Derivation

Natural-language requests are compiled into typed experiment specifications. Every mathematical transformation must identify its operator, preconditions, inputs, outputs, and evidence source. If a step cannot be represented as a declared transformation/operator, it becomes an explicit unresolved obligation.

Canonical composition:

`ψ_final = O_n ∘ ... ∘ O_2 ∘ O_1 (ψ_initial)`

## Quotient protocol

For baseline state `e_b` and candidate state `e_c`, compute:

`q_b = Q(e_b)`
`q_c = Q(e_c)`

Then evaluate the declared equivalence relation. If exact equality is not mathematically appropriate, the tolerance and metric must be declared before execution.

Reverse check:

`e_hat = R(q_c)`
`err = d(e_hat, e_c)`

The certificate must contain the domain, metric, tolerance, maximum/aggregate error, and pass/fail decision.

## Formalization

Generate Lean obligations from the certificate rather than translating benchmark prose into an ungrounded theorem. A proof may establish quotient preservation or reconstruction properties for the modelled domain while the benchmark remains an empirical result.

## Publication

Only the publisher may move an artifact into the verified index. It must consume the gate result rather than independently reinterpret raw benchmark output.
