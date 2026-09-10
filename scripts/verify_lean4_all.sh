#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-lean4}"
MODE="${2:-core}"
ROOT_ABS="$(cd "$ROOT" && pwd)"

if [[ ! -d "$ROOT_ABS" ]]; then
  echo "ERROR: Lean root not found: $ROOT" >&2
  exit 1
fi

if grep -RIn --include='*.lean' -E '\b(sorry|admit|by\?)\b' "$ROOT_ABS"; then
  echo "ERROR: unfinished proof marker detected." >&2
  exit 1
fi

if [[ "$MODE" == "core" ]]; then
  if grep -RIn --include='*.lean' -E '^[[:space:]]*import[[:space:]]+Mathlib([.]|[[:space:]]|$)' "$ROOT_ABS"; then
    echo "ERROR: Mathlib import detected in core lane." >&2
    exit 1
  fi
  FIND_ROOT="$ROOT_ABS"
  mapfile -d '' files < <(find "$FIND_ROOT" -type f -name '*.lean' ! -path '*/Mathlib/*' -print0 | sort -z)
elif [[ "$MODE" == "mathlib" ]]; then
  MROOT="$ROOT_ABS/Mathlib"
  if [[ ! -d "$MROOT" ]]; then
    echo "ERROR: Mathlib lane root not found: $MROOT" >&2
    exit 1
  fi
  mapfile -d '' files < <(find "$MROOT" -type f -name '*.lean' -print0 | sort -z)
else
  echo "ERROR: unknown mode '$MODE' (expected core or mathlib)" >&2
  exit 1
fi

if [[ "${#files[@]}" -eq 0 ]]; then
  echo "ERROR: no Lean4 sources selected for mode=$MODE" >&2
  exit 1
fi

# Remove generated objects only from the selected lane.
find "$ROOT_ABS" -type f \( -name '*.olean' -o -name '*.ilean' \) -delete

pass=0
pending=("${files[@]}")
total=${#pending[@]}
while [[ "${#pending[@]}" -gt 0 ]]; do
  pass=$((pass + 1))
  next=()
  progress=0
  echo "=== Lean4 $MODE verification pass $pass: ${#pending[@]} pending ==="
  for file in "${pending[@]}"; do
    if [[ "$MODE" == "mathlib" ]]; then
      rel="${file#${MROOT}/}"
      echo "--- lake env lean $rel"
      if (cd "$MROOT" && lake env lean "$rel"); then
        progress=$((progress + 1))
      else
        next+=("$file")
      fi
    else
      echo "--- lean -I "$ROOT_ABS" "$file""
      if lean -I "$ROOT_ABS" "$file"; then
        progress=$((progress + 1))
      else
        next+=("$file")
      fi
    fi
  done
  if [[ "${#next[@]}" -eq 0 ]]; then
    echo "LEAN4_${MODE^^}_ALL_PASS=1"
    echo "LEAN4_${MODE^^}_SOURCE_COUNT=$total"
    exit 0
  fi
  if [[ "$progress" -eq 0 || "$pass" -ge 100 ]]; then
    echo "LEAN4_${MODE^^}_ALL_PASS=0" >&2
    printf 'Unresolved/failed source: %s\n' "${next[@]}" >&2
    exit 1
  fi
  pending=("${next[@]}")
done
