#!/usr/bin/env bash
set -Eeuo pipefail

# --- THERMAL CONFIG ---
MAX_TEMP_C=74       # Throttling gate
COOLDOWN_TEMP=65    # Target resume temp
POLL_SEC=5

# --- HPC CONFIG ---
export JULIA_NUM_THREADS=4
export SIZE=1024
export REPS=10
export TRIALS=5
export MODES="4x1,2x2,1x4" # Optimized for 4 performance cores (4-7)
export PIN_CPU=1

log(){ echo "[$(date -u +%Y%m%dT%H%M%SZ)][Ω-HPC-THERMAL] $1"; }

monitor_thermal() {
    while true; do
        TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
        TEMP_C=$((TEMP / 1000))
        if [ "$TEMP_C" -lt "$MAX_TEMP_C" ]; then
            break
        fi
        log "WARNING: Thermal threshold reached ($TEMP_C°C). Cooling..."
        sleep "$POLL_SEC"
    done
}

# 1. Setup Environment
log "Initializing Sovereign HPC Pipeline..."
# Re-using your Turbo V2 script source
if [ ! -f "omega_julia_blas_dag_hpc_turbo_v2.sh" ]; then
    log "FAIL: Turbo V2 script not found."
    exit 1
fi

# 2. Execution Loop
log "Dispatching HPC Autotuning Suite..."
monitor_thermal

# Invoke Turbo V2 with taskset bound to performance cluster (4,5,6,7)
# Using the corrected mask syntax for ARMv8 cores 4-7
taskset -c 4,5,6,7 ./omega_julia_blas_dag_hpc_turbo_v2.sh

log "Pipeline Execution Complete."
