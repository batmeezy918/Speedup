# QK-XR Quotient-Tower Formal Gap Derivation

## 0. Scope
This document freezes the next QK-XR experiment as a proof-carrying, execution-preserving quotient tower. The target is not a generic feature bucket. The target is a native silicon implementation in which selected execution-relevant invariants are derived once from a live market state and then carried through all downstream operations.

## 1. State and observable algebra
Let a market state be `x`. Let `A_exec` be the finite family of downstream execution observables used by the implementation. Define an invariant signature

`I(x) = (I_spread(x), I_imbalance(x), I_exec(x))`.

For this experiment:
- `I_spread`: best-bid/best-ask spread in integer ticks.
- `I_imbalance`: top-20 depth imbalance bucket.
- `I_exec`: execution class (`SELL` when imbalance < -0.45, otherwise `HOLD`).

The refined quotient is `pi(x) = I(x)`.

## 2. Tower descent
The tower is

`X --q1--> Q_spread --q2--> Q_spread×Q_imbalance --q3--> Q_exec`.

The implementation computes the complete invariant signature once at the boundary:

`x -> I(x)`.

Every subsequent stage consumes only `I(x)` or a refinement of it. No stage recomputes the source-state invariants.

## 3. Execution-preservation obligation
The mandatory semantic gate is

`pi(x) = pi(y) => O(x) = O(y)`

for every execution observable `O` in the selected execution family.

Because `I_exec` is part of the quotient key, the current implementation proves preservation for the modeled execution class. This is a formal statement about the declared model, not a claim about profitability or all possible market behavior.

## 4. Reconstruction obligation
For a section/reconstruction map `R`, require

`pi(R(pi(x))) = pi(x)`

and, for the execution observable,

`d_exec(R(pi(x)), x) = 0`.

This is execution-equivalence reconstruction, not full raw-market-state reconstruction.

## 5. One-time overhead obligation
Let `C_I` be the cost of deriving `I(x)` once and `C_D` the downstream cost using the derived signature. For `k` downstream operations, the quotient path is

`T_Q(k) = C_I + k*C_D`.

The direct path is

`T_B(k) = k*C_B`.

The amortized advantage condition is

`C_I + k*C_D < k*C_B`,

or

`k > C_I / (C_B-C_D)` when `C_B > C_D`.

The benchmark must report both one-time derivation cost and end-to-end amortized cost; no one-time setup cost may be hidden.

## 6. Native implementation constraint
The performance implementation uses C++ with integer/fixed-point quantities where practical. Floating-point arithmetic is retained only at the input boundary for converting captured exchange quantities. The hot path operates on compact integer state/signatures.

This is intentionally closer to silicon than the previous Python reference implementation: fixed-width data, no dynamic allocation in the timed path, no hash maps in the timed path, and explicit compiler optimization flags.

## 7. Live-data evidence class
The market source is Coinbase BTC-USD Level-2 REST, captured with fresh network fetches (`maxAge=0`) at the listed timestamps. The Android/Termux device itself returned HTTP 403 for direct access, so the live snapshots are captured through the connected web acquisition path and then transferred unchanged to the device as an immutable evidence input. This is live snapshot evidence, not a continuous exchange WebSocket feed.

## 8. Gap ledger
| Gate | Obligation | Status |
|---|---|---|
| I | input integrity and source capture | PASS for captured snapshots |
| R | deterministic replay of captured snapshots | REQUIRED |
| Q | quotient equality preserves declared execution class | PASS in model/tests |
| Q^-1 | representative reconstruction returns same quotient | PASS in Lean/model |
| Ω | all selected invariants descend without recomputation | IMPLEMENTED IN NATIVE DESIGN; Lean binding REQUIRED |
| X | native baseline vs one-time quotient timing | THIS RUN |
| L | Lean proof of tower/preservation/reconstruction | REQUIRED FRESH BUILD |
| H | hardware attribution beyond software timing | OPEN |
| M | continuous live-stream validity | OPEN; REST snapshots only |
| P | profitability/execution economics | OPEN |

## 9. Promotion rule
No speedup is promoted from this experiment unless:
1. decision equivalence is exact for the captured workload;
2. quotient/reconstruction checks pass;
3. one-time derivation overhead is included;
4. native timings are measured on the same input and critical path;
5. raw timing samples are retained;
6. the Lean obligations compile without unresolved goals;
7. hardware causality is not inferred merely from software timing.

The experiment therefore separates **semantic preservation**, **compression**, and **native acceleration** instead of conflating them.


## 10. V2 cache-compression correction

The first native run measured reuse of a pre-derived signature but still iterated over every observed state in the downstream loop. That isolated the invariant-recomputation saving but did not measure cross-event quotient-class reuse.

V2 corrects this by making the quotient cache explicit:

1. derive the selected invariant signature once for each captured live state;
2. validate exact decision equivalence;
3. construct a one-time unique-signature index;
4. execute the downstream workload once per unique quotient class;
5. include derivation, validation, and cache construction in the amortized quotient cost.

For the fresh live replay used in V2:

50 live sequence changes -> 26 unique execution-preserving signatures

so the observed quotient compression is

50 / 26 = 1.92307692308x.

The native benchmark measured:

- baseline median: 66.204948 ms;
- unique-class quotient downstream median: 19.051822 ms;
- one-time derivation: 0.010000 ms;
- one-time semantic validation: 0.001458 ms;
- one-time cache construction: 0.006094 ms;
- total amortized quotient: 19.069374 ms;
- end-to-end native replay ratio: 3.47179451198x;
- exact decision equivalence: true.

This V2 result is stronger than the prior run because the quotient path now actually exploits observed class reuse. It remains a finite native replay over 50 fresh Level-2 sequence changes, not a claim of continuous WebSocket operation, profitability, or silicon-causal acceleration.

The next scaling gate should increase the captured sequence-change count substantially while retaining the same invariant definition and exact semantic gate.
