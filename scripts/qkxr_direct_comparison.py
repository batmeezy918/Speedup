#!/usr/bin/env python3
import json, time, hashlib, platform, subprocess, statistics, gc
from pathlib import Path
from qkxr.execution_quotient import MarketState, execution_signature, execution_quotient

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "qkxr"
OUT.mkdir(parents=True, exist_ok=True)

# Exact finite domain already used by the verified semantic gate.
states = [
    MarketState(84797.19, 84797.19 + s * 0.01, -1.00 + i * 0.01)
    for s in range(1, 9)
    for i in range(201)
]
# Repeat the identical replay deterministically; no random workload shaping.
REPEATS = 63
replay = states * REPEATS
N = len(replay)

def baseline():
    out = 0
    for x in replay:
        out += (execution_signature(x) == "SELL")
    return out

def quotient():
    out = 0
    for x in replay:
        q = execution_quotient(x)
        out += (q[2] == "SELL")
    return out

def timed(fn, rounds=7):
    samples=[]
    result=None
    for _ in range(2):
        result=fn()
    gc.collect()
    for _ in range(rounds):
        t0=time.perf_counter_ns()
        result=fn()
        t1=time.perf_counter_ns()
        samples.append((t1-t0)/1e6)
    return result, samples

def p(vals, q):
    return statistics.quantiles(vals,n=100,method="inclusive")[int(q*100)-1] if q < 1 else max(vals)

b_result,b = timed(baseline)
q_result,q = timed(quotient)
assert b_result == q_result, (b_result,q_result)

unique_raw = len({(x.bid,x.ask,x.imbalance) for x in replay})
unique_q = len({execution_quotient(x) for x in replay})
compression = unique_raw / unique_q
speed_ratio = statistics.median(b) / statistics.median(q)

obj = {
 "run_type":"QKXR_DIRECT_BASELINE_VS_QUOTIENT",
 "timestamp_utc":time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
 "workload":{"source":"verified finite QK-XR domain","states_per_pass":len(states),"replay_events":N,"repeats":REPEATS},
 "results":{
   "baseline_result":b_result,"quotient_result":q_result,
   "decision_equivalent":b_result==q_result,
   "baseline_ms":b,"quotient_ms":q,
   "baseline_p50_ms":statistics.median(b),"quotient_p50_ms":statistics.median(q),
   "baseline_p95_ms":p(b,.95),"quotient_p95_ms":p(q,.95),
   "baseline_max_ms":max(b),"quotient_max_ms":max(q),
   "median_baseline_over_quotient":speed_ratio,
   "unique_raw_states":unique_raw,"unique_refined_classes":unique_q,
   "compression_ratio":compression
 },
 "environment":{
   "python":platform.python_version(),"platform":platform.platform(),
   "processor":platform.processor(),"machine":platform.machine()
 },
 "claim_boundary":"Finite deterministic microbenchmark only. No live-market, profitability, latency, or HFT speedup claim.",
}
obj["source_hash"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
outpath=OUT/(obj["timestamp_utc"]+"_direct_comparison.json")
outpath.write_text(json.dumps(obj,indent=2)+"\n")
print(json.dumps(obj,indent=2))
print("EVIDENCE_FILE",outpath)
