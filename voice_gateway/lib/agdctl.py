#!/usr/bin/env python3
import argparse,json,os,time,uuid,hashlib
from pathlib import Path
ROOT=Path('/root/Speedup/voice_gateway'); LOG=ROOT/'logs/audit.jsonl'; JOBS=ROOT/'jobs'
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def audit(event,**kw):
 rec={'schema':'AGD.VOICE.AUDIT.1','ts_ns':time.time_ns(),'event':event,**kw}; LOG.parent.mkdir(parents=True,exist_ok=True)
 with LOG.open('a') as f:f.write(json.dumps(rec,separators=(',',':'))+'\n')
def main():
 ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True); p=sub.add_parser('intent'); p.add_argument('file'); sub.add_parser('status'); p=sub.add_parser('cancel'); p.add_argument('--job',default='current'); a=ap.parse_args()
 if a.cmd=='intent':
  raw=Path(a.file).read_text(); d=json.loads(raw); allowed={'status','callable','verify','benchmark','audit','reconstruct','promote','quarantine','cancel'}; intent=d.get('intent','').lower()
  if intent not in allowed:audit('REJECT',reason='unknown_intent',intent=intent); print(json.dumps({'status':'REJECTED','reason':'unknown_intent'})); return 2
  job={'schema':'AGD.VOICE.JOB.1','job_id':uuid.uuid4().hex,'intent':intent,'mode':d.get('mode','OFFLINE'),'network':bool(d.get('network',False)),'promotion':bool(d.get('promotion',False)),'source_hash':sha(raw)}
  if job['mode']=='OFFLINE' and job['network']:audit('REJECT',reason='offline_network_request',job_id=job['job_id']); print(json.dumps({'status':'REJECTED','reason':'offline_network_request'})); return 3
  out=JOBS/(job['job_id']+'.json'); out.write_text(json.dumps(job,indent=2)); audit('ACCEPT',job_id=job['job_id'],intent=intent); print(json.dumps({'status':'ACCEPTED','job_id':job['job_id'],'job_file':str(out)}))
 elif a.cmd=='status': print(json.dumps({'status':'READY','root':str(ROOT),'offline':True,'llm':'ollama','stt':'termux-speech-to-text','tts':'termux-tts-speak','lean':os.path.exists('/root/.elan/bin/lean')}))
 else:audit('CANCEL_REQUEST',job=a.job); print(json.dumps({'status':'CANCEL_REQUESTED','job':a.job}))
if __name__=='__main__':main()
