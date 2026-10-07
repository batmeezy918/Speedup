import hashlib
import json
import platform
import statistics
import time

import numpy as np

WARMUP = 3
RUNS = 15

sizes = [512, 2048, 4096]
threads_cfg = [("1", "6"), ("4", "4-7")]

results = {}
for N in sizes:
    FLOPS = 2.0 * N**3
    np.random.seed(0)
    A = np.random.rand(N, N).astype(np.float32)
    B = np.random.rand(N, N).astype(np.float32)
    ref_computed = False
    for tstr, aff in threads_cfg:
        import os
        os.environ["OPENBLAS_NUM_THREADS"] = tstr
        os.environ["OMP_NUM_THREADS"] = tstr
        import numpy as _np
        def once():
            t0 = time.perf_counter()
            C = A @ B
            return C, time.perf_counter() - t0
        global _C
        for _ in range(2):
            once()
        times = []
        for i in range(RUNS):
            C, dt = once()
            times.append(dt)
            if i == 0 and not ref_computed:
                ref = (A.astype(np.float64) @ B.astype(np.float64)).astype(np.float32)
                ref_err = float(_np.max(_np.abs(C - ref)))
                ref_computed = True
        times = sorted(times)
        t = statistics.median(times)
        key = f"N{N} O{tstr}t"
        results[key] = {
            "scenario_id": f"LADDER_N{N}_fp32_gemm_O{tstr}t_{aff}",
            "n": N,
            "threads": int(tstr),
            "affinity": aff,
            "median_s": t,
            "gflop_s": FLOPS / t / 1e9,
            "max_err": ref_err,
        }

blob = json.dumps(results, sort_keys=True).encode()
print(json.dumps(results, indent=2))
open("/root/perf_evidence/ladder_scan.json", "w").write(json.dumps(results, indent=2))