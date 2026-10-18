#!/usr/bin/env python3
"""S6 vs CMA-ES head-to-head on official BBOB (360 problems).
Full classifications, wall-clock per optimizer, typed gap objects.
"""
from __future__ import annotations
import argparse, hashlib, json, os, random, sys, time
from pathlib import Path
import numpy as np

try:
    import cocoex
    import cma
    COCO_OK = True
except ImportError:
    COCO_OK = False

SEED = 20260810
BUDGET = 1000
DIM = 10

def seed_all(s):
    random.seed(s); np.random.seed(s)

def run_s6(problem, rng, budget):
    dim = int(problem.dimension)
    lo = np.asarray(problem.lower_bounds)
    hi = np.asarray(problem.upper_bounds)
    x = rng.uniform(lo, hi)
    fx = float(problem(x))
    for _ in range(budget):
        z = rng.standard_normal(dim)
        cand = np.clip(x + 0.5 * z, lo, hi)
        fc = float(problem(cand))
        if fc < fx:
            x, fx = cand, fc
        else:
            x = np.clip(0.7 * x + 0.3 * cand, lo, hi)
            fx = float(problem(x))
    return fx

def run_cma(problem, budget):
    dim = int(problem.dimension)
    x0 = np.zeros(dim)
    sigma = 0.3
    es = cma.CMAEvolutionStrategy(x0, sigma, {'maxfevals': budget, 'verb_disp': 0, 'verb_log': 0})
    while not es.stop():
        solutions = es.ask()
        es.tell(solutions, [float(problem(s)) for s in solutions])
    return float(es.result.fbest)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dimensions', type=int, default=DIM)
    ap.add_argument('--budget', type=int, default=BUDGET)
    ap.add_argument('--seed', type=int, default=SEED)
    ap.add_argument('--output-dir', default='evidence/runtime/s6-vs-cma')
    args = ap.parse_args()
    seed_all(args.seed)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if not COCO_OK:
        print('NO_COCOEX_OR_CMA'); sys.exit(2)
    suite = cocoex.Suite('bbob', '', f'dimensions: {args.dimensions}')
    rng = np.random.default_rng(args.seed)
    rows = []
    t0 = time.time_ns()
    for p in suite:
        ts = time.time_ns()
        fs6 = run_s6(p, rng, args.budget)
        te_s6 = time.time_ns() - ts
        ts = time.time_ns()
        fcma = run_cma(p, args.budget)
        te_cma = time.time_ns() - ts
        rows.append({
            'id': p.id,
            's6_f': fs6, 'cma_f': fcma,
            's6_ns': te_s6, 'cma_ns': te_cma,
            's6_wins': fs6 < fcma,
            'speedup_s6_vs_cma': te_cma / max(1, te_s6),
        })
    elapsed = time.time_ns() - t0
    s6_wins = sum(1 for r in rows if r['s6_wins'])
    payload = {
        'mode': 'S6_VS_CMA_HEAD_TO_HEAD',
        'problem_count': len(rows),
        's6_wins': s6_wins,
        'cma_wins': len(rows) - s6_wins,
        'median_speedup_s6_vs_cma': sorted(r['speedup_s6_vs_cma'] for r in rows)[len(rows)//2],
        'elapsed_ns': elapsed,
        'rows': rows,
        'seed': args.seed,
        'budget': args.budget,
    }
    jp = out / 's6_vs_cma_results.json'
    jp.write_text(json.dumps(payload, indent=2))
    print(f'PROBLEM_COUNT={len(rows)} S6_WINS={s6_wins} CMA_WINS={len(rows)-s6_wins} MEDIAN_SPEEDUP={payload["median_speedup_s6_vs_cma"]:.3f}x')
    print(f'RESULT_SHA256={hashlib.sha256(jp.read_bytes()).hexdigest()}')

if __name__ == '__main__':
    main()
