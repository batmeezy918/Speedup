#!/usr/bin/env python3
"""Build a certificate skeleton. Does not mark unpublished gates true."""
import json
import sys

SKELETON = {
    "run_id": "REPLACE_ME",
    "gates": {
        "integrity": False,
        "reproducibility": False,
        "quotient_forward": False,
        "reconstruction_reverse": False,
        "invariants": False,
        "performance": False,
        "lean": False,
    },
}

if __name__ == "__main__":
    json.dump(SKELETON, sys.stdout, indent=2)
    sys.stdout.write("\n")
