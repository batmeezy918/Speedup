# Occurrence log — official COCO architecture

Event: 2026-09-08T19:25:00Z

## Integrity / correlation

Profile report (`tools/coco-bbo-setup/VERIFICATION_REPORT.md`) states:

`bbob f1 instance 1 dim2 f(0,0) = 80.88209408`

This event re-instantiated official `cocoex==2.8.2` Suite `bbob` and evaluated the same point:

`f(0,0) = 80.88209408`
`abs_error = 0.0`

Official numeric correlation of the architecture: **zero error**.

BBOB dim-2 suite length under cocoex 2.8.2: **360 problems** (24×15), same cardinality as dim-10.

## What was executed here

- Official package import and suite construction: yes
- Official f1/i1 correlation: yes, error 0
- S6 vs CMA-ES 4.4.4 on 6 official dim-2 problems, budget 80: yes
- Target hits: 0 / 6 for both (budget too small; documented, not hidden)
- Full dim-10 360×1000 publication run: **not** executed in this event
- SNAP/S7/S8/SPME unofficial equivalents: **not** silently accepted; matrix requires cocoex rebind

## Claim strength

`STRONG_LOCAL` for architecture + correlation only.
Not `VERIFIED` speedup. All seven PCSS gates are not true.
