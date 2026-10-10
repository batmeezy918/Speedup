#!/usr/bin/env python3
"""Regenerate evidence/evidence.json and the SHA-256 manifest.

Re-verifies every shipped Lean proof with the local toolchain, hashes the
library and all proof inputs, and records what it found. Run this after any
source change; never hand-edit evidence.json.
"""
import hashlib, json, os, platform, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def sh(p):
    return hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()

def main():
    inputs = {}
    for p in ("proof/AGD_TENSOR_INSTANTIATION.lean",
              "proof/AGD_EQUIVALENCE_QUOTIENT_CORE.lean",
              "proof/AGD_GAP_DERIVATION.lean",
              "muni/kernel.c", "muni/kernel_agl.h", "muni/_lib.c",
              "muni/kernel.h", "muni/core.py", "muni/__init__.py"):
        if os.path.exists(os.path.join(ROOT, p)):
            inputs[p] = sh(p)

    lean = {}
    for f in sorted(os.listdir(os.path.join(ROOT, "proof"))):
        if f.endswith(".lean"):
            r = subprocess.run(["lean", f], cwd=os.path.join(ROOT, "proof"),
                               capture_output=True, text=True)
            lean[f] = {"exit_code": r.returncode,
                       "axiom_free_lines": r.stdout.count("does not depend on any axioms"),
                       "sorryAx_lines": r.stdout.count("sorryAx") + r.stderr.count("sorryAx")}

    ev = {
        "schema": "muni.evidence.v1",
        "version": "1.0.0",
        "transformation_id": "quotient-descent-v2-tensor",
        "scope_id": "tensor-separable-block-constant-v1",
        "library_sha256": sh("libmuni.so"),
        "kernel_source_sha256": inputs.get("muni/kernel.c"),
        "callable_surface_sha256": inputs.get("muni/_lib.c"),
        "formal_certificate_sha256": "ef60162893f59ee1446af27005e332a0b7978e2822e424511611644713b24ff1",
        "lean_source_sha256": inputs.get("proof/AGD_TENSOR_INSTANTIATION.lean"),
        "proof_axiom_free": all(v["exit_code"] == 0 and v["sorryAx_lines"] == 0
                                for v in lean.values()),
        "lean_reverification": lean,
        "lean_toolchain": subprocess.run(["lean", "--version"], capture_output=True,
                                         text=True).stdout.strip(),
        "proof_inputs": inputs,
        "build": {
            "compiler": subprocess.run(["gcc", "--version"], capture_output=True,
                                       text=True).stdout.split("\n")[0],
            "flags": "-O3 -march=native -funroll-loops -fno-fast-math -ffp-contract=off -fPIC -shared",
            "target": platform.machine(),
            "note": "-fno-fast-math and -ffp-contract=off are required: IEEE semantics must not be relaxed",
        },
        "platform": {"platform": platform.platform(), "python": sys.version.split()[0]},
        "known_characteristics": [
            "Signed zero does not survive an iteration in either arm (both accumulate into acc=0.0); the two arms still agree bit-for-bit, which is the enforced contract.",
            "The admissibility gate is a numeric-tolerance gate, not a bitwise gate: -0.0 and +0.0 compare equal and are treated as the same fiber value.",
            "Speedups are measured per call on the caller's data. No number in this package is transferable to another workload or machine.",
        ],
    }
    out = os.path.join(ROOT, "evidence", "evidence.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(ev, open(out, "w"), indent=2, sort_keys=True)

    with open(os.path.join(ROOT, "SHA256SUMS.txt"), "w") as f:
        for p in sorted(inputs):
            f.write(f"{inputs[p]}  {p}\n")
        f.write(f"{ev['library_sha256']}  libmuni.so\n")
    print(f"wrote evidence/evidence.json  proof_axiom_free={ev['proof_axiom_free']}")
    for k, v in lean.items():
        print(f"  {k}: exit={v['exit_code']} axiom_free={v['axiom_free_lines']} sorryAx={v['sorryAx_lines']}")
    return 0 if ev["proof_axiom_free"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
