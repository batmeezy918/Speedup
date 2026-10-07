#!/usr/bin/env python3
"""
R-IMPLEMENTATION MICROBENCHMARK -- where the remaining quotient overhead is.

Interleaved A/B on this device showed:
    n=12:  pi  dense->block  326us -> 15us   (21.7x)
           R   dense->block  775us -> 355us  ( 2.2x)   <-- R is the bottleneck
           kernel                     8.4us

`pi_block` wins because it only has to READ the d-vector (64 KB).
`R` must WRITE a d-vector. The block form writes exactly the same d-vector, so the
floor is similar -- the question is purely how fast we can fill it.

np.repeat allocates and does strided copying. Alternatives are benchmarked against
it, all producing identical bytes (checked before any timing is reported).

Usage: python3 r_impl_bench.py
"""
import os, statistics, time

for v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import numpy as np

REPS, WARM = 15, 5


def med(fn):
    for _ in range(WARM):
        fn()
    ts = []
    for _ in range(REPS):
        t0 = time.perf_counter_ns()
        fn()
        ts.append(time.perf_counter_ns() - t0)
    return statistics.median(ts)


def make(n):
    d = 1 << n
    q = 1 << ((n + 1) // 2)
    m = 1 << (n // 2)
    return d, q, m


# ---- candidate implementations of (R z)_{im+j} = z_i / sqrt(m) ----------------
def r_repeat(z, q, m, out=None):
    return np.repeat(z / np.sqrt(m), m)


def r_broadcast_alloc(z, q, m):
    return np.broadcast_to((z / np.sqrt(m))[:, None], (q, m)).reshape(-1)


def r_prealloc(z, q, m, out):
    np.multiply(z, 1.0 / np.sqrt(m), out=out[:q])
    out[:q, None] = out[:q, None]          # no-op guard removed below
    return out


def r_fill(z, q, m, out):
    v = z / np.sqrt(m)
    out.reshape(q, m)[:] = v[:, None]
    return out


# NOTE: np.tile / np.concatenate are NOT valid here. They repeat the WHOLE array
# m times ([v,v,v,...]) whereas R needs each element repeated m times CONSECUTIVELY
# ([v0,v0,...,v1,v1,...]). Correctness gate below rejects them; kept out of the run.


def main():
    print(f"{'n':>3} {'d':>6} {'q':>4} {'m':>4} | " + " ".join(f"{k:>16}" for k in
          ("repeat", "bcast_alloc", "fill_prealloc")))
    print("-" * 118)
    best_rows = []
    for n in (10, 11, 12, 13):
        d, q, m = make(n)
        rng = np.random.default_rng(n)
        z = rng.normal(size=q) + 1j * rng.normal(size=q)
        ref = np.repeat(z / np.sqrt(m), m)
        out = np.empty(d, dtype=np.complex128)

        # correctness gate first
        for name, fn in (("bcast_alloc", lambda: np.broadcast_to((z / np.sqrt(m))[:, None], (q, m)).reshape(-1)),
                         ("fill_prealloc", lambda: r_fill(z, q, m, out))):
            v = np.asarray(fn())
            assert v.shape == ref.shape and np.array_equal(v, ref), f"{name} mismatch at n={n}"
        print(f"{n:>3} {d:>6} {q:>4} {m:>4} | ", end="")
        t_rep = med(lambda: r_repeat(z, q, m))
        t_bc = med(lambda: np.broadcast_to((z / np.sqrt(m))[:, None], (q, m)).reshape(-1))
        t_fl = med(lambda: r_fill(z, q, m, out))
        for t in (t_rep, t_bc, t_fl):
            print(f"{t:>13,}ns " if t == t else "", end="")
        print(f"|  x{t_rep/t_fl:>5.2f} vs fill")
        best_rows.append({"n": n, "d": d, "q": q, "m": m,
                          "repeat_ns": t_rep, "broadcast_alloc_ns": t_bc,
                          "fill_prealloc_ns": t_fl,
                          "speedup_repeat_to_fill": t_rep / t_fl})

    print()
    print("=" * 74)
    print("R-IMPLEMENTATION RESULT (all outputs byte-identical, asserted)")
    print("=" * 74)
    print(f"{'n':>3} {'d':>6} {'repeat us':>11} {'bcast us':>10} {'fill us':>10} {'best gain':>11}")
    for r in best_rows:
        print(f"{r['n']:>3} {r['d']:>6} {r['repeat_ns']/1e3:>11.1f} {r['broadcast_alloc_ns']/1e3:>10.1f} "
              f"{r['fill_prealloc_ns']/1e3:>10.1f} {r['speedup_repeat_to_fill']:>10.2f}x")

    print()
    print("IMPLIED E2E at n=12 using measured component times")
    last = best_rows[-1]
    t_full = 21_270_782
    t_kern = 8_438
    t_pi_block = 14_948
    for label, t_r in (("repeat (current)", last["repeat_ns"]),
                       ("broadcast_alloc", last["broadcast_alloc_ns"]),
                       ("fill_prealloc", last["fill_prealloc_ns"])):
        e2e = t_full / (t_pi_block + t_kern + t_r)
        print(f"  {label:<18} t_R={t_r/1e3:>7.1f}us   E2E={e2e:>9.1f}x")


if __name__ == "__main__":
    main()