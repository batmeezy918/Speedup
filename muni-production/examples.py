#!/usr/bin/env python3
"""End-to-end demonstration. Run: python3 examples.py"""
import json, sys
import muni

def show(title): print("\n" + "=" * 68); print(title); print("=" * 68)

show("1. EVIDENCE: what this package is bound to")
ev = muni.verify_evidence()
print("integrity :", ev["integrity"])
for k, v in ev["checks"].items():
    print(f"  {'OK ' if v else 'BAD'} {k}")
print("library sha256:", ev["details"]["library_sha256"])

show("2. SCOPE: the complete claim, as data")
c = muni.claim()
print("scope_id:", c["scope_id"])
print("claim   :", c["claim"])
print("excluded:")
for e in c["exclusions"]:
    print("   -", e)

show("3. ADMISSIBLE REAL-WORKLOAD SHAPE (identical fibers)")
U = [[0.9, 0.1], [0.2, 0.8]]
x = [1.0, 1.0, 2.0, 2.0]
r = muni.run(U, x, steps=64)
print("used_quotient:", r.used_quotient, " exact:", r.exact, " err:", r.max_abs_error)
print("values == reference:", r.values == r.reference)
print("reason:", r.reason)

show("4. INADMISSIBLE INPUT FAILS CLOSED, STILL EXACT")
r2 = muni.run(U, [1.0, 1.1, 2.0, 2.0], steps=64)
print("used_quotient:", r2.used_quotient, " exact:", r2.exact)
print("sector residual:", r2.sector_residual)
print("reason:", r2.reason)

show("5. MEASURED SPEEDUP ON THIS PROCESS")
r3, m3 = 64, 64
Ub = [[0.02 if i == j else 0.004 for j in range(r3)] for i in range(r3)]
xb = [0.01 * b for b in range(r3) for _ in range(m3)]
b = muni.benchmark(Ub, xb, steps=64, trials=7, reps=5)
print(f"r={b.r} m={b.m} d={b.d} steps={b.steps}")
print(f"baseline  : {b.baseline_ms:.4f} ms")
print(f"optimised : {b.optimised_ms:.4f} ms")
print(f"speedup   : {b.speedup:.2f}x   (measured here, both arms, one process)")
print("exact     :", b.exact, " max_abs_error:", b.max_abs_error)

show("6. FREE PRE-CHECK BEFORE PAYING FOR A RUN")
for label, sample in [("identical fibers", [5.0] * 12),
                      ("mixed values", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0,
                                        7.0, 8.0, 9.0, 10.0, 11.0, 12.0])]:
    resid, bad, total = muni.measure_sector(sample, m=3)
    print(f"{label:18s} residual={resid:.3e} outside={bad}/{total} "
          f"-> {'worth enabling' if bad == 0 else 'will fall back'}")

show("7. REFUSALS")
for label, call in [
    ("NaN state",  lambda: muni.run([[1.0]], [float("nan")], steps=1)),
    ("Inf operator", lambda: muni.run([[float("inf")]], [1.0], steps=1)),
    ("ragged x0",  lambda: muni.run(U, [1.0, 1.0, 2.0], steps=1)),
    ("negative steps", lambda: muni.run([[1.0]], [1.0], steps=-1)),
]:
    try:
        res = call()
        print(f"{label:16s} -> {res.status_name}  ({res.reason[:52]}...)")
    except (ValueError, TypeError) as e:
        print(f"{label:16s} -> rejected: {e}")

print("\nAll demonstrations complete. Nothing here was asserted without measuring it.")
