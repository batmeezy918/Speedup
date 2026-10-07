#!/usr/bin/env python3
import numpy as np

np.random.seed(0)

d = 64
lambda_reg = 1e-3

etas = [0.001, 0.005, 0.01, 0.02]
sigmas = [0.0, 0.001, 0.005]
ranks = [2,4,8,16,32,48,64]

# SPD matrix
A = np.random.randn(d,d)
H = A.T @ A
H = H / np.max(np.linalg.eigvalsh(H))

A_pre = np.linalg.inv(H + lambda_reg*np.eye(d)) @ H

def spectral_radius(U, eta):
    Jr = np.eye(U.shape[1]) - eta * (U.T @ A_pre @ U)
    eig = np.linalg.eigvals(Jr)
    return np.max(np.abs(eig))

print("\nΩ–Ξ–Δ BENCHMARK SYSTEM\n")

for eta in etas:
    for sigma in sigmas:
        print(f"\nη={eta} σ={sigma}")
        print("-----------------------------")

        for r in ranks:
            U, _ = np.linalg.qr(np.random.randn(d,r))

            rho = spectral_radius(U, eta)
            phi = rho**2 + sigma**2 * r

            if phi < 1:
                label = "STABLE"
            elif rho < 1:
                label = "MARGINAL"
            else:
                label = "DIVERGENT"

            print(f"r={r:<3}  ρ={rho:.6f}  Φ={phi:.6f}  => {label}")

print("\nDONE")
