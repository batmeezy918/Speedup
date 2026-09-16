#!/usr/bin/env python3
"""PCSS Native Runner — canonical unified speedup runner.

Interface:
  python3 scripts/pcss_native_runner.py --scenario <manifest> --output <dir>
       [--lean-artifact <lean_verification_output.txt>]

The runner validates the manifest, hashes the scenario identity (canonical
bytes), fingerprints source and environment, runs warmups then baseline and
candidate, captures raw timing/output/resource information, calculates direct
speedup, hashes every artifact, and emits native evidence.

The runner must NOT manufacture Q, Q^-1, Omega, L: it delegates to the
engines for those and records their results. Only Lean evidence bound via
--lean-artifact gates L=true.

Legal gate promotions from the runner itself:
  I  = integrity/provenance    (runner binds all hashes)
  R  = reproducibility         (runner records environment + seeds)
  X  = performance             (runner measures wall-clock speedup)

All semantic/formal gates are produced by their respective engines
only when the engine's check actually passes.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import platform
import resource
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from publisher import evidence_lib  # noqa: E402
from engines.linear_exact import make_model, omega_vector, omega_matrix  # noqa: E402
from engines import quotient as QE  # noqa: E402
from engines import reconstruction as RE  # noqa: E402
from engines import invariant as IE  # noqa: E402
from engines import performance as PE  # noqa: E402
from engines import attribution as AT  # noqa: E402
from engines import discovery as DIS  # noqa: E402
from engines import refinement as REF  # noqa: E402

import hashlib


# ---------------------------------------------------------------------------
# environment / source hashing
# ---------------------------------------------------------------------------

def source_hash(root: pathlib.Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*.py")):
        if ".git" in str(p):
            continue
        h.update(str(p.relative_to(root)).encode())
        h.update(p.read_bytes())
    for p in sorted(root.rglob("*.lean")):
        if ".git" in str(p):
            continue
        h.update(str(p.relative_to(root)).encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def environment_dict() -> dict:
    return {
        "os": platform.platform(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "hostname": platform.node(),
        "pid": os.getpid(),
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def sha256_file(p: pathlib.Path) -> str:
    return evidence_lib.sha256_file(p)


# ---------------------------------------------------------------------------
# trace capture
# ---------------------------------------------------------------------------

class Capture:
    """Simple resource capture per execution phase."""

    def __init__(self):
        self.times_ns: list[float] = []
        self.stdout = ""
        self.mem_peak_bytes = 0

    def time_block(self, fn) -> dict:
        t0 = evidence_lib.percentile([1.0])  # warm up; not used
        t0 = time.clock_gettime(time.CLOCK_MONOTONIC) if hasattr(time, 'clock_gettime') else time.perf_counter()
        out = fn()
        t1 = time.clock_gettime(time.CLOCK_MONOTONIC) if hasattr(time, 'clock_gettime') else time.perf_counter()
        elapsed = (t1 - t0) * 1e9
        self.times_ns.append(elapsed)
        return {"stdout": str(out) if out is not None else "", "elapsed_ns": elapsed}


def percentile(values, p):
    return evidence_lib.percentile(values, p)


def measure_trajectory(fn, *, repeats, warmups) -> dict:
    timings = []
    for _ in range(repeats + warmups):
        t0 = time.clock_gettime(time.CLOCK_MONOTONIC)
        fn()
        t1 = time.clock_gettime(time.CLOCK_MONOTONIC)
        if _ >= warmups:
            timings.append((t1 - t0) * 1e9)
    if not timings:
        return {"median": 0, "mean": 0, "p95": 0, "p99": 0, "min": 0, "max": 0,
                "samples": 0, "unit": "ns", "timings_ns": []}
    return {
        "median": evidence_lib.median(timings),
        "mean": sum(timings) / len(timings),
        "p95": evidence_lib.percentile(timings, 0.95),
        "p99": evidence_lib.percentile(timings, 0.99),
        "min": min(timings),
        "max": max(timings),
        "samples": len(timings),
        "unit": "ns",
        "timings_ns": timings,
    }


# ---------------------------------------------------------------------------
# runner core
# ---------------------------------------------------------------------------

def load_scenario(scenario_path: pathlib.Path) -> dict:
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    evidence_lib.validate_scenario_against_schema(scenario)
    return scenario


def run_native(scenario: dict, out_dir: pathlib.Path,
               lean_artifact_path: pathlib.Path | None = None,
               source_root: pathlib.Path | None = None) -> dict:
    """Execute full pipeline, write artifacts to out_dir, return draft certificate."""
    out_dir.mkdir(parents=True, exist_ok=True)
    source_root = source_root or ROOT

    # canonical scenario + hash
    scenario_canon = evidence_lib.canonicalize_scenario(scenario)
    scen_sha = evidence_lib.sha256_json(scenario_canon)
    (out_dir / "scenario.json").write_text(json.dumps(scenario_canon, indent=2) + "\n", encoding="utf-8")

    # source + environment
    src_sha = source_hash(source_root)
    env_dict = environment_dict()
    env_sha = evidence_lib.sha256_json(env_dict)
    (out_dir / "source_sha256.txt").write_text(src_sha + "\n", encoding="utf-8")
    (out_dir / "environment.json").write_text(json.dumps(env_dict, indent=2) + "\n", encoding="utf-8")

    # input hash (deterministic seed state)
    seed = scenario.get("seed", 0)
    input_sha = evidence_lib.sha256_bytes(f"seed={seed}".encode())
    (out_dir / "input_sha256.txt").write_text(input_sha + "\n", encoding="utf-8")

    # build model
    model = make_model(scenario)
    nsteps = scenario.get("parameters", {}).get("steps", 4)
    tile = scenario.get("dimensions", {}).get("tile", getattr(model, "tile", 32))
    model_model = scenario.get("parameters", {}).get("model", "vector")
    is_matrix = model_model == "matrix"

    # base state (block-constant)
    x0 = model.make_initial(seed=seed)
    x0_list = x0 if isinstance(x0, list) else [float(v) for row in x0 for v in row]

    # -- QUOTIENT ENGINE (trajectory-level forward preservation) --
    base_traj = [x0_list]
    cand_traj_q = [model.pi(x0_list)]
    base_traj_full = [x0_list]
    cand_traj_full = [model.sigma(model.pi(x0_list))]
    for _ in range(nsteps):
        xb = base_traj[-1]
        xb_next = model.T_full(xb)
        base_traj.append(xb_next)
        base_traj_full.append(xb_next)
        qb_next = model.Tbar(cand_traj_q[-1])
        cand_traj_q.append(qb_next)
        cand_traj_full.append(model.sigma(qb_next))
    quotient_ev = QE.run_quotient(model.pi, base_traj_full, cand_traj_q,
                                  T=model.T_full, Tbar=model.Tbar,
                                  candidate_projection=lambda q: q,
                                  relation=scenario.get("quotient", {}).get("relation", "exact"),
                                  tolerance=scenario.get("quotient", {}).get("tolerance", 0.0))

    # write traces (baseline_trace as raw list of lists or lists; candidate_trace same)
    trace_baseline = base_traj_full
    trace_candidate = cand_traj_full
    (out_dir / "baseline_trace.json").write_text(
        json.dumps({"trace": trace_baseline}, indent=2) + "\n", encoding="utf-8")
    (out_dir / "candidate_trace.json").write_text(
        json.dumps({"trace": trace_candidate}, indent=2) + "\n", encoding="utf-8")
    baseline_trace_sha = sha256_file(out_dir / "baseline_trace.json")
    candidate_trace_sha = sha256_file(out_dir / "candidate_trace.json")
    (out_dir / "quotient_evidence.json").write_text(json.dumps(quotient_ev, indent=2) + "\n", encoding="utf-8")

    # -- RECONSTRUCTION ENGINE --
    recon_ev = RE.run_reconstruction(
        base_traj_full, lambda e: model.sigma(model.pi(e)),
        tolerance=scenario.get("reconstruction", {}).get("tolerance", 0.0),
        metric=scenario.get("reconstruction", {}).get("metric", "max"))
    (out_dir / "reconstruction_evidence.json").write_text(json.dumps(recon_ev, indent=2) + "\n", encoding="utf-8")

    # -- INVARIANT ENGINE --
    inv_fn = omega_matrix if is_matrix else omega_vector
    inv_ev = IE.run_invariant(base_traj_full, cand_traj_full, inv_fn,
                              relation=scenario.get("invariant", {}).get("relation", "exact"),
                              tolerance=scenario.get("invariant", {}).get("tolerance", 0.0))
    (out_dir / "invariant_evidence.json").write_text(json.dumps(inv_ev, indent=2) + "\n", encoding="utf-8")

    # -- PERFORMANCE ENGINE --
    repeats = scenario.get("repetitions", 30)
    warmups = scenario.get("warmups", 0)
    def run_full_vector():
        x = list(x0_list)
        for _ in range(nsteps):
            x = model.T_full(x)
        return x
    def run_candidate_native():
        q = model.pi(x0_list)
        for _ in range(nsteps):
            q = model.Tbar(q)
        return model.sigma(q)
    perf_ev = PE.run_performance(run_full_vector, run_candidate_native,
                                 repetitions=repeats, warmups=warmups)
    perf_sha = evidence_lib.sha256_json(perf_ev)
    (out_dir / "performance_evidence.json").write_text(json.dumps(perf_ev, indent=2) + "\n", encoding="utf-8")

    # -- ATTRIBUTION --
    d = scenario.get("dimensions", {})
    baseline_ops = nsteps * (d.get("d", model.d if hasattr(model, 'd') else len(x0_list)))
    candidate_ops = nsteps * (d.get("r", model.r if hasattr(model, 'r') else len(model.pi(x0_list))))
    recon_ops = len(x0_list)
    construction_ops = 0
    attribution = AT.analyze(
        baseline_ops=baseline_ops, candidate_ops=candidate_ops,
        measured_speedup=perf_ev["direct_speedup"],
        quotient_cost=0.0, reconstruction_cost=float(recon_ops),
        wall_clock_baseline=perf_ev["baseline_measurement"]["median"],
        wall_clock_candidate=perf_ev["candidate_measurement"]["median"],
        note="operation count ratio vs wall-clock speedup reported separately; never conflated")
    (out_dir / "attribution.json").write_text(json.dumps(attribution, indent=2) + "\n", encoding="utf-8")

    # -- discovery reference run --
    disc_ev = DIS.discover(scenario, model)
    (out_dir / "discovery_evidence.json").write_text(json.dumps(disc_ev, indent=2) + "\n", encoding="utf-8")
    ref_classes = disc_ev.get("equivalence_classes", [])
    ref_ev = []
    if ref_classes:
        ref_classes_final, ref_journal = REF.refine(ref_classes, None, model, model.pi, model.T_full, model.Tbar)
        ref_ev = ref_journal
    (out_dir / "refinement_evidence.json").write_text(json.dumps(ref_ev, indent=2) + "\n", encoding="utf-8")

    # -- GATE RESULTS --
    # gates exercised by the runner itself + engine results
    lean_gate_value = False
    lean_evidence = []
    if lean_artifact_path and lean_artifact_path.is_file():
        lean_text = lean_artifact_path.read_text(encoding="utf-8", errors="replace")
        import re
        if "LEAN4_CORE_ALL_PASS=1" in lean_text or "LEAN4_MATHLIB_ALL_PASS=1" in lean_text:
            lean_gate_value = True
            lean_evidence = [lean_artifact_path.as_posix()]

    gate_results = {
        "integrity": evidence_lib.gate_pass(
            ["scenario.json", "environment.json", "source_sha256.txt",
             "input_sha256.txt", "baseline_trace.json", "candidate_trace.json"],
            detail={"scenario_hash": scen_sha, "source_hash": src_sha,
                    "environment_hash": env_sha, "input_hash": input_sha}),
        "reproducibility": evidence_lib.gate_pass(
            ["scenario.json", "environment.json"]),
        "quotient_forward": evidence_lib.gate_pass(
            ["quotient_evidence.json"]) if quotient_ev.get("pass") else evidence_lib.gate_fail(
            ["quotient_evidence.json"], detail={"reason": quotient_ev.get("reason")}),
        "reconstruction_reverse": evidence_lib.gate_pass(
            ["reconstruction_evidence.json"]) if recon_ev.get("pass") else evidence_lib.gate_fail(
            ["reconstruction_evidence.json"], detail={"reason": recon_ev.get("reason")}),
        "invariants": evidence_lib.gate_pass(
            ["invariant_evidence.json"]) if inv_ev.get("pass") else evidence_lib.gate_fail(
            ["invariant_evidence.json"], detail={"reason": inv_ev.get("reason")}),
        "performance": evidence_lib.gate_pass(
            ["performance_evidence.json", "attribution.json"]) if perf_ev.get("pass") else evidence_lib.gate_fail(
            ["performance_evidence.json", "attribution.json"], detail={"reason": perf_ev.get("reason")}),
        "lean": evidence_lib.gate_result(lean_gate_value, lean_evidence),
    }

    # artifact refs
    artifact_refs = {
        "scenario": {"path": "scenario.json", "sha256": scen_sha},
        "source": {"path": "source_sha256.txt", "sha256": src_sha},
        "input": {"path": "input_sha256.txt", "sha256": input_sha},
        "environment": {"path": "environment.json", "sha256": env_sha},
        "baseline_trace": {"path": "baseline_trace.json", "sha256": baseline_trace_sha},
        "candidate_trace": {"path": "candidate_trace.json", "sha256": candidate_trace_sha},
        "quotient": {"path": "quotient_evidence.json", "sha256": evidence_lib.sha256_file(out_dir / "quotient_evidence.json")},
        "reconstruction": {"path": "reconstruction_evidence.json", "sha256": evidence_lib.sha256_file(out_dir / "reconstruction_evidence.json")},
        "invariant": {"path": "invariant_evidence.json", "sha256": evidence_lib.sha256_file(out_dir / "invariant_evidence.json")},
        "performance": {"path": "performance_evidence.json", "sha256": perf_sha},
    }
    if lean_gate_value and lean_artifact_path:
        artifact_refs["lean"] = {
            "path": lean_artifact_path.name,
            "sha256": evidence_lib.sha256_file(lean_artifact_path),
        }
    else:
        artifact_refs["lean"] = {
            "path": lean_artifact_path.name if lean_artifact_path else "",
            "sha256": "",
        }

    # build and sign
    cert = evidence_lib.build_certificate(
        run_id=f"pcss-run-{int(time.time())}",
        scenario=scenario_canon,
        scenario_sha=scen_sha,
        source_sha=src_sha,
        input_sha=input_sha,
        env_sha=env_sha,
        baseline_trace_sha=baseline_trace_sha,
        candidate_trace_sha=candidate_trace_sha,
        gate_results=gate_results,
        speedup=perf_ev["direct_speedup"],
        baseline_measurement=perf_ev["baseline_measurement"],
        candidate_measurement=perf_ev["candidate_measurement"],
        metric=scenario.get("metric", "wall_clock_ns"),
        repetitions=repeats,
        warmups=warmups,
        seed=seed,
        tolerance=scenario.get("quotient", {}).get("tolerance", 0.0),
        toolchain={"python": platform.python_version(), "arch": platform.machine(),
                   "scenario_toolchain": scenario.get("environment", {})},
        implementation_identity={"baseline": scenario.get("baseline", {}),
                                 "candidate": scenario.get("candidate", {})},
        parameters=scenario.get("parameters", {}),
        claim_boundary={
            "quantity_measured": "direct wall-clock speedup of exact-invariant-sector step",
            "domain_covered": f"d={d.get('d', '?')}, r={d.get('r', '?')}, tile={tile}, steps={nsteps}",
            "excluded": ["universal speedup", "HPC dominance", "operation-count equality",
                         "asymptotic complexity", "mathematical novelty"],
        },
        artifact_refs=artifact_refs,
        attribution=attribution,
    )
    cert = evidence_lib.sign_certificate(cert)
    (out_dir / "native_evidence.json").write_text(json.dumps(cert, indent=2) + "\n", encoding="utf-8")

    # SHA256SUMS
    sums = []
    for p in sorted(out_dir.iterdir()):
        if p.name == "SHA256SUMS.txt":
            continue
        sums.append(f"{sha256_file(p)}  {p.name}")
    (out_dir / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")

    return cert


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PCSS canonical native runner")
    ap.add_argument("--scenario", required=True, help="path to scenario manifest JSON")
    ap.add_argument("--output", required=True, help="artifact output directory")
    ap.add_argument("--lean-artifact", default=None, help="path to Lean verification output (scripts/verify_lean4_all.sh output)")
    ap.add_argument("--source-root", default=None, help="source tree root for hashing")
    args = ap.parse_args(argv)

    scenario = load_scenario(pathlib.Path(args.scenario))
    out = run_native(scenario, pathlib.Path(args.output),
                     lean_artifact_path=pathlib.Path(args.lean_artifact) if args.lean_artifact else None,
                     source_root=pathlib.Path(args.source_root) if args.source_root else None)

    gr = out.get("gate_results", {})
    all_pass = all(gr.get(g, {}).get("value") is True for g in
                   ("integrity", "reproducibility", "quotient_forward",
                    "reconstruction_reverse", "invariants", "performance"))
    print(f"runner complete: scenario_hash={out.get('scenario_hash')[:16]}...")
    print(f"speedup={out.get('speedup'):.4f}x  semantic_pass={all_pass}  lean={'true' if gr.get('lean', {}).get('value') else 'false'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())