#!/usr/bin/env bash
# Reproducible elevation build + evidence. One command, deterministic workload.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REC="$HERE/receipts"; BIN="$HERE/bin"; SRC="$HERE/src"
mkdir -p "$REC" "$BIN"

CC=${CC:-gcc}
CFLAGS_STR="-O3 -march=native -mtune=native -funroll-loops -fomit-frame-pointer -DNDEBUG -std=c11 -D_POSIX_C_SOURCE=200809L -DAGD_COMPILER=GCC_14 -DAGD_FLAGS=-O3,-march=native -DAGD_TARGET=aarch64-linux-gnu -DAGD_SOURCE_SHA=source_manifest -Isrc"
CFLAGS=(-O3 -march=native -mtune=native -funroll-loops -fomit-frame-pointer
        -DNDEBUG -std=c11 -D_POSIX_C_SOURCE=200809L
        -DAGD_COMPILER='"GCC_14"' -DAGD_FLAGS='"-O3 -march=native"'
        -DAGD_TARGET='"aarch64-linux-gnu"' -DAGD_SOURCE_SHA='"source_manifest"'
        -I"$SRC")

echo "== build =="
"$CC" "${CFLAGS[@]}" "$SRC/agd_elev_main.c" "$SRC/agd_elev.c" "$SRC/agd_cert.c" -o "$BIN/agd_elev" -lm
"$CC" "${CFLAGS[@]}" "$SRC/agd_fuzz.c" "$SRC/agd_cert.c" -o "$BIN/agd_fuzz" -lm
"$CC" "${CFLAGS[@]}" "$SRC/agd_adversarial.c" "$SRC/agd_cert.c" -o "$BIN/agd_adversarial" -lm

echo "== adversarial =="
"$BIN/agd_adversarial" > "$REC/adversarial.txt" 2>&1; echo "adv_exit=$?"; tail -1 "$REC/adversarial.txt"

echo "== refinement selftest =="
"$BIN/agd_elev" selftest | tee "$REC/refine_selftest.txt"

echo "== property fuzz (Task 4) =="
"$BIN/agd_fuzz" 20000 | tee "$REC/fuzz.txt"

echo "== honest dense baseline (Task 1) =="
"$BIN/agd_elev" bench 2048 64 32 5 3 "$REC/bench.json" | tee "$REC/bench.txt"

echo "== named heat workload (Task 5) =="
"$BIN/agd_elev" heat 2048 64 32 5 3 "$REC/heat.json" | tee "$REC/heat.txt"

echo "== sessions + noise floor (Task 6) =="
"$HERE/run_sessions.sh" 9 2048 64 32 5 3 | tee "$REC/sessions.txt"
python3 "$HERE/aggregate_sessions.py" | tee "$REC/session_stats.txt"

echo "== provenance / reproducibility receipt =="
python3 "$HERE/capture_provenance.py" "$CFLAGS_STR" | tee "$REC/provenance.txt"

echo "== recursive formal-gap ledger (Task 7) =="
python3 "$HERE/agd_gap_ledger.py" 5 | tee "$REC/gap_ledger.txt"

echo "== full SOTA differential vs dense/BLAS (Task 8) =="
"$HERE/run_sota.sh" > "$REC/sota_full.log" 2>&1; echo "sota_exit=$?"; tail -12 "$REC/sota_full.log"

echo "== manifest =="
( cd "$HERE" && { find src bin receipts -type f ! -name deliverables.sha256; \
    ls run_all.sh run_sessions.sh aggregate_sessions.py agd_gap_ledger.py capture_provenance.py \
       run_sota.sh sota_aggregate.py REPORT.md SOTA_REPORT.md; } \
  | sort | xargs sha256sum > receipts/deliverables.sha256 )
echo "DONE"
