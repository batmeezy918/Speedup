import json,struct,hashlib
from pathlib import Path
D=Path("/root/Speedup/evidence/official-coco/coco_bfs_twin_exact_full_20261001")
m=json.loads((D/"manifest.json").read_text()); p=D/"game_tape_exact.bin"
h=hashlib.sha256(p.read_bytes()).hexdigest()
blocks=records=0; ok=True
with p.open("rb") as f:
 while True:
  h0=f.read(12)
  if not h0: break
  if len(h0)!=12 or h0[:4]!=b"CTWN": ok=False; break
  magic,ver,idx,mode=struct.unpack("<4sHHI",h0)
  z=f.read(8)
  if len(z)!=8: ok=False; break
  n,count=struct.unpack("<II",z)
  if len(f.read(n))!=n: ok=False; break
  payload=f.read(count*(12+8*m["dimension"]))
  ok &= len(payload)==count*(12+8*m["dimension"])
  blocks+=1; records+=count
print("HASH_MATCH",h==m["tape_sha256"])
print("BYTES_MATCH",p.stat().st_size==m["tape_bytes"])
print("BLOCKS",blocks,"EXPECTED",m["problems"]*2)
print("RECORDS",records,"EXPECTED",m["counts"]["baseline_calls"]+m["counts"]["quotient_calls"])
print("FORMAT_OK",ok)
