#!/usr/bin/env python3
"""Capture exact provenance so an independent reviewer can reproduce the speedups.

Reads the per-session receipts and records, in one artifact:
  - environment (CPU, cores, kernel, governor, toolchain versions)
  - the EXACT compiler flags used for baseline and candidate
  - workload dimensions
  - per-session BASELINE / CANDIDATE / REFERENCE raw wall-times (ms)
  - per-session speedups and the A/A noise floor
  - hashes of every source and binary in the run

BASELINE  = the exact operation being replaced: the full U (x) I_m operator apply.
CANDIDATE = the optimization: the quotient path.
REFERENCE = a genuine general dense d x d operator (independent of the structure).
"""
import glob
import hashlib
import json
import os
import platform
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(HERE, "receipts")


def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True,
                              text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def cpu_model():
    soc = sh("getprop ro.soc.model 2>/dev/null") or sh("getprop ro.board.platform 2>/dev/null")
    cores = sh("lscpu 2>/dev/null | awk -F: '/Model name/{print $2}' | sort -u | xargs")
    if soc or cores:
        return f"{soc} ({cores})".strip()
    for line in open("/proc/cpuinfo"):
        if line.lower().startswith("model name"):
            return line.split(":", 1)[1].strip()
    return platform.processor()


def governor():
    out = {}
    for p in glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"):
        try:
            out[p] = open(p).read().strip()
        except Exception:
            pass
    return sorted(set(out.values())) or ["(unavailable in PRoot)"]


def load(pattern):
    rows = []
    for f in sorted(glob.glob(os.path.join(REC, pattern))):
        with open(f) as fh:
            rows.append((os.path.basename(f), json.load(fh)))
    return rows


def main():
    flags = sys.argv[1] if len(sys.argv) > 1 else "(unknown)"
    sessions = load("session_[0-9]*.json")
    noise = load("noise_[0-9]*.json")
    stats = {}
    sf = os.path.join(REC, "session_stats.json")
    if os.path.exists(sf):
        stats = json.load(open(sf))

    dims = []
    if sessions:
        d0 = sessions[0][1]
        dims = {k: d0.get(k) for k in ("d", "m", "r", "steps", "trials", "reps")}

    prov = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {
            "uname": sh("uname -a"),
            "cpu_model": cpu_model(),
            "nproc": sh("nproc"),
            "governor": governor(),
            "kernel": platform.release(),
        },
        "toolchain": {
            "cc": sh("cc --version | head -1"),
            "lean": sh("lean --version"),
            "python": sys.version.split()[0],
            "compiler_flags": flags,
        },
        "workload_dimensions": dims,
        "definitions": {
            "BASELINE": "structured_ms: full U(x)I_m operator apply (exact op being replaced)",
            "CANDIDATE": "quotient_ms: quotient-descent optimized path",
            "REFERENCE": "dense_ms: general dense d x d operator (structure-independent)",
        },
        "per_session": [
            {
                "session": name,
                "structured_ms_BASELINE": r["structured_ms"],
                "quotient_ms_CANDIDATE": r["quotient_ms"],
                "dense_ms_REFERENCE": r["dense_ms"],
                "speedup_vs_structured": r["speedup_vs_structured"],
                "speedup_vs_dense": r["speedup_vs_dense"],
                "dense_vs_structured": r["dense_vs_structured"],
                "max_abs_error": r.get("max_abs_error"),
                "dense_abs_error": r.get("dense_abs_error"),
            }
            for name, r in sessions
        ],
        "aa_noise_sessions": [
            {"session": n, "noise_ratio": r["noise_ratio"]} for n, r in noise
        ],
        "aggregate": stats,
        "hashes": {
            os.path.relpath(p, HERE): sha256(p)
            for p in sorted(glob.glob(os.path.join(HERE, "src", "*"))
                            + glob.glob(os.path.join(HERE, "bin", "*")))
        },
    }

    with open(os.path.join(REC, "provenance.json"), "w") as fh:
        json.dump(prov, fh, indent=2)

    # human-readable summary
    lines = []
    lines.append("AGD / MUNI ELEVATION - PROVENANCE AND REPRODUCIBILITY RECEIPT")
    lines.append("=" * 68)
    lines.append(f"generated_at : {prov['generated_at']}")
    lines.append(f"uname        : {prov['host']['uname']}")
    lines.append(f"cpu_model    : {prov['host']['cpu_model']}")
    lines.append(f"nproc        : {prov['host']['nproc']}")
    lines.append(f"governor     : {prov['host']['governor']}")
    lines.append(f"cc           : {prov['toolchain']['cc']}")
    lines.append(f"lean         : {prov['toolchain']['lean']}")
    lines.append(f"python       : {prov['toolchain']['python']}")
    lines.append("")
    lines.append("COMPILER FLAGS (identical for baseline, candidate, reference):")
    lines.append(f"  {flags}")
    lines.append("")
    lines.append("WORKLOAD DIMENSIONS:")
    for k, v in (dims or {}).items():
        lines.append(f"  {k} = {v}")
    lines.append("")
    lines.append("PER-SESSION RAW WALL-TIMES (ms) AND SPEEDUPS")
    lines.append("  BASELINE  = structured_ms (original U(x)I_m operator)")
    lines.append("  CANDIDATE = quotient_ms   (optimized path)")
    lines.append("  REFERENCE = dense_ms      (general dense operator)")
    hdr = (f"  {'session':<14}{'base_ms':>10}{'cand_ms':>10}{'ref_ms':>11}"
           f"{'SvsBase':>10}{'SvsRef':>10}{'err':>6}")
    lines.append(hdr)
    for s in prov["per_session"]:
        lines.append(
            f"  {s['session']:<14}{s['structured_ms_BASELINE']:>10.4f}"
            f"{s['quotient_ms_CANDIDATE']:>10.5f}{s['dense_ms_REFERENCE']:>11.2f}"
            f"{s['speedup_vs_structured']:>10.2f}{s['speedup_vs_dense']:>10.1f}"
            f"{str(s['max_abs_error']):>6}")
    lines.append("")
    if stats:
        s1 = stats.get("speedup_vs_structured") or {}
        s2 = stats.get("speedup_vs_dense") or {}
        nf = stats.get("noise_floor_aa") or {}
        lines.append("AGGREGATE (median [min, max]):")
        lines.append(f"  speedup vs BASELINE : {s1.get('median')} [{s1.get('min')}, {s1.get('max')}]")
        lines.append(f"  speedup vs REFERENCE: {s2.get('median')} [{s2.get('min')}, {s2.get('max')}]")
        lines.append(f"  A/A noise floor     : median {nf.get('median')} max {nf.get('max')}")
    lines.append("")
    lines.append("HASHES (src/bin) - verbatim values in provenance.json")

    out = "\n".join(lines) + "\n"
    with open(os.path.join(REC, "provenance.txt"), "w") as fh:
        fh.write(out)
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
