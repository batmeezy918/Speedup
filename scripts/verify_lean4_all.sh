#!/usr/bin/env bash
set -euo pipefail

# Repository-wide Lean4 verifier.
# No Mathlib/Lake dependency is required for source verification.
# Lean files may live in any directory under lean4/ and may import siblings.

ROOT="${1:-lean4}"
if [[ ! -d "$ROOT" ]]; then
  echo "ERROR: Lean root not found: $ROOT" >&2
  exit 1
fi

if grep -RIn --include='*.lean' -E '^[[:space:]]*import[[:space:]]+Mathlib([.]|[[:space:]]|$)' "$ROOT"; then
  echo "ERROR: Mathlib import detected." >&2
  exit 1
fi

if grep -RIn --include='*.lean' -E '\b(sorry|admit|by\?)\b' "$ROOT"; then
  echo "ERROR: unfinished proof marker detected." >&2
  exit 1
fi

mapfile -d '' pending < <(find "$ROOT" -type f -name '*.lean' -print0 | sort -z)
if [[ "${#pending[@]}" -eq 0 ]]; then
  echo "ERROR: no Lean4 source files found under $ROOT" >&2
  exit 1
fi

# Remove stale generated objects so this run proves the checked-out sources.
find "$ROOT" -type f \( -name '*.olean' -o -name '*.ilean' \) -delete

pass=0
while [[ "${#pending[@]}" -gt 0 ]]; do
  pass=$((pass + 1))
  echo "=== Lean4 verification pass $pass: ${#pending[@]} file(s) pending ==="
  next=()
  progress=0

  for file in "${pending[@]}"; do
    echo "--- lean -I $ROOT $file"
    if lean -I "$ROOT" "$file"; then
      progress=$((progress + 1))
    else
      next+=("$file")
    fi
  done

  if [[ "${#next[@]}" -eq 0 ]]; then
    echo "LEAN4_ALL_PASS=1"
    echo "LEAN4_SOURCE_COUNT=${#pending[@]}"
    exit 0
  fi

  if [[ "$progress" -eq 0 ]]; then
    echo "LEAN4_ALL_PASS=0"
    echo "ERROR: no progress in dependency-resolution pass." >&2
    printf 'Unresolved/failed source: %s\n' "${next[@]}" >&2
    exit 1
  fi

  pending=("${next[@]}")
  if [[ "$pass" -ge 100 ]]; then
    echo "ERROR: exceeded dependency-resolution pass limit." >&2
    exit 1
  fi
done
