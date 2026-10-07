#!/usr/bin/env python3
import time, os, statistics, math, cmath

DURATION, ITER, CORES = 20, 2_000_000, 8
GATE = complex(1.0, 1.0) / math.sqrt(2.0)

def read_cpu():
    with open("/proc/stat") as f:
        return [(int(p.split()[4]), sum(map(int, p.split()[1:]))) for p in f if p.startswith("cpu") and p[3].isdigit()]

def cpu_delta(p, c):
    return [100 * (1 - (ci-pi)/(ct-pt)) if (ct-pt) != 0 else 0 for (pi, pt), (ci, ct) in zip(p, c)]

def quantum_manifold_workload():
    state = complex(1.0, 0.0)
    for i in range(ITER):
        phase = cmath.exp(complex(0, (i * 0.000001)))
        state = (state * GATE) + phase
        if abs(state) > 10.0: state = complex(1.0, 0.0)
    return state

def run():
    print("\n=== OMEGA-S4 QUANTUM PROWESS HARNESS ===\n")
    prev_cpu, start, timeline = read_cpu(), time.perf_counter(), []
    while time.perf_counter() - start < DURATION:
        t0 = time.perf_counter()
        final_state = quantum_manifold_workload()
        t1 = time.perf_counter()
        curr_cpu = read_cpu()
        usage = cpu_delta(prev_cpu, curr_cpu)
        prev_cpu = curr_cpu
        q_states_sec = ITER / (t1 - t0)
        seal = hash(final_state) & 0xFFFFFFFFFFFFFFFF
        timeline.append((usage, q_states_sec, seal))
        print(f"[{t1-start:5.2f}s] CPU={statistics.mean(usage):5.1f}% Q_STATES={q_states_sec/1e6:6.2f}M/s SEAL=0x{seal:016x}")
    
    ops = [o for u, o, s in timeline]
    print(f"\n===== QUANTUM DOMINANCE PROFILE =====")
    print(f"Peak Quantum Speed : {max(ops)/1e6:.2f} M_QSTATES/s")
    print(f"FINAL DETERMINISM  : 0x{timeline[-1][2]:016x}")

if __name__ == "__main__":
    run()
