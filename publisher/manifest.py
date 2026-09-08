#!/usr/bin/env python3
"""Canonical deterministic JSON manifest/hash helper for PCSS."""
import hashlib
import json
import sys
from pathlib import Path


def canonical_bytes(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha256(obj: dict) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: manifest.py MANIFEST.json", file=sys.stderr)
        return 2
    obj = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(sha256(obj))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
