# Gap taxonomy

A gap is an unresolved obligation that bounds a claim. Gaps are how the system
says "here is exactly what I do not know" instead of rounding up.

## Non-negotiables

1. **A gap is never deleted.** Closure creates a new evidence event and a new
   status; the historical gap and the failure that produced it stay in the
   ledger. `RECURSIVE_SPEEDUP_CONSTITUTION.md` section 7.
2. **A gap with no observable evidence is itself a `provenance` gap.**
3. **A closure criterion must be falsifiable.** "More work", "improve
   performance", "add tests" are not criteria. "Run `lean4/…` and record exit 0"
   is.
4. **A gap class is not a severity.** Several classes block promotion; one
   (`attribution`) usually just bounds the claim. The `claim_impact` field
   carries severity, the `gap_class` field carries what kind of unknown it is.

## The eleven mandatory classes

Plus `derivation`, added because SKILL.md's operator model requires an
unresolved operator specification to be recordable. All twelve are in
`GAP_CLASSES` and enforced by the `gap-record.schema.json` enum.

| Class | The unknown | Typical closure criterion | Usual claim impact |
|---|---|---|---|
| `dependency` | an unresolved or assumed dependency the result relies on | the dependency resolves, or the claim is withdrawn | blocks promotion |
| `equivalence_correctness` | candidate ≠ baseline under the declared quotient `Q` | forward equivalence and reverse reconstruction both pass at declared tolerance | blocks promotion |
| `measurement` | the timing, sample count, scope, or environment is not trustworthy | ≥ 5 interleaved samples per arm, matched scope, recorded environment | blocks promotion |
| `attribution` | no account of which component saved what work | `SavedWork_i` / `Overlap_ij` / `NewOverhead_i` recorded | qualifies claim |
| `scaling` | a single-size result standing in for a scaling claim | ≥ 2 declared sizes with aligned ratios | bounds scope |
| `hardware_mechanism` | an effect with no mechanism-specific evidence | an ablation, counterfactual, hardware counter, trace, or model fit | qualifies claim |
| `composition` | the composition was not re-run as one implementation | a fresh composed run with its own gates | blocks promotion |
| `formal_proof` | no theorem target, no command, or no successful kernel check | target + command + exit 0 + `kernel_checked` | bounds strength |
| `vacuity` | a validation batch that could not have failed | ≥ 1 substantive check with non-trivial parameters | blocks promotion |
| `provenance` | the result cannot be re-derived from what was recorded | full command, cwd, environment, versions, artifact hashes | blocks promotion |
| `reproducibility` | two runs disagree, or the result depends on undeclared state | a recorded contradiction is resolved and a second run agrees | blocks promotion |
| `derivation` | a named operator has no definition in this project | a resolvable `source_ref`, or the operator is withdrawn from the claim | blocks formal/implementation claims |

## Legacy vocabulary

The repository's existing taxonomy is preserved verbatim on import rather than
silently renamed. `GAP_CLASS_ALIASES` maps it into the canonical classes, and
the original string is kept in `legacy_alias`.

| Existing repository term | Canonical class |
|---|---|
| `DEPENDENCY_GAP` | `dependency` |
| `EQUIVALENCE_GAP` | `equivalence_correctness` |
| `RECONSTRUCTION_GAP` | `equivalence_correctness` |
| `OBSERVABLE_COMPLETENESS_GAP` | `equivalence_correctness` |
| `MEASUREMENT_GAP` | `measurement` |
| `ATTRIBUTION_GAP` | `attribution` |
| `SCALING_GAP` | `scaling` |
| `HARDWARE_MECHANISM_GAP` | `hardware_mechanism` |
| `COMPOSITION_GAP` | `composition` |
| `FORMAL_GAP` | `formal_proof` |
| `NEGATIVE`, `FAILED` | `measurement` (and a `regressed` status on the primitive) |

`NEGATIVE` and `FAILED` are statuses in this skill's model, not gap classes.
The mapping preserves the existing vocabulary for anyone reading the old
records.

## Implication chains

These are the claims a successful exit code does **not** license.

```
exit code 0                    does NOT imply correctness
correctness pass               does NOT imply a speedup
speedup on one size            does NOT imply scaling
benchmark result               does NOT imply a hardware mechanism
component VERIFIED             does NOT imply composition VERIFIED
reproduced on one machine      does NOT imply general reproducibility
a Lean proof                    does NOT imply the benchmark measures the theorem's object
```

Each arrow is a gap class you open when you cross it without evidence:
`equivalence_correctness`, `measurement`, `scaling`,
`hardware_mechanism`, `composition`, `reproducibility`, `formal_proof`.

## Record shape

```json
{
  "gap_id": "G-KERNEL-004",
  "gap_class": "hardware_mechanism",
  "primitive_id": "P-AGD-BLOCK-PI",
  "status": "open",
  "opened_at": "2026-10-08T11:04:22Z",
  "claim_impact": "qualifies_claim",
  "observable_evidence": [
    {"ref": "runs/2026-10-08/trace.json",
     "description": "eta = 0.61 against the sequential-sum model; no ablation isolating the cause"}
  ],
  "closure_criterion": "record an ablation with the block partition disabled, or withdraw the mechanism claim",
  "owner": "speedup-protocol",
  "responsible_action": "run the block-partition ablation under the declared protocol"
}
```

Required by the schema: `gap_id`, `gap_class`, `primitive_id`, `status`,
`opened_at`, `claim_impact`, at least one `observable_evidence` entry,
`closure_criterion`, `owner`, `responsible_action`.

`status` is one of `open`, `closed`, `quarantined`, `accepted_risk`,
`superseded`.

- **`closed`** requires `closed_by_evidence` naming the artifact that closed it.
  `L-GAP-2` rejects a closure without one. Closing is an evidentiary event, not
  an edit.
- **`accepted_risk`** is an admission, not a closure. It leaves the gap in
  `open_gaps` and does not raise claim strength.
- **`superseded`** points at the gap that replaced it, with
  `supersedes_gap_id`.

## Interaction with claim strength

A gap with `claim_impact: "blocks_promotion"` caps its primitive's claim at
`CANDIDATE` while it is `open` or `quarantined` (`L-GAP-3`). It does not force
`CANDIDATE` — it forbids anything stronger, so the record may legitimately say
`NONE`.

`qualifies_claim` and `bounds_scope` do not cap the strength; they require the
claim's `scope` string to name the bound. A performance claim at `STRONG_LOCAL`
with an open `attribution` gap must read like:

> "STRONG_LOCAL performance for workload W under protocol P; the attribution
> of this gain between the component and the baseline is not established."

not like an unqualified speedup number.

## Synthetic gaps

Validator fixtures carry `"synthetic": true`. They are structurally valid and
they are not evidence about anything real. The ledger validator emits
`L-SYN-1` when every record in a ledger is synthetic, so a fixture run can
never be mistaken for a result.