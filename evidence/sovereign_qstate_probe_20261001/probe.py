#!/usr/bin/env python3
import json,subprocess,time,statistics,hashlib,re
from pathlib import Path
D=Path("/root/Speedup/evidence/sovereign_qstate_probe_20261001")
D.mkdir(parents=True,exist_ok=True)
TARGETS=["1.1.1.1","8.8.8.8","9.9.9.9"]
def cmd(a,t=5):
    try:return subprocess.check_output(a,stderr=subprocess.DEVNULL,text=True,timeout=t).strip()
    except Exception:return ""
def jcmd(a):
    s=cmd(a)
    try:return json.loads(s) if s else None
    except Exception:return None
def temp():
    vals=[]
    for p in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try: vals.append(int(p.read_text())/1000)
        except: pass
    return max(vals) if vals else None
def sample():
    wifi=jcmd(["termux-wifi-connectioninfo"])
    cell=jcmd(["termux-telephony-cellinfo"])
    dev=jcmd(["termux-telephony-deviceinfo"])
    props=cmd(["getprop"])
    vals=[]
    for h in TARGETS:
        s=cmd(["ping","-c","1","-W","2",h],4)
        m=re.search(r"time[=<]([0-9.]+)",s)
        vals.append(float(m.group(1)) if m else None)
    good=[x for x in vals if x is not None]
    return {"ts":time.time(),"wifi":wifi,"cellinfo":cell,"telephony":dev,
            "latency_ms":vals,"mean_ms":statistics.fmean(good) if good else None,
            "jitter_ms":statistics.pstdev(good) if len(good)>1 else 0.0,
            "loss_pct":100*(len(vals)-len(good))/len(vals),"thermal_max_c":temp(),
            "props_sha256":hashlib.sha256(props.encode()).hexdigest() if props else None}
records=[]
for i in range(6):
    records.append(sample())
    time.sleep(2)
(D/"raw_probe.json").write_text(json.dumps({"samples":len(records),"records":records},indent=2))
groups={}
for r in records:
    w=r.get("wifi") or {}
    key=(w.get("ssid"),w.get("frequency_mhz"),w.get("rssi"),
         tuple(round(x,1) if x is not None else None for x in r["latency_ms"]))
    groups[str(key)]=groups.get(str(key),0)+1
q={"definition":"observable-state partition","class_count":len(groups),
   "raw_state_count":len(records),"compression":len(records)/max(1,len(groups)),
   "preserved_fields":["wifi.ssid","wifi.frequency_mhz","wifi.rssi","latency_ms","loss_pct"],
   "cellinfo_observed":any(r.get("cellinfo") for r in records),
   "note":"Empirical quotient probe only; not a proof of cellular-state equivalence."}
(D/"q_state.json").write_text(json.dumps(q,indent=2))
print(json.dumps(q,indent=2))
