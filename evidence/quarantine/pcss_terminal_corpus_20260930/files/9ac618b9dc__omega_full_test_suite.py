#!/usr/bin/env python3

import numpy as np
import json
import time

# =========================
# CONFIGURATION SPACE
# =========================

d = 64
K = 800

etas = [0.001, 0.005, 0.01, 0.02]
sigmas = [0.0, 0.001, 0.005]
ranks = [2, 4, 8, 16, 32, 48, 64]

np.random.seed(42)

# =========================
# SYSTEM GENERATION
# =========================

def generate_hessian(d):
    A = np.random.randn(d, d)
    H = A.T @ A
    H = H / np.max(np.linalg.eigvalsh(H))
    return H

def precondition(H, g):
    return np.linalg.solve(H + 1e-3*np.eye(len(H)), g)

def omega_project(U, x):
    return U @ (U.T @ x)

# =========================
# SIMULATION CORE
# =========================

def run_trial(H, eta, sigma, r):

    U, _ = np.linalg.qr(np.random.randn(d, r))

    x = np.random.randn(d)
    x_star = np.zeros(d)

    losses = []

    for _ in range(K):

        grad = H @ x
        xi = precondition(H, grad)

        noise = sigma * np.random.randn(d)

        x = x - eta * xi + noise
        x = omega_project(U, x)

        loss = np.linalg.norm(x - x_star) ** 2
        losses.append(loss)

    # spectral proxy
    ratios = np.diff(losses) / (np.array(losses[:-1]) + 1e-12)

    rho_est = np.mean(ratios[-100:]) if len(ratios) > 100 else float("nan")

    return loss, rho_est

# =========================
# CLASSIFIER
# =========================

def classify(rho):

    if np.isnan(rho):
        return "UNKNOWN"
    if rho < 1.0:
        return "STABLE"
    elif rho < 1.05:
        return "CRITICAL"
    return "DIVERGENT"

# =========================
# MAIN SWEEP
# =========================

def main():

    H = generate_hessian(d)

    results = []

    print("\nΩ–Ξ–Δ FULL STABILITY ATLAS SCAN\n")

    for eta in etas:
        for sigma in sigmas:
            for r in ranks:

                loss, rho = run_trial(H, eta, sigma, r)
                state = classify(rho)

                entry = {
                    "eta": eta,
                    "sigma": sigma,
                    "rank": r,
                    "final_loss": float(loss),
                    "rho": float(rho) if not np.isnan(rho) else None,
                    "state": state
                }

                results.append(entry)

                print(
                    f"η={eta:<5} σ={sigma:<6} r={r:<3} "
                    f"ρ={rho:.4f} => {state}"
                )

    # save atlas
    with open("omega_stability_atlas.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n✔ ATLAS SAVED: omega_stability_atlas.json")
    print("✔ SYSTEM SCAN COMPLETE")

if __name__ == "__main__":
    main()

