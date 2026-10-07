using SHA

const M  = Float64(2.0)
const K  = Float64(5.0)
const C  = Float64(0.2)
const DT = Float64(0.02)

const X0 = Float64(0.5)
const V0 = Float64(0.2)

const STEPS = 500

function bits(x::Float64)
    reinterpret(UInt64, x)
end

function append_u64_be!(b::Vector{UInt8}, u::UInt64)
    push!(b, UInt8((u >> 56) & 0xff))
    push!(b, UInt8((u >> 48) & 0xff))
    push!(b, UInt8((u >> 40) & 0xff))
    push!(b, UInt8((u >> 32) & 0xff))
    push!(b, UInt8((u >> 24) & 0xff))
    push!(b, UInt8((u >> 16) & 0xff))
    push!(b, UInt8((u >> 8) & 0xff))
    push!(b, UInt8(u & 0xff))
end

function append_f64_be!(b::Vector{UInt8}, x::Float64)
    append_u64_be!(b, bits(x))
end

function acceleration(x::Float64, v::Float64)
    p1 = K * x
    p2 = C * v
    s1 = p1 + p2
    q1 = s1 / M
    a1 = -q1
    return a1
end

function energy(x::Float64, v::Float64)
    h = Float64(0.5)

    p1 = h * K
    p2 = p1 * x
    p3 = p2 * x

    q1 = h * M
    q2 = q1 * v
    q3 = q2 * v

    e = p3 + q3
    return e
end

function run(perturb_step::Int=-1,
             perturb_value::Float64=0.0)

    b = UInt8[]
    sizehint!(b, 24048)

    checkpoints = Dict{Int,NTuple{5,String}}()

    x = X0
    v = V0

    for i in 0:STEPS

        if i == perturb_step
            x = x + perturb_value
        end

        ii = Float64(i)
        t = ii * DT

        a = acceleration(x,v)
        e = energy(x,v)

        append_u64_be!(b,UInt64(i))
        append_f64_be!(b,t)
        append_f64_be!(b,x)
        append_f64_be!(b,v)
        append_f64_be!(b,a)
        append_f64_be!(b,e)

        if i in (0,1,2,10,100,250,500)
            checkpoints[i] = (
                bytes2hex(reinterpret(UInt8,[t])),
                bytes2hex(reinterpret(UInt8,[x])),
                bytes2hex(reinterpret(UInt8,[v])),
                bytes2hex(reinterpret(UInt8,[a])),
                bytes2hex(reinterpret(UInt8,[e]))
            )
        end

        if i < STEPS
            a_prev = a

            av = a_prev * DT
            v_new = v + av

            xv = v * DT
            x_new = x + xv

            v = v_new
            x = x_new
        end
    end

    length(b) == 24048 || error("CANONICAL SIZE FAILURE")

    return b, bytes2hex(SHA.sha256(b)), checkpoints
end

base,bh,bc = run()
base2,bh2,bc2 = run()

pert,ph,pc = run(250,Float64(1e-15))
pert2,ph2,pc2 = run(250,Float64(1e-15))

open("julia_baseline.bin","w") do f
    write(f,base)
end

open("julia_perturbed.bin","w") do f
    write(f,pert)
end

println("JULIA")
println("SIZE=",length(base))
println("HASH=",bh)
println("REPLAY_BYTES=",base == base2)
println("REPLAY_HASH=",bh == bh2)
println("PERTURBED_HASH=",ph)
println("PERTURBED_REPLAY=",pert == pert2 && ph == ph2)
println("PERTURBATION_CHANGED=",bh != ph)
println("STATE250_CHANGED=",bc[250][2] != pc[250][2])

for i in (0,1,2,10,100,250,500)
    println(
        "CHK ",i," ",
        join(bc[i]," ")
    )
end
