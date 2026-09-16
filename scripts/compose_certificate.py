#!/usr/bin/env python3
"""PCSS certificate composition (native evidence -> strict-gate certificate).

Reads a `pcss_native_runner.py` output directory plus a Lean verification
artifact and assembles the canonical strict-gate certificate consumed by
`publisher/strict_gate.py` (the single publication authority).

Hash policy: every gate hash is the real sha256 of the artifact file produced
for that gate. No hash is fabricated; a missing artifact keeps the gate false.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from speedup import certificate  # noqa: E402
from speedup import const  # noqa: E402
from speedup.jsonutil import sha256_file  # noqa: E402
from speedup.scenario import scenario_hash  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compose strict-gate certificate from runner output")
    ap.add_argument("--run-dir", required=True, help="pcss_native_runner output directory")
    ap.add_argument("--lean-artifact", required=False, default=None,
                    help="path to Lean verification output (LEAN4_CORE_ALL_PASS=1 file)")
    ap.add_argument("--output", required=True, help="output certificate JSON path")
    ap.add_argument("--claim-strength", default="VERIFIED",
                    help="requested claim strength (only honored if all gates actually pass)")
    args = ap.parse_args(argv)

    run_dir = pathlib.Path(args.run_dir)
    native_ev = json.loads((run_dir / "native_evidence.json").read_text(encoding="utf-8"))
    scenario_manifest = json.loads((run_dir / "scenario.json").read_text(encoding="utf-8"))

    def load(name: str) -> dict:
        return json.loads((run_dir / name).read_text(encoding="utf-8"))

    quotient_ev = load("quotient_evidence.json")
    recon_ev = load("reconstruction_evidence.json")
    inv_ev = load("invariant_evidence.json")
    perf_ev = load("performance_evidence.json")

    lean_cert = None
    lean_sha = ""
    if args.lean_artifact:
        lean_path = pathlib.Path(args.lean_artifact)
        if lean_path.is_file() and "LEAN4_CORE_ALL_PASS=1" in lean_path.read_text(encoding="utf-8", errors="replace"):
            lean_cert = {"pass": True, "artifact": lean_path.as_posix()}
            lean_sha = sha256_file(str(lean_path))

    artifact_hashes = {
        "quotient_hash": sha256_file(str(run_dir / "quotient_evidence.json")),
        "reconstruction_hash": sha256_file(str(run_dir / "reconstruction_evidence.json")),
        "invariant_hash": sha256_file(str(run_dir / "invariant_evidence.json")),
        "performance_hash": sha256_file(str(run_dir / "performance_evidence.json")),
        "lean_hash": lean_sha,
    }

    cert = certificate.assemble_certificate(
        scenario_manifest=scenario_manifest,
        native_evidence=native_ev,
        quotient_evidence=quotient_ev,
        reconstruction_evidence=recon_ev,
        invariant_evidence=inv_ev,
        performance_evidence=perf_ev,
        lean_certificate=lean_cert,
        artifact_hashes=artifact_hashes,
    )

    all_gates = all(cert["gates"].values())
    if all_gates and args.claim_strength in const.CLAIM_LATTICE:
        cert["claim_strength"] = args.claim_strength
    elif all_gates:
        cert["claim_strength"] = "VERIFIED"
    else:
        cert["claim_strength"] = "QUARANTINED"

    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cert, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    print(f"composed certificate: {out}")
    print(f"gates: {pert({k: v for k, v in cert['gates'].items()})}")
    print(f"claim_strength requested={args.claim_strength} actual={cert['claim_strength']}")
    return 0


def pert(d: dict) -> str:
    return " ".join(f"{k}={v}" for k, v in d.items())


if __name__ == "__main__":
    raise SystemExit(main())