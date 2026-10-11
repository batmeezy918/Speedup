# Official benchmark corpora (pinned)

These corpora are **not vendored** into this repository (the subdirectories are
gitignored: see `.gitignore` under `benchmarks/official/`). They are fetched at
benchmark time and pinned here by commit so runs are reproducible.

| corpus | upstream remote | branch | pinned HEAD | files | size |
|---|---|---|---|---|---|
| miniF2F | https://github.com/facebookresearch/miniF2F.git | main | `e4f113090ad82d64f8ce064d2f55b613a9b6bded` | 1806 | 8.6M |
| PutnamBench | https://github.com/trishullab/PutnamBench.git | main | `97b5e9458b04e3d1044e8f8afe1724ff133f5a53` | 1764 | 11M |

Recorded: 2026-10-11. Working trees materialised at the pinned commit and
verified clean (`git status --porcelain` empty).

## Reproduce

```bash
cd benchmarks/official
git clone https://github.com/facebookresearch/miniF2F.git miniF2F
git -C miniF2F checkout e4f113090ad82d64f8ce064d2f55b613a9b6bded

git clone https://github.com/trishullab/PutnamBench.git PutnamBench
git -C PutnamBench checkout 97b5e9458b04e3d1044e8f8afe1724ff133f5a53
```

## Scope note

These are the only benchmark corpora referenced by this repository. Other
computational domains in the PCSS corpus (matrix/GEMM, vector, compiler,
quantum ATD-QG, COCO BFS) are internal workloads under `workloads/`,
`scenarios/` and `evidence/`, not external clones, so there is no upstream
repository to fetch for them.
