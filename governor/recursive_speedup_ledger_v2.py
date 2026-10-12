#!/usr/bin/env python3
"""Fail-closed schema-v2 validator for recursive proof-carrying speedup records."""
import argparse, datetime as dt, hashlib, json, math, pathlib, re, sys
STAGES=["Requirement","Derivation","Operator","Implementation","Native Run","Raw Result","Reverse Derivation","Gap Analysis","Gap Closure","Re-run","Normalized Claim"]
GATES=["I","R","Q","Q_inverse","Omega","X","L"]
GAPS={"NONE","NEGATIVE","FAILED","DEPENDENCY_GAP","EQUIVALENCE_GAP","MEASUREMENT_GAP","ATTRIBUTION_GAP","SCALING_GAP","COMPOSITION_GAP","HARDWARE_MECHANISM_GAP","RECONSTRUCTION_GAP","OBSERVABLE_COMPLETENESS_GAP","FORMAL_GAP"}
RANK={"OBSERVATION":0,"FAILED":0,"QUARANTINED":0,"EMPIRICAL":1,"STRONG_LOCAL":2,"FORMAL_PARTIAL":2,"CANDIDATE":2,"VERIFIED":3}
SHA=re.compile(r"^[0-9a-f]{64}$"); TOL=1e-6
REQ={"schema_version","record_type","primitive_id","parent_ids","timestamp","recorded_at","scenario_hash","implementation_hash","run_hash","proof_hash","evidence_class","S_ideal","S_i","S_measured","S_verified","S_composed","S_cumulative","S_product","interaction_factor","gap_status","gaps","claim_strength","evidence_strength","stage_chain","stage_status","stage_evidence","baseline_id","canonical_baseline_id","composition_id","gates","scope","run_hashes","timings","component_speedups","valid_instantiation","compatibility","attribution","hardware_mechanism","evidence_refs"}
def n(x): return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
def eq(a,b): return n(a) and n(b) and abs(a-b)<=TOL*max(1,abs(a),abs(b))
def sha(x): return isinstance(x,str) and bool(SHA.fullmatch(x))
def rank(x): return x if isinstance(x,int) else RANK.get(str(x).upper(),-1)
def time(x):
    try:
        d=dt.datetime.fromisoformat(str(x).replace("Z","+00:00"))
        return d.astimezone(dt.timezone.utc) if d.tzinfo else None
    except ValueError: return None
def load(p):
    out=[]
    for i,line in enumerate(p.read_text(encoding="utf-8").splitlines(),1):
        if line.strip():
            x=json.loads(line); x["_line"]=i; out.append(x)
    return out
def ref_ok(r,root,err,line,label):
    if not isinstance(r,dict) or not isinstance(r.get("path"),str) or not sha(r.get("sha256")):
        err.append(f"line {line}: {label} needs path and SHA-256"); return
    p=(root/r["path"]).resolve(); base=root.resolve()
    if base not in p.parents or not p.is_file(): err.append(f"line {line}: {label} missing or escapes repository root"); return
    if hashlib.sha256(p.read_bytes()).hexdigest()!=r["sha256"]: err.append(f"line {line}: {label} hash mismatch")
def refs(rs,root,err,line,label,required=False):
    if not isinstance(rs,list) or (required and not rs): err.append(f"line {line}: {label} must be {'non-empty ' if required else ''}list"); return
    for i,r in enumerate(rs): ref_ok(r,root,err,line,f"{label}[{i}]")
def ratio(t,a,b,err,line,label):
    x,y=t.get(a),t.get(b)
    if not n(x) or not n(y) or x<=0 or y<=0: err.append(f"line {line}: {label} requires positive raw timings"); return None
    return x/y
def validate(rows,root):
    err=[]; verified=set(); known={}; seen=set(); ids=set(); last=None
    for r in rows:
        line=r.get("_line","?"); start=len(err); pid=r.get("primitive_id"); status=str(r.get("evidence_class","")).upper()
        if pid in ids: err.append(f"line {line}: duplicate primitive_id")
        ids.add(pid); parents=r.get("parent_ids",[])
        if not isinstance(parents,list): err.append(f"line {line}: parent_ids must be a list"); parents=[]
        for p in parents:
            if p not in seen and p!="GENESIS": err.append(f"line {line}: parent {p} is not earlier")
        if r.get("schema_version")!="2.0":
            g=r.get("gates",{})
            if status=="VERIFIED" and isinstance(g,dict) and all(g.get(k) is True for k in GATES) and n(r.get("S_measured")) and n(r.get("S_verified")) and r.get("run_hash") not in ("","OPEN","PARTIAL","GENESIS",None):
                verified.add(pid)
            known[pid]=r; seen.add(pid); continue
        miss=sorted(REQ-r.keys())
        if miss: err.append(f"line {line}: missing v2 fields {miss}")
        if r.get("record_type") not in {"primitive","composition","negative"}: err.append(f"line {line}: invalid record_type")
        ev,rec=time(r.get("timestamp")),time(r.get("recorded_at"))
        if not ev or not rec: err.append(f"line {line}: timezone-aware timestamps required")
        elif rec<ev: err.append(f"line {line}: recorded_at precedes timestamp")
        if rec and last and rec<last: err.append(f"line {line}: append chronology regresses")
        if rec: last=rec
        if r.get("stage_chain")!=STAGES: err.append(f"line {line}: canonical 11-stage chain required")
        ss,se=r.get("stage_status"),r.get("stage_evidence")
        if not isinstance(ss,dict) or set(ss)!=set(STAGES) or any(v not in {"PASS","OPEN","FAIL","NOT_APPLICABLE"} for v in (ss.values() if isinstance(ss,dict) else [])): err.append(f"line {line}: classify all 11 stages")
        if not isinstance(se,dict) or set(se)!=set(STAGES): err.append(f"line {line}: stage evidence must cover all 11 stages")
        else:
            for s in STAGES:
                if not isinstance(se.get(s),list): err.append(f"line {line}: stage evidence {s} must be a list")
                else:
                    for j,x in enumerate(se[s]): ref_ok(x,root,err,line,f"stage {s}[{j}]")
                    if isinstance(ss,dict) and ss.get(s)=="PASS" and not se[s]: err.append(f"line {line}: PASS stage {s} lacks evidence")
        gaps=r.get("gaps")
        if not isinstance(gaps,list) or not gaps or any(x not in GAPS for x in gaps): err.append(f"line {line}: unknown/empty gaps")
        else:
            gs="NONE" if gaps==["NONE"] else "|".join(x for x in gaps if x!="NONE")
            if r.get("gap_status")!=gs: err.append(f"line {line}: gap_status does not match gaps")
        if rank(r.get("claim_strength"))<0 or rank(r.get("evidence_strength"))<0 or rank(r.get("claim_strength"))>rank(r.get("evidence_strength")): err.append(f"line {line}: ClaimStrength > EvidenceStrength")
        if not r.get("canonical_baseline_id"): err.append(f"line {line}: canonical_baseline_id required")
        sc=r.get("scope")
        if not isinstance(sc,dict) or any(not sc.get(k) for k in ("workload","environment","baseline","candidate","metric","aggregation")): err.append(f"line {line}: scope incomplete")
        g=r.get("gates")
        if not isinstance(g,dict) or any(not isinstance(g.get(k),bool) for k in GATES): err.append(f"line {line}: all seven gates must be explicit booleans")
        if status=="VERIFIED":
            for k in ("scenario_hash","implementation_hash","run_hash","proof_hash"):
                if not sha(r.get(k)): err.append(f"line {line}: VERIFIED needs SHA-256 {k}")
        refs(r.get("evidence_refs"),root,err,line,"evidence_refs",status=="VERIFIED")
        t=r.get("timings") if isinstance(r.get("timings"),dict) else {}
        rh=r.get("run_hashes") if isinstance(r.get("run_hashes"),dict) else {}
        rt=r.get("record_type"); mi=n(r.get("S_i")) and r.get("S_i")>0; mc=n(r.get("S_composed")) and r.get("S_composed")>0; mu=n(r.get("S_cumulative")) and r.get("S_cumulative")>0
        if rt in {"primitive","negative"}:
            if any(r.get(k) is not None for k in ("S_composed","S_cumulative","S_product","interaction_factor")) or r.get("component_speedups")!={}: err.append(f"line {line}: individual row has composition-only metrics")
            if mi:
                if not eq(r.get("S_measured"),r.get("S_i")): err.append(f"line {line}: S_measured != S_i")
                z=ratio(t,"individual_baseline_s","individual_candidate_s",err,line,"S_i")
                if z is not None and not eq(z,r.get("S_i")): err.append(f"line {line}: S_i disagrees with raw timings")
            elif status=="VERIFIED" or "MEASUREMENT_GAP" not in (gaps if isinstance(gaps,list) else []): err.append(f"line {line}: missing S_i requires MEASUREMENT_GAP")
            elif r.get("S_measured") is not None: err.append(f"line {line}: S_measured must remain null")
            if rt=="negative" and (not mi or not ({"NEGATIVE","FAILED"}&set(gaps or []))): err.append(f"line {line}: negative outcome not preserved")
            if status=="VERIFIED":
                if rt!="primitive" or not mi or r.get("S_i")<=1: err.append(f"line {line}: verified speedup requires S_i > 1")
                if not sha(rh.get("individual")): err.append(f"line {line}: individual run hash required")
        elif rt=="composition":
            if r.get("S_i") is not None or not parents: err.append(f"line {line}: composition needs parents and S_i=null")
            if mc:
                if not eq(r.get("S_measured"),r.get("S_composed")): err.append(f"line {line}: S_measured != S_composed")
                z=ratio(t,"composed_baseline_s","composed_candidate_s",err,line,"S_composed")
                if z is not None and not eq(z,r.get("S_composed")): err.append(f"line {line}: S_composed disagrees with raw timings")
            elif status=="VERIFIED" or "MEASUREMENT_GAP" not in (gaps if isinstance(gaps,list) else []): err.append(f"line {line}: missing S_composed requires MEASUREMENT_GAP")
            elif r.get("S_measured") is not None: err.append(f"line {line}: unmeasured composition must have S_measured=null")
            if mu:
                z=ratio(t,"canonical_baseline_s","cumulative_candidate_s",err,line,"S_cumulative")
                if z is not None and not eq(z,r.get("S_cumulative")): err.append(f"line {line}: S_cumulative disagrees with canonical baseline timing")
            elif status=="VERIFIED" or "MEASUREMENT_GAP" not in (gaps if isinstance(gaps,list) else []): err.append(f"line {line}: missing S_cumulative requires MEASUREMENT_GAP")
            c=r.get("component_speedups")
            if not isinstance(c,dict) or (c and set(c)!=set(parents)): err.append(f"line {line}: component ratios must match parents"); c={}
            cok=bool(c) and all(n(x) and x>0 for x in c.values())
            if cok:
                prod=math.prod(c.values())
                if not eq(r.get("S_product"),prod): err.append(f"line {line}: S_product not the diagnostic component product")
                if mc and not eq(r.get("interaction_factor"),r["S_composed"]/prod): err.append(f"line {line}: interaction factor not S_composed/S_product")
            elif r.get("S_product") is not None or r.get("interaction_factor") is not None: err.append(f"line {line}: product/interaction must remain null without component measurements")
            if status=="VERIFIED":
                if not mc or not mu or not cok: err.append(f"line {line}: verified composition needs direct composed/cumulative/component measurements")
                if not sha(rh.get("composed")) or not sha(rh.get("cumulative")) or rh.get("composed")==rh.get("cumulative"): err.append(f"line {line}: independent composed and cumulative run hashes required")
                co=r.get("compatibility"); need={"state_boundary_match","baseline_chain_match","observable_match","invariant_match","overlap_accounted","double_counting_checked"}
                if r.get("valid_instantiation") is not True or not isinstance(co,dict) or any(co.get(k) is not True for k in need): err.append(f"line {line}: composition compatibility not closed")
                for p in parents:
                    if p not in verified: err.append(f"line {line}: composition parent {p} is not previously VERIFIED")
                    elif p in known:
                        pr=known[p]; v=pr.get("S_composed") if pr.get("record_type")=="composition" else pr.get("S_i",pr.get("S_measured"))
                        if p in c and not eq(c[p],v): err.append(f"line {line}: component ratio mismatch for {p}")
        else: err.append(f"line {line}: unsupported record type")
        if status=="VERIFIED":
            a=r.get("attribution"); h=r.get("hardware_mechanism")
            if not isinstance(a,dict) or a.get("status")!="PASS" or a.get("double_counting_checked") is not True: err.append(f"line {line}: attribution/double-counting gate missing")
            else: refs(a.get("evidence_refs"),root,err,line,"attribution evidence",True)
            if not isinstance(h,dict) or not isinstance(h.get("claimed"),bool): err.append(f"line {line}: hardware-mechanism claim state required")
            elif h["claimed"]:
                if h.get("status")!="PASS": err.append(f"line {line}: claimed hardware mechanism did not PASS")
                refs(h.get("evidence_refs"),root,err,line,"hardware evidence",True)
            elif h.get("status")!="NOT_CLAIMED": err.append(f"line {line}: hardware mechanism must be NOT_CLAIMED when not evidenced")
            if not isinstance(ss,dict) or any(ss.get(s)!="PASS" for s in STAGES): err.append(f"line {line}: all stages must PASS")
            if not isinstance(g,dict) or any(g.get(k) is not True for k in GATES): err.append(f"line {line}: all seven PCSS gates must PASS")
            if not eq(r.get("S_verified"),r.get("S_measured")): err.append(f"line {line}: S_verified must equal measured ratio after gates")
            if gaps!=["NONE"]: err.append(f"line {line}: VERIFIED record must have gaps=['NONE']")
            for p in parents:
                if p!="GENESIS" and p not in verified: err.append(f"line {line}: dependency {p} is not VERIFIED")
        elif r.get("S_verified") is not None: err.append(f"line {line}: non-VERIFIED S_verified must be null")
        if rt=="negative" and status=="VERIFIED": err.append(f"line {line}: negative record cannot be a speedup primitive")
        if status=="VERIFIED" and len(err)==start: verified.add(pid)
        known[pid]=r; seen.add(pid)
    return err,verified
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("ledger",nargs="?",default="evidence/ledger/RECURSIVE_PRIMITIVE_LEDGER.jsonl"); a=ap.parse_args(); p=pathlib.Path(a.ledger)
    if not p.is_file(): print(f"FAIL: missing ledger {p}"); return 2
    try: rows=load(p); err,v=validate(rows,p.resolve().parents[2] if len(p.resolve().parents)>2 else p.resolve().parent)
    except (OSError,ValueError) as e: print(f"FAIL: {e}"); return 2
    if err:
        print("FAIL: recursive speedup v2 enforcement"); print("\n".join(" - "+x for x in err)); return 1
    print(f"PASS: recursive speedup v2 enforcement; records={len(rows)}; v2_records={sum(x.get('schema_version')=='2.0' for x in rows)}; verified_primitives={len(v)}"); return 0
if __name__=="__main__": sys.exit(main())
