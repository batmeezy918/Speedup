using LinearAlgebra
using Printf
using SHA
using Dates

const TILE = 8
const DEFAULT_NS = [32, 64, 128, 256, 512]

struct BlockClass
    representative::Matrix{Float32}
end

function block_count(N)
    @assert N % TILE == 0
    return N ÷ TILE
end

function make_canonical(N)
    A = fill(Float32(0.5), N, N)
    B = fill(Float32(0.5), N, N)
    return A, B
end

function make_exact_classes(N, nclasses)
    @assert N % TILE == 0
    @assert nclasses >= 1

    Bn = block_count(N)

    A = Matrix{Float32}(undef, N, N)
    C = Matrix{Float32}(undef, N, N)

    for bi in 1:Bn
        for bj in 1:Bn
            cls = mod(bi - 1 + 2*(bj - 1), nclasses)

            v = Float32(0.125 + 0.03125 * cls)

            for x in 1:TILE
                for y in 1:TILE
                    ii = (bi-1)*TILE + x
                    jj = (bj-1)*TILE + y
                    A[ii,jj] = v
                end
            end

            cls2 = mod(3*(bi - 1) + (bj - 1), nclasses)
            v2 = Float32(0.25 + 0.02734375 * cls2)

            for x in 1:TILE
                for y in 1:TILE
                    ii = (bi-1)*TILE + x
                    jj = (bj-1)*TILE + y
                    C[ii,jj] = v2
                end
            end
        end
    end

    return A, C
end

function make_random(N)
    rng = MersenneTwister(91820260910)
    A = rand(rng, Float32, N, N)
    B = rand(rng, Float32, N, N)
    return A, B
end

function extract_block(M, bi, bj)
    r1 = (bi-1)*TILE + 1
    r2 = bi*TILE
    c1 = (bj-1)*TILE + 1
    c2 = bj*TILE
    return copy(@view M[r1:r2, c1:c2])
end

function block_key(block::Matrix{Float32})
    # Exact byte-level identity.
    return bytes2hex(sha256(reinterpret(UInt8, vec(block))))
end

function classify_blocks(M, N)
    Bn = block_count(N)

    classes = BlockClass[]
    class_of = zeros(Int, Bn, Bn)

    dictionary = Dict{String,Int}()

    for bi in 1:Bn
        for bj in 1:Bn
            block = extract_block(M, bi, bj)
            key = block_key(block)

            if haskey(dictionary, key)
                id = dictionary[key]
            else
                push!(classes, BlockClass(block))
                id = length(classes)
                dictionary[key] = id
            end

            class_of[bi,bj] = id
        end
    end

    return classes, class_of
end

function block_mul(A::Matrix{Float32}, B::Matrix{Float32})
    # Small native BLAS multiplication.
    return A * B
end

function full_block_gemm(A, B, N)
    Bn = block_count(N)

    C = zeros(Float32, N, N)

    product_count = 0

    for bi in 1:Bn
        for bj in 1:Bn
            out = zeros(Float32, TILE, TILE)

            for bk in 1:Bn
                Ab = extract_block(A, bi, bk)
                Bb = extract_block(B, bk, bj)

                out .+= block_mul(Ab, Bb)
                product_count += 1
            end

            r1 = (bi-1)*TILE+1
            r2 = bi*TILE
            c1 = (bj-1)*TILE+1
            c2 = bj*TILE

            C[r1:r2,c1:c2] .= out
        end
    end

    return C, product_count
end

function quotient_gemm(A, B, N)
    Bn = block_count(N)

    QA, amap = classify_blocks(A, N)
    QB, bmap = classify_blocks(B, N)

    cache = Dict{Tuple{Int,Int},Matrix{Float32}}()

    for ia in 1:length(QA)
        for ib in 1:length(QB)
            cache[(ia,ib)] =
                block_mul(QA[ia].representative,
                          QB[ib].representative)
        end
    end

    C = zeros(Float32, N, N)

    for bi in 1:Bn
        for bj in 1:Bn
            out = zeros(Float32, TILE, TILE)

            for bk in 1:Bn
                ia = amap[bi,bk]
                ib = bmap[bk,bj]

                out .+= cache[(ia,ib)]
            end

            r1 = (bi-1)*TILE+1
            r2 = bi*TILE
            c1 = (bj-1)*TILE+1
            c2 = bj*TILE

            C[r1:r2,c1:c2] .= out
        end
    end

    return C, length(cache), length(QA), length(QB)
end

function max_abs_error(A,B)
    return maximum(abs.(A .- B))
end

function relative_error(A,B)
    denom = max(norm(A), eps(Float32))
    return Float64(norm(A-B) / denom)
end

function benchmark(fn; repeats=3)
    times = Float64[]

    result = nothing

    for _ in 1:repeats
        GC.gc()
        t = @elapsed result = fn()
        push!(times, t)
    end

    sort!(times)

    return result, median(times), minimum(times), maximum(times)
end

function run_case(name, A, B, N)
    println()
    println("="^78)
    println("CASE: $name | N=$N | TILE=$TILE")
    println("="^78)

    full_result, tf, tfmin, tfmax =
        benchmark(() -> full_block_gemm(A,B,N))

    Cfull, full_products = full_result

    q_result, tq, tqmin, tqmax =
        benchmark(() -> quotient_gemm(A,B,N))

    Cq, cached_products, qa, qb = q_result

    err = max_abs_error(Cfull,Cq)
    rel = relative_error(Cfull,Cq)

    theoretical = full_products / max(cached_products,1)

    runtime_ratio =
        tf / max(tq, eps(Float64))

    println(@sprintf("physical blocks              = %d",
        block_count(N)^2))

    println(@sprintf("A quotient classes           = %d", qa))
    println(@sprintf("B quotient classes           = %d", qb))

    println(@sprintf("full block products          = %d",
        full_products))

    println(@sprintf("actual cached product evals  = %d",
        cached_products))

    println(@sprintf("actual product-work ratio    = %.6fx",
        theoretical))

    println(@sprintf("full median runtime          = %.9fs", tf))
    println(@sprintf("quotient median runtime      = %.9fs", tq))

    println(@sprintf("runtime speedup              = %.6fx",
        runtime_ratio))

    println(@sprintf("maximum absolute error       = %.9g", err))
    println(@sprintf("relative error               = %.9g", rel))

    exact = err == 0.0

    println("exact output equality        = ", exact)

    if exact && runtime_ratio > 1.0
        println("STATUS                       = PASS_RUNTIME_SPEEDUP")
    elseif exact
        println("STATUS                       = PASS_SEMANTIC_NO_RUNTIME_SPEEDUP")
    else
        println("STATUS                       = FAIL_SEMANTIC")
    end

    return (
        name=name,
        N=N,
        qa=qa,
        qb=qb,
        full_products=full_products,
        cached_products=cached_products,
        structural_ratio=theoretical,
        full_time=tf,
        quotient_time=tq,
        runtime_speedup=runtime_ratio,
        max_error=err,
        relative_error=rel,
        exact=exact
    )
end

function main()
    println()
    println("="^78)
    println("AGD GEMM — DEFINITIVE JULIA QUOTIENT EXECUTION")
    println("="^78)

    println("Julia version : ", VERSION)
    println("Threads       : ", Threads.nthreads())
    println("BLAS config   : ", BLAS.get_config())

    results = NamedTuple[]

    for N in DEFAULT_NS
        println("\n[1/3] canonical")
        A,B = make_canonical(N)
        push!(results, run_case("canonical",A,B,N))

        println("\n[2/3] exact operator classes")
        A,B = make_exact_classes(N, min(4, block_count(N)^2))
        push!(results, run_case("exact_block_classes",A,B,N))

        println("\n[3/3] random")
        A,B = make_random(N)
        push!(results, run_case("random",A,B,N))
    end

    println()
    println("="^78)
    println("FINAL JULIA SUMMARY")
    println("="^78)

    semantic_pass =
        all(r -> r.exact, results)

    runtime_pass =
        any(r -> r.exact && r.runtime_speedup > 1.0, results)

    structural_pass =
        any(r -> r.structural_ratio > 1.0, results)

    println("semantic correctness          = ", semantic_pass)
    println("structural reduction         = ", structural_pass)
    println("runtime speedup observed     = ", runtime_pass)

    if semantic_pass && structural_pass && runtime_pass
        println("FINAL STATUS = STRONG_NATIVE_CANDIDATE")
    elseif semantic_pass && structural_pass
        println("FINAL STATUS = STRUCTURALALLY_CLOSED_RUNTIME_OPEN")
    else
        println("FINAL STATUS = FAILED")
    end

    println("="^78)
end

main()
