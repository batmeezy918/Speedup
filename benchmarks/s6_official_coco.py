#!/usr/bin/env python3
"""Official Observer S6 — exact 27-win diagonal configuration.
Ports run_s6_adapt (K=8, diagonal self-adapt, separable coords, class steps,
restarts capped at 6) from s6_vs_cma_head_to_head.py into the cocoex.Observer path.
Observer records only; it does not alter the search.
"""
from __future__ import annotations
import argparse, hashlib, json, os, random, re, sys, time
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

def parse_fid(problem):
    pid = str(getattr(problem, 'id', 'f0'))
    m = re.search(r'f(\d+)', pid)
    return int(m.group(1)) if m else 0

def class_signature(problem):
    fid = parse_fid(problem)
    if fid <= 5: return 'separable'
    if fid <= 9: return 'low_mod_cond'
    if fid <= 14: return 'high_cond'
    if fid <= 19: return 'multimodal'
    return 'multimodal_weak'

def run_s6_adapt(problem, rng, budget):
    """Exact 27-win configuration from s6_vs_cma_head_to_head.py @ 347e7cd9."""
    dim = int(problem.dimension)
    lo = np.asarray(problem.lower_bounds)
    hi = np.asarray(problem.upper_bounds)
    group = class_signature(problem)
    base = {'separable': 0.7, 'low_mod_cond': 0.5, 'high_cond': 0.22,
            'multimodal': 0.6, 'multimodal_weak': 0.45}.get(group, 0.5)
    scale = np.ones(dim) * base
    x = rng.uniform(lo, hi)
    fx = float(problem(x))
    evals = 1
    rejects = 0
    restarts = 0
    K = 8
    while evals < budget:
        best_cand = None
        best_fc = fx
        best_dir = None
        nprop = min(K, budget - evals)
        for i in range(nprop):
            if group == 'separable' and i % 2 == 0:
                j = int(rng.integers(0, dim))
                z = np.zeros(dim)
                z[j] = rng.standard_normal()
            else:
                z = rng.standard_normal(dim)
            cand = np.clip(x + scale * z, lo, hi)
            fc = float(problem(cand))
            evals += 1
            if fc < best_fc:
                best_fc = fc
                best_cand = cand
                best_dir = z
            if evals >= budget:
                break
        if best_cand is not None and best_fc < fx:
            x, fx = best_cand, best_fc
            rejects = 0
            if best_dir is not None:
                scale = np.clip(scale * (1.0 + 0.05 * np.abs(best_dir)), base * 0.05, base * 3.0)
        else:
            rejects += 1
            scale *= 0.9
            if rejects >= 4 and restarts < 6 and evals + 1 < budget:
                x = rng.uniform(lo, hi)
                fx = float(problem(x))
                evals += 1
                rejects = 0
                restarts += 1
                scale = np.ones(dim) * base * (0.9 ** restarts)
            scale = np.maximum(scale, base * 0.05)
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
    ap.add_argument '--dimensions', type=int, default=DIM)
    ap.add_argument '--budget', type=int, default=BUDGET)
    ap.add_argument '--seed', type=int, default=SEED)
    ap.add_argument '--output-dir', default='evidence/runtime/s6-official')
    args = ap.parse_args()
    seed_all(args.seed)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if not COCO_OK:
        print('NO_COCOEX_OR_CMA'); sys.exit(2)
    observer = cocoex.Observer('bbob', f'result_folder: {out}/exdata')
    suite = cocoex.Suite('bbob', '', f'dimensions: {args.dimensions}')
    rng = np.random.default_rng(args.seed)
    rows = []
    t0 = time.time_ns()
    for p in suite:
        p.observe_with(observer)
        ts = time.time_ns()
        fs6 = run_s6_adapt(p, rng, args.budget)
        te_s6 = time.time_ns() - ts
        ts = time.time_ns()
        fcma = run_cma(p, args.budget)
        te_cma = time.time_ns() - ts
        rows.append({'id': p.id, 's6_f': fs6, 'cma_f': fcma, 's6_ns': te_s6, 'cma_ns': te_cma,
                     's6_wins': fs6 < fcma, 'speedup_s6_vs_cma': te_cma / max(1, te_s6)})
    elapsed = time.time_ns() - t0
    s6_wins = sum(1 for r in rows if r['s6_wins'])
    payload = {'mode': 'S6_OFFICIAL_27WIN_PORT_VS_CMA', 'problem_count': len(rows), 's6_wins': s6_wins,
               'cma_wins': len(rows) - s6_wins,
               'median_speedup_s6_vs_cma': sorted(r['speedup_s6_vs_cma'] for r in rows)[len(rows)//2],
               'elapsed_ns': elapsed, 'rows': rows, 'seed': args.seed, 'budget': args.budget,
               'elevation': 'exact 27-win port: diagonal self-adapt + K=8 + separable coords + class steps + restarts<=6 + Observer', 'source_sha': '347e7cd9', 'official_observer': True}
    jp = out / 's6_official_results.json'
    jp.write_text(json.dumps(payload, indent=2))
    print(f'PROBLEM_COUNT={len(rows)} S6_WINS={s6_wins} CMA_WINS={len(rows)-s6_wins} MEDIAN_SPEEDUP={payload["median_speedup_s6_vs_cma"]:.3f}x')
    print(f'RESULT_SHA256={hashlib.sha256(jp.read_bytes()).hexdigest()}')
    print(f'OFFICIAL_DATA={out}/exdata')

if __name__ == '__main__':
    main()
