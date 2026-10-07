#!/usr/bin/env python3
import json,time,hashlib,platform
from pathlib import Path
from run_max_edge_composition_v2 import run_case,LIB,lib

def main():
    # Push the invariant-sector edge until reconstruction becomes the dominant floor.
    cases=[run_case(8),run_case(4)]
    cert={'schema':'PCSS-MUNI-MAX-EDGE-FLOOR-SWEEP-1.0','run_id':time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()),
      'device':{'arch':platform.machine(),'kernel':platform.release(),'backend':lib.muni_backend().decode(),'version':lib.muni_version().decode()},
      'library_sha256':hashlib.sha256(LIB.read_bytes()).hexdigest(),'cases':cases,
      'claim_boundary':['Direct E2E timing only. Operation ratios are theoretical, not runtime speedups.','Exact equality is scoped to the constructed binary32 invariant sector.','Purpose is to identify the asymptotic reconstruction floor, not to manufacture a headline multiplier.']}
    p=Path(__file__).parent/'receipts'/f"PCSS_MUNI_MAX_EDGE_FLOOR_SWEEP_{cert['run_id']}.json"; p.write_text(json.dumps(cert,indent=2)+'\n'); print(json.dumps(cert,indent=2)); print('RECEIPT='+str(p))
if __name__=='__main__': main()
