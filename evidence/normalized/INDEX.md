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
