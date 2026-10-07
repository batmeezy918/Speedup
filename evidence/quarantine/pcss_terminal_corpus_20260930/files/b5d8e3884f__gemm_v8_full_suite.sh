#!/data/data/com.termux/files/usr/bin/bash

set -u
set -o pipefail

###############################################################################
# GEMM V8
#
# SM6475 / AArch64 / Cortex-A55 + Cortex-A78
#
# Purpose:
#   1. Freeze V7 baseline
#   2. Characterize FP32 NEON/FMA ceiling
#   3. Measure single-core scaling
#   4. Measure big-core scaling
#   5. Measure 8-core scaling
#   6. Measure cache/working-set transition
#   7. Record frequency and thermal state
#   8. Preserve correctness/checksum evidence
#
# IMPORTANT:
#   This script does NOT claim a world record.
#   It measures this device under controlled conditions.
###############################################################################

ROOT="${ROOT:-$PWD/gemm_v8_run}"
CC="${CC:-clang-21}"

REPEATS="${REPEATS:-5}"
WARMUPS="${WARMUPS:-2}"

MIN_N="${MIN_N:-128}"
MAX_N="${MAX_N:-2048}"
STEP_N="${STEP_N:-128}"

mkdir -p "$ROOT"

LOG="$ROOT/gemm_v8.log"
CSV="$ROOT/gemm_v8_results.csv"
PLATFORM="$ROOT/gemm_v8_platform.txt"
THERMAL="$ROOT/gemm_v8_thermal.txt"
FREQ="$ROOT/gemm_v8_frequency.txt"

exec > >(tee "$LOG") 2>&1

echo "============================================================"
echo "GEMM V8 — AARCH64 FP32 CEILING / SCALING SUITE"
echo "============================================================"
echo "ROOT=$ROOT"
echo "CC=$CC"
echo "REPEATS=$REPEATS"
echo "WARMUPS=$WARMUPS"
echo "N=$MIN_N..$MAX_N step $STEP_N"
echo

###############################################################################
# BASIC PLATFORM
###############################################################################

echo "=== BASIC PLATFORM ==="

uname -a

ARCH="$(uname -m)"
DEVICE="$(getprop ro.product.model 2>/dev/null || true)"
SOC="$(getprop ro.soc.model 2>/dev/null || true)"
ANDROID="$(getprop ro.build.version.release 2>/dev/null || true)"
HARDWARE="$(getprop ro.hardware 2>/dev/null || true)"

echo "ARCH=$ARCH"
echo "DEVICE=$DEVICE"
echo "SOC=$SOC"
echo "ANDROID=$ANDROID"
echo "HARDWARE=$HARDWARE"

###############################################################################
# CPU IDENTIFICATION
###############################################################################

echo
echo "=== CPU TOPOLOGY ==="

grep -E \
'^(processor|CPU implementer|CPU architecture|CPU variant|CPU part|CPU revision|Features)' \
/proc/cpuinfo | tee "$PLATFORM"

echo
echo "CPU PART SUMMARY"

grep '^CPU part' /proc/cpuinfo |
    sort |
    uniq -c

###############################################################################
# CPU MAP
###############################################################################

echo
echo "=== CPU MAP ==="

echo "cpu,part,cluster,max_khz"

for cpu in /sys/devices/system/cpu/cpu[0-9]*; do

    [ -d "$cpu" ] || continue

    id="${cpu##*cpu}"

    part="$(awk -v p="$id" '
        $1=="processor" && $3==p {found=1}
        found && /^CPU part/ {print $4; exit}
    ' /proc/cpuinfo 2>/dev/null)"

    max="?"
    [ -r "$cpu/cpufreq/cpuinfo_max_freq" ] &&
        max="$(cat "$cpu/cpufreq/cpuinfo_max_freq")"

    case "$part" in
        0xd05) cluster="A55" ;;
        0xd41) cluster="A78" ;;
        *)     cluster="UNKNOWN" ;;
    esac

    echo "$id,$part,$cluster,$max"
done

###############################################################################
# FEATURES
###############################################################################

echo
echo "=== ARM FEATURES ==="

FEATURE_LINE="$(grep -m1 '^Features' /proc/cpuinfo || true)"

echo "$FEATURE_LINE"

for f in fp asimd fphp asimdhp asimdrdm asimddp sve sve2 sme sme2; do
    case " $FEATURE_LINE " in
        *" $f "*)
            echo "$f=YES"
            ;;
        *)
            echo "$f=NO"
            ;;
    esac
done

###############################################################################
# COMPILER
###############################################################################

echo
echo "=== COMPILER ==="

if ! command -v "$CC" >/dev/null 2>&1; then
    echo "ERROR: compiler not found: $CC"
    exit 1
fi

"$CC" --version | head -4

echo
echo "=== COMPILER TARGET ==="

"$CC" -### \
    -O3 \
    -ffp-contract=fast \
    -march=armv8.2-a+fp16+dotprod \
    -mtune=cortex-a78 \
    -c -x c /dev/null 2>&1 |
    tail -20

echo
echo "=== ARM MACROS ==="

"$CC" \
    -dM -E \
    -march=armv8.2-a+fp16+dotprod \
    -x c /dev/null 2>/dev/null |
    grep -E \
'__aarch64__|__ARM_FEATURE_FMA|__ARM_FEATURE_DOTPROD|__ARM_FEATURE_FP16|__ARM_ARCH'

###############################################################################
# FREQUENCY
###############################################################################

echo
echo "=== FREQUENCY ==="

: > "$FREQ"

for p in /sys/devices/system/cpu/cpufreq/policy*; do

    [ -d "$p" ] || continue

    echo "--- $p ---" | tee -a "$FREQ"

    for x in \
        related_cpus \
        cpuinfo_min_freq \
        cpuinfo_max_freq \
        scaling_cur_freq \
        scaling_governor
    do
        if [ -r "$p/$x" ]; then
            echo "$x=$(cat "$p/$x")" | tee -a "$FREQ"
        fi
    done
done

###############################################################################
# CACHE
###############################################################################

echo
echo "=== CACHE ==="

for c in /sys/devices/system/cpu/cpu0/cache/index*; do

    [ -d "$c" ] || continue

    echo "--- $c ---"

    for x in \
        level \
        type \
        size \
        coherency_line_size \
        ways_of_associativity \
        shared_cpu_list
    do
        [ -r "$c/$x" ] &&
            echo "$x=$(cat "$c/$x")"
    done
done

###############################################################################
# THERMAL
###############################################################################

echo
echo "=== THERMAL ==="

: > "$THERMAL"

for z in /sys/class/thermal/thermal_zone*; do

    [ -d "$z" ] || continue

    type="$(cat "$z/type" 2>/dev/null || true)"
    temp="$(cat "$z/temp" 2>/dev/null || true)"

    case "$type" in
        *cpu*|*CPU*|*cpuss*|*CPUSS*|*socd*|*SOCD*)
            echo "$z type=$type temp=$temp" |
                tee -a "$THERMAL"
            ;;
    esac
done

###############################################################################
# ARCHITECTURAL MODEL
###############################################################################

echo
echo "============================================================"
echo "FP32 ARCHITECTURAL MODEL"
echo "============================================================"

echo
echo "NEON register width : 128 bits"
echo "FP32 lanes/register : 4"
echo "FMA FLOPs/lane      : 2"
echo "FLOPs/FMA instruction: 8"

echo
echo "This is an architectural model."
echo "It is NOT a measured peak."

echo
echo "For a hypothetical P-pipeline core:"
echo
echo "  peak_GFLOPS = frequency_GHz × P × 8"
echo
echo "P must be established experimentally or from authoritative"
echo "microarchitecture documentation."

###############################################################################
# BUILD BENCHMARK
###############################################################################

echo
echo "============================================================"
echo "BUILD"
echo "============================================================"

if [ ! -f gemm_v7_bench.c ]; then

    echo "ERROR: gemm_v7_bench.c not found."

    echo
    echo "Place the frozen V7 benchmark source in:"
    echo
    echo "  $PWD/gemm_v7_bench.c"

    exit 2
fi

cp gemm_v7_bench.c "$ROOT/gemm_v7_bench_baseline.c"

echo
echo "Building V8 instrumented executable..."

"$CC" \
    -O3 \
    -ffast-math \
    -ffp-contract=fast \
    -march=armv8.2-a+fp16+dotprod \
    -mtune=cortex-a78 \
    -fno-math-errno \
    -fno-trapping-math \
    -fvectorize \
    -fslp-vectorize \
    -o "$ROOT/gemm_v8_bench" \
    gemm_v7_bench.c \
    -lm

if [ $? -ne 0 ]; then
    echo "BUILD FAILED"
    exit 3
fi

file "$ROOT/gemm_v8_bench"

###############################################################################
# CSV
###############################################################################

cat > "$CSV" <<CSV
suite,kernel,cores,N,ref_s,kernel_s,GFLOPS,speedup,max_abs,rmse,checksum,status
CSV

###############################################################################
# FREQUENCY SNAPSHOT FUNCTION
###############################################################################

snapshot_freq() {

    tag="$1"

    echo
    echo "=== FREQUENCY SNAPSHOT: $tag ==="

    for p in /sys/devices/system/cpu/cpufreq/policy*; do

        [ -d "$p" ] || continue

        echo -n "$p "

        related="$(cat "$p/related_cpus" 2>/dev/null || echo '?')"
        cur="$(cat "$p/scaling_cur_freq" 2>/dev/null || echo '?')"

        echo "cpus=$related cur_khz=$cur"
    done
}

###############################################################################
# RUN FUNCTION
###############################################################################

run_case() {

    label="$1"
    cpuset="$2"

    echo
    echo "============================================================"
    echo "CASE=$label"
    echo "CPUS=$cpuset"
    echo "============================================================"

    snapshot_freq "before_$label"

    if command -v taskset >/dev/null 2>&1; then
        TASKSET=(taskset -c "$cpuset")
    else
        TASKSET=()
        echo "WARNING: taskset unavailable; CPU affinity not enforced."
    fi

    echo
    echo "--- BENCHMARK ---"

    "${TASKSET[@]}" \
        "$ROOT/gemm_v8_bench" \
        "$MIN_N" \
        "$MAX_N" \
        "$STEP_N" \
        "$REPEATS" \
        "$WARMUPS" |
    tee "$ROOT/${label}.txt"

    snapshot_freq "after_$label"
}

###############################################################################
# SINGLE A78 CORE TESTS
###############################################################################

echo
echo "============================================================"
echo "SINGLE A78 CORE"
echo "============================================================"

run_case "a78_cpu4" "4"
run_case "a78_cpu5" "5"
run_case "a78_cpu6" "6"
run_case "a78_cpu7" "7"

###############################################################################
# FOUR-CORE BIG CLUSTER
###############################################################################

echo
echo "============================================================"
echo "FOUR-CORE A78 CLUSTER"
echo "============================================================"

run_case "a78_4core" "4-7"

###############################################################################
# FOUR LITTLE CORES
###############################################################################

echo
echo "============================================================"
echo "FOUR-CORE A55 CLUSTER"
echo "============================================================"

run_case "a55_4core" "0-3"

###############################################################################
# ALL CORES
###############################################################################

echo
echo "============================================================"
echo "ALL 8 CORES"
echo "============================================================"

run_case "all_8core" "0-7"

###############################################################################
# FMA MICROBENCHMARK
###############################################################################

echo
echo "============================================================"
echo "FMA MICROBENCHMARK"
echo "============================================================"

cat > "$ROOT/fma_probe.c" <<'C'
#include <arm_neon.h>
#include <stdint.h>
#include <stdio.h>
#include <time.h>

static double now(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

int main(void)
{
    volatile float sink = 0.0f;

    float32x4_t a = vdupq_n_f32(1.001f);
    float32x4_t b = vdupq_n_f32(1.002f);
    float32x4_t c = vdupq_n_f32(0.003f);

    const uint64_t iters = 100000000ULL;

    for (int i = 0; i < 1000000; ++i)
        c = vfmaq_f32(c, a, b);

    double t0 = now();

    for (uint64_t i = 0; i < iters; ++i) {
        c = vfmaq_f32(c, a, b);
        c = vfmaq_f32(c, a, b);
        c = vfmaq_f32(c, a, b);
        c = vfmaq_f32(c, a, b);
    }

    double t1 = now();

    float x[4];
    vst1q_f32(x, c);

    sink = x[0];

    double seconds = t1 - t0;

    /*
       4 FMA instructions/iteration
       4 FP32 lanes/instruction
       2 FLOPs/lane
       = 32 FLOPs/iteration
    */

    double flops = (double)iters * 32.0;
    double gflops = flops / seconds / 1e9;

    printf("FMA_PROBE_SECONDS,%.9f\n", seconds);
    printf("FMA_PROBE_GFLOPS,%.6f\n", gflops);
    printf("FMA_PROBE_SINK,%.9f\n", sink);

    return 0;
}
C

"$CC" \
    -O3 \
    -ffast-math \
    -ffp-contract=fast \
    -march=armv8.2-a+fp16+dotprod \
    -mtune=cortex-a78 \
    "$ROOT/fma_probe.c" \
    -o "$ROOT/fma_probe"

echo
echo "--- FMA CPU4 ---"

taskset -c 4 "$ROOT/fma_probe" |
    tee "$ROOT/fma_cpu4.txt"

echo
echo "--- FMA CPU7 ---"

taskset -c 7 "$ROOT/fma_probe" |
    tee "$ROOT/fma_cpu7.txt"

###############################################################################
# CHECKSUM / SOURCE RECEIPTS
###############################################################################

echo
echo "============================================================"
echo "SHA256 RECEIPTS"
echo "============================================================"

(
    cd "$ROOT"

    sha256sum \
        gemm_v8_bench \
        gemm_v7_bench_baseline.c \
        fma_probe \
        fma_probe.c \
        gemm_v8_results.csv \
        gemm_v8_platform.txt \
        gemm_v8_thermal.txt \
        gemm_v8_frequency.txt \
        2>/dev/null
) | tee "$ROOT/gemm_v8_sha256.txt"

###############################################################################
# SUMMARY
###############################################################################

echo
echo "============================================================"
echo "GEMM V8 SUMMARY"
echo "============================================================"

echo
echo "Device : $DEVICE"
echo "SoC    : $SOC"
echo "Arch   : $ARCH"
echo "Android: $ANDROID"
echo "Compiler: $CC"

echo
echo "A55 cores: 0-3"
echo "A78 cores: 4-7"

echo
echo "V7 frozen baseline:"
echo "  PACKED_NEON_8x8"
echo "  FP32"
echo "  deterministic reference"
echo "  checksum validation"

echo
echo "V8 additions:"
echo "  per-core affinity"
echo "  big-cluster scaling"
echo "  little-cluster scaling"
echo "  8-core scaling"
echo "  frequency telemetry"
echo "  thermal telemetry"
echo "  FMA microbenchmark"
echo "  extended N sweep"
echo "  SHA256 provenance"

echo
echo "============================================================"
echo "IMPORTANT INTERPRETATION"
echo "============================================================"

echo
echo "Measured performance != architectural peak."
echo
echo "A world-record claim requires a defined comparison class:"
echo "  datatype"
echo "  matrix dimensions"
echo "  CPU/core count"
echo "  frequency"
echo "  kernel/library"
echo "  compiler"
echo "  correctness criteria"
echo "  measurement methodology"
echo
echo "V8 therefore reports measurements first."
echo "It does not manufacture a record claim."

echo
echo "============================================================"
echo "FILES"
echo "============================================================"

ls -lh "$ROOT"

echo
echo "============================================================"
echo "GEMM V8 COMPLETE"
echo "============================================================"
