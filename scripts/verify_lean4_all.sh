#!/usr/bin/env bash
# PCSS canonical Lean4 verifier.
#
#   verify_lean4_all.sh [LEAN_ROOT] [core|mathlib] [--hash-out FILE] [--hash-in FILE]
#
# Discovers every Lean source under LEAN_ROOT, rejects forbidden proof holes
# (sorry/admit/by?), rejects Mathlib imports in 'core' lanes, respects the
# repository lean-toolchain, resolves dependency ordering, compiles every
# source, fails if any source cannot be compiled, reports the exact failing
# source, and emits a source hash manifest.
#
# Exit codes:
#   0  every selected source compiled, hashes emitted
#   1  any source failed, hole/mathlib marker detected, or no source selected
#   2  usage error
set -euo pipefail

ROOT_ABS="$(pwd)"
MODE="core"
HASH_OUT=""

# ---- argument parsing -------------------------------------------------------
POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --hash-out)
      HASH_OUT="$2"
      shift 2
      ;;
    --hash-in)
      # accepted for future reuse; hash verification is reported separately
      shift 2
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [[ -n "${POSITIONAL[0]:-}" ]]; then
  ROOT_ABS="$(cd "${POSITIONAL[0]}" && pwd)"
fi
if [[ -n "${POSITIONAL[1]:-}" ]]; then
  MODE="${POSITIONAL[1]}"
fi

if [[ ! -d "$ROOT_ABS" ]]; then
  echo "ERROR: Lean root not found: ${POSITIONAL[0]:-lean4}" >&2
  exit 1
fi

# ---- toolchain discipline ----------------------------------------------------
# The package build can resolve the toolchain from lean-toolchain even when
# elan has no global default. Direct `lean` invocations do not. Pin the
# verifier to the repository-declared toolchain so every source is checked
# with the same compiler as `lake build`.
export PATH="$HOME/.elan/bin:$PATH"
if [[ -f "$ROOT_ABS/lean-toolchain" && -x "$(command -v elan)" ]]; then
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
  local file="$1"
  local out="$2"
  sed -E '/^[[:space:]]*--/d; s/--.*$//g' "$file" \
    | perl -0pe 's/\/\-.*?\-\// /gs' > "$out"

  if grep -nE '\b(sorry|admit|by\?)\b' "$out" >/dev/null; then
    echo "ERROR: executable unfinished proof marker detected in $file" >&2
    grep -nE '\b(sorry|admit|by\?)\b' "$out" >&2 || true
    exit 1
  fi
}

if [[ "$MODE" == "core" ]]; then
  FIND_ROOT="$ROOT_ABS"
  mapfile -d '' files < <(
    find "$FIND_ROOT" -type f -name '*.lean' \
      ! -path '*/Mathlib/*' \
      ! -name 'lakefile.lean' \
      -print0 | sort -z
  )
  for file in "${files[@]}"; do
    rel="${file#${ROOT_ABS}/}"
    out="$TMPDIR_VERIFIER/${rel//\//__}.txt"
    scan_file "$file" "$out"
    if grep -nE '^import[[:space:]]+Mathlib([.]|[[:space:]]|$)' "$out" >/dev/null; then
      echo "ERROR: Mathlib import detected in core lane: $file" >&2
      exit 1
    fi
    if grep -nE '^[[:space:]]*(axiom|opaque)[[:space:]]+' "$out" >/dev/null; then
      echo "ERROR: axiom/opaque declaration detected in core lane: $file" >&2
      exit 1
    fi
  done
elif [[ "$MODE" == "mathlib" ]]; then
  MROOT="$ROOT_ABS/Mathlib"
  if [[ ! -d "$MROOT" ]]; then
    echo "ERROR: Mathlib lane root not found: $MROOT" >&2
    exit 1
  fi
  mapfile -d '' files < <(find "$MROOT" -type f -name '*.lean' ! -name 'lakefile.lean' -print0 | sort -z)
  for file in "${files[@]}"; do
    rel="${file#${MROOT}/}"
    out="$TMPDIR_VERIFIER/${rel//\//__}.txt"
    scan_file "$file" "$out"
  done
else
  echo "ERROR: unknown mode '$MODE' (expected core or mathlib)" >&2
  exit 1
fi

if [[ "${#files[@]}" -eq 0 ]]; then
  echo "ERROR: no Lean4 sources selected for mode=$MODE" >&2
  exit 1
fi

# ---- source hash manifest ----------------------------------------------------
if [[ -n "$HASH_OUT" ]]; then
  mkdir -p "$(dirname "$HASH_OUT")"
  : > "$HASH_OUT"
  for file in "${files[@]}"; do
    rel="${file#${ROOT_ABS}/}"
    printf '%s  %s\n' "$(sha256sum "$file" | cut -d' ' -f1)" "$rel" >> "$HASH_OUT"
  done
  echo "LEAN4_${MODE^^}_SOURCE_HASHES=$HASH_OUT"
fi

# ---- dependency-order-independent compile -------------------------------------
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
      rel="${file#${ROOT_ABS}/}"
      olean="${rel%.lean}.olean"
      mkdir -p "$(dirname "$ROOT_ABS/$olean")"
      echo "--- lean --root $ROOT_ABS -o $olean $file"
      if LEAN_PATH="$ROOT_ABS${LEAN_PATH:+:$LEAN_PATH}" lean --root="$ROOT_ABS" -o "$ROOT_ABS/$olean" "$file"; then
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