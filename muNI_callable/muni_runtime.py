#!/usr/bin/env python3
import ctypes, hashlib, json, os, platform, time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
LIB=ROOT/'libmuni.so'
lib=ctypes.CDLL(str(LIB))
lib.muni_baseline.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
lib.muni_neon.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
lib.muni_backend.restype=ctypes.c_char_p
lib.muni_version.restype=ctypes.c_char_p

def ptr(a): return a.ctypes.data_as(ctypes.c_void_p)
def call(fn,n,a,b,c): fn(n,ptr(a),ptr(b),ptr(c))
def digest(a): return hashlib.sha256(a.tobytes()).hexdigest()
def measure(fn,n,a,b,c,warmups,reps):
    for _ in range(warmups): call(fn,n,a,b,c)
    ts=[]
    for _ in range(reps):
        c.fill(0); t=time.perf_counter_ns(); call(fn,n,a,b,c); ts.append(time.perf_counter_ns()-t)
    s=sorted(ts); med=(s[(reps-1)//2]+s[reps//2])/2
    return {'timings_ns':ts,'median_ns':med,'min_ns':min(ts),'max_ns':max(ts)}

def run(n,warmups=2,reps=7):
    a=np.full((n,n),1.1,dtype=np.float32,order='C'); b=np.full((n,n),2.2,dtype=np.float32,order='C')
    cb=np.empty_like(a); cc=np.empty_like(a)
    cb.fill(0); cc.fill(0)
    call(lib.muni_baseline,n,a,b,cb); call(lib.muni_neon,n,a,b,cc)
    diff=float(np.max(np.abs(cb-cc))); checksum_b=float(np.sum(cb,dtype=np.float64)); checksum_c=float(np.sum(cc,dtype=np.float64))
    base=measure(lib.muni_baseline,n,a,b,cb,warmups,reps); cand=measure(lib.muni_neon,n,a,b,cc,warmups,reps)
    speed=base['median_ns']/cand['median_ns']; flops=2*n*n*n
    return {'n':n,'backend':lib.muni_backend().decode(),'version':lib.muni_version().decode(),'work_ratio':1.0,'max_abs_diff':diff,'checksum_baseline':checksum_b,'checksum_candidate':checksum_c,'baseline':base,'candidate':cand,'speedup':speed,'baseline_gflops':flops/base['median_ns'],'candidate_gflops':flops/cand['median_ns']}
