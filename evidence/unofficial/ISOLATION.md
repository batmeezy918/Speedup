# Isolated unofficial optimizer runs

These are **not** official COCO until rebound to `cocoex.Suite("bbob")`.

| id | source | defect |
|---|---|---|
| S6 coco-equivalent 20260515 | benchmarks/optimizer_evolution/s6 | equivalent script, not cocoex observer |
| S7 coco-equivalent 20260515 | benchmarks/optimizer_evolution/s7 | same |
| S8 covariance 20260515 | benchmarks/optimizer_evolution/s8 | same |
| SNAP core/plus/pp/pure/real/SPME | src/optimizers, archive/old_versions | no official suite |
| snap_vs_cma_* shells | archive/old_versions | unofficial metric |
| vault canonical decider 1.021 wall | evidence-vault | L2/L3 blocked; not BBOB |
| iqvf-coco | batmeezy918/iqvf-coco | not validated against cocoex 2.8.2 |

Normalization rule: wrap the optimizer as

```
suite = cocoex.Suite("bbob", "", filter)
observer = cocoex.Observer("bbob", "result_folder: NAME")
for problem in suite:
    problem.observe_with(observer)
    run_optimizer(problem, budget, seed)
```

Until that loop exists, claim_status stays QUARANTINED.
