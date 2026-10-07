#!/usr/bin/env bash
set -Eeuo pipefail

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="$PWD/OMEGA_HPC_DAG_$RUN_ID"
mkdir -p "$ROOT"/{nodes,results,logs,manifest}

LOG="$ROOT/logs/run.log"
log(){ echo "[$(date -u +%Y%m%dT%H%M%SZ)][OMEGA_HPC_DAG][$1] $2" | tee -a "$LOG"; }

log INFO "initializing deterministic HPC DAG benchmark"
log INFO "root=$ROOT"

cat > "$ROOT/bench_node.py" <<'PY'
import os, sys, json, time, hashlib, math, random, multiprocessing as mp
from pathlib import Path

node_id=sys.argv[1]
branch_id=int(sys.argv[2])
size=int(sys.argv[3])
iters=int(sys.argv[4])
out=Path(sys.argv[5])

seed=1337 + branch_id
random.seed(seed)

def matvec_branch(n,iters,seed):
    random.seed(seed)
    v=[math.sin(i+seed)*0.5 for i in range(n)]
    acc=0.0
    for t in range(iters):
        nv=[]
        for i in range(n):
            left=v[i-1] if i else v[-1]
            right=v[(i+1)%n]
            x=0.499*v[i] + 0.251*left - 0.127*right + math.sin((i+1)*(t+1))*1e-6
            nv.append(x)
            acc += x*x
        v=nv
    h=hashlib.sha256((",".join(f"{x:.12e}" for x in v)).encode()).hexdigest()
    return acc,h

start=time.perf_counter()
acc,h=matvec_branch(size,iters,seed)
elapsed=time.perf_counter()-start

result={
 "node_id":node_id,
 "branch_id":branch_id,
 "seed":seed,
 "size":size,
 "iters":iters,
 "elapsed_sec":elapsed,
 "work_units":size*iters,
 "work_units_per_sec":(size*iters)/elapsed if elapsed else None,
 "accumulator":acc,
 "state_sha256":h
}

out.write_text(json.dumps(result,indent=2,sort_keys=True))
print(json.dumps(result,sort_keys=True))
PY

cat > "$ROOT/reduce.py" <<'PY'
import json, hashlib, sys
from pathlib import Path

root=Path(sys.argv[1])
results=sorted((root/"results").glob("node_*.json"))

rows=[]
for p in results:
    rows.append(json.loads(p.read_text()))

total_work=sum(r["work_units"] for r in rows)
total_elapsed=sum(r["elapsed_sec"] for r in rows)
max_elapsed=max((r["elapsed_sec"] for r in rows), default=0)
throughput=sum(r["work_units_per_sec"] for r in rows)

combined_hash=hashlib.sha256(
    "".join(r["state_sha256"] for r in rows).encode()
).hexdigest()

summary={
 "branches":len(rows),
 "total_work_units":total_work,
 "sum_elapsed_sec":total_elapsed,
 "critical_path_elapsed_sec":max_elapsed,
 "aggregate_branch_throughput":throughput,
 "combined_state_sha256":combined_hash,
 "results":rows
}

(root/"manifest/summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True))

md=[]
md.append("# OMEGA HPC DAG Benchmark Verdict\n")
md.append("## Operator Form\n")
md.append("```text")
md.append("ψ_initial = deterministic seeded vector state")
md.append("ψ_branch_i = O_branch_i ψ_initial")
md.append("ψ_final = O_reduce ∘ (O_branch_1 ⊕ O_branch_2 ⊕ ... ⊕ O_branch_n) ψ_initial")
md.append("Ω(Oψ) = combined_state_sha256")
md.append("heat_trace(O) = elapsed/work density across branches")
md.append("curvature(ψ) = branch throughput variance")
md.append("```")
md.append("\n## Summary\n")
for k,v in summary.items():
    if k!="results":
        md.append(f"- **{k}**: `{v}`")
md.append("\n## Branch Results\n")
for r in rows:
    md.append(f"\n### Node {r['node_id']} / Branch {r['branch_id']}")
    md.append(f"- Work units: `{r['work_units']}`")
    md.append(f"- Elapsed seconds: `{r['elapsed_sec']:.6f}`")
    md.append(f"- Throughput: `{r['work_units_per_sec']:.2f}` work/sec")
    md.append(f"- SHA256: `{r['state_sha256']}`")

(root/"manifest/VERDICT.md").write_text("\n".join(md))
PY

NODES="${1:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)}"
SIZE="${SIZE:-6000}"
ITERS="${ITERS:-200}"

log INFO "nodes=$NODES size=$SIZE iters=$ITERS"

for i in $(seq 1 "$NODES"); do
  python "$ROOT/bench_node.py" "local_node_$i" "$i" "$SIZE" "$ITERS" "$ROOT/results/node_$i.json" \
    > "$ROOT/logs/node_$i.stdout" 2> "$ROOT/logs/node_$i.stderr" &
done

wait
log PASS "all branches complete"

python "$ROOT/reduce.py" "$ROOT"

sha256sum "$ROOT"/results/*.json "$ROOT/manifest/summary.json" "$ROOT/manifest/VERDICT.md" \
  > "$ROOT/manifest/SHA256SUMS.txt"

tar -czf "$ROOT.tar.gz" -C "$(dirname "$ROOT")" "$(basename "$ROOT")"

log PASS "benchmark complete"
log INFO "verdict=$ROOT/manifest/VERDICT.md"
log INFO "summary=$ROOT/manifest/summary.json"
log INFO "archive=$ROOT.tar.gz"

cat "$ROOT/manifest/VERDICT.md"
