#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-lean4}"
MODE="${2:-core}"
ROOT_ABS="$(cd "$ROOT" && pwd)"

if [[ ! -d "$ROOT_ABS" ]]; then
  echo "ERROR: Lean root not found: $ROOT" >&2
  exit 1
fi

if [[ "$MODE" == "core" && -f "$ROOT_ABS/lean-toolchain" && -x "$(command -v elan || true)" ]]; then
  TOOLCHAIN="$(tr -d '\r\n' < "$ROOT_ABS/lean-toolchain")"
  if [[ -z "$TOOLCHAIN" ]]; then
    echo "ERROR: empty Lean toolchain declaration: $ROOT_ABS/lean-toolchain" >&2
    exit 1
  fi
  elan default "$TOOLCHAIN"
fi

TMPDIR_VERIFIER="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_VERIFIER"' EXIT

scan_file() {
  local file="$1" out="$2"
  sed -E '/^[[:space:]]*--/d; s/--.*$//g' "$file" \
    | perl -0pe 's/\/\-.*?\-\// /gs' > "$out"
  if grep -nE '\b(sorry|admit|by\?)\b' "$out" >/dev/null; then
    echo "ERROR: executable unfinished proof marker detected in $file" >&2
    exit 1
  fi
}

if [[ "$MODE" == "core" ]]; then
  FIND_ROOT="$ROOT_ABS"
  mapfile -d '' files < <(find "$FIND_ROOT" -type f -name '*.lean' ! -path '*/Mathlib/*' ! -name 'lakefile.lean' -print0 | sort -z)
elif [[ "$MODE" == "mathlib" ]]; then
  MROOT="$ROOT_ABS/Mathlib"
  [[ -d "$MROOT" ]] || { echo "ERROR: Mathlib lane root not found: $MROOT" >&2; exit 1; }
  mapfile -d '' files < <(find "$MROOT" -type f -name '*.lean' ! -name 'lakefile.lean' -print0 | sort -z)
else
  echo "ERROR: unknown mode '$MODE' (expected core or mathlib)" >&2
  exit 1
fi

[[ "${#files[@]}" -gt 0 ]] || { echo "ERROR: no Lean4 sources selected for mode=$MODE" >&2; exit 1; }

for file in "${files[@]}"; do
  rel="${file#${ROOT_ABS}/}"
  out="$TMPDIR_VERIFIER/${rel//\//__}.txt"
  scan_file "$file" "$out"
  if [[ "$MODE" == "core" ]] && grep -nE '^import[[:space:]]+Mathlib([.]|[[:space:]]|$)' "$out" >/dev/null; then
    echo "ERROR: Mathlib import detected in core lane: $file" >&2
    exit 1
  fi
done

find "$ROOT_ABS" -type f \( -name '*.olean' -o -name '*.ilean' \) -delete

if [[ "$MODE" == "core" && -f "$ROOT_ABS/lakefile.lean" ]] && grep -q 'lean_lib' "$ROOT_ABS/lakefile.lean"; then
  echo "=== Lean4 package build: $(basename "$ROOT_ABS") ==="
  (cd "$ROOT_ABS" && lake build)
fi

pass=0
pending=("${files[@]}")
total=${#pending[@]}
while [[ "${#pending[@]}" -gt 0 ]]; do
  pass=$((pass + 1)); next=(); progress=0
  echo "=== Lean4 $MODE verification pass $pass: ${#pending[@]} pending ==="
  for file in "${pending[@]}"; do
    if [[ "$MODE" == "mathlib" ]]; then
      rel="${file#${MROOT}/}"
      echo "--- lake env lean $rel"
      if (cd "$MROOT" && lake env lean "$rel"); then progress=$((progress + 1)); else next+=("$file"); fi
    elif [[ -f "$ROOT_ABS/lakefile.lean" ]] && grep -q 'lean_lib' "$ROOT_ABS/lakefile.lean"; then
      rel="${file#${ROOT_ABS}/}"
      echo "--- lake env lean $rel"
      if (cd "$ROOT_ABS" && lake env lean "$rel"); then progress=$((progress + 1)); else next+=("$file"); fi
    else
      rel="${file#${ROOT_ABS}/}"
      dir="$(dirname "$file")"
      echo "--- lean --root $dir $rel"
      if (cd "$dir" && lean --root="$dir" "$(basename "$file")"); then progress=$((progress + 1)); else next+=("$file"); fi
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
