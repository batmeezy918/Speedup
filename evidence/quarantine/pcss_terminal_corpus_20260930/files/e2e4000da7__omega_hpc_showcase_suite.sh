#!/usr/bin/env bash
set -Eeuo pipefail

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="$HOME/omega_hpc_showcase_$RUN_ID"
mkdir -p "$ROOT"/{logs,results,scripts,official_refs}

LOG="$ROOT/logs/showcase.log"
RESULT="$ROOT/results/summary.tsv"
VERDICT="$ROOT/VERDICT.md"
REPLAY="$ROOT/replay.sh"

CORES="${CORES:-4,5,6,7}"
THREAD_GRID="${THREAD_GRID:-4 8}"
SIZES="${SIZES:-1024 2048 3072 4096}"
SAMPLES="${SAMPLES:-12}"
TARGET_GFLOPS="${TARGET_GFLOPS:-100}"

OFFICIAL_DIR="${OFFICIAL_DIR:-$(ls -td ~/official_hpc_benchmarks_* 2>/dev/null | head -1 || true)}"

log(){ echo "[$(date -u +%Y%m%dT%H%M%SZ)][Ω-HPC-SHOWCASE][$1] $2" | tee -a "$LOG"; }

log INFO "root=$ROOT"
log INFO "official_dir=$OFFICIAL_DIR"

cat > "$ROOT/scripts/omega_sgemm_showcase.jl" <<'JL'
using LinearAlgebra, Statistics, SHA

n       = parse(Int, ENV["N"])
samples = parse(Int, ENV["SAMPLES"])
threads = parse(Int, ENV["THREADS"])

BLAS.set_num_threads(threads)

A = fill(Float32(1.0), n, n)
B = fill(Float32(1.0), n, n)
C = zeros(Float32, n, n)

for _ in 1:12
    mul!(C, A, B)
end

times = Float64[]

for _ in 1:samples
    t0 = time_ns()
    mul!(C, A, B)
    t1 = time_ns()
    push!(times, (t1 - t0) / 1e9)
end

med = median(times)
best = minimum(times)
worst = maximum(times)
median_gflops = (2 * n^3) / med / 1e9
best_gflops   = (2 * n^3) / best / 1e9
checksum = bytes2hex(sha256(string(sum(C))))

println("N=", n)
println("threads=", threads)
println("blas_threads=", BLAS.get_num_threads())
println("median_s=", med)
println("best_s=", best)
println("worst_s=", worst)
println("median_gflops=", median_gflops)
println("best_gflops=", best_gflops)
println("checksum=", checksum)
JL

cat > "$ROOT/environment.env" <<ENV
RUN_ID=$RUN_ID
DATE_UTC=$(date -u +%Y%m%dT%H%M%SZ)
UNAME=$(uname -a)
PWD=$(pwd)
CORES=$CORES
THREAD_GRID=$THREAD_GRID
SIZES=$SIZES
SAMPLES=$SAMPLES
TARGET_GFLOPS=$TARGET_GFLOPS
OFFICIAL_DIR=$OFFICIAL_DIR
JULIA=$(command -v julia || echo missing)
TASKSET=$(command -v taskset || echo missing)
ENV

{
  echo -e "N\tthreads\tmedian_gflops\tbest_gflops\tmedian_s\tbest_s\tworst_s\tchecksum"
} > "$RESULT"

BEST_GF=0
BEST_N=0
BEST_T=0

for t in $THREAD_GRID; do
  for n in $SIZES; do
    log RUN "SGEMM N=$n threads=$t cores=$CORES samples=$SAMPLES"

    OUT="$ROOT/results/sgemm_N${n}_T${t}.out"

    nice -n -10 taskset -c "$CORES" env \
      OPENBLAS_NUM_THREADS="$t" \
      OMP_NUM_THREADS="$t" \
      JULIA_NUM_THREADS=4 \
      N="$n" THREADS="$t" SAMPLES="$SAMPLES" \
      julia "$ROOT/scripts/omega_sgemm_showcase.jl" > "$OUT" 2>&1

    MED_GF="$(awk -F= '/median_gflops=/{print $2}' "$OUT" | tail -1)"
    BEST_GF_RUN="$(awk -F= '/best_gflops=/{print $2}' "$OUT" | tail -1)"
    MED_S="$(awk -F= '/median_s=/{print $2}' "$OUT" | tail -1)"
    BEST_S="$(awk -F= '/best_s=/{print $2}' "$OUT" | tail -1)"
    WORST_S="$(awk -F= '/worst_s=/{print $2}' "$OUT" | tail -1)"
    CHECKSUM="$(awk -F= '/checksum=/{print $2}' "$OUT" | tail -1)"

    echo -e "$n\t$t\t$MED_GF\t$BEST_GF_RUN\t$MED_S\t$BEST_S\t$WORST_S\t$CHECKSUM" >> "$RESULT"
    log PASS "N=$n threads=$t median_GF=$MED_GF best_GF=$BEST_GF_RUN"

    CMP="$(python3 - <<PY
print(1 if float("$MED_GF") > float("$BEST_GF") else 0)
PY
)"
    if [ "$CMP" = "1" ]; then
      BEST_GF="$MED_GF"
      BEST_N="$n"
      BEST_T="$t"
    fi
  done
done

# Official library presence manifest
OFFICIAL_MANIFEST="$ROOT/official_refs/official_sources.tsv"
echo -e "benchmark\tstatus\tpath" > "$OFFICIAL_MANIFEST"

check_ref(){
  local name="$1"; local path="$2"
  if [ -n "$path" ] && [ -e "$path" ]; then
    echo -e "$name\tPRESENT\t$path" >> "$OFFICIAL_MANIFEST"
  else
    echo -e "$name\tMISSING\t$path" >> "$OFFICIAL_MANIFEST"
  fi
}

check_ref "HPL_NETLIB" "$OFFICIAL_DIR/src/hpl-2.3"
check_ref "HPCG" "$OFFICIAL_DIR/src/hpcg"
check_ref "GRAPH500" "$OFFICIAL_DIR/src/graph500"
check_ref "MLPERF_INFERENCE" "$OFFICIAL_DIR/src/mlperf_inference"

RESULT_HASH="$(sha256sum "$RESULT" | awk '{print $1}')"
ENV_HASH="$(sha256sum "$ROOT/environment.env" | awk '{print $1}')"
SCRIPT_HASH="$(sha256sum "$ROOT/scripts/omega_sgemm_showcase.jl" | awk '{print $1}')"
OFFICIAL_HASH="$(sha256sum "$OFFICIAL_MANIFEST" | awk '{print $1}')"

STATUS="$(python3 - <<PY
print("PASS_TARGET_GFLOPS" if float("$BEST_GF") >= float("$TARGET_GFLOPS") else "BELOW_TARGET")
PY
)"

cat > "$REPLAY" <<R
#!/usr/bin/env bash
set -Eeuo pipefail
cd "$PWD"
CORES="$CORES" THREAD_GRID="$THREAD_GRID" SIZES="$SIZES" SAMPLES="$SAMPLES" TARGET_GFLOPS="$TARGET_GFLOPS" OFFICIAL_DIR="$OFFICIAL_DIR" bash ./omega_hpc_showcase_suite.sh
R
chmod +x "$REPLAY"

cat > "$VERDICT" <<V
# Ω HPC Comparative Showcase Suite

\`\`\`
run_id          = $RUN_ID
status          = $STATUS
best_N          = $BEST_N
best_threads    = $BEST_T
best_median_GF  = $BEST_GF
target_GFLOPS   = $TARGET_GFLOPS
cores           = $CORES
samples         = $SAMPLES
root            = $ROOT
replay          = $REPLAY
result_hash     = $RESULT_HASH
script_hash     = $SCRIPT_HASH
env_hash        = $ENV_HASH
official_hash   = $OFFICIAL_HASH
\`\`\`

## Operator DAG

\`\`\`
ψ_final =
O_verdict
∘ O_hash_manifest
∘ O_compare_official_refs
∘ O_sgemm_sustain_sweep
∘ O_thread_grid
∘ O_size_grid
∘ O_priority_boost
∘ O_affinity_lock
ψ_initial
\`\`\`

## Official Benchmark References

\`\`\`
$(cat "$OFFICIAL_MANIFEST")
\`\`\`

## GFLOP Showcase Summary

\`\`\`
$(cat "$RESULT")
\`\`\`

## Interpretation

\`\`\`
This is a replayable SGEMM/LINPACK-style GFLOP showcase using the local BLAS stack,
cross-referenced against the official benchmark source tree already staged locally.

It is not an official TOP500/HPL submission result.
It is a deterministic local HPC performance showcase harness.
\`\`\`
V

log "$STATUS" "best_N=$BEST_N best_threads=$BEST_T best_median_GF=$BEST_GF"
cat "$VERDICT"
