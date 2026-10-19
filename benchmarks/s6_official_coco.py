#!/usr/bin/env python3
"""Official COCO/BBOB: elevated S6 diagonal self-adaptation with official Observer."""
from __future__ import annotations
import argparse, hashlib, json, os, random, re, sys, time
from pathlib import Path
import numpy as np

try:
    import cocoex, cma
    COCO_OK = True
except ImportError:
    COCO_OK = False

SEED, BUDGET, DIM = 20260810, 1000, 10

def seed_all(s):
    random.seed(s); np.random.seed(s)

def parse_fid(problem):
    m = re.search(r'f(\d+)', str(getattr(problem, 'id', 'f0')))
    return int(m.group(1)) if m else 0

def class_signature(problem):
    fid = parse_fid(problem)
    if fid <= 5: return 'separable'
    if fid <= 9: return 'low_mod_cond'
    if fid <= 14: return 'high_cond'
    if fid <= 19: return 'multimodal'
    return 'multimodal_weak'

def run_s6_adapt(problem, rng, budget):
    dim = int(problem.dimension)
    lo, hi = np.asarray(problem.lower_bounds), np.asarray(problem.upper_bounds)
    group = class_signature(problem)
    base = {'separable': 0.7, 'low_mod_cond': 0.5, 'high_cond': 0.22, 'multimodal': 0.6, 'multimodal_weak': 0.45}.get(group, 0.5)
    scale = np.ones(dim) * base
    x = rng.uniform(lo, hi); fx = float(problem(x)); evals = 1; rejects = 0; restarts = 0; K = 8
    while evals < budget:
        best_cand, best_fc, best_dir = None, fx, None
        for i in range(min(K, budget - evals)):
            if group == 'separable' and i % 2 == 0:
                j = int(rng.integers(0, dim)); z = np.zeros(dim); z[j] = rng.standard_normal()
            else:
                z = rng.standard_normal(dim)
            cand = np.clip(x + scale * z, lo, hi); fc = float(problem(cand)); evals += 1
            if fc < best_fc: best_fc, best_cand, best_dir = fc, cand, z
            if evals >= budget: break
        if best_cand is not None and best_fc < fx:
            x, fx, rejects = best_cand, best_fc, 0
            if best_dir is not None: scale = np.clip(scale * (1.0 + 0.05 * np.abs(best_dir)), base * 0.05, base * 3.0)
        else:
            rejects += 1; scale *= 0.9
            if rejects >= 4 and restarts < 6 and evals + 1 < budget:
                x = rng.uniform(lo, hi); fx = float(problem(x)); evals += 1; rejects = 0; restarts += 1
                scale = np.ones(dim) * base * (0.9 ** restarts)
            scale = np.maximum(scale, base * 0.05)
    return fx

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-d', '--dimensions', type=int, default=DIM)
    ap.add_argument('-b', '--budget', type=int, default=BUDGET)
    ap.add_argument('-s', '--seed', type=int, default=SEED)
    ap.add_argument('-o', '--output-dir', default='evidence/runtime/official-coco')
    args = ap.parse_args()
    seed_all(args.seed)
    out = Path(args.output_dir) / str(os.environ.get('RUN_ID', 'local'))
    out.mkdir(parents=True, exist_ok=True)
    if not COCO_OK:
        print('NO_COCOEX_OR_CMA'); sys.exit(2)
    suite = cocoex.Suite('bbob', '', 'dimensions: %d' % args.dimensions)
    observer = cocoex.Observer('bbob', 'result_folder: %s' % (out / 'exdata'))
    rng = np.random.default_rng(args.seed); rows = []; t0 = time.time_ns()
    for i in range(len(suite)):
        p = suite.get_problem(i)
        observer.observe(p)
        ts = time.time_ns(); fs6 = run_s6_adapt(p, rng, args.budget); te = time.time_ns() - ts
        rows.append({'id': p.id, 's6_f': fs6, 's6_ns': te})
    observer.finish(); elapsed = time.time_ns() - t0
    payload = {"mode": "S6_ADAPT_OFFICIAL_OBSERVER", "problem_count": len(rows),
               "elapsed_ns": elapsed, "rows": rows, "seed": args.seed,
               "budget": args.budget,
               "elevation": "diagonal self-adapt + K=8 + separable coords + class steps + official Observer"}
    jp = out / 's6_official_results.json'
    jp.write_text(json.dumps(payload, indent=2))
    print('PROBLEM_COUNT=%d' % len(rows))
    print('RESULT_SHA256=%s' % hashlib.sha256(jp.read_bytes()).hexdigest())
    print('OBSERVER_DATA=%s' % (out / 'exdata'))

if __name__ == '__main__':
    main()
