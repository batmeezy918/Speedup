# COCI Governor — OpenCode Invocation Skill

## Trigger

Invoke this skill when the task involves Speedup repository activity, proof/build activity, benchmark execution, evidence artifacts, telemetry, operator composition, or repository-state witnessing.

## Required behavior

1. Read `governor/COCI_GOVERNOR.md` and `skills/coci-governor/SKILL.md`.
2. Treat COCI as an observational constitutional witness, not as a theorem prover or claim authority.
3. Before/after substantial repository work, invoke:

```bash
python3 governor/coci_governor.py --root . --ledger governor/ledger/coci.jsonl
```

4. Never use COCI observation as proof of correctness.
5. Never let COCI overwrite source or historical witness records.
6. Preserve the distinction among observation, measurement, derivation, formal proof, and claim.
7. If a result is contradictory, incomplete, or outside declared scope, record it as an observation/gap rather than promoting it.

## Current experiment isolation

While the existing proof-repair experiment is running, COCI must remain observational. It must not instruct the proof agent which mathematical conclusion to reach, modify its proof obligations, or alter the build configuration merely to obtain a desired status.

## Future extension point

When the separate Telemetry Mapper and Thermal Governor are introduced, COCI remains the constitutional witness layer that records their activity and evidence transitions. Those components require their own explicit interfaces and gates.
