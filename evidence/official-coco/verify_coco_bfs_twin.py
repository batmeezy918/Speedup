import json,struct,hashlib
from pathlib import Path
D=Path("/root/Speedup/evidence/official-coco/coco_bfs_twin_full_20261001")
m=json.loads((D/"manifest.json").read_text())
p=D/"game_tape.bin"
h=hashlib.sha256(p.read_bytes()).hexdigest()
blocks=records=0; ok=True
with p.open("rb") as f:
    while True:
        h0=f.read(16)
        if not h0: break
        if len(h0)!=16 or h0[:4]!=b"COCO":
            ok=False; break
        magic,ver,idx,mode,dim,count=struct.unpack("<4sHHIHH",h0)
        nbuf=f.read(4)
        if len(nbuf)!=4: ok=False; break
        n=struct.unpack("<I",nbuf)[0]
        if len(f.read(n))!=n: ok=False; break
        recsz=37+8*dim
        payload=f.read(recsz*count)
        ok &= len(payload)==recsz*count
        blocks+=1; records+=count
print("HASH_MATCH",h==m["tape_sha256"])
print("BYTES_MATCH",p.stat().st_size==m["tape_bytes"])
print("BLOCKS",blocks,"RECORDS",records)
print("FORMAT_OK",ok)
print("EXPECTED_BLOCKS",m["problem_count"]*2)
