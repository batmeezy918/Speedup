# COCI Governor — Constitutional Citizen / Constitutional Witness

## Operational position

COCI is the witness/governor layer for the Speedup system. It sits beside execution and verification rather than replacing either authority.

```text
activity
  -> observation
  -> classification
  -> operator identity
  -> witness event
  -> evidence/ledger ingestion
  -> admissibility gate
```

The governor's constitutional invariant is:

`CLAIM_STRENGTH <= EVIDENCE_STRENGTH`

The existing PCSS constitution makes evidence supremacy, deterministic scenario identity, quotient/reconstruction gates, invariant preservation, performance scope, formal separation, quarantine, and publication gates mandatory. COCI records observations in accordance with those boundaries; it does not override them.

## Witness duties

- Observe only authorized roots supplied at invocation.
- Never execute discovered content merely because it was observed.
- Never mutate observed source, theorem, benchmark, or artifact files.
- Hash observed files and preserve chronology.
- Classify activity into proof, implementation, benchmark, telemetry, evidence, configuration, documentation, or unknown.
- Emit append-only JSONL witness events with previous-event linkage.
- Represent unavailable information as unavailable rather than guessed.
- Keep observation, derivation, measurement, proof, and claim as separate evidence states.
- Preserve failed/contradictory observations for later gap analysis.

## Operator model

COCI assigns an observation operator identifier:

`COCI.<CATEGORY>.OBSERVE`

This is a provenance label, not a claim that the observed operation is mathematically correct. Future operators may add explicit admissibility predicates and proof obligations.

## Invocation

Single observation:

```bash
python3 governor/coci_governor.py --root . --ledger governor/ledger/coci.jsonl
```

Polling observation:

```bash
python3 governor/coci_governor.py --root . --ledger governor/ledger/coci.jsonl --watch 2
```

## Deliberate separation from current proof inference

COCI v0.1 is observational and must not steer, repair, or rewrite the current Lean proof experiment. This preserves the ability to observe what the proof agent independently infers.

## Future governed layers

The next layers are intentionally separate:

1. **Telemetry Mapper** — normalize runtime/silicon observations into canonical telemetry records.
2. **Thermal Governor/Regulator** — reason over available thermal signals and bounded control actions; no claim of hardware-level control without evidence.
3. **Instantiation Governor** — map verified abstract primitives into declared workload/substrate boundaries.
4. **Recursive Witness** — connect native runs, reverse reconstruction, gap analysis, and reusable primitive lineage.

These layers must preserve the existing recursive constitution and may not promote component results into composed claims automatically.
