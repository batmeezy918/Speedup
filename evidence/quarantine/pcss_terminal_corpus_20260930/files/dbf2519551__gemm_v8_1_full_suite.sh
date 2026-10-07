#!/data/data/com.termux/files/usr/bin/bash
set -u
set -o pipefail

###############################################################################
# GEMM V8.1 — FULL AARCH64 / SM6475 CHARACTERIZATION SUITE
#
# Purpose:
#   Freeze V7 evidence.
#   Establish reproducible single-core / cluster / all-core measurements.
#   Test working-set scaling.
#   Test FMA throughput.
#   Record frequency + thermal state.
#   Preserve source/binary/result hashes.
#
# NO WORLD-RECORD CLAIM IS MADE BY THIS SCRIPT.
###############################################################################

ROOT="${ROOT:-$HOME/gemm_v8_1_run}"
CC="${CC:-clang-21}"

REPEATS="${REPEATS:-5}"
WARMUPS="${WARMUPS:-2}"

MIN_N="${MIN_N:-128}"
MAX_N="${MAX_N:-2048}"
STEP_N="${STEP_N:-128}"

mkdir -p "$ROOT"

LOG="$ROOT/gemm_v8_1.log"
CSV="$ROOT/gemm_v8_1_results.csv"
META="$ROOT/gemm_v8_1_metadata.txt"
SHA="$ROOT/gemm_v8_1_sha256.txt"

exec > >(tee "$LOG") 2>&1

die() {
    echo
    echo "FATAL: $*"
    exit 1
}

echo "============================================================"
echo " GEMM V8.1 — FULL SM6475 CHARACTERIZATION"
echo "============================================================"
echo "ROOT=$ROOT"
echo "CC=$CC"
echo "REPEATS=$REPEATS"
echo "WARMUPS=$WARMUPS"
echo "N=$MIN_N..$MAX_N STEP=$STEP_N"
echo

###############################################################################
# LOCATE FROZEN V7 SOURCE
###############################################################################

SRC=""

for candidate in \
    "$PWD/gemm_v7_bench.c" \
    "$HOME/gemm_v7_bench.c" \
    "$HOME/downloads/gemm_v7_bench.c" \
    "$HOME/storage/downloads/gemm_v7_bench.c"
do
    if [ -f "$candidate" ]; then
        SRC="$candidate"
        break
    fi
done

[ -n "$SRC" ] || die \
"Could not locate gemm_v7_bench.c.

Expected one of:
  $PWD/gemm_v7_bench.c
  $HOME/gemm_v7_bench.c
  $HOME/downloads/gemm_v7_bench.c
  $HOME/storage/downloads/gemm_v7_bench.c"

echo "V7 SOURCE=$SRC"

###############################################################################
# BASIC PLATFORM
###############################################################################

{
    echo "=== PLATFORM ==="
    date -u '+UTC=%Y-%m-%dT%H:%M:%SZ'
    uname -a

    echo "ARCH=$(uname -m)"
    echo "DEVICE=$(getprop ro.product.model 2>/dev/null || true)"
    echo "SOC=$(getprop ro.soc.model 2>/dev/null || true)"
    echo "ANDROID=$(getprop ro.build.version.release 2>/dev/null || true)"
    echo "HARDWARE=$(getprop ro.hardware 2>/dev/null || true)"
    echo "KERNEL=$(uname -r)"

    echo
    echo "=== CPU PARTS ==="
    grep -E '^(processor|CPU implementer|CPU architecture|CPU variant|CPU part|CPU revision)' \
        /proc/cpuinfo || true

    echo
    echo "=== FEATURES ==="
    grep -m1 '^Features' /proc/cpuinfo || true

    echo
    echo "=== COMPILER ==="
    "$CC" --version | head -4

    echo
    echo "=== V7 SOURCE HASH ==="
    sha256sum "$SRC"

    echo
    echo "=== V7 SOURCE SIZE ==="
    wc -c "$SRC"
} | tee "$META"

###############################################################################
# CPU MAP
###############################################################################

echo
echo "============================================================"
echo "CPU MAP"
echo "============================================================"

echo "cpu,part,cluster,max_khz"

for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
    [ -d "$cpu" ] || continue

    id="${cpu##*cpu}"

    case "$id" in
        0|1|2|3)
            cluster="A55"
            ;;
        4|5|6|7)
            cluster="A78"
            ;;
        *)
            cluster="UNKNOWN"
            ;;
    esac

    part="$(awk -v p="$id" '
        $1=="processor" && $3==p {f=1; next}
        f && /^CPU part/ {print $4; exit}
    ' /proc/cpuinfo 2>/dev/null)"

    max="$(cat "$cpu/cpufreq/cpuinfo_max_freq" 2>/dev/null || echo '?')"

    echo "$id,$part,$cluster,$max"
done | tee "$ROOT/cpu_map.csv"

###############################################################################
# FEATURES
###############################################################################

echo
echo "============================================================"
echo "ARM ISA"
echo "============================================================"

FEATURES="$(grep -m1 '^Features' /proc/cpuinfo || true)"
echo "$FEATURES"

for f in fp asimd fphp asimdhp asimdrdm asimddp sve sve2 sme sme2; do
    if echo " $FEATURES " | grep -q " $f "; then
        echo "$f=YES"
    else
        echo "$f=NO"
    fi
done

###############################################################################
# COMPILER TARGET
###############################################################################

echo
echo "============================================================"
echo "COMPILER TARGET"
echo "============================================================"

"$CC" -### \
    -O3 \
    -ffp-contract=fast \
    -march=armv8.2-a+fp16+dotprod \
    -mtune=cortex-a78 \
    -c -x c /dev/null 2>&1 |
    tail -30

echo
echo "=== MACROS ==="

"$CC" -dM -E \
    -march=armv8.2-a+fp16+dotprod \
    -x c /dev/null 2>/dev/null |
grep -E '__aarch64__|__ARM_FEATURE_FMA|__ARM_FEATURE_DOTPROD|__ARM_FEATURE_FP16|__ARM_ARCH'

###############################################################################
# CACHE
###############################################################################

echo
echo "============================================================"
echo "CACHE"
echo "============================================================"

for c in /sys/devices/system/cpu/cpu0/cache/index*; do
    [ -d "$c" ] || continue

    echo "--- $c ---"

    for x in \
        level type size coherency_line_size \
        ways_of_associativity shared_cpu_list
    do
        [ -r "$c/$x" ] && echo "$x=$(cat "$c/$x")"
    done
done | tee "$ROOT/cache.txt"

###############################################################################
# INITIAL THERMAL
###############################################################################

thermal_snapshot() {
    tag="$1"
    outfile="$ROOT/thermal_${tag}.txt"

    {
        echo "timestamp=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

        for z in /sys/class/thermal/thermal_zone*; do
            [ -d "$z" ] || continue

            type="$(cat "$z/type" 2>/dev/null || true)"
            temp="$(cat "$z/temp" 2>/dev/null || true)"

            case "$type" in
                *cpu*|*CPU*|*cpuss*|*CPUSS*|*socd*|*SOCD*)
                    echo "$z type=$type temp=$temp"
                    ;;
            esac
        done
    } | tee "$outfile"
}

freq_snapshot() {
    tag="$1"
    outfile="$ROOT/frequency_${tag}.txt"

    {
        echo "timestamp=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

        for p in /sys/devices/system/cpu/cpufreq/policy*; do
            [ -d "$p" ] || continue

            echo "--- $p ---"

            for x in \
                related_cpus \
                cpuinfo_min_freq \
                cpuinfo_max_freq \
                scaling_cur_freq \
                scaling_governor
            do
                [ -r "$p/$x" ] &&
                    echo "$x=$(cat "$p/$x")"
            done
        done
    } | tee "$outfile"
}

thermal_snapshot "initial"
freq_snapshot "initial"

###############################################################################
# BUILD
###############################################################################

echo
echo "============================================================"
echo "BUILD V8.1"
echo "============================================================"

cp "$SRC" "$ROOT/gemm_v7_bench_baseline.c"

echo "Baseline copied:"
echo "$ROOT/gemm_v7_bench_baseline.c"

echo
echo "Building benchmark..."

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
    "$SRC" \
    -lm ||
    die "GEMM build failed."

file "$ROOT/gemm_v8_bench"

###############################################################################
# RESULT CSV
###############################################################################

cat > "$CSV" <<'CSV'
suite,kernel,cpuset,N,ref_s,kernel_s,GFLOPS,speedup,max_abs,rmse,checksum,status
CSV

###############################################################################
# RUN CASE
###############################################################################

run_case() {

    label="$1"
    cpuset="$2"

    echo
    echo "============================================================"
    echo "CASE: $label"
    echo "CPUSET: $cpuset"
    echo "============================================================"

    thermal_snapshot "before_${label}"
    freq_snapshot "before_${label}"

    if command -v taskset >/dev/null 2>&1; then
        taskset -c "$cpuset" \
            "$ROOT/gemm_v8_bench" \
            "$MIN_N" "$MAX_N" "$STEP_N" \
            "$REPEATS" "$WARMUPS" |
            tee "$ROOT/${label}.txt"
    else
        echo "WARNING: taskset unavailable"
        "$ROOT/gemm_v8_bench" \
            "$MIN_N" "$MAX_N" "$STEP_N" \
            "$REPEATS" "$WARMUPS" |
            tee "$ROOT/${label}.txt"
    fi

    thermal_snapshot "after_${label}"
    freq_snapshot "after_${label}"

    # Extract benchmark result records into master CSV.
    awk -F',' '
        /^GEMM_V7_RESULT,/ {
            print "V8.1," \
                  $2 "," \
                  "'"$cpuset"'," \
                  $3 "," \
                  $5 "," \
                  $6 "," \
                  $7 "," \
                  $8 "," \
                  $9 "," \
                  $10 "," \
                  $11 "," \
                  $12
        }
    ' "$ROOT/${label}.txt" >> "$CSV"
}

###############################################################################
# BENCHMARK CASES
###############################################################################

echo
echo "============================================================"
echo "SINGLE A78 CORE"
echo "============================================================"

run_case "a78_cpu4" "4"
run_case "a78_cpu5" "5"
run_case "a78_cpu6" "6"
run_case "a78_cpu7" "7"

echo
echo "============================================================"
echo "FOUR A78 CORES"
echo "============================================================"

run_case "a78_4core" "4-7"

echo
echo "============================================================"
echo "FOUR A55 CORES"
echo "============================================================"

run_case "a55_4core" "0-3"

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
    return (double)ts.tv_sec +
           (double)ts.tv_nsec * 1e-9;
}

int main(void)
{
    volatile float sink;

    float32x4_t a = vdupq_n_f32(1.001f);
    float32x4_t b = vdupq_n_f32(1.002f);
    float32x4_t c = vdupq_n_f32(0.003f);

    const uint64_t ITERS = 100000000ULL;

    for (int i = 0; i < 1000000; ++i) {
        c = vfmaq_f32(c,a,b);
        c = vfmaq_f32(c,a,b);
        c = vfmaq_f32(c,a,b);
        c = vfmaq_f32(c,a,b);
    }

    double t0 = now();

    for (uint64_t i = 0; i < ITERS; ++i) {
        c = vfmaq_f32(c,a,b);
        c = vfmaq_f32(c,a,b);
        c = vfmaq_f32(c,a,b);
        c = vfmaq_f32(c,a,b);
    }

    double t1 = now();

    float x[4];
    vst1q_f32(x,c);
    sink=x[0];

    double sec=t1-t0;
    double flops=(double)ITERS*32.0;
    double gflops=flops/sec/1e9;

    printf("FMA_PROBE_SECONDS,%.9f\n",sec);
    printf("FMA_PROBE_GFLOPS,%.6f\n",gflops);
    printf("FMA_PROBE_SINK,%.9f\n",sink);

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
    -o "$ROOT/fma_probe" ||
    die "FMA build failed."

for cpu in 4 7; do
    echo
    echo "--- FMA CPU $cpu ---"

    thermal_snapshot "before_fma_cpu${cpu}"
    freq_snapshot "before_fma_cpu${cpu}"

    taskset -c "$cpu" \
        "$ROOT/fma_probe" |
        tee "$ROOT/fma_cpu${cpu}.txt"

    thermal_snapshot "after_fma_cpu${cpu}"
    freq_snapshot "after_fma_cpu${cpu}"
done

###############################################################################
# CHECKSUMS
###############################################################################

echo
echo "============================================================"
echo "SHA256 PROVENANCE"
echo "============================================================"

(
    cd "$ROOT"

    sha256sum \
        gemm_v7_bench_baseline.c \
        gemm_v8_bench \
        fma_probe.c \
        fma_probe \
        gemm_v8_1_results.csv \
        cpu_map.csv \
        cache.txt \
        2>/dev/null
) | tee "$SHA"

###############################################################################
# AUTOMATIC RESULT ANALYSIS
###############################################################################

echo
echo "============================================================"
echo "RESULT ANALYSIS"
echo "============================================================"

python3 - "$CSV" <<'PY'
import csv
import sys
from collections import defaultdict

path=sys.argv[1]

rows=[]

with open(path,newline="") as f:
    for r in csv.DictReader(f):
        if r.get("status")=="PASS":
            try:
                r["GFLOPS"]=float(r["GFLOPS"])
                r["speedup"]=float(r["speedup"])
                r["N"]=int(r["N"])
                rows.append(r)
            except:
                pass

print("PASS_ROWS,",len(rows))

if not rows:
    print("NO_VALID_PASS_ROWS")
    sys.exit(0)

bycase=defaultdict(list)

for r in rows:
    bycase[r["cpuset"]].append(r)

print()
print("CASE_MAX_GFLOPS")

for case,rs in sorted(bycase.items()):
    best=max(rs,key=lambda x:x["GFLOPS"])
    print(
        case,
        "N="+str(best["N"]),
        "GFLOPS=%.6f"%best["GFLOPS"],
        "speedup=%.6fx"%best["speedup"]
    )

print()
best=max(rows,key=lambda x:x["GFLOPS"])

print("GLOBAL_MAX")
print("cpuset=",best["cpuset"])
print("N=",best["N"])
print("GFLOPS=%.6f"%best["GFLOPS"])
print("speedup=%.6fx"%best["speedup"])
print("checksum=",best["checksum"])

###############################################################################
# Correctness invariant
###############################################################################

bad=[]

for r in rows:
    try:
        if float(r["max_abs"]) < 0 or float(r["rmse"]) < 0:
            bad.append(r)
    except:
        bad.append(r)

print()
print("CORRECTNESS_ROWS_CHECKED,",len(rows))
print("CORRECTNESS_FORMAT_STATUS,", "PASS" if not bad else "FAIL")
PY

###############################################################################
# FINAL STATE
###############################################################################

thermal_snapshot "final"
freq_snapshot "final"

echo
echo "============================================================"
echo "V8.1 EVIDENCE SUMMARY"
echo "============================================================"

echo "Source:"
sha256sum "$ROOT/gemm_v7_bench_baseline.c"

echo
echo "Binary:"
sha256sum "$ROOT/gemm_v8_bench"

echo
echo "Results:"
wc -l "$CSV"

echo
echo "Result rows:"
grep -c '^V8.1,' "$CSV" || true

echo
echo "PASS rows:"
grep -c ',PASS$' "$CSV" || true

echo
echo "Output directory:"
ls -lh "$ROOT"

echo
echo "============================================================"
echo "INTERPRETATION"
echo "============================================================"

cat <<'TXT'

1. The GEMM result is a DEVICE-SPECIFIC MEASUREMENT.

2. The V7 checksum/correctness behavior is preserved as the baseline.

3. A measured speedup against the reference implementation is not,
   by itself, evidence of a world record.

4. The FMA probe measures sustained throughput of the selected CPU
   under the current Android scheduler/frequency/thermal state.

5. CPU frequency is dynamic under WALT, therefore a benchmark result
   must be interpreted together with the frequency snapshots.

6. The most important comparison outputs are:
      single A78
      four A78
      four A55
      eight-core
      N scaling
      FMA throughput

7. Any external "world record" comparison requires a separately
   defined benchmark class and independently verified competitor data.

============================================================
GEMM V8.1 COMPLETE
============================================================
TXT
