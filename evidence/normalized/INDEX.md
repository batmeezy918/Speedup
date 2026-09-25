# Normalized empirical runs

Timestamp: 2026-09-08T19:19:00Z

These folders re-attach PCSS proof requirements to runs whose **existence** was verified.
They are not verified publications. `claim_status` is `CANDIDATE` on every family.

| experiment_id | existence | published speedup |
|---|---|---|
| coco-deterministic-s6 | harness+contract yes; captured double-run no | none |
| coco-head-to-head-s6-vs-cma-4.4.4 | protocol yes; 360-problem capture no | none |
| vault-canonical-decider-20260531T112101Z | 10 repeats + decision JSON yes | 1.021 wall reported, **not** X-gate true |

Next: lock scenario hashes, re-execute, then `python publisher/gate.py certificate.json`.

## Chroncle (2026-09-25) — PCSS strict-gate verified publications

Run-dirs under `evidence/runs/chronicle-2026-09-25/` feed `scripts/compose_certificate.py`
and `publisher/strict_gate.py`; every gate hash is the real sha256 of its artifact file.

| run-dir id | claim | published speedup | certificate sha256 (ledger) |
|---|---|---|---|
| equivalence_faithful_gaussian | exact-invariant-sector decomposition (gaussian, d=64..1024) | 18.89x (max 459.76x) | `a0bd422e...` |
| unfold_bench2 | quotient-path compiler/interpreter (N=2000..50000) | 485.7x (max 2891x) | `0165a8e7...` |

Closure certifications without a measured wall-clock speedup (threadlock v4,
nonlinear eod v5, sic maximal-response, Lean obligation lane) are recorded as
`publish_closure` ledger entries and are **not** promoted to VERIFIED.
