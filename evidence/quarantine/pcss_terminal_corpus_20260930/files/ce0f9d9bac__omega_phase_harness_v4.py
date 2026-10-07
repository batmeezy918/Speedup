#!/usr/bin/env python3
import json
import math
import itertools

# =========================================================
# OPERATOR SPACE DEFINITIONS
# ψ_{k+1} = O ψ_k
# O ∈ A = ⟨S, Δ, Ω, Ξ⟩
# =========================================================

def S(x):  # spectral inversion stabilizer
    return 1.0 / (1.0 + abs(x))

def Δ(x, baseline):
    return x - baseline

def Ω(x, y, z):
    return (x * y) / (1.0 + abs(z))

def Ξ(curvature, spectral_gap):
    return curvature * math.exp(-spectral_gap)

# =========================================================
# METRIC ENGINE
# =========================================================

def compute_metrics(Omega, alpha):
    contraction = 1.0 + 0.15 * math.sin(Omega * alpha)
    variance = 1.0 / (1.0 + alpha) + 0.1 * Omega
    entropy = 50.0 / (1.0 + Omega * alpha)

    xi_curvature = (Omega**2 + alpha**2) / (1.0 + Omega + alpha)
    spectral_gap = 1.0 / (1.0 + abs(Omega - alpha))

    phase_indicator = math.sqrt(xi_curvature * spectral_gap)

    return {
        "contraction": contraction,
        "variance": variance,
        "entropy": entropy,
        "xi_curvature": xi_curvature,
        "spectral_gap": spectral_gap,
        "phase_indicator": phase_indicator
    }

# =========================================================
# SCORING FUNCTION (NORMALIZED OPERATOR TRACE)
# =========================================================

def score(metrics):
    return (
        10 * S(metrics["variance"]) +
        5 * S(metrics["entropy"]) +
        8 * metrics["phase_indicator"] +
        2 * S(metrics["spectral_gap"])
    )

# =========================================================
# PHASE DETECTION OPERATOR
# =========================================================

def detect_transitions(results):
    phase_values = [r["metrics"]["phase_indicator"] for r in results]
    mean_phase = sum(phase_values) / len(phase_values)

    transitions = [
        r for r in results
        if r["metrics"]["phase_indicator"] > 2.0 * mean_phase
    ]
    return transitions

# =========================================================
# SWEEP OPERATOR SPACE
# =========================================================

def run_sweep():
    Omegas = [0.6, 0.8, 1.0, 1.2, 1.4]
    alphas = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5]

    results = []

    for O, a in itertools.product(Omegas, alphas):
        m = compute_metrics(O, a)

        result = {
            "Omega": O,
            "alpha": a,
            "metrics": m,
            "score": score(m)
        }
        results.append(result)

    best = max(results, key=lambda x: x["score"])
    transitions = detect_transitions(results)

    return results, best, transitions

# =========================================================
# MAIN EXECUTION LAYER
# =========================================================

def main():
    results, best, transitions = run_sweep()

    print("\n=== BEST CONFIGURATION ===")
    print(json.dumps(best, indent=2))

    print("\n=== PHASE TRANSITIONS ===")
    print(json.dumps(transitions, indent=2))

    with open("omega_phase_v4_full.json", "w") as f:
        json.dump(results, f, indent=2)

    with open("omega_phase_v4_transitions.json", "w") as f:
        json.dump(transitions, f, indent=2)

    print("\n=== Ω HARNESS v4 COMPLETE ===")

if __name__ == "__main__":
    main()

