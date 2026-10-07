#!/usr/bin/env python3
"""
DEVICE SPEEDUP CONTRACT HARNESS
==============================

Purpose: determine, by measurement on THIS device, whether the elevated AGD
quotient speedups actually obtain in its functions -- and how much of the
currently-reported E2E number is recoverable by using the quotient operators
the way they are actually defined.

Background (from docs/assessments/2026-10-07/):
    build_quotient(n) in AGD_QUANTUM_GENERALITY_DEFINITIVE_EOF.py defines
        pi = I_q (x) p        p = m^{-1/2} * ones(1,m)
        R  = I_q (x) p^T
        d = 2^n,  q = 2^ceil(n/2),  m = 2^floor(n/2),  d = q*m
    The generator TIMES pi and R as DENSE (d x q) matvecs.
    But both have O(d) block implementations:
        (pi x)_i    = m^{-1/2} * sum_j x_{im+j}          -> d adds
        (R z)_{im+j} = z_i / sqrt(m)                     -> d writes
    So the dense form wastes a factor of q on two of the three quotient stages.

This harness measures three arms per n, plus a correctness cross-check:

  FULL     : u @ psi                     (dense d x d, u = Ubar (x) I_m)
  E2E_DENSE: pi@psi + Ubar@q + R@q       (what the generator times today)
  E2E_BLOCK: block-sum + Ubar@q + block-fill   (uses the definition)

Every arm is required to agree numerically before any timing is reported.

Discipline:
  * warmups then timed reps; median AND MAD (not just mean/std)
  * full telemetry per arm: cpu, freq, governor, thermal, affinity
  * BLAS threads forced to 1 so the measurement is single-core and comparable
  * correctness is a gate, not a footnote

Usage:
    python3 device_speedup_contract.py                 # default affinity
    taskset -c 4-7 python3 device_speedup_contract.py  # pin to A78 cluster
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import sys
import time

import numpy as np

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_v] = "1"

WARMUPS = 5
REPS = 15
N_LIST = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
GATE_TOL = 1e-10


# ---------------------------------------------------------------- telemetry
def _read(p):
    try:
        with open(p) as f:
            return f.read().strip()
    except OSError:
        return None


def telemetry() -> dict:
    freqs = {}
    for i in range(8):
        d = f"/sys/devices/system/cpu/cpu{i}/cpufreq"
        cur, mx, gov = _read(f"{d}/scaling_cur_freq"), _read(f"{d}/cpuinfo_max_freq"), _read(f"{d}/scaling_governor")
        if cur:
            freqs[f"cpu{i}"] = {"cur_mhz": int(cur) / 1000.0, "max_mhz": int(mx) / 1000.0 if mx else None,
                                "gov": gov}
    thermal = {}
    for z in sorted(os.listdir("/sys/class/thermal")) if os.path.isdir("/sys/class/thermal") else []:
        t = _read(f"/sys/class/thermal/{z}/temp")
        if t and t.lstrip("-").isdigit():
            v = int(t)
            if 0 < v < 120000:
                thermal[z] = v / 1000.0
    mem = {}
    mi = _read("/proc/meminfo")
    if mi:
        for line in mi.splitlines()[:4]:
            k, _, v = line.partition(":")
            mem[k] = v.strip()
    return {
        "affinity": sorted(os.sched_getaffinity(0)),
        "cpu_freq": freqs,
        "governor": (freqs.get("cpu0", {}) or {}).get("gov"),
        "thermal_max_c": max(thermal.values()) if thermal else None,
        "thermal_zones": len(thermal),
        "mem": mem,
        "blas_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
    }


# ------------------------------------------------- exact quotient definitions
def build_quotient(n: int):
    """Verbatim from AGD_QUANTUM_GENERALITY_DEFINITIVE_EOF.py::build_quotient."""
    d = 1 << n
    nq = (n + 1) // 2
    nf = n // 2
    q = 1 << nq
    m = 1 << nf
    p = (1.0 / np.sqrt(m)) * np.ones((1, m), dtype=np.complex128)
    pi = np.kron(np.eye(q), p)
    r = np.kron(np.eye(q), p.T)
    return d, q, m, pi, r


def pi_block(m: int, q: int, x: np.ndarray) -> np.ndarray:
    """(pi x)_i = m^{-1/2} sum_j x_{im+j}   -- O(d) instead of O(d*q)."""
    return x.reshape(q, m).sum(axis=1) / np.sqrt(m)


def r_block(m: int, q: int, z: np.ndarray) -> np.ndarray:
    """(R z)_{im+j} = z_i / sqrt(m)         -- O(d) instead of O(d*q)."""
    return np.repeat(z / np.sqrt(m), m)


# ------------------------------------------------------------------ timing
def measure(fn, warmups=WARMUPS, reps=REPS):
    for _ in range(warmups):
        fn()
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        fn()
        ts.append((time.perf_counter_ns() - t0) / 1e9)
    med = statistics.median(ts)
    mad = statistics.median([abs(x - med) for x in ts])
    sd = statistics.stdev(ts) if len(ts) > 1 else 0.0
    return {"median_s": med, "mad_s": mad, "std_s": sd, "min_s": min(ts),
            "cv_pct": 100.0 * sd / med if med else float("nan"), "reps": reps}


def sha(*arrays) -> str:
    h = hashlib.sha256()
    for a in arrays:
        h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


# -------------------------------------------------------------------- main
def main() -> int:
    print("=" * 78)
    print("DEVICE SPEEDUP CONTRACT -- measured on this host")
    print("=" * 78)
    tel = telemetry()
    print(f"affinity        : {tel['affinity']}")
    print(f"governor        : {tel['governor']}")
    print(f"cpu0 max/cur    : {tel['cpu_freq']['cpu0']['max_mhz']} / {tel['cpu_freq']['cpu0']['cur_mhz']} MHz")
    print(f"cpu4 max/cur    : {tel['cpu_freq']['cpu4']['max_mhz']} / {tel['cpu_freq']['cpu4']['cur_mhz']} MHz")
    print(f"thermal max     : {tel['thermal_max_c']} C over {tel['thermal_zones']} zones")
    print(f"MemAvailable    : {tel['mem'].get('MemAvailable')}")
    print(f"warmups/reps    : {WARMUPS}/{REPS}   BLAS threads: {tel['blas_threads']}")
    print()

    rows = []
    all_ok = True
    for n in N_LIST:
        d, q, m, pi, r = build_quotient(n)
        rng = np.random.default_rng(1000 + n)
        ubar = rng.normal(size=(q, q)) + 1j * rng.normal(size=(q, q))
        alpha_q = rng.normal(size=q) + 1j * rng.normal(size=q)
        psi = r @ alpha_q
        u = np.kron(ubar, np.eye(m))

        # ---- correctness gate: all three arms must agree -------------------
        full_out = u @ psi
        alpha_out_d = pi @ psi
        alpha_out_b = pi_block(m, q, psi)
        rec_d = r @ (ubar @ alpha_out_d)      # dense path: R(Ubar (pi psi))
        rec_b = r_block(m, q, ubar @ alpha_q)  # block path: R(Ubar (pi psi))
        e_pi = float(np.max(np.abs(alpha_out_d - alpha_out_b)))
        e_rec = float(np.max(np.abs(rec_d - rec_b)))
        e_full = float(np.max(np.abs(full_out - rec_b)))
        ok = e_pi <= GATE_TOL and e_rec <= GATE_TOL and e_full <= GATE_TOL
        all_ok &= ok
        if not ok:
            print(f"n={n:>2}  CORRECTNESS FAIL  err_pi={e_pi:.3e} err_rec={e_rec:.3e} err_full={e_full:.3e}")
            rows.append({"n": n, "d": d, "q": q, "m": m, "correct": False})
            continue

        t_full = measure(lambda: u @ psi)
        t_kern = measure(lambda: ubar @ alpha_q)
        t_pi_d = measure(lambda: pi @ psi)
        t_r_d = measure(lambda: r @ (ubar @ alpha_out_d))
        t_pi_b = measure(lambda: pi_block(m, q, psi))
        t_r_b = measure(lambda: r_block(m, q, alpha_out_b))

        e2e_dense = (t_pi_d["median_s"] + t_kern["median_s"] + t_r_d["median_s"])
        e2e_block = (t_pi_b["median_s"] + t_kern["median_s"] + t_r_b["median_s"])
        kern = t_full["median_s"] / t_kern["median_s"]
        sp_dense = t_full["median_s"] / e2e_dense
        sp_block = t_full["median_s"] / e2e_block
        pi_gain = t_pi_d["median_s"] / t_pi_b["median_s"]
        r_gain = t_r_d["median_s"] / t_r_b["median_s"]

        rows.append({
            "n": n, "d": d, "q": q, "m": m, "correct": True,
            "err_pi_dense_vs_block": e_pi, "err_recon_dense_vs_block": e_rec,
            "err_full_vs_block_recon": e_full,
            "t_full_median_s": t_full["median_s"], "t_full_cv_pct": t_full["cv_pct"],
            "t_kernel_median_s": t_kern["median_s"],
            "t_pi_dense_median_s": t_pi_d["median_s"], "t_pi_block_median_s": t_pi_b["median_s"],
            "t_r_dense_median_s": t_r_d["median_s"], "t_r_block_median_s": t_r_b["median_s"],
            "kernel_speedup": kern,
            "e2e_speedup_dense": sp_dense, "e2e_speedup_block": sp_block,
            "block_speedup_gain": sp_block / sp_dense if sp_dense > 0 else float("nan"),
            "pi_dense_to_block_gain": pi_gain, "r_dense_to_block_gain": r_gain,
            "thermal_max_c": telemetry()["thermal_max_c"],
        })

        print(f"n={n:>2} d={d:>5} q={q:>3} m={m:>3} | full={t_full['median_s']:.4e}s "
              f"kernel={kern:>9.3f}x | E2E dense={sp_dense:>8.3f}x  block={sp_block:>9.3f}x  "
              f"gain={sp_block/sp_dense if sp_dense>0 else float('nan'):>7.2f}x  "
              f"[pi {pi_gain:>6.2f}x, R {r_gain:>6.2f}x]  ok")
    print()

    ok_rows = [r for r in rows if r.get("correct")]
    if ok_rows:
        print("-" * 78)
        print("SUMMARY")
        print("-" * 78)
        be_d = next((r["n"] for r in ok_rows if r["e2e_speedup_dense"] > 1), None)
        be_b = next((r["n"] for r in ok_rows if r["e2e_speedup_block"] > 1), None)
        last = ok_rows[-1]
        print(f"correctness          : {'ALL PASS' if all_ok else 'FAIL'} (tolerance {GATE_TOL})")
        print(f"E2E break-even (dense): n >= {be_d}")
        print(f"E2E break-even (block): n >= {be_b}")
        print(f"largest n tested     : n={last['n']}  d={last['d']}")
        print(f"kernel speedup       : {last['kernel_speedup']:.3f}x")
        print(f"E2E dense            : {last['e2e_speedup_dense']:.3f}x")
        print(f"E2E block            : {last['e2e_speedup_block']:.3f}x")
        print(f"block gain over dense: {last['block_speedup_gain']:.2f}x")
        print(f"median block gain    : "
              f"{statistics.median([r['block_speedup_gain'] for r in ok_rows if r['e2e_speedup_dense']>0]):.2f}x")
        print()

    out = {"telemetry": tel, "warmups": WARMUPS, "reps": REPS,
           "rows": rows, "all_correct": all_ok}
    dest = sys.argv[1] if len(sys.argv) > 1 else "device_speedup_contract_results.json"
    with open(dest, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print(f"wrote {dest}")
    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())