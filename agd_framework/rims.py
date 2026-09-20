import json, hashlib, time
from pathlib import Path
from typing import Dict, List, Optional
from agd_framework.utils import *
from agd_framework.canonical import CanonicalState
from agd_framework.omega import OmegaObservable
from agd_framework.quotient import Phase3Quotient
from agd_framework.decision import Phase4Decision
from agd_framework.factorization import Phase6Factorization
from agd_framework.false_merge import Phase5FalseMerge

class Phase16RIMS:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.receipt: Dict = {}
        self.sha256_sums: List[str] = []

    def generate_receipt(self, run_id: str,
                           baseline_artifact_hash: str,
                           agd_artifact_hash: str,
                           adversarial_hash: str,
                           factorization_hash: str,
                           timing_hash: str,
                           stdout_hash: str,
                           stderr_hash: str,
                           git_sha: str,
                           benchmark_sha: str,
                           model_identity: str,
                           model_hash: str,
                           environment_fingerprint: str,
                           dataset_hashes: List[str],
                           omega_version: str,
                           quotient_algo_version: str) -> Dict:
        self.receipt = {
            "RUN_ID": run_id,
            "timestamp": now_iso(),
            "git_SHA": git_sha,
            "benchmark_SHA": benchmark_sha,
            "model_identity": model_identity,
            "model_hash": model_hash,
            "environment_fingerprint": environment_fingerprint,
            "dataset_hashes": dataset_hashes,
            "Omega_version": omega_version,
            "quotient_algorithm_version": quotient_algo_version,
            "baseline_artifact_hash": baseline_artifact_hash,
            "AGD_artifact_hash": agd_artifact_hash,
            "adversarial_artifact_hash": adversarial_hash,
            "factorization_artifact_hash": factorization_hash,
            "timing_artifact_hash": timing_hash,
            "stdout_hash": stdout_hash,
            "stderr_hash": stderr_hash,
        }
        return self.receipt

    def generate_sha256sums(self, paths: List[Path]) -> List[str]:
        sums = []
        for p in sorted(paths):
            if p.exists():
                h = sha256_file(p)
                sums.append(f"{h}  {p}")
        self.sha256_sums = sums
        return sums

    def write_receipts(self, receipt_dir: Path):
        receipt_dir.mkdir(parents=True, exist_ok=True)

        if self.receipt:
            rpath = receipt_dir / "RIMS_RECEIPT.json"
            rpath.write_text(json.dumps(self.receipt, indent=2))

        md_lines = ["# RIMS Receipt", ""]
        for k, v in self.receipt.items():
            md_lines.append(f"## {k}")
            if isinstance(v, list):
                for item in v:
                    md_lines.append(f"- {item}")
            else:
                md_lines.append(str(v))
            md_lines.append("")
        (receipt_dir / "RIMS_RECEIPT.md").write_text("\n".join(md_lines))

        if self.sha256_sums:
            (receipt_dir / "SHA256SUMS.txt").write_text(
                "\n".join(self.sha256_sums)
            )
