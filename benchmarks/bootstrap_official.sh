#!/usr/bin/env bash
set -euo pipefail

# Gold-standard benchmark bootstrap for the Speedup/PCSS repository.
# Public repositories are pinned through explicit variables so each campaign
# can record exactly what was tested. Licensed/proprietary suites are NOT
# redistributed; the script detects local installations instead.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXT="$ROOT/benchmarks/external"
mkdir -p "$EXT"

HPL_REF="${HPL_REF:-master}"
MLPERF_REF="${MLPERF_REF:-master}"

clone_or_update() {
  local url="$1" dir="$2" ref="$3"
  if [[ -d "$dir/.git" ]]; then
    git -C "$dir" fetch --tags --prune origin
    git -C "$dir" checkout "$ref"
    git -C "$dir" pull --ff-only origin "$ref" || true
  else
    git clone "$url" "$dir"
    git -C "$dir" checkout "$ref"
  fi
  git -C "$dir" rev-parse HEAD
}

echo "== Public official/reference suites =="
echo "HPL"
hpl_sha=$(clone_or_update https://github.com/icl-utk-edu/hpl.git "$EXT/hpl" "$HPL_REF")
echo "HPL_SHA=$hpl_sha"

echo "MLPerf Inference reference implementation"
mlperf_sha=$(clone_or_update https://github.com/mlcommons/inference.git "$EXT/mlperf-inference" "$MLPERF_REF")
echo "MLPERF_INFERENCE_SHA=$mlperf_sha"

echo

echo "== Licensed/vendor suites: local installation checks =="

if command -v runcpu >/dev/null 2>&1; then
  echo "SPEC_CPU=FOUND"
  runcpu --version || true
else
  echo "SPEC_CPU=NOT_FOUND"
  echo "Obtain SPEC CPU 2026 from SPEC under its license, then expose runcpu in PATH."
fi

if [[ -n "${CUDA_HOME:-}" && -d "$CUDA_HOME" ]]; then
  echo "CUDA_HOME=$CUDA_HOME"
else
  echo "CUDA_HOME=NOT_SET"
  echo "Install the official NVIDIA CUDA Toolkit/HPC SDK on a supported NVIDIA system before the cuBLAS campaign."
fi

if command -v nvcc >/dev/null 2>&1; then
  echo "NVCC=$(command -v nvcc)"
  nvcc --version || true
fi

cat <<EOF

Bootstrap complete.

Next step: run one benchmark family at a time through the corresponding
campaign adapter. Do not mix benchmark families in a single timing claim.
Record all source SHAs and local vendor versions in the PCSS scenario manifest.
EOF
