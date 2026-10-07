#!/usr/bin/env python3
# ============================================================
# EOS UNIFIED TENSOR BENCHMARK HARNESS
# RCoH + Commutator Geometry + Optimizer Flow Comparison
# ============================================================

import numpy as np
import json
import time

np.random.seed(42)

# ============================================================
# REALITY OPERATOR (grounding map)
# ============================================================
def R(x):
    # bounded "reality projection"
    return np.tanh(x)

# ============================================================
# RCoH (Reality Coherence Metric)
# ============================================================
def RCoH(x):
    return 1.0 - np.linalg.norm(x - R(x))

# ============================================================
# OBJECTIVE + GRADIENT
# ============================================================
def f(x):
    return np.sum(x**2)

def grad(x):
    return 2.0 * x

# ============================================================
# COMMUTATOR ERROR TENSOR
# C = R(O(x)) - O(R(x))
# ============================================================
def commutator(Ox, x):
    return np.linalg.norm(R(Ox) - Ox) + np.linalg.norm(Ox - R(x))

# ============================================================
# METRIC TENSOR (EOS CORE OBJECT)
# ============================================================
def metric_tensor(x, x_new):
    g = grad(x)
    grad_norm = np.linalg.norm(g)
    coh = RCoH(x)
    comm = commutator(x_new, x)
    var = np.var(x)

    G = np.array([
        [grad_norm, coh, comm],
        [coh, 1.0/(1.0 + grad_norm), coh - comm],
        [comm, coh - comm, var]
    ])
    return G

# ============================================================
# OPTIMIZERS
# ============================================================
def SGD(x, lr=0.01):
    return x - lr * grad(x)

def Adam(x, m, v, t, lr=0.01):
    b1, b2 = 0.9, 0.999

    m = b1 * m + (1 - b1) * grad(x)
    v = b2 * v + (1 - b2) * (grad(x)**2)

    m_hat = m / (1 - b1**t)
    v_hat = v / (1 - b2**t)

    return x - lr * m_hat / (np.sqrt(v_hat) + 1e-8), m, v

def CMAES(x):
    noise = np.random.normal(0, 0.1, size=x.shape)
    return x + noise

def SIM2XR(x, lr=0.01):
    projected = R(x)
    return projected - lr * grad(projected)

# ============================================================
# RUN ENGINE
# ============================================================
def run_optimizer(name, steps=60, dim=10):
    x = np.random.randn(dim)

    m = np.zeros_like(x)
    v = np.zeros_like(x)

    log = []

    for t in range(1, steps + 1):

        if name == "SGD":
            x_new = SGD(x)

        elif name == "Adam":
            x_new, m, v = Adam(x, m, v, t)

        elif name == "CMAES":
            x_new = CMAES(x)

        elif name == "SIM2XR":
            x_new = SIM2XR(x)

        else:
            raise ValueError("unknown optimizer")

        G = metric_tensor(x, x_new)

        log.append({
            "step": t,
            "optimizer": name,
            "loss": float(f(x)),
            "RCoH": float(RCoH(x)),
            "commutator": float(commutator(x_new, x)),
            "G_trace": float(np.trace(G))
        })

        x = x_new

    return log

# ============================================================
# EOS BENCHMARK SUITE
# ============================================================
def benchmark():
    optimizers = ["SGD", "Adam", "CMAES", "SIM2XR"]

    results = {}

    for opt in optimizers:
        results[opt] = run_optimizer(opt)

    summary = {}

    for opt in optimizers:
        RCoH_avg = np.mean([r["RCoH"] for r in results[opt]])
        comm_avg = np.mean([r["commutator"] for r in results[opt]])
        trace_avg = np.mean([r["G_trace"] for r in results[opt]])
        loss_avg = np.mean([r["loss"] for r in results[opt]])

        summary[opt] = {
            "RCoH_mean": RCoH_avg,
            "commutator_mean": comm_avg,
            "metric_trace_mean": trace_avg,
            "loss_mean": loss_avg
        }

    return results, summary

# ============================================================
# EXECUTION + EXPORT
# ============================================================
if __name__ == "__main__":
    t0 = time.time()

    logs, summary = benchmark()

    with open("eos_logs.json", "w") as f:
        json.dump(logs, f, indent=2)

    with open("eos_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n==============================")
    print("EOS UNIFIED TENSOR SUMMARY")
    print("==============================\n")

    for k, v in summary.items():
        print(k, v)

    print("\nRuntime:", time.time() - t0)
