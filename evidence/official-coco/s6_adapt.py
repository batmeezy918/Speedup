#!/usr/bin/env python3
"""Diagonal-adaptation S6 optimizer for official COCO/BBOB.

Contract: receives a cocoex Problem (has .dimension, .lower_bounds,
.upper_bounds, is callable). Never receives an Observer.

Diagonal adaptation: maintains a per-coordinate step-size vector sigma[d]
adapted from accepted/rejected step history. Projection (omega, xi)
preserved from the S6 quotient. On stall (sigma collapse + no improvement),
a restart re-samples x and resets sigma while counting against the same budget.

Evidence class: FORMAL_PARTIAL. No wall-clock or B(H) claims.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np


def omega(x: np.ndarray) -> float:
    return float(x[0])


def xi(x: np.ndarray) -> float:
    return float(x[2] - 2.0 * x[1] + x[0]) if x.size > 2 else 0.0


def project(x: np.ndarray, omega_ref: float, xi_ref: float) -> np.ndarray:
    y = np.array(x, dtype=float, copy=True)
    y[0] = omega_ref
    if y.size > 2:
        y[2] = 2.0 * y[1] - y[0] + xi_ref
    return y


def run_s6_adapt(
    problem: Any,
    seed: int = 20260810,
    budget: int = 1000,
    c_sigma: float = 0.3,
    sigma0: float = 0.5,
    stall_window: int = 40,
    max_restarts: int = 5,
) -> dict[str, Any]:
    """Run diagonal-adaptive S6 on one COCO problem.

    Restart rule: if no improvement for stall_window steps and mean sigma
    has collapsed below 0.01 * sigma0, re-sample x, reset sigma, and
    continue (up to max_restarts). Each restart consumes the remaining budget.
    """
    if not hasattr(problem, "dimension"):
        raise TypeError(
            f"run_s6_adapt received {type(problem).__name__}, "
            "which has no .dimension — Observer was passed, not Problem."
        )

    dim = int(problem.dimension)
    lo = np.asarray(problem.lower_bounds, dtype=float)
    hi = np.asarray(problem.upper_bounds, dtype=float)
    rng = np.random.default_rng(seed)

    sigma = np.full(dim, sigma0, dtype=float)

    t0_wall = time.perf_counter_ns()
    t0_cpu = time.process_time_ns()

    x = rng.uniform(lo, hi)
    fx = float(problem(x))
    best_f = fx
    evaluations = 1
    accepted_count = 1
    restarts = 0
    steps_since_improve = 0

    omega_ref = omega(x)
    xi_ref = xi(x)

    trace = [{
        "eval_idx": evaluations,
        "f": fx,
        "best_f": best_f,
        "omega": omega_ref,
        "xi": xi_ref,
        "accepted": True,
        "op_type": "initial",
        "sigma_mean": float(sigma.mean()),
        "restarts": restarts,
    }]

    while evaluations < budget:
        z = rng.standard_normal(dim)
        step = sigma * z
        candidate = project(np.clip(x + step, lo, hi), omega_ref, xi_ref)

        if evaluations >= budget:
            break

        t_eval = time.perf_counter_ns()
        fc = float(problem(candidate))
        t_eval = time.perf_counter_ns() - t_eval
        evaluations += 1

        if fc < fx:
            x, fx = candidate, fc
            accepted_count += 1
            op = "accept_candidate"
            sigma = sigma * (1.0 + c_sigma * np.abs(z) / (np.linalg.norm(z) + 1e-15))
            steps_since_improve = 0
        else:
            op = "rejection_fallback"
            sigma = sigma * (1.0 - c_sigma * np.abs(z) / (np.linalg.norm(z) + 1e-15))
            steps_since_improve += 1
            if evaluations < budget:
                x = project(np.clip(0.7 * x + 0.3 * candidate, lo, hi), omega_ref, xi_ref)
                t2 = time.perf_counter_ns()
                fx = float(problem(x))
                t_eval += time.perf_counter_ns() - t2
                evaluations += 1

        sigma = np.clip(sigma, 1e-6, 5.0)
        best_f = min(best_f, fx)

        # Restart on stall
        if (
            restarts < max_restarts
            and steps_since_improve >= stall_window
            and float(sigma.mean()) < 0.01 * sigma0
            and evaluations < budget
        ):
            x = rng.uniform(lo, hi)
            fx = float(problem(x))
            evaluations += 1
            sigma = np.full(dim, sigma0, dtype=float)
            omega_ref = omega(x)
            xi_ref = xi(x)
            steps_since_improve = 0
            restarts += 1
            op = "restart"
            best_f = min(best_f, fx)

        trace.append({
            "eval_idx": evaluations,
            "f": fx,
            "best_f": best_f,
            "omega": omega(x),
            "xi": xi(x),
            "accepted": op == "accept_candidate",
            "op_type": op,
            "sigma_mean": float(sigma.mean()),
            "restarts": restarts,
        })

    t_wall = time.perf_counter_ns() - t0_wall
    t_cpu = time.process_time_ns() - t0_cpu

    return {
        "problem_id": getattr(problem, "id", "unknown"),
        "dimension": dim,
        "final_f": fx,
        "best_f": best_f,
        "evaluations": evaluations,
        "accepted_count": accepted_count,
        "acceptance_rate": accepted_count / max(evaluations, 1),
        "final_sigma_mean": float(sigma.mean()),
        "restarts": restarts,
        "omega_ref": omega_ref,
        "xi_ref": xi_ref,
        "omega_equal": bool(abs(omega(x) - omega_ref) < 1e-12),
        "xi_equal": bool(abs(xi(x) - xi_ref) < 1e-12),
        "wall_time_ns": t_wall,
        "cpu_time_ns": t_cpu,
        "trace": trace,
        "evidence_class": "FORMAL_PARTIAL",
    }
