# SIM2XR PCSS Sandbox Closure — 2026-09-12

## Verdict

**CLOSED_WITH_GAPS / PCSS NOT PUBLISHABLE / VERIFIED SPEEDUP PRIMITIVE NOT ESTABLISHED.**

This closure records an independent sandbox validation of the supplied SIM2XR campaign archives. It does not promote empirical benchmark values to theorem status.

### Evidence rule

`CLAIM_STRENGTH <= EVIDENCE_STRENGTH`

The sandbox validator independently recomputes numerical identities where the supplied artifacts contain sufficient data, validates archive manifests against their payloads, and checks the webapp operator-chain implementation statically. It does **not** infer unavailable native reruns, hardware attribution, full reverse reconstruction, or Lean closure.

## Validated campaign layers

### TEST1 — definitive scaling

- 210 `scaling_raw.csv` records; manifest also declares 210.
- Recomputed every stored `speedup` as `dense_s / reduced_s`.
- Maximum absolute recomputation discrepancy: `0.0`.
- Maximum measured speedup: `139.40863003017623x`.
- Maximum relative error: `4.8096324702166476e-15`.
- Wall-clock measurements stop at `d=4096`; larger-d values are not treated as measured timings.
- **Classification: internally consistent empirical scaling evidence.**

### FULL TEST SUITE

- 10 declared test families.
- 35 aggregate result rows.
- Manifest/result structure validated.
- Ω antisymmetry error: `0.0`.
- QFI noncommuting difference: `1.1918838432789958`.
- Amplitude-damping control: `span(Z)` closure error `0.9441494461795135`; expanded `span(Z,Y)` closure error `0.0`.
- Physical trace error: `6.661338147750939e-16`.
- Physical hermiticity error: `0.0`.
- Unitary invariance error: `5.995204332975845e-15`.
- SIM2X definition error: `0`.
- **Classification: internally consistent numerical/falsification evidence.**

### TEST3 — definitive comparative/falsification suite

- 176 records.
- 6 declared tests.
- 25 speedup observations identified from metric=`speedup` rows.
- Maximum measured speedup: `98.96895754923221x`.
- Maximum relative error: `3.241182505409006e-15`.
- Control `span(Z)` closure error: `0.9441494461795135`.
- Control `span(Z,Y)` closure error: `0.0`.
- **Classification: internally consistent comparative/falsification evidence.**

### QSIM definitive campaign

Payload structure validated:

- regimes: 28 rows
- advantage ledger: 20 rows
- control closure: 4 rows
- QFI/Ξ: 2 rows
- open systems: 20 rows

The supplied QSIM artifacts distinguish retained-space/compression measurements from advantage gates and retain explicit negative cases. No universal quantum-advantage or hardware claim is promoted.

### AGD/SIM2XR webapp

The self-contained HTML implementation contains the declared operator chain:

`P -> Π -> C -> Π -> R`

and explicit implementations of `P`, `Π`, `C`, `R`, `Full`, `forward`, replay/hash checking, and verification gates.

The implementation is a synthetic laboratory prototype and is not treated as physical-terminal or external-conformance evidence.

## Mathematical closure

For the specified diagonal construction in the supplied proof dossier:

`A Q = Q A_r`

and therefore

`A^N Q = Q A_r^N`

for every finite `N` by induction. The selected coordinate sector is invariant, and the ideal closed-sector task reconstruction is exact.

The adversarial coupled matrix has nonzero cross-block closure (`0.3`), so rejection is mathematically justified.

**Classification: PROVED FOR THE SPECIFIED CONSTRUCTION.**

This is not a proof for arbitrary operators, arbitrary quotients, or arbitrary workloads.

## PCSS gate state

| Gate | State | Reason |
|---|---|---|
| Scenario identity | PARTIAL | Campaign manifests identify runs but are not a newly locked PCSS scenario for native rerun |
| Source/input hashes | PARTIAL | Archive hashes are recorded below; executable source identity for original campaigns is not fully supplied in the archives |
| Native rerun | OPEN | Supplied packages contain results/logs, not the complete original benchmark executables |
| Q forward | PARTIAL | Quotient/admissibility mathematics and numerical controls are present |
| Q inverse / reconstruction | PARTIAL | Closed-sector mathematical reconstruction is proved; complete campaign artifact reconstruction is not closed |
| Ω/invariants | PARTIAL | Domain-specific invariants are numerically checked; no universal Ω theorem is inferred |
| Performance X | EMPIRICAL | Measured values are platform/runtime-specific |
| Attribution | OPEN | No independent hardware-mechanism attribution closure |
| Scaling | EMPIRICAL | Measured only within declared finite dimensions |
| Lean | OPEN | No new end-to-end Lean verification was executed from these supplied packages |
| Publication predicate | FAIL | `I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L` is not fully established |
| Verified primitive | FAIL/CANDIDATE | Evidence is not sufficient for PCSS VERIFIED status |

## Important negative evidence

The webapp contains a bounded synthetic state/constraint system. Its `forward(n)` loop terminates early if `Full()` rejects a step. Therefore successful short-chain execution must not be interpreted as proof of unrestricted multi-step continuation.

This boundary is retained as regression evidence rather than hidden.

## Archive SHA-256

| Package | SHA-256 |
|---|---|
| TEST1 scaling | `79d04637dc91c8890ca8a032bc1e836f84266134f1d9f4b094c65bc35e38984c` |
| FULL suite | `191ce2e570e52ad599d91731a03d3e401f35ae2aaf2fab422075bb1ccb80a298` |
| QSIM campaign | `0df42b6c08c360ee23b90d0d00edead0d1b884a098f8f08105721775bd057be4` |
| TEST3 | `8e4955e86869dd2eff3c592e954b499cecfcdb33ab25f6e09f9572042d8a781f` |
| AGD/SIM2XR webapp | `7315b10d18c57dd4e1131b35848795c4ee32e5a1971b27bc0b460b00c3b3baba` |

## Closure artifact

`pcss_closure_result.json` is the machine-readable output of `validate_pcss.py`.

The validator is deliberately fail-closed with respect to PCSS publication: successful data-consistency checks do not set `pcss_verified_primitive=true`.

## Next closure requirement

To upgrade this candidate, supply/recover the executable benchmark sources and run them under a newly locked PCSS scenario/environment, capturing raw trace, exact quotient, reverse reconstruction, invariants, performance uncertainty, attribution, and Lean obligations. Then rerun the composed workload directly; isolated speedup ratios must not be multiplied.
