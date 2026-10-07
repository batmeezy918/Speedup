using SHA

###############################################################################
# AGD RECURSIVE QUOTIENT TEST
#
# Minimal Runtime
# The MIR is the program.
###############################################################################

##############################
# STATE
##############################

struct State
    ψ::Dict{Symbol,Any}
end

heat(s::State)=get(s.ψ,:heat,0)
curvature(s::State)=get(s.ψ,:curvature,1.0)

##############################
# OPERATOR REGISTRY
##############################

const OPS=Dict{String,Function}()

function register!(name,f)
    OPS[name]=f
end

##############################
# Generic operator
##############################

register!("identity") do ψ
    ψ
end

##############################
# Runtime
##############################

function step(node,state)

    ψ=copy(state.ψ)

    ψ=OPS[node["operator"]](ψ)

    ψ[:heat]=heat(state)+1
    ψ[:curvature]=Float64(node["curvature"])

    return State(ψ)

end

##############################
# Fixed point
##############################

function fixedpoint(node,state)

    node["next"]===nothing &&
    curvature(state)==0.0

end

##############################
# Recursive Unfold
##############################

function unfold(graph,nodeid,state)

    node=graph[string(nodeid)]

    println()

    println("================================")
    println("Q$(nodeid)")
    println("Intent      : ",node["intent"])
    println("Heat        : ",heat(state))
    println("Curvature   : ",curvature(state))

    newstate=step(node,state)

    @assert heat(newstate)>heat(state)
    @assert curvature(newstate)<=curvature(state)

    if fixedpoint(node,newstate)

        println()
        println("================================")
        println("LEAST FIXED POINT REACHED")
        println("================================")

        fp=bytes2hex(
            sha256(codeunits(string(newstate.ψ)))
        )

        println("Fingerprint : ",fp[1:16])
        println("Heat        : ",heat(newstate))
        println("Curvature   : ",curvature(newstate))

        return newstate

    end

    return unfold(
        graph,
        node["next"],
        newstate
    )

end

##############################
# MIR
##############################

graph=Dict(

"1"=>Dict(
"intent"=>"BOOT",
"operator"=>"identity",
"curvature"=>0.85,
"next"=>2
),

"2"=>Dict(
"intent"=>"SCAN",
"operator"=>"identity",
"curvature"=>0.60,
"next"=>3
),

"3"=>Dict(
"intent"=>"CONNECT",
"operator"=>"identity",
"curvature"=>0.35,
"next"=>4
),

"4"=>Dict(
"intent"=>"ATR",
"operator"=>"identity",
"curvature"=>0.18,
"next"=>5
),

"5"=>Dict(
"intent"=>"APDU",
"operator"=>"identity",
"curvature"=>0.08,
"next"=>6
),

"6"=>Dict(
"intent"=>"VERIFY",
"operator"=>"identity",
"curvature"=>0.00,
"next"=>nothing
)

)

##############################
# Root
##############################

ψ0=State(Dict(

:heat=>0,
:curvature=>1.0

))

##############################
# Execute
##############################

println()
println("========================================")
println("AGD RECURSIVE QUOTIENT RUNTIME")
println("========================================")

ψstar=unfold(graph,1,ψ0)

println()
println("DONE")
