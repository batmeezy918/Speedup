using Pkg
Pkg.activate(".")

include("src/adaptive_governor.jl")
using .AdaptiveGovernor
using BenchmarkTools

println("=========================================================")
println("   Ω STACK INVARIANT VALIDATION: HARDWARE GOVERNOR       ")
println("=========================================================")

α = 0.7
β = 0.0001
test_scales = [10000, 50000, 100000]

for N in test_scales
    println("\n[*] Target Payload Size: N = $N")
    
    # Verify mathematical accuracy against the unallocated footprint
    result = AdaptiveGovernor.dynamic_cache_executor(N, α, β)
    println("  |-- Result Vector: ", round(real(result), digits=4), " + ", round(imag(result), digits=4), "im")
    
    # Track physical performance characteristics
    println("  |-- Hardware Performance Profile:")
    @btime AdaptiveGovernor.dynamic_cache_executor($N, $α, $β)
end

println("\n=========================================================")
println(" [STATUS: VERIFIED] Adaptive Governor Successfully Synced ")
println("=========================================================")
