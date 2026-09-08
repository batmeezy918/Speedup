# Remote Commander ↔ Termux Protocol v1.0

## Boundary

PCSS assumes an authorized remote machine exposed through the Remote Desktop Commander. That machine is the execution substrate. Termux is an execution target when the workload resides on Android/Termux.

## Required handshake

1. Confirm remote device is online.
2. Identify target workspace.
3. Verify `git` and required runtime tools.
4. Compute environment fingerprint.
5. Compute scenario/source hashes.
6. Execute in a controlled shell.
7. Capture stdout/stderr/exit status/timing.
8. Capture filesystem mutation manifest where authorized.
9. Emit certificate.
10. Return certificate and artifact paths to the orchestration layer.

## Execution command contract

The runner SHOULD expose a single entrypoint:

```text
pcss-run <scenario.json>
```

The command MUST fail closed when the scenario is malformed, required binaries are missing, or the requested workspace is outside the declared execution boundary.

## Timing separation

Record separate clocks for:

`transport_start`
`process_start`
`process_end`
`transport_end`

The scheduler MUST NOT represent remote transport latency as application execution speedup unless the scenario explicitly declares end-to-end latency as its metric.

## Artifact contract

The remote runner writes only into the declared PCSS artifact directory:

```text
runs/<run_id>/
```

and emits:

```text
scenario.json
environment.json
stdout.log
stderr.log
trace.jsonl
performance.json
mutations.json
quotient.json
reconstruction.json
invariants.json
certificate.json
derivation.json
```

## Termux-specific environment data

When executing under Termux, capture available runtime identifiers such as architecture, kernel, Termux package/runtime versions, compiler/interpreter versions, CPU information, memory availability, and relevant environment settings. Do not capture secrets.

## No implicit privilege

The protocol does not authorize privilege escalation, root-only operations, destructive filesystem operations, or access to unrelated credentials. The runner uses only permissions already granted to the remote session.

## Proof handoff

The remote execution artifact is evidence, not a proof. The evidence-to-Lean compiler consumes the certificate and generates formal obligations. Publication remains blocked until the Lean gate succeeds.
