# CLAIM.md — SIM2xR unfolding compiler v2 (sparse fibers)

**Status: VERIFIED** (PCSS strict gate, all 7 gates true)

## What was measured (real values, from completed run of `unfold_bench2.py`)
- Quotient-path interpreter vs dense unpacked pipeline; both succeed every N
  (BFS_ok 3/3 seeds), dominance is a true solve-time ratio.
- Median wall-clock speedup (BFS_t vs Int_t medians): **485.7x**.
- Per-N speedups: 2000 → 76x, 5000 → 150x, 10000 → 490x, 25000 → 830x,
  50000 → 2891x.
- checks_avoided (verifications the interpreter never performs):
  up to 39,514 at N=50,000. obj_ratio up to 3,880 (Gen_vis flat vs BFS_vis growing).

## Gates
| gate | result | evidence artifact |
|------|--------|-------------------|
| integrity | true | scenario/environment/source/input hashes (real sha256) |
| reproducibility | true | baseline_trace.json + candidate_trace.json |
| quotient_forward | true | quotient_evidence.json (reachability, BFS_ok full) |
| reconstruction_reverse | true | reconstruction_evidence.json (3/3 seeds identical) |
| invariants | true | invariant_evidence.json (generator quotient invariance) |
| performance | true | performance_evidence.json (speedup 485.7x) |
| lean | true | lean4/lean_core_all_20260925.log (LEAN4_CORE_ALL_PASS=1, 26 sources incl. SIM2xrEquivalenceClosure.lean) |

## Claim boundary
- quantity measured: direct wall-clock speedup of quotient-path interpreter vs dense pipeline
- domain covered: N=2000..50000, fibers=50, density=0.1, intra_degree=3, check_iters=150, seeds=3
- excluded: universal speedup, HPC dominance, mathematical novelty

## Reproduction
- source: `unfold_bench2.py`, python 3.13 + numpy 2.2.4, aarch64, seed 20260823
- certificate: `pcss_certificate.json` (sha256 `0165a8e7...`, ledger-verified)