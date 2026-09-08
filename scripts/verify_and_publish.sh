#!/usr/bin/env bash
set -euo pipefail

CERTIFICATE="${1:-evidence/certificate.json}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python3 "$ROOT/publisher/gate.py" "$ROOT/$CERTIFICATE"

if [[ "${PCSS_SKIP_LEAN:-0}" != "1" ]]; then
  if command -v lake >/dev/null 2>&1 && [[ -f "$ROOT/lean4/lakefile.lean" ]]; then
    (cd "$ROOT/lean4" && lake build)
  else
    echo "LEAN_GATE_UNAVAILABLE: Lean workspace must be configured before verified publication" >&2
    exit 1
  fi
fi

echo "PCSS VERIFIED PIPELINE: artifact is eligible for repository publication"
