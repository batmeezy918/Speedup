#!/usr/bin/env python3
import os,sys,json,hashlib,struct,time
from pathlib import Path
import numpy as np, cocoex
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from projected_s6_coco_harness import run_full_s6,run_projected_s6,capture_silicon_env
RUN=os.environ.get("RUN_ID","coco_bfs_twin_exact_20261001")
D=int(os.environ.get("DIM","10")); B=int(os.environ.get("BUDGET","1000")); SEED=int(os.environ.get("SEED","20260810"))
OUT=ROOT/RUN; OUT.mkdir(parents=True,exist_ok=True); TAPE=OUT/"game_tape_exact.bin"
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1<<20),b""): h.update(b)
 return h.hexdigest()
class Recorder:
 def __init__(self,problem,mode):
  self.problem=problem; self.mode=mode; self.dimension=problem.dimension
  self.lower_bounds=problem.lower_bounds; self.upper_bounds=problem.upper_bounds
  self.id=problem.id; self.calls=[]
 def __call__(self,x):
  a=np.asarray(x,dtype=np.float64).copy()
  y=float(self.problem(a))
  self.calls.append({"eval":len(self.calls)+1,"x":a,"f":y,
                     "x_sha256":hashlib.sha256(a.astype("<f8").tobytes()).hexdigest(),
                     "x_hex":a.astype("<f8").tobytes().hex()})
  return y
def write_block(f,pid,idx,mode,calls):
 b=pid.encode(); f.write(struct.pack("<4sHHI",b"CTWN",1,idx,mode))
 f.write(struct.pack("<II",len(b),len(calls))); f.write(b)
 for e in calls:
  x=e["x"]; f.write(struct.pack("<Id",e["eval"],e["f"]))
  f.write(x.astype("<f8",copy=False).tobytes())
def main():
 s1=cocoex.Suite("bbob","",f"dimensions: {D}"); s2=cocoex.Suite("bbob","",f"dimensions: {D}")
 rows=[]; t0=time.perf_counter_ns()
 with TAPE.open("wb") as tf:
  for i,(p1,p2) in enumerate(zip(s1,s2)):
   r1=Recorder(p1,0); r2=Recorder(p2,1)
   a=run_full_s6(r1,seed=SEED,budget=B); q=run_projected_s6(r2,seed=SEED,budget=B)
   pid=p1.id
   write_block(tf,pid,i,0,r1.calls); write_block(tf,pid,i,1,r2.calls)
   rows.append({"index":i,"problem_id":pid,"baseline_calls":len(r1.calls),
    "quotient_calls":len(r2.calls),"f_full":a["final_f"],"f_quot":q["final_f"],
    "best_full":a["best_f"],"best_quot":q["best_f"],
    "f_diff":abs(a["final_f"]-q["final_f"]),
    "best_diff":abs(a["best_f"]-q["best_f"]),
    "objective_equal":abs(a["final_f"]-q["final_f"])<1e-12,
    "best_equal":abs(a["best_f"]-q["best_f"])<1e-12,
    "full_wall_ns":a["wall_time_ns"],"quotient_wall_ns":q["wall_time_ns"],
    "input_bytes_sha256":hashlib.sha256(b"".join(e["x"].astype("<f8").tobytes() for e in r1.calls)).hexdigest()})
   if i%10==0: print(f"{i+1}/360 {pid}",flush=True)
 elapsed=time.perf_counter_ns()-t0; tape_sha=sha(TAPE)
 out={"schema":"COCO-BFS-TWIN-EXACT-1.0","run_id":RUN,"suite":"bbob","dimension":D,
 "budget":B,"seed":SEED,"problems":len(rows),"game_tape":str(TAPE),
 "tape_sha256":tape_sha,"tape_bytes":TAPE.stat().st_size,"elapsed_ns":elapsed,
 "environment":capture_silicon_env(),
 "counts":{"objective_equal":sum(r["objective_equal"] for r in rows),
           "best_equal":sum(r["best_equal"] for r in rows),
           "baseline_calls":sum(r["baseline_calls"] for r in rows),
           "quotient_calls":sum(r["quotient_calls"] for r in rows)},
 "rows":rows}
 (OUT/"manifest.json").write_text(json.dumps({k:v for k,v in out.items() if k!="rows"},indent=2))
 (OUT/"summary.json").write_text(json.dumps(out,indent=2))
 print(json.dumps({k:v for k,v in out.items() if k!="rows"},indent=2))
if __name__=="__main__": main()
