#!/usr/bin/env python3
"""
ISOLATED STAGE TIMING -- the correct device E2E ladder.

Two earlier harnesses were wrong and are corrected here:

 1. device_speedup_contract.py measured each stage once per n in sequence, so
    cache state and thermal drift between stages biased the dense arm.
 2. ab_affinity.py timed  r_block(m,q, ubar @ (pi @ psi))  -- i.e. it recomputed
    the DENSE projection INSIDE the timed region, inflating t_R_block ~30x and
    understating the block gain.

Here every stage input is precomputed OUTSIDE the timed region, so each stage is
timed in isolation. Stages are then composed arithmetically for the E2E ladder,
which is legitimate: the generator composes them the same way, and each stage's
input is the previous stage's OUTPUT, so composition is exact.

Correctness is asserted before any timing.
"""
import os, statistics, time, json, hashlib

for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import numpy as np

REPS, WARM = 15, 5
TRIALS = 5
NS = (10, 11, 12, 13)


def build(n):
    d = 1 << n
    q = 1 << ((n + 1) // 2)
    m = 1 << (n // 2)
    p = (1.0 / np.sqrt(m)) * np.ones((1, m), dtype=np.complex128)
    return d, q, m, np.kron(np.eye(q), p), np.kron(np.eye(q), p.T)


def pi_block(m, q, x):
    return x.reshape(q, m).sum(axis=1) / np.sqrt(m)


def med(fn, reps=REPS, warm=WARM):
    for _ in range(warm):
        fn()
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        fn()
        ts.append(time.perf_counter_ns() - t0)
    return statistics.median(ts)


def thermal():
    hi = 0.0
    try:
        for z in os.listdir("/sys/class/thermal"):
            try:
                v = int(open(f"/sys/class/thermal/{z}/temp").read().strip())
                if 0 < v < 120000:
                    hi = max(hi, v / 1000.0)
            except (OSError, ValueError):
                pass
    except OSError:
        pass
    return hi


def main():
    print(f"{'n':>3} {'d':>6} {'q':>4} {'m':>3} | {'t_full':>11} {'t_kern':>8} | "
          f"{'pi_dense':>10} {'pi_block':>9} {'x':>6} | {'R_dense':>10} {'R_block':>9} {'x':>6} | "
          f"{'E2E_dense':>10} {'E2E_block':>10} {'gain':>7}")
    print("-" * 128)
    rows = []
    for n in NS:
        d, q, m, pi, r = build(n)
        rng = np.random.default_rng(1000 + n)
        ubar = rng.normal(size=(q, q)) + 1j * rng.normal(size=(q, q))
        u = np.kron(ubar, np.eye(m))

        # ---- precompute every stage input ONCE, outside all timing ----
        aq = rng.normal(size=q) + 1j * rng.normal(size=q)
        psi = r @ aq
        alpha_q = pi @ psi            # stage 1 output (dense)
        alpha_out = ubar @ alpha_q     # stage 2 output
        out_buf = np.empty(d, dtype=np.complex128)

        # ---- correctness gate ----
        assert np.max(np.abs(alpha_q - pi_block(m, q, psi))) < 1e-10
        ref = np.repeat(alpha_out / np.sqrt(m), m)
        got = np.empty(d, dtype=np.complex128)
        got.reshape(q, m)[:] = (alpha_out / np.sqrt(m))[:, None]
        assert np.array_equal(got, ref)
        assert np.max(np.abs(u @ psi - r @ alpha_out)) < 1e-9

        acc = {k: [] for k in ("t_full", "t_kern", "pi_d", "pi_b", "r_d", "r_b")}
        for _ in range(TRIALS):
            acc["t_full"].append(med(lambda: u @ psi))
            acc["t_kern"].append(med(lambda: ubar @ alpha_q))
            acc["pi_d"].append(med(lambda: pi @ psi))
            acc["pi_b"].append(med(lambda: pi_block(m, q, psi)))
            acc["r_d"].append(med(lambda: r @ alpha_out))
            acc["r_b"].append(med(lambda: r_block_into(m, q, alpha_out, out_buf)))
        f = lambda k: statistics.median(acc[k])
        M = f
        e2e_d = M("t_full") / (M("pi_d") + M("t_kern") + M("r_d"))
        e2e_b = M("t_full") / (M("pi_b") + M("t_kern") + M("r_b"))
        print(f"{n:>3} {d:>6} {q:>4} {m:>3} | {M('t_full'):>10,}ns {M('t_kern'):>7,}ns | "
              f"{M('pi_d'):>9,}ns {M('pi_b'):>8,}ns {M('pi_d')/M('pi_b'):>5.1f}x | "
              f"{M('r_d'):>9,}ns {M('r_b'):>8,}ns {M('r_d')/M('r_b'):>5.1f}x | "
              f"{e2e_d:>9.1f}x {e2e_b:>9.1f}x {e2e_b/e2e_d:>6.2f}x")
        rows.append({"n": n, "d": d, "q": q, "m": m,
                     **{k: M(k) for k in acc},
                     "pi_gain": M("pi_d") / M("pi_b"), "r_gain": M("r_d") / M("r_b"),
                     "e2e_dense": e2e_d, "e2e_block": e2e_b, "block_gain": e2e_b / e2e_d,
                     "flop_ratio_pi": q, "flop_ratio_R": q,
                     "kernel_speedup": M("t_full") / M("t_kern"),
                     "thermal_c": thermal()})

    print()
    print("=" * 96)
    print("ISOLATED-STAGE DEVICE E2E LADDER  (median of "
          f"{TRIALS} trials x {REPS} reps, correctness asserted)")
    print("=" * 96)
    print(f"{'n':>3} {'d':>6} {'kernel':>11} {'E2E dense':>11} {'E2E block':>11} "
          f"{'block gain':>11} {'pi gain':>9} {'R gain':>8} {'FLOP pred':>10} {'eff vs pred':>12}")
    for r in rows:
        # FLOP prediction for the quotient path: (2dq+q^2)/(2d+q^2)
        pred = (2 * r["d"] * r["q"] + r["q"] ** 2) / (2 * r["d"] + r["q"] ** 2)
        print(f"{r['n']:>3} {r['d']:>6} {r['kernel_speedup']:>10.1f}x {r['e2e_dense']:>10.1f}x "
              f"{r['e2e_block']:>10.1f}x {r['block_gain']:>10.2f}x {r['pi_gain']:>8.1f}x "
              f"{r['r_gain']:>7.1f}x {pred:>9.1f}x {r['block_gain']/pred:>11.3f}")

    best = rows[-1]
    print()
    print(f"HEADLINE (n={best['n']}, d={best['d']}) measured on this device:")
    print(f"  kernel (dense {best['d']}x{best['d']} vs {best['q']}x{best['q']}) : "
          f"{best['kernel_speedup']:.1f}x")
    print(f"  E2E as generated today (dense pi, R)              : {best['e2e_dense']:.1f}x")
    print(f"  E2E with block-structured pi and R               : {best['e2e_block']:.1f}x")
    print(f"  improvement                                      : {best['block_gain']:.2f}x")
    floor = best["t_full"] / (best["d"] + best["t_kern"] + best["d"])
    print(f"  memory-bandwidth floor for the quotient path     : {floor:.1f}x")
    json.dump({"trials": TRIALS, "reps": REPS, "rows": rows},
              open("isolated_stage_results.json", "w"), indent=2)
    print("\nwrote isolated_stage_results.json")


def r_block_into(m, q, z, out):
    out.reshape(q, m)[:] = (z / np.sqrt(m))[:, None]
    return out


if __name__ == "__main__":
    main()