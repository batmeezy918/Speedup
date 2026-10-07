import numpy as np
import time
import cma
from scipy.linalg import svd

SEED = 42
DIM = 32
BUDGET = 10000
RANK = 8
LATENT_DIM = RANK   # use rank as latent dimension
LAMBDA_POP = 50     # population size per generation

np.random.seed(SEED)

print("=== Ω∞‑Opt vs CMA‑ES VALIDATION SUITE ===")
print(f"DIM = {DIM}, BUDGET = {BUDGET}, RANK = {RANK}")
print()

# ------------------------------------------------------------------
# Rosenbrock objective (standard benchmark)
# ------------------------------------------------------------------
def objective(x):
    x = np.asarray(x)
    return np.sum(100.0 * (x[1:] - x[:-1]**2)**2 + (1.0 - x[:-1])**2)

# ------------------------------------------------------------------
# Ω∞‑Opt: Sovereign Optimizer using SIM2XR quotient framework
# ------------------------------------------------------------------
class OmegaOpt:
    def __init__(self, dim, rank=8, budget=10000, lr=0.01):
        self.dim = dim
        self.rank = rank
        self.budget = budget
        self.lr = lr
        self.Xi = 1.0
        self.evals = 0
        self.mu = np.random.uniform(-3, 3, dim)
        self.C = np.eye(dim)  # will be low-rank
        self.U = np.eye(dim, rank)   # initial random projection
        self.Sigma = np.eye(rank)    # covariance in latent space
        self.history = []            # store (mu, objective) for quotient learning
        self.F_tilde = self._default_F_tilde()
        self.best = objective(self.mu)
        self.best_x = self.mu.copy()
        self.pop_size = LAMBDA_POP
        self._update_projection()    # initial PCA from random samples

    def _default_F_tilde(self):
        # identity map (will be learned from data)
        return lambda q: q

    def _update_projection(self):
        # Use SVD of recent history to update U
        if len(self.history) < 20:
            return
        X = np.array([h[0] for h in self.history[-50:]])  # recent mu's
        Xc = X - np.mean(X, axis=0)
        U, s, Vt = svd(Xc, full_matrices=False)
        self.U = U[:, :self.rank]
        # Project covariance to latent
        # We'll keep Sigma as identity for simplicity; can be refined later

    def _learn_quotient_dynamics(self):
        # Fit linear map from previous mu to current mu in latent space
        if len(self.history) < 10:
            return
        # Collect pairs of latent vectors
        qs = []
        q_nexts = []
        for i in range(len(self.history)-1):
            mu_old = self.history[i][0]
            mu_new = self.history[i+1][0]
            q_old = self.U.T @ (mu_old - np.mean(mu_old))  # simplified
            q_new = self.U.T @ (mu_new - np.mean(mu_new))
            qs.append(q_old)
            q_nexts.append(q_new)
        if len(qs) < 2:
            return
        Q = np.array(qs)
        Qn = np.array(q_nexts)
        # Least squares: Qn ≈ A Q
        A, _, _, _ = np.linalg.lstsq(Q, Qn, rcond=None)
        self.F_tilde = lambda q: A @ q

    def step(self):
        # 1. Project current mean to latent
        q = self.U.T @ (self.mu - np.mean(self.mu))  # centered

        # 2. Evolve in latent using learned dynamics
        q_pred = self.F_tilde(q)

        # 3. Lift back to original space
        mu_pred = self.mu + self.U @ (q_pred - q)   # approximate lift

        # 4. Sample candidates around mu_pred in latent space
        z_samples = np.random.multivariate_normal(np.zeros(self.rank), self.Sigma, size=self.pop_size)
        candidates = mu_pred + self.U @ z_samples.T   # shape (dim, pop_size)

        # 5. Evaluate candidates and find best
        scores = np.array([objective(c) for c in candidates.T])
        best_idx = np.argmin(scores)
        best_candidate = candidates[:, best_idx]
        best_score = scores[best_idx]

        # 6. Update best
        if best_score < self.best:
            self.best = best_score
            self.best_x = best_candidate.copy()

        # 7. Update mean (move towards best candidate)
        step = self.lr * (best_candidate - self.mu)
        self.mu += step

        # 8. Update low-rank covariance using rank-1 update (simplified)
        # For simplicity, we keep Sigma fixed; a full CMA-ES style update could be added.
        # We'll adjust Sigma based on success (adaptive)
        if best_score < np.mean(scores):
            self.Sigma *= 1.02   # expand if good
        else:
            self.Sigma *= 0.98   # contract if poor
        self.Sigma = np.clip(self.Sigma, 0.01, 10.0)

        # 9. Adaptive Xi (governor)
        # Compute contraction rate
        if len(self.history) > 1:
            prev_mu = self.history[-1][0]
            rho = np.linalg.norm(self.mu - prev_mu) / (np.linalg.norm(prev_mu) + 1e-8)
            if rho < 0.1:
                self.Xi = min(2.0, self.Xi * 1.01)
            elif rho > 0.5:
                self.Xi = max(0.5, self.Xi * 0.99)
            self.Xi = np.clip(self.Xi, 0.5, 2.0)

        # 10. Store history for quotient learning
        self.history.append((self.mu.copy(), best_score))
        if len(self.history) > 100:
            self.history = self.history[-100:]

        # 11. Periodically update projection and quotient dynamics
        if len(self.history) % 20 == 0:
            self._update_projection()
            self._learn_quotient_dynamics()

        # 12. Update evaluation count
        self.evals += self.pop_size
        return best_score, self.evals

    def optimize(self):
        start = time.time()
        while self.evals < self.budget:
            score, evals = self.step()
            if evals % 1000 == 0:
                print(f"  Ω∞-Opt: evals={evals}, best={self.best:.4f}")
        runtime = time.time() - start
        return {
            "best": self.best,
            "runtime": runtime,
            "evals": self.evals,
            "Xi": self.Xi,
        }

# ------------------------------------------------------------------
# Standard CMA-ES
# ------------------------------------------------------------------
def run_cmaes():
    np.random.seed(SEED)
    x0 = np.random.uniform(-3, 3, DIM)
    start = time.time()
    es = cma.CMAEvolutionStrategy(
        x0,
        0.5,
        {
            'seed': SEED,
            'maxfevals': BUDGET,
            'verbose': -9
        }
    )
    while not es.stop():
        X = es.ask()
        F = [objective(x) for x in X]
        es.tell(X, F)
    runtime = time.time() - start
    return {
        "best": es.best.f,
        "runtime": runtime,
        "evals": es.result.evaluations,
    }

# ------------------------------------------------------------------
# Main benchmark
# ------------------------------------------------------------------
print("Running Ω∞‑Opt...")
opt = OmegaOpt(DIM, rank=RANK, budget=BUDGET, lr=0.02)
res_omega = opt.optimize()

print("\nRunning CMA-ES...")
res_cma = run_cmaes()

print("\n===================================")
print("FINAL RESULTS")
print("===================================")
print(f"\nΩ∞‑Opt")
print(f"  Best Score : {res_omega['best']:.6f}")
print(f"  Runtime    : {res_omega['runtime']:.3f}s")
print(f"  Evals      : {res_omega['evals']}")
print(f"  Xi Final   : {res_omega['Xi']:.3f}")

print(f"\nCMA-ES")
print(f"  Best Score : {res_cma['best']:.6f}")
print(f"  Runtime    : {res_cma['runtime']:.3f}s")
print(f"  Evals      : {res_cma['evals']}")

print()
if res_omega['best'] < res_cma['best']:
    print("🏆 WINNER: Ω∞‑Opt")
else:
    print("⚠️ WINNER: CMA-ES (for now – tune hyperparameters)")
print("=== COMPLETE ===")
