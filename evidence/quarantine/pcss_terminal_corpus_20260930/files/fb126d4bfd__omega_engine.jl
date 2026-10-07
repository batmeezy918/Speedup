using LinearAlgebra
using LinearAlgebra.BLAS

# Set threads to match your actual core count for stability
BLAS.set_num_threads(4) 

const PIPE_PATH = "/data/data/com.termux/files/home/quantum_pipe"

function engage()
    N = 1024 # Increased size for more sustained "Prowess"
    A = rand(Float64, N, N)
    B = rand(Float64, N, N)
    
    println("[!] OMEGA CORE: ENGAGED")
    
    while true
        start_t = time()
        C = A * B
        t = time() - start_t
        
        gflops = (2.0 * N^3) / t / 1e9
        # Status 2 (Torsion) if we break 30 GFLOPS
        status = gflops > 30 ? 2 : 1
        
        try
            open(PIPE_PATH, "w") do f
                # Clean pipe format: STATUS|VALUE
                write(f, "$status|$(round(gflops, digits=2)) GFLOPS")
            end
        catch
            # Bridge busy, cycle through
        end
        yield()
    end
end

engage()
