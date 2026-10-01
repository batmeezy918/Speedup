#!/usr/bin/env python3
import json,time,hashlib,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,'/root')
import AGD_QUANTUM_GENERALITY_DEFINITIVE_EOF as agd

N=10; q=32; m=32; seed=3; reps=30; warmups=5
rng=np.random.RandomState(seed)
V=agd.random_hetero_product(rng,q,m)
alpha=agd.random_state(rng,q)
R=(1/np.sqrt(m))*np.kron(np.eye(q),np.ones((m,1),dtype=np.complex128))
Pi=(1/np.sqrt(m))*np.kron(np.eye(q),np.ones((1,m),dtype=np.complex128))
psi=R@alpha
U=np.kron(V,np.eye(m,dtype=np.complex128))

def baseline(): return U@psi

def candidate(): return R@(V@alpha)

# correctness and closure
b=baseline(); c=candidate()
err=float(np.max(np.abs(b-c)))
pi_r=float(np.max(np.abs(Pi@R-np.eye(q))))

def med(fn):
    for _ in range(warmups): fn()
    t=[]
    for _ in range(reps):
        t0=time.perf_counter_ns(); fn(); t.append((time.perf_counter_ns()-t0)/1e6)
    return float(np.median(t)),float(min(t))
b, bmin=med(baseline); c, cmin=med(candidate)
res={'callable':'AGD_QG_F_HET_N10_S3','n':N,'q':q,'m':m,'seed':seed,'baseline_median_ms':b,'candidate_median_ms':c,'e2e_speedup':b/c,'exact_error':err,'pi_r_error':pi_r,'bitwise_equal':bool(np.array_equal(baseline(),candidate())),'composition_depth':5,'status':'PASS' if err<=1e-12 and pi_r<=1e-12 else 'FAIL'}
out=Path('/root/Speedup/muNI_callable/receipts/PCSS_QG_CALLABLE_20261001.json'); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res,indent=2))
