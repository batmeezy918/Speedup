#!/usr/bin/env python3

import numpy as np

# =========================
# DETERMINISTIC SEEDING
# =========================
np.random.seed(42)

# =========================
# SYSTEM PARAMETERS
# =========================
d = 64
K = 1500

etas = [0.001, 0.005, 0.01]
sigmas = [0.0, 0.001, 0.005]
ranks = [2, 4, 8, 16, 32, 48, 64]

# =========================
# FIXED HESSIAN (STRUCTURE)
# =========================
def make_hessian(d):
    A = np.random.randn(d, d)
    H = A.T @ A
    H /= np.max(np.linalg.eigvalsh(H))
    return H

# =========================
# NATURAL GRADIENT (Ξ)
# =========================
def xi(H, g):
    return np.linalg.solve(H + 1e-3*np.eye(len(H)), g)

# =========================
# Ω PROJECTION
# =========================
def omega(U, x):
    return U @ (U.T @ x)

# =========================
# INVARIANT ENERGY
# =========================
def I(x):
    return np.dot(x, x)

# =========================
# RUN SYSTEM
# =========================
def run(H, r, eta, sigma):

    U, _ = np.linalg.qr(np.random.randn(d, r))

    x = np.random.randn(d)
    x_star = np.zeros(d)

    I_vals = []

    for k in range(K):

        grad = H @ x
        step = xi(H, grad)

        noise = sigma * np.random.randn(d)

        x = x - eta * step + noise
        x = omega(U, x)

        I_vals.append(I(x))

    ratios = np.array(I_vals[1:]) / (np.array(I_vals[:-1]) + 1e-12)

    rho_emp = np.mean(ratios[-200:])

    return rho_emp

# =========================
# PHASE CLASSIFIER
# =========================
def classify(rho):
    if rho < 0.98:
        return "STRONG_CONTRACTION"
    elif rho < 1.02:
        return "CRITICAL"
    else:
        return "DIVERGENT"

# =========================
# MAIN EXPERIMENT
# =========================
def main():

    H = make_hessian(d)

    print("\n===================================")
    print("Ω–Ξ–Δ PHASE FALSIFICATION ENGINE")
    print("===================================\n")

    results = []

    for eta in etas:
        for sigma in sigmas:

            print(f"\nη={eta} σ={sigma}")
            print("-----------------------------------")

            for r in ranks:

                rho = run(H, r, eta, sigma)
                label = classify(rho)

                results.append((eta, sigma, r, rho, label))

                print(f"r={r:<3}  ρ={rho:.6f}  => {label}")

    print("\n===================================")
    print("PHASE SUMMARY")
    print("===================================")

    contraction = sum(1 for r in results if r[-1]=="STRONG_CONTRACTION")
    divergence   = sum(1 for r in results if r[-1]=="DIVERGENT")

    print(f"Strong contraction regimes: {contraction}")
    print(f"Divergent regimes: {divergence}")

    if contraction > divergence:
        print("\nRESULT: SYSTEM IS PREDOMINANTLY CONTRACTIVE")
    else:
        print("\nRESULT: SYSTEM IS NOT GLOBALLY CONTRACTIVE")

if __name__ == "__main__":
    main()
