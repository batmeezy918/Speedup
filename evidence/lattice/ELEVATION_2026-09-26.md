# Elevation ledger — 2026-09-26

Action taken by the architect pack. No claim was moved to VERIFIED.

## Elevated (class now matches the certificate)

| id | old public posture | new class |
|---|---|---|
| sim2xr-invariant-sector-20260908 | stored under `verified/` | STRONG_LOCAL |
| qrt-ej-1.0-20260910 | template instance | STRONG_LOCAL |
| agd-real-speedup-gauntlet | historical narrative | STRONG_LOCAL |
| omega-gf2-pos-interval-xor-n500 | historical narrative | STRONG_LOCAL |
| cocoex-bbob-dim10-budget1000-20260910 | run existed, under-cited as a result | NEGATIVE |
| graph500 official + chronophole | "digital twin of BFS" | MEASURED_BASELINE |
| kernel-agd-oic-pcss | "103 theorems" | FORMAL_PARTIAL |

## Demoted

| id | old posture | new class |
|---|---|---|
| ledger 254.30× / 1024× / 80.9× / 209.23× | speedup ledger | THEORETICAL_OR_SIMULATED |
| S6/S7/S8 20260515 | BENCHMARK_INDEX "complete" | QUARANTINED (already PCSS law) |

## Unchanged because evidence is incomplete

| id | class |
|---|---|
| vault-canonical-decider 1.021× | CANDIDATE |
| snap-24-case | CANDIDATE |
| any packet with lean: false | not VERIFIED |

## Folder debt left in place

`verified/sim2xr/2026-09-08/` is not moved in this PR (history
preservation). A `CLASS.md` notice is added in-tree so the directory
name cannot be cited as publication.

## Next elevation that would be legal

SIM2XR or QRT becomes VERIFIED only after:

1. scenario/source/input/environment hashes frozen
2. Lean module names those hashes and proves the *identity obligation*
3. `publisher/gate.py` returns publishable
4. REGISTRY class flips from STRONG_LOCAL to VERIFIED in the same commit
   as the gate receipt

Until then verified_count remains 0.
