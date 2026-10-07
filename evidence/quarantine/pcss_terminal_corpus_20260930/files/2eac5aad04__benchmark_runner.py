#!/usr/bin/env python3 -u
"""Benchmark the orchestrator across configurations."""
import subprocess, os, sys, json, time, statistics
from pathlib import Path
from datetime import datetime, timezone

CONFIGS = [
    {"threads": 1, "bound": 128.0, "label": "single_thread"},
    {"threads": max(1, (os.cpu_count() or 2) - 1), "bound": 128.0, "label": "multi_thread"},
    {"threads": max(1, (os.cpu_count() or 2) - 1), "bound": 64.0,  "label": "bound64"},
    {"threads": max(1, (os.cpu_count() or 2) - 1), "bound": 256.0, "label": "bound256"},
]
REPEATS = 3

def run_config(threads, bound, label, repeat):
    results = []
    for i in range(repeat):
        env = os.environ.copy()
        env["STABLE_THREADS"] = str(threads)
        env["COMPRESSION_BOUND"] = str(bound)
        start = time.time()
        proc = subprocess.run(
            ["python3", "-u", "/root/agd_orchestrator_v7.py"],
            env=env,
            capture_output=True,
            text=True
        )
        dur = time.time() - start
        fp = "none"
        for line in proc.stdout.splitlines():
            if "FINGERPRINT=" in line:
                fp = line.split("FINGERPRINT=")[-1].strip()
        success = "BUILD_SUCCESS=True" in proc.stdout
        results.append({
            "run": i+1,
            "time": dur,
            "success": success,
            "fingerprint": fp,
            "stdout": proc.stdout,
            "stderr": proc.stderr
        })
    return results

def main():
    print("="*70)
    print("AGD BENCHMARK SUITE")
    print(f"Configs: {len(CONFIGS)}, Repeats: {REPEATS}")
    print("="*70)
    summary = []
    for cfg in CONFIGS:
        label = cfg["label"]
        t = cfg["threads"]
        b = cfg["bound"]
        print(f"\n--- Running config: {label} (threads={t}, bound={b}) ---")
        res = run_config(t, b, label, REPEATS)
        times = [r["time"] for r in res]
        successes = [r["success"] for r in res]
        fps = [r["fingerprint"] for r in res if r["fingerprint"] != "none"]
        entry = {
            "label": label,
            "threads": t,
            "compression_bound": b,
            "repeats": REPEATS,
            "time_stats": {
                "min": min(times),
                "max": max(times),
                "mean": statistics.mean(times),
                "median": statistics.median(times),
                "std": statistics.stdev(times) if len(times) > 1 else 0.0,
            },
            "success_count": sum(successes),
            "fingerprints": fps,
            "deterministic": len(set(fps)) == 1 if fps else False,
            "individual_runs": res
        }
        summary.append(entry)
        print(f"  OK: {entry['success_count']}/{REPEATS}, avg time: {entry['time_stats']['mean']:.2f}s")
        print(f"  Fingerprints: {', '.join(fps[:3])}")
    report_path = Path.cwd() / "benchmark_report.json"
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "configs": summary
    }
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\nReport saved to {report_path}")
    print("\n"+"="*70)
    print("SUMMARY TABLE")
    print(f"{'Label':<20} {'Success':<10} {'Median(s)':<12} {'Deterministic':<15}")
    for e in summary:
        det = "✅" if e["deterministic"] and e["success_count"] == REPEATS else "❌"
        print(f"{e['label']:<20} {e['success_count']}/{REPEATS:<6} {e['time_stats']['median']:<12.2f} {det}")
    print("="*70)

if __name__ == "__main__":
    main()
