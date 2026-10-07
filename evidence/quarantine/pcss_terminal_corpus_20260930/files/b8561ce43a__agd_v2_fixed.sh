#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# AGD DEFINITIVE BENCHMARK v2 (FIXED) — no ordering errors
#
# Usage:
#   bash agd_v2_fixed.sh              # 10000 cases, seed 20260809
#   bash agd_v2_fixed.sh 5000         # 5000 cases
#   bash agd_v2_fixed.sh 5000 12345   # custom seed
# =============================================================================

CASES="${1:-10000}"
SEED="${2:-20260809}"
ROOT="$(pwd)"
BENCH="$ROOT/agd_v2_fixed.jl"
REPORT="$ROOT/agd_v2_fixed_results.txt"

echo "============================================================"
echo " AGD DEFINITIVE BENCHMARK v2 (FIXED)"
echo "============================================================"
echo "Cases: $CASES"
echo "Seed : $SEED"
echo

if ! [[ "$CASES" =~ ^[0-9]+$ ]] || (( CASES < 100 )); then
  echo "[ERROR] Cases must be an integer >= 100."
  exit 2
fi

if ! [[ "$SEED" =~ ^[0-9]+$ ]]; then
  echo "[ERROR] Seed must be an integer."
  exit 2
fi

if ! command -v julia >/dev/null 2>&1; then
  echo "[ERROR] Julia is not installed or not in PATH."
  exit 127
fi

echo "[OK] $(julia --version)"
echo "[OK] Working directory: $ROOT"
echo

echo "[1/2] Writing benchmark source..."
cat > "$BENCH" <<'JULIA_END'
#!/usr/bin/env julia
using Random, Statistics, LinearAlgebra, Printf, SHA, Dates

# -----------------------------------------------------------------------------
# Parameters
# -----------------------------------------------------------------------------
const NPAIRS = length(ARGS)>=1 ? parse(Int, ARGS[1]) : 100_000
const SEED   = length(ARGS)>=2 ? parse(Int, ARGS[2]) : 20260809
const NSEM   = min(10_000, NPAIRS)
const NIDEM  = min(10_000, NPAIRS)
const NTIME  = min(5_000, NPAIRS)          # timing loops per depth
const REPLAY_REPEATS = 3
const MATRIX_SIZES = (5,10,25,50,100)
const MAX_DEPTH = 10
const SCALING_DEPTHS = [2,4,6,8,10,15,20]  # for complexity scaling

NPAIRS >= 100 || error("Use at least 100 pairs")

# -----------------------------------------------------------------------------
# Expression types
# -----------------------------------------------------------------------------
abstract type Op end
struct Leaf <: Op; name::Symbol; end
struct Mul <: Op; a::Op; b::Op; end
struct T <: Op; x::Op; end
struct Invariants; symmetric::Set{Symbol}; end

canon(x::Op)::String =
    x isa Leaf ? string(x.name) :
    x isa T   ? "T($(canon(x.x)))" :
    x isa Mul ? "M($(canon(x.a)),$(canon(x.b)))" :
    error("unknown Op")
hashcanon(x) = bytes2hex(sha256(canon(x)))

# -----------------------------------------------------------------------------
# Projection (Π)
# -----------------------------------------------------------------------------
function projection_pass(x::Op, inv::Invariants)
    if x isa Leaf
        return x, 0
    elseif x isa T
        y,k = projection_pass(x.x, inv)
        if y isa T
            return y.x, k+1
        elseif y isa Mul
            return Mul(T(y.b), T(y.a)), k+1
        elseif y isa Leaf && y.name in inv.symmetric
            return y, k+1
        else
            return T(y), k
        end
    elseif x isa Mul
        a,ka = projection_pass(x.a, inv)
        b,kb = projection_pass(x.b, inv)
        return Mul(a,b), ka+kb
    end
    error("unknown Op")
end

function project(x::Op, inv::Invariants)
    cur = x; steps = 0
    for _ in 1:(MAX_DEPTH*4+20)
        nxt,k = projection_pass(cur, inv); steps += k
        canon(nxt) == canon(cur) && return nxt, steps
        cur = nxt
    end
    error("projection did not converge: $(canon(x))")
end

# -----------------------------------------------------------------------------
# Heuristic prediction (P)
# -----------------------------------------------------------------------------
hscore(x::Op) =
    x isa Leaf ? 1 :
    x isa T   ? 2 + hscore(x.x) :
    x isa Mul ? 3 + hscore(x.a) + hscore(x.b) :
    typemax(Int)

candidates(x::Op, inv::Invariants)
    out = Op[x]
    if x isa T
        x.x isa T   && push!(out, x.x.x)
        x.x isa Mul && push!(out, Mul(T(x.x.b), T(x.x.a)))
        x.x isa Leaf && x.x.name in inv.symmetric && push!(out, x.x)
    end
    out
end

function prediction_pass(x::Op, inv::Invariants)
    if x isa Leaf
        return x, 0
    elseif x isa T
        y,k = prediction_pass(x.x, inv)
        base = T(y)
        cs = candidates(base, inv)
        best = cs[argmin(map(hscore, cs))]
        return best, k + (canon(best) == canon(base) ? 0 : 1)
    elseif x isa Mul
        a,ka = prediction_pass(x.a, inv)
        b,kb = prediction_pass(x.b, inv)
        return Mul(a,b), ka+kb
    end
    error("unknown Op")
end

function predict(x::Op, inv::Invariants)
    cur = x; steps = 0
    for _ in 1:(MAX_DEPTH*4+20)
        nxt,k = prediction_pass(cur, inv); steps += k
        canon(nxt) == canon(cur) && return nxt, steps
        cur = nxt
    end
    error("prediction did not converge: $(canon(x))")
end

# -----------------------------------------------------------------------------
# Matrix semantics
# -----------------------------------------------------------------------------
function leaf_matrix(name::Symbol, n::Int, inv::Invariants, rng)
    sid = sum(Int(c) for c in string(name))
    rng2 = MersenneTwister(SEED + 7919*sid + 104729*n)
    A = randn(rng2, n, n)
    name in inv.symmetric && (A = (A + A')/2)
    A
end

function semantics(x::Op, n::Int, inv::Invariants, rng)
    x isa Leaf && return leaf_matrix(x.name, n, inv, rng)
    x isa T   && return semantics(x.x, n, inv, rng)'
    x isa Mul && return semantics(x.a, n, inv, rng) * semantics(x.b, n, inv, rng)
    error("unknown Op")
end

sem_equal(A,B; atol=1e-8, rtol=1e-8) = norm(A-B) <= atol + rtol*max(norm(A), norm(B), 1.0)

# -----------------------------------------------------------------------------
# Expression generation and equivalence rules
# -----------------------------------------------------------------------------
const NAMES = (:A,:B,:C,:D,:E,:F,:G,:H)
randleaf(rng) = Leaf(NAMES[rand(rng, 1:length(NAMES))])

function random_expr(rng, depth)
    depth <= 0 && return randleaf(rng)
    p = rand(rng)
    p < 0.33 ? T(random_expr(rng, depth-1)) :
    p < 0.78 ? Mul(random_expr(rng, depth-1), random_expr(rng, depth-1)) :
    randleaf(rng)
end

# Apply one equivalence rule to a random subexpression (or top-level)
function apply_rule_to_expr(x::Op, inv::Invariants, rng)
    # Return a new expression that is equivalent to x.
    # We'll apply a rule to a subexpression chosen by recursive random walk.
    # For simplicity, we apply to top-level if possible.
    # Rules:
    # 1. T(T(y)) -> y
    # 2. T(Mul(a,b)) -> Mul(T(b), T(a))
    # 3. If Leaf is symmetric, T(Leaf) -> Leaf
    # We'll randomly pick one.

    # Helper: try to apply to subexpressions.
    # We'll just randomly choose to apply at top level or recurse.
    if x isa Leaf
        # cannot apply rule to leaf except symmetric leaf (but that's a rule)
        # we'll apply symmetric rule if appropriate
        if x.name in inv.symmetric && rand(rng) < 0.5
            return T(x)  # T(Leaf) which will then simplify to Leaf in projection
            # Actually we want to produce an equivalent expression: T(Leaf) is equivalent to Leaf when symmetric.
            # So we can return T(x) and later projection will collapse it.
            # But for testing equivalence, we want T(Leaf) -> Leaf, so we need to apply rule that removes T.
            # Let's instead return T(x) (which is equivalent) and test that projection of both agree.
            # That's fine.
        else
            return x
        end
    elseif x isa T
        # apply rule 1 or 2 on the inner part
        if rand(rng) < 0.5
            # T(T(y)) -> y
            if x.x isa T
                return x.x.x
            else
                # try to apply to inner
                return T(apply_rule_to_expr(x.x, inv, rng))
            end
        else
            # T(Mul(a,b)) -> Mul(T(b), T(a))
            if x.x isa Mul
                a = x.x.a; b = x.x.b
                return Mul(T(b), T(a))
            else
                return T(apply_rule_to_expr(x.x, inv, rng))
            end
        end
    elseif x isa Mul
        # apply rule to one of the children randomly
        if rand(rng) < 0.5
            return Mul(apply_rule_to_expr(x.a, inv, rng), x.b)
        else
            return Mul(x.a, apply_rule_to_expr(x.b, inv, rng))
        end
    end
    return x
end

# Generate an equivalent pair: base and variant
function equivalent_pair(rng, inv, maxdepth=MAX_DEPTH)
    base = random_expr(rng, rand(rng, 1:maxdepth))
    variant = apply_rule_to_expr(base, inv, rng)
    # Return the rule name for reporting, but we don't need it
    return base, variant, :rule_applied
end

# Non-equivalent pair: two independent random expressions
function non_equivalent_pair(rng, inv, maxdepth=MAX_DEPTH)
    a = random_expr(rng, rand(rng, 1:maxdepth))
    b = random_expr(rng, rand(rng, 1:maxdepth))
    return a, b
end

# -----------------------------------------------------------------------------
# Timing and statistics helpers
# -----------------------------------------------------------------------------
function timed(f)
    GC.gc()
    t = time_ns()
    v = f()
    v, (time_ns() - t) / 1e6  # ms
end

function pct(v, p)
    s = sort(v)
    s[clamp(Int(ceil(p * length(s))), 1, length(s))]
end

function stats(v)
    Dict(
        "n" => length(v),
        "mean_ms" => mean(v),
        "median_ms" => median(v),
        "std_ms" => (length(v) > 1 ? std(v) : 0.0),
        "p90_ms" => pct(v, 0.90),
        "p95_ms" => pct(v, 0.95),
        "p99_ms" => pct(v, 0.99),
        "min_ms" => minimum(v),
        "max_ms" => maximum(v)
    )
end

function bootstrap_ci(x, y; B=2000)
    d = y .- x
    rng = MersenneTwister(SEED+555555)
    vals = Vector{Float64}(undef, B)
    n = length(d)
    for b in 1:B
        total = 0.0
        for _ in 1:n
            total += d[rand(rng, 1:n)]
        end
        vals[b] = total / n
    end
    sort!(vals)
    mean(d), vals[max(1, Int(floor(0.025*B)))], vals[min(B, Int(ceil(0.975*B)))]
end

# -----------------------------------------------------------------------------
# Main benchmark
# -----------------------------------------------------------------------------
function main()
    rng = MersenneTwister(SEED)
    inv = Invariants(Set(rand(rng, collect(NAMES[1:3]), rand(rng, 0:2))))

    println("="^88)
    println("AGD DEFINITIVE BENCHMARK v2 (FIXED)")
    println("="^88)
    println("Equivalent pairs: $NPAIRS  Semantic: $NSEM  Idempotence: $NIDEM  Timing: $NTIME  Seed: $SEED")
    println()

    # -------------------------------------------------------------------------
    # 1. Known-equivalent pair canonicalization
    # -------------------------------------------------------------------------
    println("[1/10] Known-equivalent pair canonicalization...")
    eq_pass = 0
    eq_fail = String[]
    for i in 1:NPAIRS
        base, variant, _ = equivalent_pair(rng, inv)
        p1,_ = project(base, inv)
        p2,_ = project(variant, inv)
        if canon(p1) == canon(p2)
            eq_pass += 1
        else
            push!(eq_fail, "pair $i base=$(canon(base)) variant=$(canon(variant)) p1=$(canon(p1)) p2=$(canon(p2))")
        end
        i % max(1, NPAIRS÷10) == 0 && @printf("  %d/%d\n", i, NPAIRS)
    end
    println("  PASS: $eq_pass/$NPAIRS")

    # -------------------------------------------------------------------------
    # 2. Negative-pair test (non-equivalent should not collapse)
    # -------------------------------------------------------------------------
    println("[2/10] Negative-pair test (non-equivalent should not collapse)...")
    neg_pass = 0
    neg_fail = String[]
    for i in 1:NPAIRS
        a, b = non_equivalent_pair(rng, inv)
        p1,_ = project(a, inv)
        p2,_ = project(b, inv)
        if canon(p1) != canon(p2)
            neg_pass += 1
        else
            push!(neg_fail, "non-equivalent pair $i a=$(canon(a)) b=$(canon(b)) collapsed to $(canon(p1))")
        end
        i % max(1, NPAIRS÷10) == 0 && @printf("  %d/%d\n", i, NPAIRS)
    end
    println("  PASS: $neg_pass/$NPAIRS (failure to collapse = correct)")

    # -------------------------------------------------------------------------
    # 3. Idempotence Π²=Π
    # -------------------------------------------------------------------------
    println("[3/10] Idempotence Π²=Π...")
    idem_pass = 0
    idem_fail = String[]
    for i in 1:NIDEM
        x = random_expr(rng, rand(rng, 1:MAX_DEPTH))
        p1,_ = project(x, inv)
        p2,_ = project(p1, inv)
        if canon(p1) == canon(p2)
            idem_pass += 1
        else
            push!(idem_fail, "case $i x=$(canon(x)) p=$(canon(p1)) pp=$(canon(p2))")
        end
    end
    println("  PASS: $idem_pass/$NIDEM")

    # -------------------------------------------------------------------------
    # 4. Semantic preservation of projection
    # -------------------------------------------------------------------------
    println("[4/10] Semantic preservation (real matrices)...")
    sem_pass = 0
    sem_fail = String[]
    for i in 1:NSEM
        x = random_expr(rng, rand(rng, 1:8))
        n = MATRIX_SIZES[rand(rng, 1:length(MATRIX_SIZES))]
        p,_ = project(x, inv)
        sem_ok = sem_equal(semantics(x, n, inv, rng), semantics(p, n, inv, rng))
        if sem_ok
            sem_pass += 1
        else
            push!(sem_fail, "case $i n=$n x=$(canon(x)) p=$(canon(p))")
        end
    end
    println("  PASS: $sem_pass/$NSEM")

    # -------------------------------------------------------------------------
    # 5. Deterministic replay
    # -------------------------------------------------------------------------
    println("[5/10] Deterministic replay (same input -> same output)...")
    det_pass = 0
    det_fail = String[]
    for i in 1:NIDEM
        x = random_expr(rng, rand(rng, 1:MAX_DEPTH))
        hs = String[]
        for _ in 1:REPLAY_REPEATS
            p,_ = project(x, inv)
            push!(hs, hashcanon(p))
        end
        if length(unique(hs)) == 1
            det_pass += 1
        else
            push!(det_fail, "case $i hashes=$(hs)")
        end
    end
    println("  PASS: $det_pass/$NIDEM")

    # -------------------------------------------------------------------------
    # 6. Certificate replay (reproducible result)
    # -------------------------------------------------------------------------
    println("[6/10] Certificate replay (reproducible result)...")
    cert_pass = 0
    cert_fail = String[]
    for i in 1:NIDEM
        x = random_expr(rng, rand(rng, 1:MAX_DEPTH))
        p,s = project(x, inv)
        pc,sc = project(x, inv)  # run again
        if canon(p) == canon(pc) && s >= 0 && sc >= 0
            cert_pass += 1
        else
            push!(cert_fail, "case $i x=$(canon(x))")
        end
    end
    println("  PASS: $cert_pass/$NIDEM")

    # -------------------------------------------------------------------------
    # 7. Metamorphic stability (successive equivalence transformations)
    # -------------------------------------------------------------------------
    println("[7/10] Metamorphic stability (successive equivalence transformations)...")
    meta_pass = 0
    meta_fail = String[]
    for i in 1:NPAIRS
        x = random_expr(rng, rand(rng, 1:MAX_DEPTH))
        cur = x
        # apply 1-4 random rules in sequence
        for _ in 1:rand(rng, 1:4)
            cur = apply_rule_to_expr(cur, inv, rng)
        end
        p1,_ = project(x, inv)
        p2,_ = project(cur, inv)
        if canon(p1) == canon(p2)
            meta_pass += 1
        else
            push!(meta_fail, "metamorphic case $i x=$(canon(x)) final=$(canon(cur)) p1=$(canon(p1)) p2=$(canon(p2))")
        end
        i % max(1, NPAIRS÷10) == 0 && @printf("  %d/%d\n", i, NPAIRS)
    end
    println("  PASS: $meta_pass/$NPAIRS")

    # -------------------------------------------------------------------------
    # 8. Rule-completeness (explicit rule tests)
    # -------------------------------------------------------------------------
    println("[8/10] Rule-completeness (explicit rule tests)...")
    # We'll test three rules by generating expressions that exercise them.
    rule_results = Dict{Symbol,Bool}()
    # Rule 1: T(T(x)) -> x
    pass1 = 0
    for _ in 1:100
        x = random_expr(rng, rand(rng, 1:MAX_DEPTH))
        y = T(T(x))
        p1,_ = project(x, inv)
        p2,_ = project(y, inv)
        if canon(p1) == canon(p2)
            pass1 += 1
        end
    end
    rule_results[:transpose_transpose] = pass1 == 100

    # Rule 2: T(Mul(a,b)) -> Mul(T(b),T(a))
    pass2 = 0
    for _ in 1:100
        a = random_expr(rng, rand(rng, 1:MAX_DEPTH-1))
        b = random_expr(rng, rand(rng, 1:MAX_DEPTH-1))
        x = Mul(a,b)
        y = T(x)  # T(Mul(a,b))
        p1,_ = project(x, inv)  # project of x itself? Actually we need to compare projection of T(Mul(a,b)) vs projection of Mul(T(b),T(a))
        # But we don't have y as T(Mul(a,b)); we need to project both and compare.
        # Actually the rule is T(Mul(a,b)) -> Mul(T(b),T(a)).
        # So we take x = T(Mul(a,b)), and y = Mul(T(b),T(a)).
        # We'll generate x as T(Mul(a,b)) and y as Mul(T(b),T(a)).
        # But we need to ensure a,b are available.
        # Let's redo:
        a = random_expr(rng, rand(rng, 1:MAX_DEPTH-1))
        b = random_expr(rng, rand(rng, 1:MAX_DEPTH-1))
        x = T(Mul(a,b))
        y = Mul(T(b), T(a))
        p1,_ = project(x, inv)
        p2,_ = project(y, inv)
        if canon(p1) == canon(p2)
            pass2 += 1
        end
    end
    rule_results[:transpose_product] = pass2 == 100

    # Rule 3: T(Leaf) -> Leaf if Leaf.name in symmetric
    pass3 = 0
    for _ in 1:100
        # pick a symmetric leaf if any, else skip
        sym = filter(s -> s in inv.symmetric, NAMES)
        if isempty(sym)
            break
        end
        s = rand(rng, sym)
        x = T(Leaf(s))
        y = Leaf(s)
        p1,_ = project(x, inv)
        p2,_ = project(y, inv)
        if canon(p1) == canon(p2)
            pass3 += 1
        end
    end
    # If no symmetric leaves, we treat as pass
    rule_results[:symmetric_leaf] = pass3 == 100 || isempty(filter(s -> s in inv.symmetric, NAMES))

    for (rulename, ok) in rule_results
        println("  $rulename: $(ok ? "PASS" : "FAIL")")
    end

    # -------------------------------------------------------------------------
    # 9. Depth scaling (timing vs expression complexity)
    # -------------------------------------------------------------------------
    println("[9/10] Depth scaling timing (projection vs prediction)...")
    depth_stats = Dict{Int,Any}()
    for depth in SCALING_DEPTHS
        println("  Depth $depth...")
        pt = Float64[]
        qt = Float64[]
        ps = Int[]
        qs = Int[]
        for _ in 1:NTIME
            x = random_expr(rng, rand(rng, 1:depth))
            (pp,s1), t1 = timed(() -> project(x, inv))
            (qq,s2), t2 = timed(() -> predict(x, inv))
            push!(pt, t1); push!(qt, t2); push!(ps, s1); push!(qs, s2)
        end
        pst = stats(pt)
        qst = stats(qt)
        mean_ratio = mean(qt) / mean(pt)
        median_ratio = median(qt) / median(pt)
        p95_ratio = pct(qt, 0.95) / pct(pt, 0.95)
        p99_ratio = pct(qt, 0.99) / pct(pt, 0.99)
        dm, lo, hi = bootstrap_ci(pt, qt)
        depth_stats[depth] = (pst, qst, mean_ratio, median_ratio, p95_ratio, p99_ratio, dm, lo, hi)
        @printf("    proj mean=%.3f ms, pred mean=%.3f ms, ratio=%.2fx, CI=[%.3f, %.3f]\n",
                pst["mean_ms"], qst["mean_ms"], mean_ratio, lo, hi)
    end

    # -------------------------------------------------------------------------
    # 10. Summary report
    # -------------------------------------------------------------------------
    println("\n[10/10] Final validation results")
    println("="^88)
    println("Test                         Result")
    println("---------------------------- --------")
    @printf("Known-equivalent collapse      %d/%d\n", eq_pass, NPAIRS)
    @printf("Negative-pair non-collapse     %d/%d\n", neg_pass, NPAIRS)
    @printf("Idempotence                    %d/%d\n", idem_pass, NIDEM)
    @printf("Semantic preservation          %d/%d\n", sem_pass, NSEM)
    @printf("Deterministic replay           %d/%d\n", det_pass, NIDEM)
    @printf("Certificate replay             %d/%d\n", cert_pass, NIDEM)
    @printf("Metamorphic stability          %d/%d\n", meta_pass, NPAIRS)
    println("Rule tests:")
    for (rulename, ok) in rule_results
        @printf("  %s: %s\n", rulename, ok ? "PASS" : "FAIL")
    end

    println("\nDepth scaling ratios (pred/proj):")
    for depth in SCALING_DEPTHS
        pst, qst, mean_ratio, median_ratio, p95_ratio, p99_ratio, dm, lo, hi = depth_stats[depth]
        @printf("  depth %2d: mean=%.2fx, median=%.2fx, p95=%.2fx, p99=%.2fx, CI=[%.3f, %.3f]\n",
                depth, mean_ratio, median_ratio, p95_ratio, p99_ratio, lo, hi)
    end

    # -------------------------------------------------------------------------
    # Save report
    # -------------------------------------------------------------------------
    open("agd_v2_fixed_results.txt", "w") do io
        println(io, "AGD BENCHMARK v2 (FIXED) RESULTS")
        println(io, "Timestamp: ", now())
        println(io, "Seed: $SEED, NPAIRS: $NPAIRS")
        println(io, "eq_pass: $eq_pass/$NPAIRS")
        println(io, "neg_pass: $neg_pass/$NPAIRS")
        println(io, "idem_pass: $idem_pass/$NIDEM")
        println(io, "sem_pass: $sem_pass/$NSEM")
        println(io, "det_pass: $det_pass/$NIDEM")
        println(io, "cert_pass: $cert_pass/$NIDEM")
        println(io, "meta_pass: $meta_pass/$NPAIRS")
        println(io, "rule_results: $rule_results")
        println(io, "Depth scaling:")
        for depth in SCALING_DEPTHS
            pst, qst, mean_ratio, median_ratio, p95_ratio, p99_ratio, dm, lo, hi = depth_stats[depth]
            println(io, "  depth $depth: mean_ratio=$mean_ratio, median_ratio=$median_ratio, p95_ratio=$p95_ratio, p99_ratio=$p99_ratio, CI=[$lo, $hi]")
        end
        println(io, "eq_failures: ", length(eq_fail))
        println(io, "neg_failures: ", length(neg_fail))
        println(io, "idem_failures: ", length(idem_fail))
        println(io, "sem_failures: ", length(sem_fail))
        println(io, "det_failures: ", length(det_fail))
        println(io, "cert_failures: ", length(cert_fail))
        println(io, "meta_failures: ", length(meta_fail))
    end

    println("\nReport saved to agd_v2_fixed_results.txt")
    println("="^88)
end

main()
JULIA_END

echo "[OK] $BENCH"
echo

echo "[2/2] Running benchmark..."
echo "------------------------------------------------------------"

julia --startup-file=no --history-file=no "$BENCH" "$CASES" "$SEED"
STATUS=$?

echo "------------------------------------------------------------"
if (( STATUS != 0 )); then
  echo "[FAIL] Benchmark exited with code $STATUS."
  exit "$STATUS"
fi

echo
echo "============================================================"
echo " BENCHMARK COMPLETE"
echo "============================================================"
if [[ -f "$REPORT" ]]; then
  echo "[OK] Report: $REPORT"
else
  echo "[WARN] Expected report not found: $REPORT"
fi
echo
