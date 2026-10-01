#!/usr/bin/env python3
import json, socket, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RECEIPT=sorted((ROOT/'receipts').glob('PCSS_MUNI_MAX_EDGE_COMPOSITION_V2_*.json'))[-1]
SPOOL=ROOT/'receipts'/'datadog_spool.ndjson'

def emit(metric,value,tags):
    line=f"{metric}:{value}|g|#"+','.join(tags)
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.settimeout(.2)
        s.sendto(line.encode(),('127.0.0.1',8125)); s.close()
        return 'dogstatsd'
    except Exception:
        return 'spool'

def main():
    cert=json.loads(RECEIPT.read_text()); run=cert['run_id']; modes=[]
    for c in cert['cases']:
        tags=[f"run_id:{run}",f"case:{c['case']}",f"backend:{cert['device']['backend']}"]
        for k,v in c['speedups'].items():
            modes.append(emit('pcss.muni.'+k,v,tags))
        modes.append(emit('pcss.muni.correctness',1 if c['correctness']['bitwise_equal'] else 0,tags))
    if any(m=='spool' for m in modes):
        with SPOOL.open('a') as f:
            for c in cert['cases']:
                tags={'run_id':run,'case':c['case'],'backend':cert['device']['backend']}
                f.write(json.dumps({'ts':time.time(),'metrics':c['speedups'],'correctness':c['correctness'],'tags':tags})+'\n')
    print(json.dumps({'receipt':str(RECEIPT),'modes':modes,'spool':str(SPOOL) if 'spool' in modes else None}))
if __name__=='__main__': main()
