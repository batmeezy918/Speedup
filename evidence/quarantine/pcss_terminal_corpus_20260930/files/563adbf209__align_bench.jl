using Printf

function profile_stride_latency(aligned::Bool, buffer_size_mb::Int = 64, iterations::Int = 10)
    bytes = buffer_size_mb * 1024 * 1024
    raw_ptr = ccall(:malloc, Ptr{UInt8}, (Csize_t,), bytes + 64)
    ccall(:memset, Ptr{Cvoid}, (Ptr{Cvoid}, Cint, Csize_t), raw_ptr, 0xAA, bytes + 64)

    # 1-byte offset forces L1/L2 cache line boundary crossing (split-load)
    target_ptr = aligned ? Ptr{UInt64}(raw_ptr) : Ptr{UInt64}(raw_ptr + 1)
    strides = div(bytes, 64)

    # Warmup cache
    acc = UInt64(0)
    for i in 0:(strides - 1)
        acc += unsafe_load(target_ptr + (i * 64))
    end

    # High-Precision Monotonic Timer Benchmark
    t_start = time_ns()
    for iter in 1:iterations
        for i in 0:(strides - 1)
            acc += unsafe_load(target_ptr + (i * 64))
        end
    end
    t_end = time_ns()

    ccall(:free, Cvoid, (Ptr{Cvoid},), raw_ptr)

    total_time_ms = (t_end - t_start) / 1e6
    avg_pass_ms = total_time_ms / iterations
    total_bytes_read = Float64(bytes) * iterations
    gb_per_sec = (total_bytes_read / 1e9) / ((t_end - t_start) / 1e9)

    return (time_ms = avg_pass_ms, bandwidth_gbs = gb_per_sec, checksum = acc)
end

function main()
    println("\n========================================================")
    println("  REAL-WORLD ARM HARDWARE ALIGNMENT BENCHMARK (TIMED)   ")
    println("========================================================")

    buf_mb = 64
    iters = 10

    println("Running 64-Byte Aligned Fetch...")
    aligned_res = profile_stride_latency(true, buf_mb, iters)

    println("Running 1-Byte Misaligned Fetch (Split-Loads)...")
    unaligned_res = profile_stride_latency(false, buf_mb, iters)

    @printf("\n[64-BYTE ALIGNED ACCESS]\n")
    @printf("  Avg Time / Pass:   %10.3f ms\n", aligned_res.time_ms)
    @printf("  Effective Bandwidth: %8.2f GB/s\n", aligned_res.bandwidth_gbs)

    @printf("\n[MISALIGNED / SPLIT-LOAD ACCESS]\n")
    @printf("  Avg Time / Pass:   %10.3f ms\n", unaligned_res.time_ms)
    @printf("  Effective Bandwidth: %8.2f GB/s\n", unaligned_res.bandwidth_gbs)

    penalty_ratio = unaligned_res.time_ms / aligned_res.time_ms
    @printf("\nEmpirical Hardware Latency Penalty: %.2fx Slower\n", penalty_ratio)
    println("========================================================\n")
end

main()
