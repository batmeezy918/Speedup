#!/usr/bin/env bash
# Full SOTA differential run: AGD/MuNi quotient descent vs dense/BLAS baselines.
# Interleaved A/B, warmup discarded, N trials, A/A noise floor, rotating order.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REC="$HERE/receipts"; BIN="$HERE/bin"; SRC="$HERE/src"
mkdir -p "$REC" "$BIN"

CC=${CC:-gcc}
CFLAGS=(-O3 -march=native -mtune=native -funroll-loops -fomit-frame-pointer
        -DNDEBUG -std=c11 -D_POSIX_C_SOURCE=200809L
        -DAGD_COMPILER='"GCC_14"' -DAGD_FLAGS='"-O3 -march=native"'
        -DAGD_TARGET='"aarch64-linux-gnu"' -DAGD_SOURCE_SHA='"source_manifest"'
        -I"$SRC")

echo "== build sota_bench (OpenBLAS) =="
"$CC" "${CFLAGS[@]}" "$SRC/sota_bench.c" "$SRC/agd_elev.c" "$SRC/agd_cert.c" \
      -o "$BIN/sota_bench" -lopenblas -lm
ldd "$BIN/sota_bench" | grep -i blas | tee "$REC/sota_blas_link.txt" || true

# SOTA baseline identity (OpenBLAS prints its own config/version).
python3 - <<'PY' | tee "$REC/sota_blas_config.txt"
import ctypes
try:
    b = ctypes.CDLL("libopenblas.so")
    b.openblas_get_config.restype = ctypes.c_char_p
    print("OPENBLAS_CONFIG", b.openblas_get_config().decode())
    try:
        b.openblas_get_parallel.restype = ctypes.c_int
        print("OPENBLAS_PARALLEL_MODE", b.openblas_get_parallel())
    except Exception as e:
        print("OPENBLAS_PARALLEL_MODE unavailable", e)
except Exception as e:
    print("OPENBLAS unavailable", e)
PY

# label d m r steps trials reps [flags]
CONFIGS=(
  "s512   512   32   16  1000 9 2"
  "s1024  1024  32   32   500 9 2"
  "s2048  2048  64   32   200 9 2 nonaive"
  "s4096  4096  64   64    40 9 2 nonaive"
  "s65536 65536 256 256    10 9 2 noblas nonaive"
)

echo "== running ${#CONFIGS[@]} configs =="
for c in "${CONFIGS[@]}"; do
  set -- $c
  label="$1"; shift
  echo "-- $label : $*"
  "$BIN/sota_bench" "$@" | tee "$REC/sota_raw_${label}.txt"
done

echo "== aggregate =="
python3 "$HERE/sota_aggregate.py" "$REC"/sota_raw_*.txt | tee "$REC/sota_report.txt"
echo "DONE"
