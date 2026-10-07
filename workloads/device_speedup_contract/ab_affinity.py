#!/usr/bin/env python3
"""
INTERLEAVED A/B -- is the device speedup CONSTANT, or is it run-to-run noise?

The single-shot runs disagreed at small n (E2E_block n=12: 752x unpinned vs 584x
pinned). Before claiming any affinity or optimisation benefit, this alternates
the two conditions within a single process so that thermal drift, background
load and frequency changes hit both arms equally.

Design:
  * conditions are interleaved block-by-block, not run-by-run
  * BOTH arms are timed inside each block, so the comparison is paired
  * report median, MAD, and the paired ratio distribution
  * a signal is only declared if it exceeds the measured paired noise floor

Usage:  python3 ab_affinity.py [trials] [n_list]
"""
import os, statistics, sys, time, json

for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"

import numpy as np

TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 7
NS = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [10, 11, 12]
REPS = 15
WARMUPS = 5


def build(n):
    d = 1 << n
    q = 1 << ((n + 1) // 2)
    m = 1 << (n // 2)
    p = (1.0 / np.sqrt(m)) * np.ones((1, m), dtype=np.complex128)
    return d, q, m, np.kron(np.eye(q), p), np.kron(np.eye(q), p.T)


def pi_block(m, q, x):
    return x.reshape(q, m).sum(axis=1) / np.sqrt(m)


def r_block(m, q, z):
    return np.repeat(z / np.sqrt(m), m)


def med(fn):
    for _ in range(WARMUPS):
        fn()
    ts = []
    for _ in range(REPS):
        t0 = time.perf_counter_ns()
        fn()
        ts.append(time.perf_counter_ns() - t0)
    return statistics.median(ts)


def thermal():
    hi = 0.0
    try:
        for z in os.listdir("/sys/class/thermal"):
            p = f"/sys/class/thermal/{z}/temp"
            try:
                v = int(open(p).read().strip())
                if 0 < v < 120000:
                    hi = max(hi, v / 1000.0)
            except (OSError, ValueError):
                pass
    except OSError:
        pass
    return hi


def main():
    cases = {}
    for n in NS:
        d, q, m, pi, r = build(n)
        rng = np.random.default_rng(1000 + n)
        ubar = rng.normal(size=(q, q)) + 1j * rng.normal(size=(q, q))
        aq = rng.normal(size=q) + 1j * rng.normal(size=q)
        psi = r @ aq
        u = np.kron(ubar, np.eye(m))
        cases[n] = dict(d=d, q=q, m=m, pi=pi, r=r, ubar=ubar, aq=aq, psi=psi, u=u)

    # sanity: block == dense, once, before any timing
    for n, c in cases.items():
        e = np.max(np.abs(c["pi"] @ c["psi"] - pi_block(c["m"], c["q"], c["psi"])))
        e2 = np.max(np.abs(c["r"] @ (c["ubar"] @ (c["pi"] @ c["psi"]))
                           - r_block(c["m"], c["q"], c["ubar"] @ (c["pi"] @ c["psi"]))))
        assert e < 1e-10 and e2 < 1e-10, f"n={n} block/dense mismatch {e:.3e} {e2:.3e}"
    print("correctness: block == dense on all cases (tol 1e-10) OK")

    ALL = sorted(os.sched_getaffinity(0))
    BIG = sorted({i for i in ALL if i >= 4}) or ALL
    CONDITIONS = [("default", ALL), ("a78", BIG)]
    print(f"interleaving conditions: default={ALL}  a78={BIG}")
    obs = []
    for t in range(TRIALS):
      for cond, mask in CONDITIONS:
        try:
            os.sched_setaffinity(0, set(mask))
        except OSError as e:
            print(f"  (cannot set affinity {mask}: {e})"); break
        for n in NS:
            c = cases[n]
            tf = med(lambda: c["u"] @ c["psi"])
            tk = med(lambda: c["ubar"] @ c["aq"])
            tpi_d = med(lambda: c["pi"] @ c["psi"])
            tpi_b = med(lambda: pi_block(c["m"], c["q"], c["psi"]))
            tr_d = med(lambda: c["r"] @ (c["ubar"] @ (c["pi"] @ c["psi"])))
            tr_b = med(lambda: r_block(c["m"], c["q"], c["ubar"] @ (c["pi"] @ c["psi"])))
            e2e_d = tf / (tpi_d + tk + tr_d)
            e2e_b = tf / (tpi_b + tk + tr_b)
            obs.append({"trial": t, "cond": cond, "n": n, "thermal": thermal(),
                        "affinity": sorted(os.sched_getaffinity(0)),
                        "t_full_ns": tf, "t_kernel_ns": tk,
                        "t_pi_dense_ns": tpi_d, "t_pi_block_ns": tpi_b,
                        "t_r_dense_ns": tr_d, "t_r_block_ns": tr_b,
                        "kernel": tf / tk, "e2e_dense": e2e_d, "e2e_block": e2e_b,
                        "gain": e2e_b / e2e_d,
                        "pi_gain": tpi_d / tpi_b, "r_gain": tr_d / tr_b})
            print(f"  t{t} {cond:>7} n={n:>2} therm={obs[-1]['thermal']:.1f}C  "
                  f"kernel={obs[-1]['kernel']:>9.2f}x  e2e_dense={e2e_d:>8.2f}x  "
                  f"e2e_block={e2e_b:>9.2f}x  gain={obs[-1]['gain']:>6.2f}x "
                  f"[pi {obs[-1]['pi_gain']:>5.2f}x R {obs[-1]['r_gain']:>5.2f}x]")

    print()
    print("=" * 74)
    print(f"INTERLEAVED SUMMARY  trials={TRIALS}  n={NS}")
    print("=" * 74)
    print(f"{'n':>3} {'e2e_dense med':>14} {'MAD':>8} {'CV%':>6} | "
          f"{'e2e_block med':>14} {'MAD':>8} {'CV%':>6} | {'gain med':>9} {'gain min':>9} {'gain max':>9}")
    summary = []
    for n in NS:
        g = [o for o in obs if o["n"] == n]
        def s(key):
            v = [o[key] for o in g]
            m = statistics.median(v)
            mad = statistics.median([abs(x - m) for x in v])
            sd = statistics.stdev(v) if len(v) > 1 else 0.0
            return m, mad, (100 * sd / m if m else float("nan"))
        dd, dmad, dcv = s("e2e_dense")
        bb, bmad, bcv = s("e2e_block")
        gv = [o["gain"] for o in g]
        print(f"{n:>3} {dd:>14.2f} {dmad:>8.2f} {dcv:>6.1f} | "
              f"{bb:>14.2f} {bmad:>8.2f} {bcv:>6.1f} | "
              f"{statistics.median(gv):>9.2f} {min(gv):>9.2f} {max(gv):>9.2f}")
        summary.append({"n": n, "e2e_dense_median": dd, "e2e_dense_mad": dmad, "e2e_dense_cv_pct": dcv,
                        "e2e_block_median": bb, "e2e_block_mad": bmad, "e2e_block_cv_pct": bcv,
                        "gain_median": statistics.median(gv), "gain_min": min(gv), "gain_max": max(gv),
                        "kernel_median": statistics.median([o["kernel"] for o in g])})

    print()
    for n in NS:
        r = [s for s in summary if s["n"] == n][0]
        spread = (r["gain_max"] - r["gain_min"]) / r["gain_median"]
        print(f"n={n:>2}: block gain {r['gain_median']:.2f}x, run-to-run spread "
              f"{100*spread:.1f}% of median  -> "
              f"{'CONSTANT (signal > noise)' if spread < 0.35 else 'NOT CONSTANT (noise dominates)'}")
    print()
    print("PER-CONDITION (affinity) COMPARISON -- paired by trial")
    print(f"{'n':>3} {'cond':>8} {'e2e_dense':>11} {'e2e_block':>11} {'gain':>7} {'kernel':>10}")
    for n in NS:
        for cond, _m in CONDITIONS:
            g = [o for o in obs if o["n"] == n and o.get("cond") == cond]
            if not g: continue
            print(f"{n:>3} {cond:>8} {statistics.median([o['e2e_dense'] for o in g]):>11.2f} "
                  f"{statistics.median([o['e2e_block'] for o in g]):>11.2f} "
                  f"{statistics.median([o['gain'] for o in g]):>7.2f} "
                  f"{statistics.median([o['kernel'] for o in g]):>10.2f}")
    print()
    print("COMPONENT MEDIANS (ns), pooled")
    print(f"{'n':>3} {'cond':>8} {'t_full':>12} {'t_kernel':>10} {'t_pi_dense':>11} {'t_pi_block':>11} {'t_r_dense':>11} {'t_r_block':>10}")
    for n in NS:
        for cond, _m in CONDITIONS:
            g = [o for o in obs if o["n"] == n and o.get("cond") == cond]
            if not g: continue
            f=lambda k: statistics.median([o[k] for o in g])
            print(f"{n:>3} {cond:>8} {f('t_full_ns'):>12.0f} {f('t_kernel_ns'):>10.0f} "
                  f"{f('t_pi_dense_ns'):>11.0f} {f('t_pi_block_ns'):>11.0f} "
                  f"{f('t_r_dense_ns'):>11.0f} {f('t_r_block_ns'):>10.0f}")
    json.dump({"trials": TRIALS, "n": NS, "obs": obs, "summary": summary},
              open("ab_affinity_results.json", "w"), indent=2)
    print("\nwrote ab_affinity_results.json")


if __name__ == "__main__":
    main()