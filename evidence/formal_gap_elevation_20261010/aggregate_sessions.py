#!/usr/bin/env python3
"""Aggregate independent sessions into between-session statistics + noise floor.

Reads receipts/session_*.json (bench: structured/dense/quotient) and
receipts/noise_*.json (A/A: quotient vs quotient). Reports, for each ratio,
the between-session median, min, max, and the A/A noise floor (median and
half-spread), so a reader can see whether a claimed speedup exceeds the floor.
"""
import glob
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(HERE, "receipts")


def load(pattern):
    out = []
    for f in sorted(glob.glob(os.path.join(REC, pattern))):
        try:
            with open(f) as fh:
                out.append((os.path.basename(f), json.load(fh)))
        except Exception as e:  # noqa
            print(f"skip {f}: {e}", file=sys.stderr)
    return out


def stats(xs):
    if not xs:
        return None
    xs = sorted(xs)
    return {
        "n": len(xs),
        "median": statistics.median(xs),
        "min": xs[0],
        "max": xs[-1],
        "p25": xs[len(xs) // 4],
        "p75": xs[(3 * len(xs)) // 4],
    }


def main():
    sessions = load("session_[0-9]*.json")
    noise = load("noise_[0-9]*.json")
    if not sessions:
        print("no sessions found", file=sys.stderr)
        return 1

    s_struct = [d["speedup_vs_structured"] for _, d in sessions]
    s_dense = [d["speedup_vs_dense"] for _, d in sessions]
    d_vs_s = [d["dense_vs_structured"] for _, d in sessions]
    n_ratio = [d["noise_ratio"] for _, d in noise]

    result = {
        "sessions": len(sessions),
        "noise_sessions": len(noise),
        "speedup_vs_structured": stats(s_struct),
        "speedup_vs_dense": stats(s_dense),
        "dense_vs_structured": stats(d_vs_s),
        "noise_floor_aa": stats(n_ratio),
    }
    print(json.dumps(result, indent=2))

    if result["noise_floor_aa"]:
        nf = result["noise_floor_aa"]
        floor = abs(nf["max"] - 1.0) if nf["max"] > 1 else abs(1.0 - nf["min"])
        print(f"\nA/A noise floor (max |ratio-1|): {floor:.4f} "
              f"({floor*100:.2f}% dispersion on a null difference)")
    with open(os.path.join(REC, "session_stats.json"), "w") as fh:
        json.dump(result, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
