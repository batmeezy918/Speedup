#!/usr/bin/env bash
set -Eeuo pipefail

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="$PWD/OMEGA_JULIA_BLAS_DAG_TURBO_$RUN_ID"
mkdir -p "$ROOT"/{src,results,logs,manifest}

LOG="$ROOT/logs/run.log"
log(){ echo "[$(date -u +%Y%m%dT%H%M%SZ)][Ω-BLAS-TURBO][$1] $2" | tee -a "$LOG"; }

command -v julia >/dev/null || { log FAIL "Julia missing"; exit 1; }

SIZE="${SIZE:-1024}"
REPS="${REPS:-10}"

cat > "$ROOT/src/turbo_blas_dag.jl" <<'JL'
using LinearAlgebra, Random, SHA, Statistics, Dates, Printf

ROOT=ARGS[1]
SIZE=parse(Int,ARGS[2])
REPS=parse(Int,ARGS[3])

modes = [
    (8,1),  # 8 DAG branches, 1 BLAS thread each
    (4,2),  # 4 branches, 2 BLAS threads each
    (2,4),  # 2 branches, 4 BLAS threads each
    (1,8)   # 1 branch, 8 BLAS threads
]

function sha_vec(x)
    bytes2hex(sha256(reinterpret(UInt8, vec(Float64.(x)))))
end

function compute_branch(branch,n,reps)
    Random.seed!(0xA17A0000 + branch)
    A=randn(Float64,n,n)
    B=randn(Float64,n,n)
    C=Matrix{Float64}(undef,n,n)
    x=randn(Float64,n)
    y=zeros(Float64,n)

    λ=1.0 + branch/1000
    A .*= λ
    B .*= 2.0-λ

    t0=time()
    for r in 1:reps
        mul!(C,A,B)
        mul!(y,C,x)
        A,B = B,C ./ n
    end
    elapsed=time()-t0

    Dict(
        "branch"=>branch,
        "elapsed_sec"=>elapsed,
        "gflops"=>(2.0*n^3*reps + 2.0*n^2*reps)/elapsed/1e9,
        "sha256"=>sha_vec(y)
    )
end

allruns=[]

for (branches,blas_threads) in modes
    BLAS.set_num_threads(blas_threads)
    GC.gc()

    results=Vector{Any}(undef,branches)
    t0=time()
    Threads.@threads for b in 1:branches
        results[b]=compute_branch(b,SIZE,REPS)
    end
    wall=time()-t0

    combined=bytes2hex(sha256(join([r["sha256"] for r in results],"")))
    work=sum(2.0*SIZE^3*REPS + 2.0*SIZE^2*REPS for _ in 1:branches)
    wall_gflops=work/wall/1e9

    push!(allruns, Dict(
        "branches"=>branches,
        "blas_threads"=>blas_threads,
        "julia_threads"=>Threads.nthreads(),
        "wall_sec"=>wall,
        "effective_wall_gflops"=>wall_gflops,
        "sum_branch_gflops"=>sum(r["gflops"] for r in results),
        "unique_hashes"=>length(unique([r["sha256"] for r in results])),
        "combined_sha256"=>combined,
        "results"=>results
    ))
end

best = sort(allruns, by=x->x["effective_wall_gflops"], rev=true)[1]

function esc(s) replace(string(s), "\\"=>"\\\\", "\""=>"\\\"", "\n"=>"\\n") end
function js(x)
    x isa String && return "\""*esc(x)*"\""
    x isa Number && return string(x)
    x isa Bool && return string(x)
    x isa Vector && return "["*join(js.(x),",")*"]"
    x isa Dict && return "{"*join([js(string(k))*":"*js(v) for (k,v) in sort(collect(x), by=p->string(p[1]))],",")*"}"
    return js(string(x))
end

summary=Dict(
    "run_utc"=>string(now(UTC)),
    "matrix_size"=>SIZE,
    "reps"=>REPS,
    "modes_tested"=>allruns,
    "best_mode"=>best
)

write(joinpath(ROOT,"results","summary.json"), js(summary))

open(joinpath(ROOT,"manifest","VERDICT.md"),"w") do io
    println(io,"# Ω Julia BLAS DAG TURBO Verdict\n")
    println(io,"## Best Throughput Mode\n")
    println(io,"- Branches: `$(best["branches"])`")
    println(io,"- BLAS threads per branch: `$(best["blas_threads"])`")
    println(io,"- Julia threads: `$(best["julia_threads"])`")
    println(io,"- Wall sec: `$(@sprintf("%.6f", best["wall_sec"]))`")
    println(io,"- Effective wall GFLOPS: `$(@sprintf("%.4f", best["effective_wall_gflops"]))`")
    println(io,"- Sum branch GFLOPS: `$(@sprintf("%.4f", best["sum_branch_gflops"]))`")
    println(io,"- Unique hashes: `$(best["unique_hashes"]) / $(best["branches"])`")
    println(io,"- Ω hash: `$(best["combined_sha256"])`")
    println(io,"\n## Operator Form\n```text")
    println(io,"ψ_final = O_reduce ∘ O_autotune ∘ (⊕ᵢ O_BLAS_i) ψ_initial")
    println(io,"O_total = O_reduce ∘ O_select_max_GFLOPS ∘ O_SIMD ∘ O_BLAS ∘ O_branch")
    println(io,"Ω(Oψ) = combined_sha256")
    println(io,"heat_trace(O) = wall_sec across modes")
    println(io,"curvature(ψ) = GFLOPS spread across modes")
    println(io,"```")
    println(io,"\n## All Tested Modes\n")
    for r in allruns
        println(io,"### Mode $(r["branches"]) branches × $(r["blas_threads"]) BLAS threads")
        println(io,"- Wall sec: `$(@sprintf("%.6f", r["wall_sec"]))`")
        println(io,"- Effective wall GFLOPS: `$(@sprintf("%.4f", r["effective_wall_gflops"]))`")
        println(io,"- Ω hash: `$(r["combined_sha256"])`\n")
    end
end
JL

export JULIA_NUM_THREADS="${JULIA_NUM_THREADS:-8}"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1

log INFO "running turbo autotune SIZE=$SIZE REPS=$REPS JULIA_NUM_THREADS=$JULIA_NUM_THREADS"

julia --threads "$JULIA_NUM_THREADS" "$ROOT/src/turbo_blas_dag.jl" "$ROOT" "$SIZE" "$REPS" | tee "$ROOT/logs/julia.stdout"

sha256sum "$ROOT/src/turbo_blas_dag.jl" "$ROOT/results/summary.json" "$ROOT/manifest/VERDICT.md" > "$ROOT/manifest/SHA256SUMS.txt"
tar -czf "$ROOT.tar.gz" -C "$(dirname "$ROOT")" "$(basename "$ROOT")"

log PASS "complete"
log INFO "verdict=$ROOT/manifest/VERDICT.md"
log INFO "archive=$ROOT.tar.gz"

cat "$ROOT/manifest/VERDICT.md"
