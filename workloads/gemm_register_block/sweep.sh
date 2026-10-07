#!/usr/bin/env bash
# Scaling sweep: does the register-blocking gain grow with n?
#
# Hypothesis (from sovereign_kernel_opt.c:12-16): the baseline is memory-bound
# because C is re-streamed (n/B_TILE)^2 times; the candidate holds C in
# registers. If that is the mechanism, the advantage must GROW with n, because
# the excess C traffic grows with n while the flops grow faster.
#
# Runs ab_harness at each n, single core, same binary, back to back, then writes
# a single summary the Python side can audit. Governor and core affinity are
# recorded because they are confounders we cannot eliminate, only disclose.
set -u
cd "$(dirname "$0")"
OUT=${1:-/tmp/sweep}
mkdir -p "$OUT"
export OMP_NUM_THREADS=1
echo "host: cores=$(nproc) gov=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null) model=$(lscpu | awk -F: '/Model name/{print $2;exit}' | xargs)" > "$OUT/env.txt"
for n in 256 512 1024 2048 4096; do
  echo "=== n=$n ===" >> "$OUT/env.txt"
  /usr/bin/time -f "wall=%e maxrss=%MkB" ./ab_harness "$n" "$OUT/ab_$n.json" 2>> "$OUT/env.txt"
  echo "exit=$?" >> "$OUT/env.txt"
done
echo "SWEEP_DONE" >> "$OUT/env.txt"