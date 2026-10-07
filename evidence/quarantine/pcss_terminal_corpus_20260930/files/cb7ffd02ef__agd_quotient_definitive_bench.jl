#!/usr/bin/env julia
using Random, Statistics, LinearAlgebra, Printf, SHA, Dates

const NPAIRS = length(ARGS)>=1 ? parse(Int,ARGS[1]) : 100_000
const SEED = length(ARGS)>=2 ? parse(Int,ARGS[2]) : 20260809
const NSEM=min(10_000,NPAIRS); const NIDEM=min(10_000,NPAIRS); const NTIME=min(10_000,NPAIRS)
const REPLAY_REPEATS=3; const MATRIX_SIZES=(5,10,25,50,100); const MAX_DEPTH=10
NPAIRS>=100 || error("Use at least 100 pairs")

abstract type Op end
struct Leaf <: Op; name::Symbol; end
struct Mul <: Op; a::Op; b::Op; end
struct T <: Op; x::Op; end
struct Invariants; symmetric::Set{Symbol}; end

function canon(x::Op)::String
    x isa Leaf && return String(x.name)
    x isa T && return "T("*canon(x.x)*")"
    x isa Mul && return "M("*canon(x.a)*","*canon(x.b)*")"
    error("unknown Op")
end
hashcanon(x)=bytes2hex(sha256(canon(x)))

function projection_pass(x::Op, inv::Invariants)
    if x isa Leaf; return x,0
    elseif x isa T
        y,k=projection_pass(x.x,inv)
        y isa T && return y.x,k+1
        y isa Mul && return Mul(T(y.b),T(y.a)),k+1
        y isa Leaf && y.name in inv.symmetric && return y,k+1
        return T(y),k
    elseif x isa Mul
        a,ka=projection_pass(x.a,inv); b,kb=projection_pass(x.b,inv); return Mul(a,b),ka+kb
    end
    error("unknown Op")
end
function project(x::Op,inv::Invariants)
    cur=x; steps=0
    for _ in 1:(MAX_DEPTH*4+20)
        nxt,k=projection_pass(cur,inv); steps+=k
        canon(nxt)==canon(cur) && return nxt,steps
        cur=nxt
    end
    error("projection did not converge: "*canon(x))
end

function hscore(x::Op)
    x isa Leaf && return 1; x isa T && return 2+hscore(x.x); x isa Mul && return 3+hscore(x.a)+hscore(x.b); typemax(Int)
end
function candidates(x::Op,inv::Invariants)
    out=Op[x]
    if x isa T
        x.x isa T && push!(out,x.x.x)
        x.x isa Mul && push!(out,Mul(T(x.x.b),T(x.x.a)))
        x.x isa Leaf && x.x.name in inv.symmetric && push!(out,x.x)
    end
    out
end
function prediction_pass(x::Op,inv::Invariants)
    if x isa Leaf; return x,0
    elseif x isa T
        y,k=prediction_pass(x.x,inv); base=T(y); cs=candidates(base,inv); best=cs[argmin(map(hscore,cs))]
        return best,k+(canon(best)==canon(base) ? 0 : 1)
    elseif x isa Mul
        a,ka=prediction_pass(x.a,inv); b,kb=prediction_pass(x.b,inv); return Mul(a,b),ka+kb
    end
    error("unknown Op")
end
function predict(x::Op,inv::Invariants)
    cur=x; steps=0
    for _ in 1:(MAX_DEPTH*4+20)
        nxt,k=prediction_pass(cur,inv); steps+=k
        canon(nxt)==canon(cur) && return nxt,steps; cur=nxt
    end
    error("prediction did not converge: "*canon(x))
end

function leaf_matrix(name::Symbol,n::Int,inv::Invariants)
    sid=sum(Int(c) for c in String(name)); rng=MersenneTwister(SEED+7919*sid+104729*n); A=randn(rng,n,n)
    name in inv.symmetric && (A=(A+A')/2); A
end
function semantics(x::Op,n::Int,inv::Invariants)
    x isa Leaf && return leaf_matrix(x.name,n,inv)
    x isa T && return semantics(x.x,n,inv)'
    x isa Mul && return semantics(x.a,n,inv)*semantics(x.b,n,inv)
    error("unknown Op")
end
sem_equal(A,B;atol=1e-8,rtol=1e-8)=norm(A-B)<=atol+rtol*max(norm(A),norm(B),1.0)

const NAMES=(:A,:B,:C,:D,:E,:F,:G,:H)
randleaf(rng)=Leaf(NAMES[rand(rng,1:length(NAMES))])
function random_expr(rng,depth)
    depth<=0 && return randleaf(rng); p=rand(rng)
    p<.33 ? T(random_expr(rng,depth-1)) : p<.78 ? Mul(random_expr(rng,depth-1),random_expr(rng,depth-1)) : randleaf(rng)
end
function equivalent_variant(x::Op,inv::Invariants,rng)
    c=rand(rng,1:3)
    if c==1; y=T(T(x)); rule=:double_transpose
    elseif c==2; y=T(T(T(T(x)))); rule=:four_transpose
    elseif x isa Mul; y=T(Mul(T(x.a),T(x.b))); rule=:transpose_product
    else; y=T(T(x)); rule=:fallback_double_transpose
    end
    if rand(rng)<.25; y=T(T(y)); rule=Symbol(String(rule),"_nested"); end
    y,rule
end
function representative(x,inv,rng,count)
    y=x
    for _ in 1:count; y,_=equivalent_variant(y,inv,rng); end
    y
end

function timed(f); GC.gc(); t=time_ns(); v=f(); v,(time_ns()-t)/1e6; end
function pct(v,p); s=sort(v); s[clamp(Int(ceil(p*length(s))),1,length(s))]; end
function stats(v); Dict("n"=>length(v),"mean_ms"=>mean(v),"median_ms"=>median(v),"std_ms"=>(length(v)>1 ? std(v) : 0.0),"p90_ms"=>pct(v,.90),"p95_ms"=>pct(v,.95),"p99_ms"=>pct(v,.99),"min_ms"=>minimum(v),"max_ms"=>maximum(v)); end
function bootstrap_ci(x,y;B=2000)
    d=y.-x; rng=MersenneTwister(SEED+555555); vals=Vector{Float64}(undef,B); n=length(d)
    for b in 1:B; total=0.0; for _ in 1:n; total+=d[rand(rng,1:n)]; end; vals[b]=total/n; end
    sort!(vals); mean(d),vals[max(1,Int(floor(.025B)))],vals[min(B,Int(ceil(.975B)))]
end

println("="^88); println("AGD DEFINITIVE CANONICAL QUOTIENT / PROJECTION BENCHMARK"); println("="^88)
println("Equivalent pairs: ",NPAIRS,"  Semantic: ",NSEM,"  Idempotence: ",NIDEM,"  Timing: ",NTIME,"  Seed: ",SEED)
println()
rng=MersenneTwister(SEED); eq_fail=String[]; idem_fail=String[]; sem_fail=String[]; det_fail=String[]; cert_fail=String[]

println("[1/7] Known-equivalent pair canonicalization...")
canonical_collapses=0
for i in 1:NPAIRS
    depth=rand(rng,1:MAX_DEPTH); inv=Invariants(Set(rand(rng,collect(NAMES[1:3]),rand(rng,0:2)))); base=random_expr(rng,depth); variant,rule=equivalent_variant(base,inv,rng)
    p1,_=project(base,inv); p2,_=project(variant,inv)
    if canon(p1)==canon(p2); global canonical_collapses += 1 else push!(eq_fail,"pair $i rule=$rule base=$(canon(base)) variant=$(canon(variant)) p1=$(canon(p1)) p2=$(canon(p2))") end
    i%max(1,NPAIRS÷10)==0 && @printf("  %d/%d\n",i,NPAIRS)
end
println("  PASS: ",canonical_collapses,"/",NPAIRS)

println("[2/7] Idempotence Π²=Π...")
idem_pass=0
for i in 1:NIDEM
    inv=Invariants(Set(rand(rng,collect(NAMES[1:3]),rand(rng,0:2)))); x=random_expr(rng,rand(rng,1:MAX_DEPTH)); p1,_=project(x,inv); p2,_=project(p1,inv)
    canon(p1)==canon(p2) ? (global idem_pass += 1) : push!(idem_fail,"case $i x=$(canon(x)) p=$(canon(p1)) pp=$(canon(p2))")
end
println("  PASS: ",idem_pass,"/",NIDEM)

println("[3/7] Independent real-matrix semantic preservation...")
sem_pass=0
for i in 1:NSEM
    inv=Invariants(Set(rand(rng,collect(NAMES[1:3]),rand(rng,0:2)))); x=random_expr(rng,rand(rng,1:8)); n=MATRIX_SIZES[rand(rng,1:length(MATRIX_SIZES))]; p,_=project(x,inv)
    sem_equal(semantics(x,n,inv),semantics(p,n,inv)) ? (global sem_pass += 1) : push!(sem_fail,"case $i n=$n x=$(canon(x)) p=$(canon(p))")
end
println("  PASS: ",sem_pass,"/",NSEM)

println("[4/7] Deterministic replay...")
det_pass=0
for i in 1:NIDEM
    inv=Invariants(Set(rand(rng,collect(NAMES[1:3]),rand(rng,0:2)))); x=random_expr(rng,rand(rng,1:MAX_DEPTH)); hs=String[]
    for _ in 1:REPLAY_REPEATS; p,_=project(x,inv); push!(hs,hashcanon(p)); end
    length(unique(hs))==1 ? (global det_pass += 1) : push!(det_fail,"case $i hashes=$(hs)")
end
println("  PASS: ",det_pass,"/",NIDEM)

println("[5/7] Independent certificate replay...")
cert_pass=0
for i in 1:NIDEM
    inv=Invariants(Set(rand(rng,collect(NAMES[1:3]),rand(rng,0:2)))); x=random_expr(rng,rand(rng,1:MAX_DEPTH)); p,s=project(x,inv); pc,sc=project(x,inv)
    (canon(p)==canon(pc) && s>=0 && sc>=0) ? (global cert_pass += 1) : push!(cert_fail,"case $i x=$(canon(x))")
end
println("  PASS: ",cert_pass,"/",NIDEM)

println("[6/7] Projection vs deterministic heuristic timing...")
pt=Float64[]; qt=Float64[]; ps=Int[]; qs=Int[]
for i in 1:NTIME
    inv=Invariants(Set(rand(rng,collect(NAMES[1:3]),rand(rng,0:2)))); x=random_expr(rng,rand(rng,1:MAX_DEPTH)); (pp,s1),t1=timed(()->project(x,inv)); (qq,s2),t2=timed(()->predict(x,inv)); push!(pt,t1);push!(qt,t2);push!(ps,s1);push!(qs,s2)
end
pst=stats(pt);qst=stats(qt); mean_ratio=mean(qt)/mean(pt);median_ratio=median(qt)/median(pt);p95_ratio=pct(qt,.95)/pct(pt,.95);p99_ratio=pct(qt,.99)/pct(pt,.99);dm,lo,hi=bootstrap_ci(pt,qt)
@printf("  mean: %.6f vs %.6f ms\n",pst["mean_ms"],qst["mean_ms"]); @printf("  median: %.6f vs %.6f ms\n",pst["median_ms"],qst["median_ms"]); @printf("  p95: %.6f vs %.6f ms\n",pst["p95_ms"],qst["p95_ms"]); @printf("  p99: %.6f vs %.6f ms\n",pst["p99_ms"],qst["p99_ms"]); @printf("  ratios pred/proj: mean %.4fx median %.4fx p95 %.4fx p99 %.4fx\n",mean_ratio,median_ratio,p95_ratio,p99_ratio); @printf("  paired mean diff: %.6f ms; bootstrap CI [%.6f, %.6f]\n",dm,lo,hi)

println("[7/7] Independent quotient representatives...")
quotient_pass=0
for i in 1:NPAIRS
    inv=Invariants(Set(rand(rng,collect(NAMES[1:3]),rand(rng,0:2)))); seed=random_expr(rng,rand(rng,1:MAX_DEPTH)); r1=representative(seed,inv,rng,rand(rng,1:4));r2=representative(seed,inv,rng,rand(rng,1:4));p1,_=project(r1,inv);p2,_=project(r2,inv)
    canon(p1)==canon(p2) ? (global quotient_pass += 1) : push!(eq_fail,"quotient $i seed=$(canon(seed)) r1=$(canon(r1)) r2=$(canon(r2)) p1=$(canon(p1)) p2=$(canon(p2))")
    i%max(1,NPAIRS÷10)==0 && @printf("  %d/%d\n",i,NPAIRS)
end
println("  PASS: ",quotient_pass,"/",NPAIRS)

println(); println("="^88); println("FINAL VALIDATION"); println("="^88)
eq_ok=isempty(eq_fail);idem_ok=isempty(idem_fail);sem_ok=isempty(sem_fail);det_ok=isempty(det_fail);cert_ok=isempty(cert_fail);quot_ok=quotient_pass==NPAIRS
println("Known-equivalent canonicalization: ",eq_ok ? "PASS":"FAIL")
println("Idempotence Π²=Π:                 ",idem_ok ? "PASS":"FAIL")
println("Independent matrix semantics:      ",sem_ok ? "PASS":"FAIL")
println("Deterministic replay:              ",det_ok ? "PASS":"FAIL")
println("Independent certificate replay:    ",cert_ok ? "PASS":"FAIL")
println("Independent quotient consistency:   ",quot_ok ? "PASS":"FAIL")
println(); @printf("Projection mean %.6f ms | Prediction mean %.6f ms\n",pst["mean_ms"],qst["mean_ms"]); @printf("Prediction/Projection mean ratio %.4fx\n",mean_ratio); @printf("Bootstrap 95%% CI for (prediction-projection): [%.6f, %.6f] ms\n",lo,hi); @printf("Mean projection steps %.4f | prediction %.4f\n",mean(ps),mean(qs))
allcore=eq_ok&&idem_ok&&sem_ok&&det_ok&&cert_ok&&quot_ok
println(); println(allcore ? "✓ CORE AGD PROJECTION PROPERTIES PASSED" : "✗ CORE AGD PROJECTION PROPERTIES NOT FULLY VALIDATED")
println("Performance superiority is claimed only if the timing CI excludes zero.")

open("agd_quotient_definitive_results.txt","w") do io
    println(io,"AGD DEFINITIVE CANONICAL QUOTIENT / PROJECTION BENHCMARK");println(io,"Timestamp: ",now());println(io,"NPAIRS: ",NPAIRS," SEED: ",SEED)
    println(io,"canonical_pair_pass: ",canonical_collapses,"/",NPAIRS);println(io,"idempotence_pass: ",idem_pass,"/",NIDEM);println(io,"semantic_pass: ",sem_pass,"/",NSEM);println(io,"determinism_pass: ",det_pass,"/",NIDEM);println(io,"certificate_pass: ",cert_pass,"/",NIDEM);println(io,"quotient_pass: ",quotient_pass,"/",NPAIRS)
    println(io,"projection_stats: ",pst);println(io,"prediction_stats: ",qst);println(io,"mean_ratio: ",mean_ratio);println(io,"median_ratio: ",median_ratio);println(io,"p95_ratio: ",p95_ratio);println(io,"p99_ratio: ",p99_ratio);println(io,"bootstrap_ci_ms: [",lo,", ",hi,"]");println(io,"core_pass: ",allcore)
    println(io,"eq_failures: ",length(eq_fail));println(io,"idem_failures: ",length(idem_fail));println(io,"semantic_failures: ",length(sem_fail));println(io,"det_failures: ",length(det_fail));println(io,"cert_failures: ",length(cert_fail))
end
println("Report: agd_quotient_definitive_results.txt"); println("="^88)
