"""PCSS canonical native runner.

Pipeline executed for each primitive:
    scenario manifest -> canonical scenario identity -> environment fingerprint
    -> warmups -> baseline repetitions -> candidate repetitions
    -> raw timing + output + resource capture -> direct speedup
    -> hash every artifact -> native evidence certificate

This runner NEVER manufactures quotient (Q), reconstruction (Q^-1),
invariant (Omega) or formal (L) evidence.  Timing is timing.  Semantic
evidence is semantic evidence.  Formal proof is formal proof.
"""
from __future__ import annotations

import json
import math
import os
import resource
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from . import scenario as scenario_mod
from .environment import capture_environment
from .jsonutil import sha256, sha256_file


class RunnerError(RuntimeError):
    pass


@dataclass
class RunResult:
    elapsed_ns: int
    stdout: str
    peak_rss_kb: int
    exit_code: int


def _read_peak_rss(pid: int) -> int:
    try:
        with open(f"/proc/{pid}/status", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmHWM:"):
                    return int(line.split()[1])
    except Exception:
        pass
    return 0


def run_command_checked(cmd: List[str], cwd: str, timeout_s: float) -> RunResult:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise RunnerError(f"command timed out after {timeout_s:.1f}s: {cmd}") from None
    return RunResult(
        elapsed_ns=0,
        stdout=proc.stdout,
        peak_rss_kb=_read_peak_rss(proc.pid),
        exit_code=proc.returncode,
    )


def run_and_time(
    cmd: List[str],
    cwd: str,
    warmup: bool = False,
    timeout_s: float = 120.0,
) -> RunResult:
    """Run a command once, wall-clock timed, capturing stdout and peak RSS."""
    start = time.perf_counter_ns()
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    elapsed = time.perf_counter_ns() - start
    return RunResult(
        elapsed_ns=elapsed,
        stdout=proc.stdout,
        peak_rss_kb=_read_peak_rss(proc.pid),
        exit_code=proc.returncode,
    )


def resolve_command(template: str, params: Dict[str, Any]) -> List[str]:
    """Substitute {d} {seed} {r} {N} placeholders into a command template."""
    parts = template.split()
    out = []
    for part in parts:
        for key in ("d", "seed", "r", "N"):
            if f"{{{key}}}" in part:
                part = part.replace(f"{{{key}}}", str(params.get(key, "")))
        if part:
            out.append(part)
    return out


def median(values: List[float]) -> float:
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0


def summarize(samples_ns: List[int]) -> Dict[str, float]:
    samples_s = [v / 1e9 for v in samples_ns]
    mean = sum(samples_s) / len(samples_s)
    variance = sum((v - mean) ** 2 for v in samples_s) / len(samples_s)
    return {
        "median_s": median(samples_s),
        "mean_s": mean,
        "std_s": math.sqrt(variance),
        "min_s": min(samples_s),
        "max_s": max(samples_s),
        "samples": len(samples_s),
    }


def run_native(
    repo_root: str,
    manifest: Dict[str, Any],
    output_dir: str,
    timeout_s: float = 120.0,
) -> Dict[str, Any]:
    """Execute warmups + repetitions for baseline and candidate.

    Returns a native evidence object with hashes.  Does not set any of the
    semantic gates (Q, Q^-1, Omega, L).
    """
    canonical, sc_hash = scenario_mod.canonicalize_manifest(manifest), scenario_mod.scenario_hash(
        manifest
    )
    scenario_mod.validate_manifest(manifest)

    params = dict(manifest.get("parameters", {}))
    dims = manifest.get("dimensions", {})
    params.update({k: v for k, v in dims.items() if v is not None})
    params.setdefault("seed", manifest.get("seed"))

    if params.get("seed") is None:
        params["seed"] = 0

    repetitions = int(manifest["repetitions"])
    warmups = int(manifest["warmups"])

    env = capture_environment()

    run_id = f"run_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}_{sc_hash[:8]}"

    out = Path(output_dir)
    trace_dir = out / "traces"
    trace_dir.mkdir(parents=True, exist_ok=True)

    # Source fingerprint: scenario manifest + workload command sources.
    source_payload = {"scenario": canonical, "commands": {
        "baseline": manifest["baseline"]["command"],
        "candidate": manifest["candidate"]["command"],
    }}
    source_hash = sha256(source_payload)
    input_hash = sha256(params)

    def run_series(command_template: str, name: str) -> List[RunResult]:
        results: List[RunResult] = []
        for idx in range(warmups + repetitions):
            cmd = resolve_command(command_template, params)
            res = run_and_time(cmd, cwd=repo_root, timeout_s=timeout_s)
            if res.exit_code != 0:
                raise RunnerError(
                    f"{name} step {idx} failed (exit={res.exit_code}): " + res.stdout[-1000:]
                )
            tfile = trace_dir / f"{name}_{idx:04d}.txt"
            tfile.write_text(res.stdout, encoding="utf-8")
            results.append(res)
        return results

    base_raw = run_series(manifest["baseline"]["command"], "baseline")
    cand_raw = run_series(manifest["candidate"]["command"], "candidate")

    # split warmups out of the timed samples
    base_samples = [r.elapsed_ns for r in base_raw[warmups:]]
    cand_samples = [r.elapsed_ns for r in cand_raw[warmups:]]

    base_summary = summarize(base_samples)
    cand_summary = summarize(cand_samples)

    direct_speedup = None
    if cand_summary["median_s"] > 0:
        direct_speedup = base_summary["median_s"] / cand_summary["median_s"]

    # hash raw trace artifacts
    trace_files_b = sorted(trace_dir.glob("baseline_*.txt"))
    trace_files_c = sorted(trace_dir.glob("candidate_*.txt"))
    baseline_trace_hash = sha256("".join(sha256_file(str(p)) for p in trace_files_b))
    candidate_trace_hash = sha256("".join(sha256_file(str(p)) for p in trace_files_c))

    evidence = {
        "schema_version": "1.0",
        "evidence_class": "NATIVE_EVIDENCE",
        "run_id": run_id,
        "scenario_id": manifest["scenario_id"],
        "scenario_hash": sc_hash,
        "source_hash": source_hash,
        "input_hash": input_hash,
        "environment_hash": env["environment_hash"],
        "baseline_trace_hash": baseline_trace_hash,
        "candidate_trace_hash": candidate_trace_hash,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "toolchain": {"python": env["python"], "platform": env["platform"]},
        "implementation_identity": {
            "baseline": manifest["baseline"]["implementation"],
            "candidate": manifest["candidate"]["implementation"],
        },
        "parameters": params,
        "seed": params["seed"],
        "repetitions": repetitions,
        "warmups": warmups,
        "timing_source": manifest["timing_source"],
        "baseline_measurement": base_summary,
        "candidate_measurement": cand_summary,
        "direct_speedup": direct_speedup,
        "uncertainty": {
            "treatment": "median-based ratio with std spread",
            "baseline_std_s": base_summary["std_s"],
            "candidate_std_s": cand_summary["std_s"],
        },
        "environment": env,
        "claim_strength": "CANDIDATE",
        "claim_boundary": "native wall-clock timing only; no semantic equivalence asserted",
        "gates": {},  # semantic gates are filled ONLY by the corresponding engines/publisher
        "artifact_paths": [
            {"path": str(trace_dir.relative_to(out)) + "/", "sha256": "dir"}
        ],
    }

    # hash each measured sample sequence into the evidence so the certificate
    # can later re-derive the direct speedup independently.
    evidence["raw_sample_ns"] = {"baseline": base_samples, "candidate": cand_samples}
    evidence_hash = sha256(evidence)
    evidence["evidence_hash"] = evidence_hash

    (out / "native_evidence.json").write_text(
        json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="PCSS native runner")
    ap.add_argument("--scenario", required=True, help="scenario manifest JSON")
    ap.add_argument("--output", required=True, help="output artifact directory")
    ap.add_argument("--timeout", type=float, default=120.0)
    args = ap.parse_args(argv)

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest = scenario_mod.load_manifest(args.scenario)
    scenario_mod.validate_manifest(manifest)
    run_native(repo_root, manifest, args.output, timeout_s=args.timeout)
    print(f"native evidence written to {args.output}/native_evidence.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())