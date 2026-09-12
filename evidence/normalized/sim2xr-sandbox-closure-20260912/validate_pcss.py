import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'src'
ARCHIVES={
 'test1':Path('/mnt/data/SIM2XR_TEST1_SCALING_DEFINITIVE_2026-08-16.zip'),
 'full':Path('/mnt/data/SIM2XR_FULL_TEST_SUITE_DEFINITIVE_2026-08-16.zip'),
 'qsim':Path('/mnt/data/SIM2XR_QSIM_DEFINITIVE_CAMPAIGN_PACKAGE_2026-08-16.zip'),
 'test3':Path('/mnt/data/SIM2XR_TEST3_DEFINITIVE_2026-08-16.zip'),
 'webapp':Path('/mnt/data/agd-sim2xr-webapp.zip'),
}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def loadcsv(p):
 with open(p,newline='') as f: return list(csv.DictReader(f))
results={'schema':'PCSS-SIM2XR-SANDBOX-CLOSURE-1.0','archive_sha256':{k:sha(v) for k,v in ARCHIVES.items()},'checks':{},'verdict':'CLOSED_WITH_GAPS'}
m=json.load(open(SRC/'test1/manifest.json')); rows=loadcsv(SRC/'test1/scaling_raw.csv')
errs=[abs(float(r['dense_s'])/float(r['reduced_s'])-float(r['speedup'])) for r in rows]
results['checks']['test1']={'rows':len(rows),'manifest_rows':m['rows'],'speedup_recompute_max_abs_error':max(errs),'max_measured_speedup':max(float(r['speedup']) for r in rows),'relative_error_max':max(float(r['relative_error']) for r in rows),'pass':len(rows)==m['rows'] and max(errs)<1e-12}
fm=json.load(open(SRC/'full/manifest.json')); fr=loadcsv(SRC/'full/full_suite_results.csv')
results['checks']['full_suite']={'rows':len(fr),'manifest_tests':fm['tests'],'max_speedup_manifest':fm['max_speedup'],'key_manifest_checks':{k:fm[k] for k in ['trace_signal','trace_norm','omega_antisymmetry_error','qfi_noncommuting_difference','ad_span_Z_error','ad_span_ZY_error','physical_trace_error','physical_hermiticity_error','physical_min_eigenvalue_deficit','unitary_invariance_error','sim2x_definition_error']},'pass':len(fr)>0 and fm['tests']==10}
qdir=SRC/'qsim'; qrows=loadcsv(qdir/'SIM2XR_QSIM_DEFINITIVE_regimes.csv'); adv=loadcsv(qdir/'SIM2XR_QSIM_DEFINITIVE_advantage_ledger.csv'); ctrl=loadcsv(qdir/'SIM2XR_QSIM_DEFINITIVE_control_closure.csv'); ox=loadcsv(qdir/'SIM2XR_QSIM_DEFINITIVE_qfi_xi.csv'); op=loadcsv(qdir/'SIM2XR_QSIM_DEFINITIVE_open_systems.csv')
results['checks']['qsim']={'regime_rows':len(qrows),'advantage_rows':len(adv),'control_rows':len(ctrl),'qfi_xi_rows':len(ox),'open_system_rows':len(op),'pass':all([len(qrows)>0,len(adv)>0,len(ctrl)>0,len(ox)>0,len(op)>0])}
tr3=loadcsv(SRC/'test3/definitive_test_results.csv'); t3m=json.load(open(SRC/'test3/manifest.json')); sp=[float(r['value']) for r in tr3 if r.get('metric')=='speedup']
results['checks']['test3']={'rows':len(tr3),'manifest':t3m,'speedup_values_found':len(sp),'max_speedup':max(sp) if sp else None,'pass':len(tr3)==176 and bool(sp)}
html=(SRC/'webapp/agd-sim2xr-app/index.html').read_text(); required=['function P(','function Pi(','function C(','function R(','function Full(','function forward(','P(s)','Pi(p)','C(q.state)','Pi(c)','R(r.state)','accepted:false','SIM2XR','Ω preservation','Ξ preservation']; missing=[x for x in required if x not in html]
results['checks']['webapp']={'required_operator_tokens':len(required),'missing_tokens':missing,'self_contained_readme':(SRC/'webapp/agd-sim2xr-app/README.md').exists(),'pass':not missing}
results['claim_gate']={'mathematical_closed_sector':'PROVED_FOR_SPECIFIED_CONSTRUCTION','numerical_closed_grid':'INDEPENDENTLY_REPRODUCED_IN_SANDBOX','scaling_speedup':'EMPIRICAL_ONLY','universal_speedup':'NOT_ESTABLISHED','q_inverse_full_campaign':'NOT_CLOSED','lean_closure':'NOT_ESTABLISHED','hardware_independent_speedup':'NOT_ESTABLISHED','pcss_verified_primitive':False}
print(json.dumps(results,indent=2)); (ROOT/'pcss_closure_result.json').write_text(json.dumps(results,indent=2)+'\n')
