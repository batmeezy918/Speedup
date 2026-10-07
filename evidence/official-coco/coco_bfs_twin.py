#!/usr/bin/env python3
import os,sys,json,hashlib,struct,time,platform
from pathlib import Path
import numpy as np
import cocoex
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from projected_s6_coco_harness import run_equivalence, capture_silicon_env

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
RUN=os.environ.get("RUN_ID","coco_bfs_twin_20261001")
OUT=ROOT/RUN
OUT.mkdir(parents=True,exist_ok=True)
TAPE=OUT/"game_tape.bin"
MANIFEST=OUT/"manifest.json"
SUMMARY=OUT/"summary.json"
DIM=int(os.environ.get("DIM","10"))
BUDGET=int(os.environ.get("BUDGET","1000"))
SEED=int(os.environ.get("SEED","20260810"))

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def write_header(f, problem_id, idx, mode, dim, budget):
    pid=problem_id.encode()
    f.write(struct.pack("<4sHHIHH",b"COCO",1,idx,mode,dim,budget))
    f.write(struct.pack("<I",len(pid))); f.write(pid)

def write_trace(f, problem_id, idx, mode, trace, dim):
    write_header(f,problem_id,idx,mode,dim,len(trace))
    for e in trace:
        x=np.asarray(e.get("state") or e.get("quotient_state"),dtype=np.float64)
        if len(x)!=dim: raise ValueError("dimension mismatch")
        f.write(struct.pack("<IBdddd",int(e["eval_idx"]),mode,float(e["f"]),
                             float(e["best_f"]),float(e.get("omega",0.0)),
                             float(e.get("xi",0.0))))
        f.write(x.astype("<f8",copy=False).tobytes(order="C"))

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def run():
    suite=cocoex.Suite("bbob","",f"dimensions: {DIM}")
    env=capture_silicon_env()
    rows=[]; eq_pass=inv_pass=rec_pass=obs_pass=0
    t0=time.perf_counter_ns()
    with open(TAPE,"wb") as tf:
        for idx,problem in enumerate(suite):
            eq=run_equivalence(problem,seed=SEED,budget=BUDGET)
            pid=getattr(problem,"id",f"problem_{idx}")
            write_trace(tf,pid,idx,0,eq["full"]["trace"],DIM)
            write_trace(tf,pid,idx,1,eq["quotient"]["trace"],DIM)
            g=eq["gates"]
            eq_pass += int(eq["equivalence_pass"])
            inv_pass += int(g["I_invariant"])
            rec_pass += int(g["R_reconstruction"])
            obs_pass += int(g["L_literal_observable"])
            rows.append({
                "index":idx,"problem_id":pid,
                "equivalence_pass":bool(eq["equivalence_pass"]),
                "invariant_pass":bool(g["I_invariant"]),
                "reconstruction_pass":bool(g["R_reconstruction"]),
                "observable_pass":bool(g["L_literal_observable"]),
                "f_diff":eq["f_diff"],"best_diff":eq["best_diff"],
                "full_wall_ns":eq["full"]["wall_time_ns"],
                "quotient_wall_ns":eq["quotient"]["wall_time_ns"],
                "full_evaluations":eq["full"]["evaluations"],
                "quotient_evaluations":eq["quotient"]["evaluations"]})
            if idx%10==0: print(f"{idx+1}/{len(suite)} {pid}",flush=True)
    elapsed=time.perf_counter_ns()-t0
    td=sha256_file(TAPE)
    total_full=sum(r["full_wall_ns"] for r in rows)
    total_q=sum(r["quotient_wall_ns"] for r in rows)
    manifest={
      "schema":"COCO-BFS-TWIN-1.0","run_id":RUN,"suite":"bbob","dimension":DIM,
      "budget":BUDGET,"seed":SEED,"problem_count":len(rows),
      "source_harness":str(ROOT/"projected_s6_coco_harness.py"),
      "mapping":{"Q":"Omega/Xi projection + representative state",
                 "R":"constructive reconstruction from quotient state",
                 "intertwining":"tested through executed trace",
                 "observable":"COCO objective and best objective",
                 "game_tape":"IEEE-754 binary64 little-endian state records"},
      "environment":env,"tape_sha256":td,"tape_bytes":TAPE.stat().st_size,
      "elapsed_ns":elapsed,
      "counts":{"equivalence_pass":eq_pass,"invariant_pass":inv_pass,
                "reconstruction_pass":rec_pass,"observable_pass":obs_pass},
      "timing":{"full_ns":total_full,"quotient_ns":total_q,
                "naive_timing_ratio":total_full/max(total_q,1)}}
    MANIFEST.write_text(json.dumps(manifest,indent=2))
    SUMMARY.write_text(json.dumps({"manifest":manifest,"rows":rows},indent=2))
    print(json.dumps(manifest,indent=2))
if __name__=="__main__":
    run()
from projected_s6_coco_harness import run_equivalence, capture_silicon_env