# PCSS RUNBOOK — First Connected Speedup Proof

## Objective

Connect the authorized Remote Desktop Commander execution substrate to the `batmeezy918/Speedup` proof workflow, then produce the first evidence-backed speedup run without bypassing the proof gate.

## Phase 1 — Remote substrate

1. Verify the remote device is online.
2. Establish a low-latency ping baseline.
3. Locate the designated Speedup workspace or clone target.
4. Locate the Termux execution boundary when applicable.
5. Capture the environment fingerprint before changing state.

## Phase 2 — Scenario lock

Create a deterministic manifest with:

- source/script path
- source SHA-256
- exact command
- input SHA-256
- parameters
- repetitions
- warmup count
- random seed
- timing source
- filesystem scope
- expected quotient observables
- invariant definitions

The manifest becomes immutable for the run.

## Phase 3 — Baseline/candidate

Run baseline and candidate under the same declared protocol. Do not optimize the benchmark itself. Separate transport, process startup, CPU, I/O, and end-to-end timing.

## Phase 4 — Quotient

Normalize raw traces, map them through the declared observable quotient, and compare candidate against baseline.

Then reconstruct the observable state from the certificate and compare the reverse quotient against the forward quotient.

## Phase 5 — Proof

Generate Lean obligations from the certificate. Formalize mathematical relations actually justified by the evidence. Do not encode empirical measurements as axioms merely to force a theorem through the compiler.

## Phase 6 — Gate

Run:

```text
integrity
reproducibility
quotient_forward
reconstruction_reverse
invariants
performance
lean
```

All seven must be true for `VERIFIED`.

## Phase 7 — Publication

Only a verified certificate may be promoted into the verified publication namespace. Failed/unknown results remain quarantined with their diagnostic artifacts.

## Phase 8 — Cross-repository proof lineage

The Speedup repository is the empirical/evidence corpus. The existing `batmeezy918/chronoflow-proof` repository is the formal proof corpus. A successful run should record the Speedup commit/certificate hash and the corresponding Lean proof commit/hash.

## First experiment recommendation

Start with a small deterministic local workload whose semantics are easy to quotient exactly, such as a pure transformation over fixed input. Establish the pipeline before attempting large optimizations or system-level performance claims.

## Safety boundary

Execution is limited to the authorized remote device and declared workspace. Do not request or expose credentials, tokens, unrelated files, or destructive operations.
