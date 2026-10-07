#!/usr/bin/env bash
set -Eeuo pipefail

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="$PWD/OMEGA_JULIA_BLAS_DAG_TURBO_V2_$RUN_ID"
mkdir -p "$ROOT"/{src,results,logs,manifest}

LOG="$ROOT/logs/run.log"
log(){ echo "[$(date -u +%Y%m%dT%H%M%SZ)][Ω-BLAS-TURBO-V2][$1] $2" | tee -a "$LOG"; }

command -v julia >/dev/null || { log FAIL "Julia missing"; exit 1; }

SIZE="${SIZE:-1024}"
REPS="${REPS:-10}"
TRIALS="${TRIALS:-5}"
JULIA_NUM_THREADS="${JULIA_NUM_THREADS:-8}"

# Optional custom modes:
#   MODES="8x1,4x2,2x4,1x8"
MODES="${MODES:-AUTO}"

# Tie / stability controls.
MIN_WIN_MARGIN="${MIN_WIN_MARGIN:-0.01}"   # 1% median GFLOPS margin
PIN_CPU="${PIN_CPU:-0}"                    # PIN_CPU=1 uses taskset if available
SEED_BASE="${SEED_BASE:-2707423232}"

export JULIA_NUM_THREADS
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export BLIS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export LC_ALL=C
export LANG=C

log INFO "root=$ROOT"
log INFO "SIZE=$SIZE REPS=$REPS TRIALS=$TRIALS JULIA_NUM_THREADS=$JULIA_NUM_THREADS MODES=$MODES"

{
  echo "# Ω Julia BLAS DAG Turbo V2 Environment"
  echo
  echo "## Runtime"
  echo "- run_utc: $RUN_ID"
  echo "- pwd: $PWD"
  echo "- SIZE: $SIZE"
  echo "- REPS: $REPS"
  echo "- TRIALS: $TRIALS"
  echo "- JULIA_NUM_THREADS: $JULIA_NUM_THREADS"
  echo "- MODES: $MODES"
  echo "- MIN_WIN_MARGIN: $MIN_WIN_MARGIN"
  echo "- PIN_CPU: $PIN_CPU"
  echo
  echo "## System"
  uname -a || true
  echo
  echo "## CPU"
  if command -v lscpu >/dev/null; then lscpu || true; fi
  echo
  echo "## Julia"
  julia --version || true
} > "$ROOT/manifest/ENVIRONMENT.md"

cat > "$ROOT/src/turbo_blas_dag_v2.jl" <<'JL'
using LinearAlgebra
using Random
using SHA
using Statistics
using Dates
using Printf
using InteractiveUtils

const ROOT = ARGS[1]
const SIZE = parse(Int, ARGS[2])
const REPS = parse(Int, ARGS[3])
const TRIALS = parse(Int, ARGS[4])
const MODE_SPEC = ARGS[5]
const MIN_WIN_MARGIN = parse(Float64, ARGS[6])
const SEED_BASE = parse(UInt64, ARGS[7])

function esc(s)
    replace(string(s), "\\"=>"\\\\", "\""=>"\\\"", "\n"=>"\\n", "\t"=>"\\t")
end

function js(x)
    x === nothing && return "null"
    x isa String && return "\"" * esc(x) * "\""
    x isa Integer && return string(x)
    x isa AbstractFloat && return isfinite(x) ? @sprintf("%.17g", x) : js(string(x))
    x isa Bool && return x ? "true" : "false"
    x isa Vector && return "[" * join(js.(x), ",") * "]"
    x isa Tuple && return "[" * join(js.(collect(x)), ",") * "]"
    x isa Dict && return "{" * join([js(string(k))*":"*js(v) for (k,v) in sort(collect(x), by=p->string(p[1]))], ",") * "}"
    return js(string(x))
end

function sha_vec64(x::Vector{Float64})
    bytes2hex(sha256(reinterpret(UInt8, x)))
end

function parse_modes(spec::String, T::Int)
    if spec != "AUTO"
        pairs = Tuple{Int,Int}[]
        for token in split(spec, ",")
            m = split(strip(token), "x")
            length(m) == 2 || error("Bad mode token: $token. Expected e.g. 8x1")
            branches = parse(Int, m[1])
            blas_threads = parse(Int, m[2])
            branches >= 1 || error("branches must be >= 1")
            blas_threads >= 1 || error("blas_threads must be >= 1")
            push!(pairs, (branches, blas_threads))
        end
        return unique(pairs)
    end

    vals = Int[]
    push!(vals, 1)
    push!(vals, T)

    p = 1
    while p <= T
        push!(vals, p)
        p *= 2
    end

    for d in 1:T
        if T % d == 0
            push!(vals, d)
        end
    end

    vals = sort(unique(filter(x -> x >= 1 && x <= T, vals)))

    pairs = Tuple{Int,Int}[]
    for branches in vals
        blas_threads = max(1, fld(T, branches))
        if branches * blas_threads <= T
            push!(pairs, (branches, blas_threads))
        end
    end
    for blas_threads in vals
        branches = max(1, fld(T, blas_threads))
        if branches * blas_threads <= T
            push!(pairs, (branches, blas_threads))
        end
    end

    pairs = unique(pairs)

    # Prefer high occupancy, then more branches, then fewer BLAS threads.
    sort!(pairs, by = x -> (x[1]*x[2], x[1], -x[2]), rev=true)

    return pairs
end

function median_abs_dev(xs)
    m = median(xs)
    return median(abs.(xs .- m))
end

function compute_branch(branch::Int, n::Int, reps::Int, seed_base::UInt64)
    seed = Int(mod(seed_base + UInt64(branch) * UInt64(0x9E3779B97F4A7C15), UInt64(typemax(Int))))
    rng = MersenneTwister(seed)

    A = randn(rng, Float64, n, n)
    B = randn(rng, Float64, n, n)
    C = Matrix{Float64}(undef, n, n)
    T = Matrix{Float64}(undef, n, n)

    x = randn(rng, Float64, n)
    y = zeros(Float64, n)

    λ = 1.0 + branch / 1000.0
    A .*= λ
    B .*= 2.0 - λ

    invn = 1.0 / n

    GC.gc()
    old_gc = GC.enable(false)
    t0 = time()

    for _ in 1:reps
        mul!(C, A, B)
        mul!(y, C, x)

        @inbounds @simd for i in eachindex(T)
            T[i] = C[i] * invn
        end

        A, B, T = B, T, A
    end

    elapsed = time() - t0
    GC.enable(old_gc)

    flops = 2.0*n^3*reps + 2.0*n^2*reps

    return Dict(
        "branch" => branch,
        "elapsed_sec" => elapsed,
        "gflops" => flops / elapsed / 1e9,
        "sha256" => sha_vec64(y)
    )
end

function run_mode(branches::Int, blas_threads::Int, trial::Int)
    BLAS.set_num_threads(blas_threads)

    # Compile / warm up outside measured mode wall.
    if trial == 1
        warm_n = min(128, SIZE)
        _ = compute_branch(10_000 + branches + blas_threads, warm_n, 1, SEED_BASE)
        GC.gc()
    end

    results = Vector{Any}(undef, branches)

    GC.gc()
    old_gc = GC.enable(false)
    t0 = time()

    Threads.@threads for b in 1:branches
        results[b] = compute_branch(b, SIZE, REPS, SEED_BASE)
    end

    wall = time() - t0
    GC.enable(old_gc)

    hashes = [r["sha256"] for r in results]
    combined = bytes2hex(sha256(join(hashes, "")))

    work = sum(2.0*SIZE^3*REPS + 2.0*SIZE^2*REPS for _ in 1:branches)
    wall_gflops = work / wall / 1e9

    return Dict(
        "trial" => trial,
        "branches" => branches,
        "blas_threads" => blas_threads,
        "julia_threads" => Threads.nthreads(),
        "blas_config" => string(BLAS.get_config()),
        "wall_sec" => wall,
        "effective_wall_gflops" => wall_gflops,
        "sum_branch_gflops" => sum(r["gflops"] for r in results),
        "unique_branch_hashes" => length(unique(hashes)),
        "combined_sha256" => combined,
        "results" => results
    )
end

function summarize_mode(branches::Int, blas_threads::Int, trials::Vector)
    gf = [t["effective_wall_gflops"] for t in trials]
    wall = [t["wall_sec"] for t in trials]
    hashes = [t["combined_sha256"] for t in trials]

    return Dict(
        "branches" => branches,
        "blas_threads" => blas_threads,
        "julia_threads" => Threads.nthreads(),
        "trials" => trials,
        "median_wall_sec" => median(wall),
        "min_wall_sec" => minimum(wall),
        "max_wall_sec" => maximum(wall),
        "median_effective_wall_gflops" => median(gf),
        "max_effective_wall_gflops" => maximum(gf),
        "min_effective_wall_gflops" => minimum(gf),
        "mad_effective_wall_gflops" => median_abs_dev(gf),
        "hashes_stable" => length(unique(hashes)) == 1,
        "unique_trial_hashes" => length(unique(hashes)),
        "representative_sha256" => hashes[argmax(gf)]
    )
end

function verdict_for(summaries)
    ordered = sort(summaries, by=x -> x["median_effective_wall_gflops"], rev=true)
    best = ordered[1]
    second = length(ordered) >= 2 ? ordered[2] : nothing

    confidence = "DEFINITE"
    margin = Inf

    if second !== nothing
        margin = (
            best["median_effective_wall_gflops"] -
            second["median_effective_wall_gflops"]
        ) / max(second["median_effective_wall_gflops"], eps())

        if margin < MIN_WIN_MARGIN
            confidence = "NEAR_TIE_DETERMINISTIC_TIEBREAK"
        end
    end

    unstable_hash_modes = [
        "$(s["branches"])x$(s["blas_threads"])" for s in summaries if !s["hashes_stable"]
    ]

    if !isempty(unstable_hash_modes)
        confidence = confidence == "DEFINITE" ? "FAST_BUT_HASH_UNSTABLE" : confidence * "_HASH_UNSTABLE"
    end

    return Dict(
        "confidence" => confidence,
        "best_mode" => best,
        "second_mode" => second,
        "relative_margin_over_second" => margin,
        "unstable_hash_modes" => unstable_hash_modes
    )
end

modes = parse_modes(MODE_SPEC, Threads.nthreads())

all_mode_summaries = Any[]

for (branches, blas_threads) in modes
    println("[$(now(UTC))] MODE branches=$branches blas_threads=$blas_threads")
    flush(stdout)

    trials = Any[]
    for trial in 1:TRIALS
        r = run_mode(branches, blas_threads, trial)
        push!(trials, r)

        @printf(
            "[%s] trial=%d mode=%dx%d wall=%.6f gflops=%.4f hash=%s\n",
            string(now(UTC)),
            trial,
            branches,
            blas_threads,
            r["wall_sec"],
            r["effective_wall_gflops"],
            r["combined_sha256"]
        )
        flush(stdout)
    end

    push!(all_mode_summaries, summarize_mode(branches, blas_threads, trials))
end

verdict = verdict_for(all_mode_summaries)

summary = Dict(
    "run_utc" => string(now(UTC)),
    "matrix_size" => SIZE,
    "reps" => REPS,
    "trials" => TRIALS,
    "mode_spec" => MODE_SPEC,
    "julia_threads" => Threads.nthreads(),
    "blas_vendor" => string(BLAS.get_config()),
    "seed_base" => string(SEED_BASE),
    "modes_tested" => all_mode_summaries,
    "verdict" => verdict
)

write(joinpath(ROOT, "results", "summary.json"), js(summary))

open(joinpath(ROOT, "manifest", "VERDICT.md"), "w") do io
    best = verdict["best_mode"]
    second = verdict["second_mode"]

    println(io, "# Ω Julia BLAS DAG TURBO V2 Verdict\n")

    println(io, "## Definitive Selection\n")
    println(io, "- Verdict confidence: `$(verdict["confidence"])`")
    println(io, "- Relative margin over second: `$(isfinite(verdict["relative_margin_over_second"]) ? @sprintf("%.6f", verdict["relative_margin_over_second"]) : "INF")`")
    println(io, "- Best branches: `$(best["branches"])`")
    println(io, "- Best BLAS threads per branch: `$(best["blas_threads"])`")
    println(io, "- Julia threads: `$(best["julia_threads"])`")
    println(io, "- Median wall sec: `$(@sprintf("%.6f", best["median_wall_sec"]))`")
    println(io, "- Median effective wall GFLOPS: `$(@sprintf("%.4f", best["median_effective_wall_gflops"]))`")
    println(io, "- Max effective wall GFLOPS: `$(@sprintf("%.4f", best["max_effective_wall_gflops"]))`")
    println(io, "- MAD effective wall GFLOPS: `$(@sprintf("%.6f", best["mad_effective_wall_gflops"]))`")
    println(io, "- Hashes stable across trials: `$(best["hashes_stable"])`")
    println(io, "- Unique trial hashes: `$(best["unique_trial_hashes"])`")
    println(io, "- Ω representative hash: `$(best["representative_sha256"])`")

    if second !== nothing
        println(io, "\n## Second Place\n")
        println(io, "- Branches: `$(second["branches"])`")
        println(io, "- BLAS threads per branch: `$(second["blas_threads"])`")
        println(io, "- Median effective wall GFLOPS: `$(@sprintf("%.4f", second["median_effective_wall_gflops"]))`")
    end

    println(io, "\n## Determinism Notes\n")
    if isempty(verdict["unstable_hash_modes"])
        println(io, "- All tested modes produced stable combined hashes across trials.")
    else
        println(io, "- Hash instability detected in modes: `$(join(verdict["unstable_hash_modes"], ", "))`")
        println(io, "- This usually indicates BLAS/vendor/runtime floating-point ordering differences under threading.")
    end

    println(io, "\n## Operator Form\n")
    println(io, "```text")
    println(io, "ψ_final = O_reduce ∘ O_autotune ∘ O_median_select ∘ (⊕ᵢ O_BLAS_i) ψ_initial")
    println(io, "O_total = O_reduce ∘ O_select_median_max_GFLOPS ∘ O_hash_verify ∘ O_SIMD ∘ O_BLAS ∘ O_branch")
    println(io, "Ω(Oψ) = representative_sha256")
    println(io, "heat_trace(O) = median_wall_sec across modes")
    println(io, "curvature(ψ) = GFLOPS dispersion / MAD across modes")
    println(io, "stability(ψ) = hash_stability ∧ median_margin")
    println(io, "```")

    println(io, "\n## All Tested Modes\n")
    for s in sort(all_mode_summaries, by=x -> x["median_effective_wall_gflops"], rev=true)
        println(io, "### Mode $(s["branches"]) branches × $(s["blas_threads"]) BLAS threads\n")
        println(io, "- Median wall sec: `$(@sprintf("%.6f", s["median_wall_sec"]))`")
        println(io, "- Min wall sec: `$(@sprintf("%.6f", s["min_wall_sec"]))`")
        println(io, "- Max wall sec: `$(@sprintf("%.6f", s["max_wall_sec"]))`")
        println(io, "- Median effective wall GFLOPS: `$(@sprintf("%.4f", s["median_effective_wall_gflops"]))`")
        println(io, "- Max effective wall GFLOPS: `$(@sprintf("%.4f", s["max_effective_wall_gflops"]))`")
        println(io, "- MAD effective wall GFLOPS: `$(@sprintf("%.6f", s["mad_effective_wall_gflops"]))`")
        println(io, "- Hashes stable: `$(s["hashes_stable"])`")
        println(io, "- Ω representative hash: `$(s["representative_sha256"])`")
        println(io)
    end
end
JL

sha256sum "$ROOT/src/turbo_blas_dag_v2.jl" > "$ROOT/manifest/SOURCE_SHA256SUMS.txt"

JULIA_CMD=(julia --threads "$JULIA_NUM_THREADS" "$ROOT/src/turbo_blas_dag_v2.jl" "$ROOT" "$SIZE" "$REPS" "$TRIALS" "$MODES" "$MIN_WIN_MARGIN" "$SEED_BASE")

if [[ "$PIN_CPU" == "1" ]] && command -v taskset >/dev/null; then
  LAST_CPU=$((JULIA_NUM_THREADS - 1))
  log INFO "using taskset CPU range 0-$LAST_CPU"
  taskset -c "0-$LAST_CPU" "${JULIA_CMD[@]}" | tee "$ROOT/logs/julia.stdout"
else
  "${JULIA_CMD[@]}" | tee "$ROOT/logs/julia.stdout"
fi

sha256sum \
  "$ROOT/src/turbo_blas_dag_v2.jl" \
  "$ROOT/results/summary.json" \
  "$ROOT/manifest/VERDICT.md" \
  "$ROOT/manifest/ENVIRONMENT.md" \
  > "$ROOT/manifest/SHA256SUMS.txt"

tar -czf "$ROOT.tar.gz" -C "$(dirname "$ROOT")" "$(basename "$ROOT")"

log PASS "complete"
log INFO "verdict=$ROOT/manifest/VERDICT.md"
log INFO "summary=$ROOT/results/summary.json"
log INFO "archive=$ROOT.tar.gz"

cat "$ROOT/manifest/VERDICT.md"
