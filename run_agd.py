from __future__ import annotations
import os, sys, json, time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(WORKSPACE / "agd_framework"))

from agd_framework.main import AGDFramework


def main():
    start = time.time()
    fw = AGDFramework()
    results = fw.run_full_pipeline()

    elapsed = time.time() - start
    print(f"\nTotal elapsed: {elapsed:.2f}s")
    print(f"Run ID: {results['run_id']}")

    with open(WORKSPACE / "agd_framework" / "pipeline_result.json", "w") as f:
        json.dump({
            "run_id": results["run_id"],
            "elapsed_seconds": elapsed,
            "quotient_states": results["quotient"].states_count,
            "quotient_classes": results["quotient"].classes_count,
            "false_merge_violations": len(results["false_merge"].violations),
            "factorization_residual": results["factorization"].residual,
            "pcss_decision": results["pcss"]["publication_decision"],
        }, f, indent=2)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
