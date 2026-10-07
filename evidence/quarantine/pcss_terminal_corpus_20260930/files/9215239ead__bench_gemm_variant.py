import hashlib
import json
import platform
import statistics
import sys
import time

import numpy as np

N = 1024
WARMUP = 5
RUNS = 25
FLOPS = 2.0 * N**3

threads = int(sys.argv[1])
affinity = sys.argv[2] if len(sys.argv) > 2 else ""

np.random.seed(0)
A = np.random.rand(N, N).astype(np.float32)
B = np.random.rand(N, N).astype(np.float32)


def run_once():
    t0 = time.perf_counter()
    C = A @ B
    dt = time.perf_counter() - t0
    return C, dt


for _ in range(WARMUP):
    run_once()

times = []
for i in range(RUNS):
    C, dt = run_once()
    times.append(dt)
    if i == 0:
        ref = (A.astype(np.float64) @ B.astype(np.float64)).astype(np.float32)
        max_err = float(np.max(np.abs(C - ref)))

times = sorted(times)
t_med = statistics.median(times)
t_min = times[0]
t_iqr = times[RUNS // 4 * 3] - times[RUNS // 4]

entry = {
    "scenario_id": f"P1_N1024_fp32_gemm_O{threads}t_{affinity}",
    "primitive": {"id": "P1", "operator": f"openblas_threads={threads}", "affinity": affinity},
    "workload": {"op": "gemm", "n": N, "flops_per_matmul": FLOPS, "dtype": "float32"},
    "hardware": {"cpu": platform.machine(), "affinity": affinity},
    "measurement": {
        "warmup": WARMUP,
        "runs": RUNS,
        "median_s": t_med,
        "min_s": t_min,
        "iqr_s": t_iqr,
        "median_gflop_s": FLOPS / t_med / 1e9,
        "min_gflop_s": FLOPS / t_min / 1e9,
        "times_s": times,
    },
    "correctness": {
        "contract": "max_abs_err_vs_float64_ref",
        "max_abs_err": max_err,
        "all_finite": bool(np.isfinite(C).all()),
    },
    "raw": {"seed": 0},
}

blob = json.dumps(entry, sort_keys=True).encode()
entry["artifact_sha256"] = hashlib.sha256(blob).hexdigest()

print(json.dumps(entry, indent=2, sort_keys=True))
with open(f"/root/perf_evidence/p1_run_o{threads}t_{affinity}.json", "w") as f:
    json.dump(entry, f, indent=2, sort_keys=True)