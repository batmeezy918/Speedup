import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "governor"))
import recursive_speedup_ledger_v2 as ledger

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_artifact(root, rel, content):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"path": rel, "sha256": digest(p)}

def genesis():
    return {
        "primitive_id":"GENESIS","parent_ids":[],"timestamp":"2026-10-12T00:00:00Z",
        "scenario_hash":"GENESIS","implementation_hash":"GENESIS","run_hash":"GENESIS","proof_hash":"GENESIS",
        "evidence_class":"OBSERVATION","S_ideal":None,"S_measured":None,"S_verified":None,
        "S_composed":None,"S_cumulative":None,"interaction_factor":None,"gap_status":"NONE",
        "claim_strength":"OBSERVATION","evidence_strength":"OBSERVATION","stage_chain":ledger.STAGES,
        "baseline_id":"GENESIS","composition_id":None,"gates":{g:False for g in ledger.GATES}
    }

def make_v2(root,pid,when,parents,ratio=2.0,status="VERIFIED",record_type="primitive"):
    stage_refs={}
    for i,stage in enumerate(ledger.STAGES):
        stage_refs[stage]=[write_artifact(root,f"evidence/{pid}/stage_{i}.txt",f"{pid}:{stage}")]
    scenario=write_artifact(root,f"evidence/{pid}/scenario.json",json.dumps({"id":pid,"when":when}))
    impl=write_artifact(root,f"evidence/{pid}/implementation.py",f"# implementation {pid}\n")
    run=write_artifact(root,f"evidence/{pid}/run.json",json.dumps({"run":pid,"ratio":ratio}))
    proof=write_artifact(root,f"evidence/{pid}/proof.lean",f"theorem {pid.replace('-','_')}_ok : True := by trivial\n")
    attr=write_artifact(root,f"evidence/{pid}/attribution.json",json.dumps({"double_counting_checked":True}))
    composed=write_artifact(root,f"evidence/{pid}/composed.json",f"composed {pid}")
    cumulative=write_artifact(root,f"evidence/{pid}/cumulative.json",f"cumulative {pid}")
    passed=status=="VERIFIED"
    row={
        "schema_version":"2.0","primitive_id":pid,"record_type":record_type,"parent_ids":parents,
        "timestamp":when,"recorded_at":when,"scenario_hash":scenario["sha256"],"implementation_hash":impl["sha256"],
        "run_hash":run["sha256"],"proof_hash":proof["sha256"],"evidence_class":status,
        "S_ideal":ratio*1.1 if ratio else None,"S_i":ratio if record_type in {"primitive","negative"} else None,
        "S_measured":ratio if record_type in {"primitive","negative"} else None,
        "S_verified":ratio if passed and record_type=="primitive" else None,"S_composed":None,"S_cumulative":None,
        "S_product":None,"interaction_factor":None,"gap_status":"NONE" if passed else "MEASUREMENT_GAP",
        "gaps":["NONE"] if passed else ["MEASUREMENT_GAP"],"claim_strength":"VERIFIED" if passed else "CANDIDATE",
        "evidence_strength":"VERIFIED" if passed else "CANDIDATE","stage_chain":ledger.STAGES,
        "baseline_id":f"baseline-{pid}","canonical_baseline_id":f"canonical-{pid}","composition_id":None,
        "gates":{g:passed for g in ledger.GATES},"stage_status":{s:("PASS" if passed else "OPEN") for s in ledger.STAGES},
        "stage_evidence":stage_refs,"scope":{"workload":"synthetic-test","environment":"test-env",
        "baseline":f"baseline-{pid}","candidate":pid,"metric":"wall_clock_seconds","aggregation":"median"},
        "run_hashes":{"individual":run["sha256"] if passed else None},
        "timings":{"individual_baseline_s":10.0,"individual_candidate_s":10.0/ratio} if passed else {},
        "component_speedups":{},"valid_instantiation":None,"compatibility":{},
        "attribution":{"status":"PASS","double_counting_checked":True,"evidence_refs":[attr],
        "saved_work_by_component":{pid:1.0},"overlap_accounted":True,"new_overhead":0.1,"net_saved_work":0.9} if passed else {},
        "hardware_mechanism":{"claimed":False,"status":"NOT_CLAIMED","evidence_refs":[]},
        "evidence_refs":[scenario,impl,run,proof]
    }
    return row,{"composed":composed,"cumulative":cumulative}

def make_composition(root,pid,when,parents,parent_ratios,comp_ratio=4.0,cumulative_ratio=10.0):
    row,refs=make_v2(root,pid,when,parents,ratio=comp_ratio,status="VERIFIED",record_type="composition")
    row.update({"S_i":None,"S_measured":comp_ratio,"S_verified":comp_ratio,"S_composed":comp_ratio,
        "S_cumulative":cumulative_ratio,"S_product":1.0,"interaction_factor":None,
        "baseline_id":"composition-baseline","canonical_baseline_id":"original-canonical-baseline",
        "composition_id":pid,"component_speedups":dict(parent_ratios),
        "timings":{"composed_baseline_s":20.0,"composed_candidate_s":20.0/comp_ratio,
        "canonical_baseline_s":100.0,"cumulative_candidate_s":100.0/cumulative_ratio},
        "run_hashes":{"composed":refs["composed"]["sha256"],"cumulative":refs["cumulative"]["sha256"]},
        "valid_instantiation":True,"compatibility":{"state_boundary_match":True,"baseline_chain_match":True,
        "observable_match":True,"invariant_match":True,"overlap_accounted":True,"double_counting_checked":True}})
    row["S_product"]=1.0
    for v in parent_ratios.values(): row["S_product"]*=v
    row["interaction_factor"]=comp_ratio/row["S_product"]
    row["scope"]["baseline"]="composition-baseline"
    return row

class RecursiveLedgerV2Tests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.root=pathlib.Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def check(self,rows):
        for i,row in enumerate(rows,1): row["_line"]=i
        return ledger.validate(rows,self.root)

    def test_verified_primitive_and_direct_composition(self):
        p1,_=make_v2(self.root,"P1","2026-10-12T00:01:00Z",["GENESIS"],2.0)
        p2,_=make_v2(self.root,"P2","2026-10-12T00:02:00Z",["GENESIS"],4.0)
        c=make_composition(self.root,"C1","2026-10-12T00:03:00Z",["P1","P2"],{"P1":2.0,"P2":4.0})
        errors,verified=self.check([genesis(),p1,p2,c])
        self.assertEqual(errors,[]); self.assertEqual(verified,{"P1","P2","C1"})
        self.assertEqual(c["S_composed"],4.0); self.assertEqual(c["S_cumulative"],10.0)
        self.assertEqual(c["interaction_factor"],0.5)

    def test_unmeasured_candidate_keeps_measurement_gap(self):
        p,_=make_v2(self.root,"PENDING","2026-10-12T00:01:00Z",["GENESIS"],None,"CANDIDATE")
        p.update({"S_i":None,"S_measured":None,"S_ideal":None,"timings":{},"run_hashes":{}})
        errors,verified=self.check([genesis(),p])
        self.assertEqual(errors,[]); self.assertEqual(verified,set())

    def test_candidate_parent_cannot_verify_composition(self):
        p1,_=make_v2(self.root,"P1","2026-10-12T00:01:00Z",["GENESIS"],2.0)
        p2,_=make_v2(self.root,"P2","2026-10-12T00:02:00Z",["GENESIS"],4.0,"CANDIDATE")
        p2.update({"S_i":None,"S_measured":None,"S_verified":None,"timings":{},"run_hashes":{},
                   "stage_status":{s:"OPEN" for s in ledger.STAGES},"stage_evidence":{s:[] for s in ledger.STAGES},
                   "evidence_refs":[],"attribution":{},"gates":{g:False for g in ledger.GATES}})
        c=make_composition(self.root,"C1","2026-10-12T00:03:00Z",["P1","P2"],{"P1":2.0,"P2":4.0})
        errors,_=self.check([genesis(),p1,p2,c])
        self.assertTrue(any("composition parent P2 is not previously VERIFIED" in e for e in errors))

    def test_interaction_factor_is_recomputed(self):
        p1,_=make_v2(self.root,"P1","2026-10-12T00:01:00Z",["GENESIS"],2.0)
        p2,_=make_v2(self.root,"P2","2026-10-12T00:02:00Z",["GENESIS"],4.0)
        c=make_composition(self.root,"C1","2026-10-12T00:03:00Z",["P1","P2"],{"P1":2.0,"P2":4.0})
        c["interaction_factor"]=1.0
        errors,_=self.check([genesis(),p1,p2,c])
        self.assertTrue(any("interaction factor not S_composed/S_product" in e for e in errors))

    def test_claim_strength_cannot_exceed_evidence(self):
        p,_=make_v2(self.root,"P1","2026-10-12T00:01:00Z",["GENESIS"],2.0)
        p["claim_strength"]="VERIFIED"; p["evidence_strength"]="OBSERVATION"
        errors,_=self.check([genesis(),p])
        self.assertTrue(any("ClaimStrength > EvidenceStrength" in e for e in errors))

    def test_bad_artifact_hash_fails_closed(self):
        p,_=make_v2(self.root,"P1","2026-10-12T00:01:00Z",["GENESIS"],2.0)
        p["evidence_refs"][0]["sha256"]="0"*64
        errors,_=self.check([genesis(),p])
        self.assertTrue(any("hash mismatch" in e for e in errors))

    def test_speedup_below_one_cannot_be_promoted(self):
        p,_=make_v2(self.root,"P1","2026-10-12T00:01:00Z",["GENESIS"],0.8)
        errors,_=self.check([genesis(),p])
        self.assertTrue(any("verified speedup requires S_i > 1" in e for e in errors))

    def test_negative_result_is_preserved_not_promoted(self):
        n,_=make_v2(self.root,"NEG1","2026-10-12T00:01:00Z",["GENESIS"],0.8,"FAILED","negative")
        n.update({"S_verified":None,"claim_strength":"OBSERVATION","evidence_strength":"STRONG_LOCAL",
        "gaps":["NEGATIVE","FAILED"],"gap_status":"NEGATIVE|FAILED","stage_status":{s:"OPEN" for s in ledger.STAGES},
        "stage_evidence":{s:[] for s in ledger.STAGES},"evidence_refs":[],"attribution":{},"run_hashes":{},
        "timings":{"individual_baseline_s":8.0,"individual_candidate_s":10.0}})
        errors,verified=self.check([genesis(),n])
        self.assertEqual(errors,[]); self.assertEqual(verified,set())

if __name__=="__main__": unittest.main()
