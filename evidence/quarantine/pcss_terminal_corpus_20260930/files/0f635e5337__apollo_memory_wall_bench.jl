using LinearAlgebra, Statistics, Printf

# ============================================================
# ⚙️ Ω-STREAMING BENCHMARK: L1 THROUGHPUT VS RAM BANDWIDTH
# ============================================================

# 1 Gigabyte of Float64 data
const GIGABYTE_SIZE = 1024 * 1024 * 1024
const NUM_ELEMENTS = GIGABYTE_SIZE ÷ 8 # 8 bytes per Float64
const ε = 0.06195316

function run_streaming_bench()
    println("\n\033[95m[!] INITIATING GIGABYTE-STREAMING BENCHMARK\033[0m")
    println("Target: 1.0 GB Data Stream through Ω-Sieve")
    println("--------------------------------------------------")

    # Allocate 1GB in RAM
    println("Allocating 1GB Buffer...")
    data = randn(Float64, NUM_ELEMENTS)
    
    # 1. BASELINE: RAW MEMORY ACCESS (READ/WRITE)
    println("Measuring Raw Memory Bandwidth...")
    start_raw = time_ns()
    for i in 1:NUM_ELEMENTS
        @inbounds data[i] = data[i] * 1.0000001 # Minimal op
    end
    end_raw = time_ns()
    raw_time = (end_raw - start_raw) / 1e9
    raw_bw = (GIGABYTE_SIZE / raw_time) / 1e9

    # 2. Ω-SIEVE: COMPUTE-BOUND STREAMING
    println("Streaming through Ω-Sieve (L1-resident logic)...")
    start_omega = time_ns()
    for i in 1:NUM_ELEMENTS
        # This is the Ω-deform. It happens in the CPU Registers/L1
        # as the data is streamed from RAM.
        @inbounds val = data[i]
        @inbounds data[i] = val - ε * (abs(val)^2 * val)
    end
    end_omega = time_ns()
    omega_time = (end_omega - start_omega) / 1e9
    omega_bw = (GIGABYTE_SIZE / omega_time) / 1e9

    # ============================================================
    # ENGINEERING REPORT
    # ============================================================
    println("--------------------------------------------------")
    @printf("RAW MEMORY TIME : %.4f sec (%.2f GB/s)\n", raw_time, raw_bw)
    @printf("Ω-STREAM TIME   : %.4f sec (%.2f GB/s)\n", omega_time, omega_bw)
    
    compute_overhead = ((omega_time - raw_time) / raw_time) * 100
    @printf("COMPUTE OVERHEAD: %.2f%%\n", compute_overhead)

    if compute_overhead < 15.0
        println("\033[92m[✓] COMPUTE-BOUND: L1 throughput matches RAM speed.\033[0m")
    else
        println("\033[93m[!] MEMORY-BOUND: CPU is waiting on RAM bus.\033[0m")
    end
    println("--------------------------------------------------")
end

run_streaming_bench()
