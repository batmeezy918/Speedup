#!/usr/bin/env python3
import json, os, platform, subprocess, time
from pathlib import Path
from muni_runtime import run, LIB
OUT=Path(__file__).resolve().parent/'receipts'
OUT.mkdir(exist_ok=True)
os.environ.setdefault('OMP_NUM_THREADS','1')
ns=[512,1024,2048]
results=[]
for n in ns:
    print(f'=== MuNi CALLABLE N={n} ===',flush=True)
    r=run(n,2,7); results.append(r)
    print(json.dumps(r,indent=2),flush=True)
cert={'schema':'MUNI-CALLABLE-RUNTIME-0.1','arch':platform.machine(),'kernel':platform.release(),'omp_threads':os.environ['OMP_NUM_THREADS'],'library':str(LIB),'library_sha256':subprocess.check_output(['sha256sum',str(LIB)],text=True).split()[0],'results':results,'claim_boundary':['Speedups are measured end-to-end from Python ctypes dispatch into native AArch64 code for preallocated matrices.','The mathematical work ratio is exactly 1.0; no reduction in 2*n^3 FLOPs is claimed.','The speedup is scoped to this device, compiler, binary and runtime configuration.','Correctness is empirical here: baseline and candidate output arrays are compared.','This receipt does not by itself establish the full PCSS publication gate or Lean theorem.']}
p=OUT/f'callable_{time.strftime("%Y%m%dT%H%M%SZ",time.gmtime())}.json'; p.write_text(json.dumps(cert,indent=2)+'\n'); print(f'RECEIPT={p}',flush=True)
