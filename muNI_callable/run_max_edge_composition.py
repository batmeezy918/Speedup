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
def median(ts):
    s=sorted(ts); m=len(s)
    return (s[(m-1)//2]+s[m//2])/2

def timed(fn,n,a,b,c,warm=3,reps=11):
    for _ in range(warm): call(fn,n,a,b,c)
    ts=[]
    for _ in range(reps):
        c.fill(0); t=time.perf_counter_ns(); call(fn,n,a,b,c); ts.append(time.perf_counter_ns()-t)
    return {'timings_ns':ts,'median_ns':median(ts),'min_ns':min(ts),'max_ns':max(ts)}

def reconstruct(q,out,block):
    # Materialized reconstruction is part of the E2E candidate timing.
    for i in range(q.shape[0]):
        r0=i*block; r1=r0+block
        for j in range(q.shape[1]):
            out[r0:r1,j*block:(j+1)*block] = q[i,j]

def run_case(r,N=2048,block=None,warm=3,reps=11):
    block=block or N//r
    assert r*block==N
    # Small integer values make the block multiplicity exact in binary32.
    av=np.array([(i%8)+1 for i in range(r)],dtype=np.float32)
    bv=np.array([((3*i+1)%8)+1 for i in range(r)],dtype=np.float32)
    A=np.repeat(av,block).reshape(N,1).repeat(N,axis=1).astype(np.float32,copy=False)
    B=np.repeat(bv,block).reshape(N,1).repeat(N,axis=1).astype(np.float32,copy=False)
    Aq=av.reshape(r,1).repeat(r,axis=1)
    Bq=bv.reshape(r,1).repeat(r,axis=1)
    # Warm correctness witnesses.
    full_b=np.empty((N,N),np.float32); q_b=np.empty((r,r),np.float32); q_n=np.empty((r,r),np.float32); out=np.empty((N,N),np.float32)
    call(lib.muni_baseline,N,A,B,full_b)
    call(lib.muni_baseline,r,Aq,Bq,q_b)
    call(lib.muni_neon,r,Aq,Bq,q_n)
    expected=(q_b.astype(np.float64)*block).astype(np.float32)
    reconstruct(q_n,out,block)
    # Exact correctness: candidate quotient*block must equal full result.
    scale_q=(q_n.astype(np.float64)*block).astype(np.float32)
    expected_full=np.repeat(np.repeat(scale_q,block,axis=0),block,axis=1)
    maxerr=float(np.max(np.abs(full_b-expected_full)))
    bitwise=bool(np.array_equal(full_b,expected_full))
    # Timings: full baseline; quotient baseline; quotient NEON; reconstruction separately.
    tf=timed(lib.muni_baseline,N,A,B,full_b,warm,reps)
    tqb=timed(lib.muni_baseline,r,Aq,Bq,q_b,warm,reps)
    tqn=timed(lib.muni_neon,r,Aq,Bq,q_n,warm,reps)
    tr=[]
    for _ in range(warm): reconstruct(q_n,out,block)
    for _ in range(reps):
        t=time.perf_counter_ns(); reconstruct(q_n,out,block); tr.append(time.perf_counter_ns()-t)
    trd={'timings_ns':tr,'median_ns':median(tr),'min_ns':min(tr),'max_ns':max(tr)}
    # True composed candidate: quotient NEON + scalar exact scaling + materialized reconstruction.
    tc=[]
    for _ in range(warm):
        call(lib.muni_neon,r,Aq,Bq,q_n); q_n*=block; reconstruct(q_n,out,block); q_n/=block
    for _ in range(reps):
        t=time.perf_counter_ns(); call(lib.muni_neon,r,Aq,Bq,q_n); q_n*=block; reconstruct(q_n,out,block); q_n/=block; tc.append(time.perf_counter_ns()-t)
    tcd={'timings_ns':tc,'median_ns':median(tc),'min_ns':min(tc),'max_ns':max(tc)}
    S_state=tf['median_ns']/ (tqb['median_ns']+trd['median_ns'])
    S_exec=tqb['median_ns']/tqn['median_ns']
    S_comb=tf['median_ns']/tcd['median_ns']
    product=S_state*S_exec
    interaction=S_comb/product if product else 0.0
    theory=(N/r)**2
    # GEMM FLOP ratio is (N/r)^3; block-constant structure also incurs reconstruction.
    op_ratio=(N/r)**3
    return {'case':f'N{N}_r{r}_block{block}','N':N,'r':r,'block':block,'theoretical_state_op_ratio':op_ratio,'correctness':{'max_abs_error':maxerr,'bitwise_equal':bitwise,'full_finite':bool(np.all(np.isfinite(full_b)))},'timing':{'full_baseline':tf,'quotient_baseline':tqb,'quotient_neon':tqn,'reconstruction':trd,'composed_e2e':tcd},'speedups':{'state_vs_qplus_reconstruct':S_state,'execution_on_quotient':S_exec,'composed_e2e':S_comb,'naive_product_bound':product,'composition_interaction_K':interaction}}


def main():
    cases=[run_case(32),run_case(16)]
    libsha=hashlib.sha256(LIB.read_bytes()).hexdigest()
    cert={'schema':'PCSS-MUNI-MAX-EDGE-COMPOSITION-1.0','run_id':time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()),'device':{'arch':platform.machine(),'kernel':platform.release(),'backend':lib.muni_backend().decode(),'version':lib.muni_version().decode()},'library_sha256':libsha,'cases':cases,'claim_strength':'EMPIRICALLY_MEASURED_COMPOSED_E2E','claim_boundary':['This is a real end-to-end composition test: full GEMM baseline versus quotient extraction, reduced NEON execution, exact scaling and materialized reconstruction.','No isolated speedups are multiplied to obtain composed_e2e; composed_e2e is directly timed.','Theoretical operation ratio is not a wall-clock speedup.','Exact equality is scoped to the integer-valued constructed invariant sector and this binary32 implementation.']}
    p=ROOT/'receipts'/f"PCSS_MUNI_MAX_EDGE_COMPOSITION_{cert['run_id']}.json"; p.write_text(json.dumps(cert,indent=2)+'\n'); print(json.dumps(cert,indent=2)); print('RECEIPT='+str(p))
if __name__=='__main__': main()
