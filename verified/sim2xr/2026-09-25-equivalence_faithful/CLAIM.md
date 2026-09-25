# CLAIM.md — SIM2xR equivalence-faithful (gaussian)

**Status: VERIFIED** (PCSS strict gate, all 7 gates true)

## What was measured (real values, transcribed from the completed run)
- 122 measured scenarios, all PASS: `A = Q*Ar*Q' + Qp*Ap*Qp'` exact invariant
  decomposition (gaussian family, spectrally separated complement), domains
  d ∈ {64,128,256,512,1024}, r ∈ {2,4,8}, 5 trials each.
- Direct wall-clock kernel speedup (median of dense vs reduced kernel step):
  **18.89x** (min 2.06x, max 459.76x).
- Per-dimension kernel speedup medians: d=64 → 5.7x, 128 → 6.3x, 256 → 19.1x,
  512 → 65.3x, 1024 → 279.9x.
- Closure error ≤ 1.338e-12, task error ≤ 1.493e-12, unfold error ≤ 1.367e-15,
  quotient error ≤ 8.113e-14 — all ≤ 1e-10 tolerance.

## Gates
| gate | result | evidence artifact |
|------|--------|-------------------|
| integrity | true | scenario/environment/source/input hashes (real sha256) |
| reproducibility | true | baseline_trace.json + candidate_trace.json |
| quotient_forward | true | quotient_evidence.json (forward_residual 1.338e-12) |
| reconstruction_reverse | true | reconstruction_evidence.json (max error 1.493e-12) |
| invariants | true | invariant_evidence.json (spectral sector separation) |
| performance | true | performance_evidence.json (speedup 18.89x) |
| lean | true | lean4/lean_core_all_20260925.log (LEAN4_CORE_ALL_PASS=1, 26 sources incl. SIM2xrEquivalenceClosure.lean) |

## Claim boundary
- quantity measured: direct wall-clock speedup of the exact-invariant-sector kernel step
- domain covered: d=64..1024, r=2/4/8, gaussian, 122 measured scenarios
- excluded: universal speedup, HPC dominance, operation-count equality, asymptotic complexity, mathematical novelty

## Reproduction
- source: `sim2xr_equivalence_faithful.jl`, julia 1.11.1, aarch64, seed 20260823
- full CSV: `sim2xr_equivalence_faithful.csv` (122 rows, all PASS)
- certificate: `pcss_certificate.json` (sha256 `a0bd422e...`, ledger-verified)