#!/usr/bin/env bash
set -Eeuo pipefail

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="$PWD/OMEGA_JULIA_BLAS_DAG_$RUN_ID"
mkdir -p "$ROOT"/{src,results,logs,manifest}

LOG="$ROOT/logs/run.log"
log(){ echo "[$(date -u +%Y%m%dT%H%M%SZ)][Ω-JULIA-BLAS-DAG][$1] $2" | tee -a "$LOG"; }

log INFO "initializing Julia BLAS DAG HPC benchmark"
command -v julia >/dev/null || { log FAIL "Julia not found in this environment"; exit 1; }

export JULIA_NUM_THREADS="${JULIA_NUM_THREADS:-8}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export BLIS_NUM_THREADS="${BLIS_NUM_THREADS:-1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

SIZE="${SIZE:-768}"
REPS="${REPS:-8}"
BRANCHES="${BRANCHES:-8}"

cat > "$ROOT/src/omega_blas_dag.jl" <<'JL'
using LinearAlgebra, Random, SHA, Dates, Statistics, Printf

const ROOT = ARGS[1]
const BRANCHES = parse(Int, ARGS[2])
const SIZE = parse(Int, ARGS[3])
const REPS = parse(Int, ARGS[4])

BLAS.set_num_threads(1)

function readthermal()
    temps = Float64[]
    for z in readdir("/sys/class/thermal"; join=true)
        p = joinpath(z, "temp")
        if isfile(p)
            try
                v = parse(Float64, strip(read(p,String)))
                push!(temps, v > 1000 ? v/1000 : v)
            catch
            end
        end
    end
    isempty(temps) ? missing : maximum(temps)
end

function readfreqs()
    freqs = Int[]
    base = "/sys/devices/system/cpu"
    if isdir(base)
        for cpu in filter(x -> occursin(r"cpu\d+$", x), readdir(base; join=true))
            p = joinpath(cpu, "cpufreq/scaling_cur_freq")
            if isfile(p)
                try push!(freqs, parse(Int, strip(read(p,String)))) catch end
            end
        end
    end
    freqs
end

function sha_vec(x)
    bytes = reinterpret(UInt8, vec(Float64.(x)))
    bytes2hex(sha256(bytes))
end

function branch_compute(branch::Int, n::Int, reps::Int)
    Random.seed!(0xA17A0000 + branch)

    A = randn(Float64, n, n)
    B = randn(Float64, n, n)
    x = randn(Float64, n)

    # branch-divergent deterministic operator perturbation
    λ = 1.0 + branch / 1000
    A .*= λ
    B .*= (2.0 - λ)

    t0 = time()
    temp0 = readthermal()
    freq0 = readfreqs()

    y = zeros(Float64, n)
    checksum_acc = 0.0

    for r in 1:reps
        C = mul!(Matrix{Float64}(undef,n,n), A, B)
        y = mul!(y, C, x)
        checksum_acc += sum(abs2, y) / (r + branch)
        A, B = B, C ./ n
    end

    elapsed = time() - t0
    temp1 = readthermal()
    freq1 = readfreqs()

    state_hash = sha_vec(y)
    gflops_est = (2.0 * n^3 * reps + 2.0 * n^2 * reps) / elapsed / 1e9

    return Dict(
        "branch" => branch,
        "size" => n,
        "reps" => reps,
        "elapsed_sec" => elapsed,
        "estimated_gflops" => gflops_est,
        "checksum" => checksum_acc,
        "state_sha256" => state_hash,
        "thermal_start_c" => temp0,
        "thermal_end_c" => temp1,
        "freq_start_khz" => freq0,
        "freq_end_khz" => freq1,
        "blas_threads" => BLAS.get_num_threads(),
        "julia_threads" => Threads.nthreads()
    )
end

println("[Ω] Julia threads=", Threads.nthreads(), " BLAS threads=", BLAS.get_num_threads())
println("[Ω] branches=", BRANCHES, " size=", SIZE, " reps=", REPS)

results = Vector{Any}(undef, BRANCHES)

tglobal = time()
Threads.@threads for b in 1:BRANCHES
    results[b] = branch_compute(b, SIZE, REPS)
end
wall = time() - tglobal

hash_join = join([r["state_sha256"] for r in results], "")
combined_hash = bytes2hex(sha256(hash_join))

elapsed = [r["elapsed_sec"] for r in results]
gflops = [r["estimated_gflops"] for r in results]
hash_unique = length(unique([r["state_sha256"] for r in results]))

summary = Dict(
    "run_utc" => string(now(UTC)),
    "branches" => BRANCHES,
    "matrix_size" => SIZE,
    "reps" => REPS,
    "julia_threads" => Threads.nthreads(),
    "blas_threads_per_branch" => BLAS.get_num_threads(),
    "wall_elapsed_sec" => wall,
    "sum_branch_elapsed_sec" => sum(elapsed),
    "critical_path_elapsed_sec" => maximum(elapsed),
    "mean_branch_elapsed_sec" => mean(elapsed),
    "min_branch_elapsed_sec" => minimum(elapsed),
    "max_branch_elapsed_sec" => maximum(elapsed),
    "total_estimated_gflops_sum" => sum(gflops),
    "effective_wall_gflops" => sum(2.0 * SIZE^3 * REPS + 2.0 * SIZE^2 * REPS for _ in 1:BRANCHES) / wall / 1e9,
    "unique_branch_hashes" => hash_unique,
    "combined_state_sha256" => combined_hash,
    "results" => results
)

function json_escape(s)
    replace(string(s), "\\"=>"\\\\", "\""=>"\\\"", "\n"=>"\\n")
end

function tojson(x)
    if x === missing
        return "null"
    elseif x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa Number || x isa Bool
        return string(x)
    elseif x isa Vector
        return "[" * join(map(tojson,x), ",") * "]"
    elseif x isa Dict
        parts = String[]
        for k in sort(collect(keys(x)); by=string)
            push!(parts, tojson(string(k)) * ":" * tojson(x[k]))
        end
        return "{" * join(parts,",") * "}"
    else
        return tojson(string(x))
    end
end

write(joinpath(ROOT,"results","summary.json"), tojson(summary))

open(joinpath(ROOT,"manifest","VERDICT.md"), "w") do io
    println(io, "# Ω Julia BLAS DAG HPC Benchmark Verdict\n")
    println(io, "## Operator Chain\n")
    println(io, "```text")
    println(io, "ψ_initial  = seeded Float64 matrix/vector state")
    println(io, "ψ_branch_i = O_BLAS_i ψ_initial")
    println(io, "ψ_final    = O_reduce ∘ (⊕ᵢ O_BLAS_i) ψ_initial")
    println(io, "O_total    = O_reduce ∘ O_thermal ∘ O_SIMD ∘ O_BLAS ∘ O_branch")
    println(io, "Ω(Oψ)      = combined_state_sha256")
    println(io, "heat_trace(O) = thermal_start/end + critical path timing")
    println(io, "curvature(ψ)  = branch timing variance + GFLOPS spread")
    println(io, "```")
    println(io, "\n## Saturation Summary\n")
    println(io, "- Julia threads: `$(Threads.nthreads())`")
    println(io, "- BLAS threads per branch: `$(BLAS.get_num_threads())`")
    println(io, "- DAG branches: `$BRANCHES`")
    println(io, "- Matrix size: `$SIZE x $SIZE`")
    println(io, "- Reps per branch: `$REPS`")
    println(io, "- Wall elapsed sec: `$(@sprintf("%.6f", wall))`")
    println(io, "- Critical path sec: `$(@sprintf("%.6f", maximum(elapsed)))`")
    println(io, "- Effective wall GFLOPS: `$(@sprintf("%.4f", summary["effective_wall_gflops"]))`")
    println(io, "- Sum branch GFLOPS: `$(@sprintf("%.4f", sum(gflops)))`")
    println(io, "- Unique branch hashes: `$hash_unique / $BRANCHES`")
    println(io, "- Combined Ω hash: `$combined_hash`")
    println(io, "\n## Branch Results\n")
    for r in results
        println(io, "### Branch $(r["branch"])")
        println(io, "- elapsed_sec: `$(@sprintf("%.6f", r["elapsed_sec"]))`")
        println(io, "- estimated_gflops: `$(@sprintf("%.4f", r["estimated_gflops"]))`")
        println(io, "- thermal_start_c: `$(r["thermal_start_c"])`")
        println(io, "- thermal_end_c: `$(r["thermal_end_c"])`")
        println(io, "- state_sha256: `$(r["state_sha256"])`")
        println(io)
    end
end
JL

log INFO "running Julia DAG with JULIA_NUM_THREADS=$JULIA_NUM_THREADS"
julia --threads "$JULIA_NUM_THREADS" "$ROOT/src/omega_blas_dag.jl" "$ROOT" "$BRANCHES" "$SIZE" "$REPS" | tee "$ROOT/logs/julia.stdout"

sha256sum "$ROOT/src/omega_blas_dag.jl" "$ROOT/results/summary.json" "$ROOT/manifest/VERDICT.md" \
  > "$ROOT/manifest/SHA256SUMS.txt"

tar -czf "$ROOT.tar.gz" -C "$(dirname "$ROOT")" "$(basename "$ROOT")"

log PASS "complete"
log INFO "verdict=$ROOT/manifest/VERDICT.md"
log INFO "summary=$ROOT/results/summary.json"
log INFO "archive=$ROOT.tar.gz"

cat "$ROOT/manifest/VERDICT.md"
