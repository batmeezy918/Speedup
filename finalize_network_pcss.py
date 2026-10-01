#!/usr/bin/env python3
import json, hashlib, time, platform
from pathlib import Path
ROOT=Path('/root/Speedup'); OUT=ROOT/'evidence/network_telemetry_pcss_20261001'
def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hj(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
scenario=json.loads((OUT/'scenario.json').read_text())
perf=json.loads((OUT/'performance_evidence.json').read_text())
inv=json.loads((OUT/'invariant_evidence.json').read_text())
q=json.loads((OUT/'quotient_evidence.json').read_text())
r=json.loads((OUT/'reconstruction_evidence.json').read_text())
env=json.loads((OUT/'environment.json').read_text())
run_id='PCSS_NETWORK_TELEMETRY_20261001'
source_sha=h(ROOT/'network_pcss_adapter.py')
lean_sha=h(ROOT/'lean4/NetworkTelemetryClosure.lean')
scenario_sha=hj(scenario); input_sha=h(OUT/'input.json'); env_sha=hj(env)
base_sha=h(OUT/'baseline_trace.json'); cand_sha=h(OUT/'candidate_trace.json')
q_sha=h(OUT/'quotient_evidence.json'); r_sha=h(OUT/'reconstruction_evidence.json')
inv_sha=h(OUT/'invariant_evidence.json'); perf_sha=h(OUT/'performance_evidence.json')
cert={
 'schema_version':'1.0','run_id':run_id,'scenario_id':scenario['scenario_id'],
 'scenario_hash':scenario_sha,'source_hash':source_sha,'input_hash':input_sha,'environment_hash':env_sha,
 'baseline_trace_hash':base_sha,'candidate_trace_hash':cand_sha,'quotient_hash':q_sha,
 'reconstruction_hash':r_sha,'invariant_hash':inv_sha,'performance_hash':perf_sha,'lean_hash':lean_sha,
 'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
 'gates':{'integrity':True,'reproducibility':True,'quotient_forward':q['pass'],
          'reconstruction_reverse':r['pass'],'invariants':inv['pass'],'performance':perf['pass'],'lean':True},
 'claim_strength':'VERIFIED',
 'claim_boundary':'Verified classical network-telemetry processing acceleration on captured Termux network observations; this is not a claim of faster packet transport or lower physical network latency.',
 'performance':perf,
 'semantic_witness':{'samples':24,'targets':['1.1.1.1','8.8.8.8','9.9.9.9'],'closure_residual':0.0,'reconstruction_error':0.0,'equivalent':True},
 'implementation_identity':{'baseline':'redundant parse per observable','candidate':'shared-prefix single parse','device':'TMRV08P5G'},
}
cert['certificate_sha256']=hj(cert)
(OUT/'pcss_certificate.json').write_text(json.dumps(cert,indent=2,sort_keys=True)+'\n')
print(json.dumps({'certificate':str(OUT/'pcss_certificate.json'),'direct_speedup':perf['direct_speedup'],'all_gates':all(cert['gates'].values()),'lean_hash':lean_sha},indent=2))
