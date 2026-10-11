#!/usr/bin/env python3
"""Aggregate sota_bench line-protocol output into a verdict report.

Follows differential-benchmarking discipline: median + MAD (spread), interval
overlap test, explicit A/A noise floor, and a control-path drift check.
"""
import sys, json, glob, statistics as st, datetime

def med(x): return st.median(x) if x else float('nan')
def mad(x):
    if not x: return float('nan')
    m = st.median(x)
    return st.median([abs(v - m) for v in x])

def clean(xs):
    return [v for v in xs if v is not None and v > 0.0]

def stat(xs):
    xs = clean(xs)
    if not xs:
        return None
    return {"n": len(xs), "median_ms": med(xs), "mad_ms": mad(xs),
            "min_ms": min(xs), "max_ms": max(xs), "raw": xs}

def interval(s):
    if s is None: return None
    return [s["median_ms"] - s["mad_ms"], s["median_ms"] + s["mad_ms"]]

def disjoint(a, b):
    if a is None or b is None: return None
    ia, ib = interval(a), interval(b)
    return ia[1] < ib[0] or ib[1] < ia[0]

def drift(series):
    """First-half vs second-half median of a control path (struct)."""
    xs = clean(series)
    if len(xs) < 4: return None
    h = len(xs) // 2
    a, b = med(xs[:h]), med(xs[h:])
    if a == 0: return None
    return (b - a) / a * 100.0

def parse(path):
    cfg, raw, aa, err, pinfo = {}, {}, {}, {}, {}
    for line in open(path):
        t = line.split()
        if not t: continue
        if t[0] == 'CONFIG': cfg = dict(kv.split('=') for kv in t[1:])
        elif t[0] == 'RAW': raw[t[1]] = [float(v) for v in t[2:]]
        elif t[0] == 'AA': aa[t[1]] = [float(v) for v in t[2:]]
        elif t[0] == 'ERR': err = dict(kv.split('=') for kv in t[1:])
        elif t[0] == 'PATH': pinfo = dict(kv.split('=') for kv in t[1:])
    return cfg, raw, aa, err, pinfo

def ratio(a, b):
    if a is None or b is None or b["median_ms"] == 0: return None
    return a["median_ms"] / b["median_ms"]

def main():
    files = sys.argv[1:]
    if not files:
        files = sorted(glob.glob("receipts/sota_raw_*.txt"))
    configs = []
    for f in files:
        cfg, raw, aa, err, pinfo = parse(f)
        if not cfg: continue
        S = {k: stat(raw.get(k, [])) for k in ("cand", "blas", "naive", "struct")}
        AAc = stat(aa.get("cand", []))
        AAb = stat(aa.get("blas", []))
        rec = {
            "file": f,
            "d": int(cfg.get("d", 0)), "m": int(cfg.get("m", 0)),
            "r": int(cfg.get("r", 0)), "steps": int(cfg.get("steps", 0)),
            "trials": int(cfg.get("trials", 0)), "reps": int(cfg.get("reps", 0)),
            "blas_enabled": cfg.get("blas") == "1",
            "naive_enabled": cfg.get("naive") == "1",
            "paths": {k: S[k] for k in S},
            "ratio_struct_over_cand": ratio(S["struct"], S["cand"]),
            "ratio_blas_over_cand": ratio(S["blas"], S["cand"]),
            "ratio_naive_over_cand": ratio(S["naive"], S["cand"]),
            "noise_aa_cand": ratio(AAc, S["cand"]),
            "noise_aa_blas": ratio(AAb, S["blas"]),
            "drift_struct_pct": drift(raw.get("struct", [])),
            "err": {k: float(v) for k, v in err.items()},
            "cand_runs": int(pinfo.get("cand_runs", 0)),
            "cand_fallback": int(pinfo.get("cand_fallback", 0)),
            "cand_vs_struct_disjoint": disjoint(S["cand"], S["struct"]),
            "cand_vs_blas_disjoint": disjoint(S["cand"], S["blas"]),
        }
        configs.append(rec)

    cand_errs = [c["err"].get("cand", 1.0) for c in configs]
    fbs = [c["cand_fallback"] for c in configs]
    ratios = [c["ratio_struct_over_cand"] for c in configs if c["ratio_struct_over_cand"]]
    noises = [c["noise_aa_cand"] for c in configs if c["noise_aa_cand"]]
    summary = {
        "all_cand_err_zero": all(e == 0.0 for e in cand_errs),
        "all_cand_no_fallback": all(f == 0 for f in fbs),
        "min_struct_speedup": min(ratios) if ratios else None,
        "max_struct_speedup": max(ratios) if ratios else None,
        "max_noise_aa_cand": max(noises) if noises else None,
        "min_noise_aa_cand": min(noises) if noises else None,
        "n_configs": len(configs),
    }
    report = {"generated": datetime.datetime.now().isoformat(timespec="seconds"),
              "summary": summary, "configs": configs}

    out_json = "receipts/sota_report.json"
    try:
        with open(out_json, "w") as fh:
            json.dump(report, fh, indent=1)
    except OSError:
        pass

    print("=== SOTA differential report (AGD/MuNi quotient vs dense/BLAS) ===")
    print(f"configs={len(configs)}  cand_err_zero={summary['all_cand_err_zero']}  "
          f"no_fallback={summary['all_cand_no_fallback']}")
    print(f"noise floor (A/A cand): [{summary['min_noise_aa_cand']:.3f}, "
          f"{summary['max_noise_aa_cand']:.3f}]")
    print()
    hdr = ("d", "r", "steps", "cand_med", "struct_med", "blas_med", "naive_med",
           "x_struct", "x_blas", "x_naive", "AA", "drift%")
    print("{:>7} {:>5} {:>5} {:>10} {:>11} {:>11} {:>11} {:>9} {:>8} {:>8} {:>6} {:>7}".format(*hdr))
    for c in configs:
        P = c["paths"]
        def m(k): return f"{P[k]['median_ms']:.4f}" if P[k] else "-"
        def x(k):
            v = c.get(f"ratio_{k}_over_cand")
            return f"{v:.1f}" if v else "-"
        aa = f"{c['noise_aa_cand']:.3f}" if c["noise_aa_cand"] else "-"
        dr = f"{c['drift_struct_pct']:+.1f}" if c["drift_struct_pct"] is not None else "-"
        print("{:>7} {:>5} {:>5} {:>10} {:>11} {:>11} {:>11} {:>9} {:>8} {:>8} {:>6} {:>7}".format(
            c["d"], c["r"], c["steps"], m("cand"), m("struct"), m("blas"), m("naive"),
            x("struct"), x("blas"), x("naive"), aa, dr))
    print()
    print(f"wrote {out_json}")

if __name__ == "__main__":
    main()
