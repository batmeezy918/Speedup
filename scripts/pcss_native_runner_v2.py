#!/usr/bin/env python3
"""PCSS native runner v2: locked source/input identity + direct timing only.

The generated certificate is intentionally not publishable. It contains no
inferred quotient, reconstruction, invariant, attribution, or Lean proof.
Those gates must be closed by independent artifacts and then evaluated by
publisher/strict_gate.py.
"""
from __future__ import annotations
import argparse, hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path
from statistics import median


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_paths(paths: list[Path], root: Path) -> tuple[str, dict[str, str]]:
    items = {}
    for p in paths:
        p = p.resolve()
        if not p.is_file():
            raise FileNotFoundError(p)
        rel = str(p.relative_to(root.resolve())) if p.is_relative_to(root.resolve()) else str(p)
        items[rel] = sha256(p.read_bytes())
    blob = json.dumps(items, sort_keys=True, separators=(",", ":")).encode()
    return sha256(blob), items


def run(command: str, cwd: Path) -> dict:
    t0 = time.perf_counter_ns()
    p = subprocess.run(command, shell=True, cwd=cwd, capture_output=True)
    t1 = time.perf_counter_ns()
    return {"command": command, "exit_code": p.returncode, "wall_ns": t1-t0,
            "stdout_sha256": sha256(p.stdout), "stderr_sha256": sha256(p.stderr),
            "stdout_bytes": len(p.stdout), "stderr_bytes": len(p.stderr)}


def deterministic(rows: list[dict]) -> bool:
    return len({(r["exit_code"], r["stdout_sha256"], r["stderr_sha256"]) for r in rows}) == 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--source", action="append", required=True, help="source file; repeat for multiple files")
    ap.add_argument("--input", action="append", required=True, help="input file; repeat for multiple files")
    ap.add_argument("--scenario-id", required=True)
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--out", default="pcss-native-run-v2")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--warmups", type=int, default=1)
    args = ap.parse_args()
    if args.repeats < 1 or args.warmups < 0:
        ap.error("repeats must be >= 1 and warmups >= 0")
    root = Path(args.workdir).resolve()
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    source_hash, source_manifest = hash_paths([Path(x) for x in args.source], root)
    input_hash, input_manifest = hash_paths([Path(x) for x in args.input], root)
    scenario = {"scenario_id":args.scenario_id,"baseline_command":args.baseline,"candidate_command":args.candidate,
                "source_hash":source_hash,"input_hash":input_hash,"source_manifest":source_manifest,
                "input_manifest":input_manifest,"workdir":str(root),"repeats":args.repeats,
                "warmups":args.warmups,"timing_source":"perf_counter_ns","shell":True}
    scenario_blob = json.dumps(scenario, sort_keys=True, separators=(",", ":")).encode()
    scenario_hash = sha256(scenario_blob); (out/"scenario.json").write_bytes(scenario_blob+b"\n")
    env = {"platform":platform.platform(),"python":sys.version,"machine":platform.machine(),
           "processor":platform.processor(),"hostname":platform.node(),"cwd":str(root),
           "git_revision":os.popen("git rev-parse HEAD 2>/dev/null").read().strip(),
           "git_status":os.popen("git status --porcelain 2>/dev/null").read()}
    env_blob=json.dumps(env,sort_keys=True,separators=(",",":")).encode(); env_hash=sha256(env_blob)
    (out/"environment.json").write_bytes(env_blob+b"\n")
    warmups=[]
    for label,cmd in (("baseline",args.baseline),("candidate",args.candidate)):
        for i in range(args.warmups): warmups.append({"implementation":label,"index":i,**run(cmd,root)})
    rows=[]
    for label,cmd in (("baseline",args.baseline),("candidate",args.candidate)):
        for i in range(args.repeats): rows.append({"implementation":label,"index":i,**run(cmd,root)})
    trace={"warmups":warmups,"runs":rows}; trace_blob=json.dumps(trace,sort_keys=True,separators=(",",":")).encode()
    trace_hash=sha256(trace_blob); (out/"trace.json").write_bytes(trace_blob+b"\n")
    base=[r["wall_ns"] for r in rows if r["implementation"]=="baseline"]; cand=[r["wall_ns"] for r in rows if r["implementation"]=="candidate"]
    perf={"metric":"wall_ns","samples":args.repeats,"baseline_samples":base,"candidate_samples":cand,
          "median_baseline":median(base),"median_candidate":median(cand),
          "speedup_measured":median(base)/median(cand),
          "baseline_deterministic":deterministic([r for r in rows if r["implementation"]=="baseline"]),
          "candidate_deterministic":deterministic([r for r in rows if r["implementation"]=="candidate"]),
          "all_exit_zero":all(r["exit_code"]==0 for r in rows)}
    perf_blob=json.dumps(perf,sort_keys=True,separators=(",",":")).encode(); perf_hash=sha256(perf_blob); (out/"performance.json").write_bytes(perf_blob+b"\n")
    cert={"run_id":args.scenario_id,"scenario_hash":scenario_hash,"source_hash":source_hash,"input_hash":input_hash,
          "environment_hash":env_hash,"trace_hash":trace_hash,"performance_hash":perf_hash,
          "quotient_hash":None,"reverse_hash":None,"invariants_hash":None,"attribution_hash":None,"proof_hash":None,
          "artifacts":{"scenario.json":scenario_hash,"environment.json":env_hash,"trace.json":trace_hash,"performance.json":perf_hash},
          "performance":perf,
          "gates":{"integrity":False,"reproducibility":perf["baseline_deterministic"] and perf["candidate_deterministic"],
                   "quotient_forward":False,"reconstruction_reverse":False,"invariants":False,"performance":perf["all_exit_zero"],"lean":False},
          "claim_strength":"STRONG_LOCAL","evidence_strength":"STRONG_LOCAL","status":"NATIVE_RUN_ONLY"}
    (out/"certificate.json").write_text(json.dumps(cert,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"NATIVE_RUN_ONLY","scenario_hash":scenario_hash,"source_hash":source_hash,"input_hash":input_hash,
                      "speedup_measured":perf["speedup_measured"],"out":str(out)},indent=2))
    return 0 if perf["all_exit_zero"] else 1

if __name__ == "__main__": raise SystemExit(main())
