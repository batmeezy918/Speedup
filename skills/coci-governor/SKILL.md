# COCI Governor Skill

**Name:** COCI — Constitutional Citizen / Constitutional Witness Governor  
**Role:** invoked governor + witness architecture  
**Status:** operational v0.1

## Invocation

```bash
python3 governor/coci_governor.py --root . --ledger governor/ledger/coci.jsonl
```

Continuous observation:

```bash
python3 governor/coci_governor.py --root . --ledger governor/ledger/coci.jsonl --watch 2
```

## Mission

COCI is an epistemic and operational governor. It observes authorized activity, classifies activity into constitutional categories, creates deterministic operator-style records, preserves provenance, and emits append-only witness events.

COCI does **not** silently promote observations to theorems, speedup claims, hardware claims, or scientific novelty claims.

## Duties

1. Observe only explicitly authorized roots.
2. Record activity without changing the observed artifact.
3. Classify activity as `proof`, `implementation`, `benchmark`, `telemetry`, `evidence`, `configuration`, `documentation`, or `unknown`.
4. Hash observed files and record size/mtime metadata.
5. Associate events with an operator identifier derived from category + event kind + path class.
6. Preserve event chronology and parent event identifiers.
7. Maintain the invariant `claim_strength <= evidence_strength`.
8. Quarantine ambiguous or contradictory evidence rather than upgrading it.
9. Emit machine-readable JSONL suitable for later ingestion by the Speedup recursive ledger.
10. Remain substrate-neutral: CPU, QPU, simulator, protocol, and other runtimes are observations unless a separate governed instantiation declares their scope.

## Witness semantics

A COCI witness event states what was observed and how it was classified. It is not itself a proof of the observed system's correctness.

Minimum transition:

`activity -> observation -> classification -> operator record -> immutable/hash-linked witness event`

Future governed layers may extend this to:

`witness -> admissibility -> reconstruction -> evidence -> proof obligation`.

## Non-authority rules

COCI cannot manufacture telemetry, infer unavailable hardware fields, change theorem status, convert a benchmark into a theorem, multiply isolated speedup ratios, declare universal speedup or optimality, claim physical hardware modification from user-space observation, or overwrite historical witness events.

## Scope

The v0.1 governor is intentionally separated from the proof repair agent. Its purpose is to observe and record, not steer the current Lean inference experiment. Future telemetry, thermal, and instantiation governors should be separate layers with explicit interfaces.
