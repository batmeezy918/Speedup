# Official COCO/BBOB architecture (profile-locked)

Source of truth on profile:
- `chronofold/tools/coco-bbo-setup/VERIFICATION_REPORT.md` (2026-08-26)
- `chronofold/tools/coco-bbo-setup/requirements.txt`
- `chronofold/benchmarks/coco_deterministic`
- `chronofold/benchmarks/coco_head_to_head`

Official stack for every Speedup COCO claim:

| piece | version | role |
|---|---|---|
| coco-experiment / cocoex | 2.8.2 | official BBOB suite + observer |
| cma | 4.4.4 | official reference optimizer |
| numpy | 2.2.6 (det harness) or 2.5.2 (setup report) | numeric |
| seed | 20260810 | S6/H2H contract |
| suite | `cocoex.Suite("bbob", "", "dimensions: D")` | official problems only |
| metric | function evaluations to `final_target_hit` | official COCO runtime |
| secondary | final best f at fixed budget | allowed, not substituted |

Not official:
- homemade sphere/RSA stand-ins labeled as COCO
- SNAP/S7/S8 `*_coco_equivalent.py` that do not import cocoex
- vault wall-clock ratios across unequal L2 tasks
- any 18x filename factor

Publication size for dim-D BBOB: 24 functions × 15 instances = 360 problems.
Dim-2 smoke is architecture/correlation evidence only.
