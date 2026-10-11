#!/usr/bin/env bash
# Task 6: independent interleaved sessions + A/A noise floor.
# Each session is a separate process (true independence), workload fixed across
# sessions so the only variation is timing noise.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="$HERE/bin/agd_elev"
REC="$HERE/receipts"
mkdir -p "$REC"
K="${1:-11}"
D="${2:-2048}"; M="${3:-64}"; STEPS="${4:-32}"; TRIALS="${5:-5}"; REPS="${6:-3}"

for i in $(seq 1 "$K"); do
  "$BIN" bench "$D" "$M" "$STEPS" "$TRIALS" "$REPS" "$REC/session_${i}.json" >/dev/null
  "$BIN" noise "$D" "$M" "$STEPS" "$TRIALS" "$REPS" "$REC/noise_${i}.json"  >/dev/null
done
echo "SESSIONS_DONE=$K d=$D m=$M steps=$STEPS trials=$TRIALS reps=$REPS"
