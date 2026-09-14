# Gold-Standard Competitive Benchmark Matrix

Purpose: make the Speedup repository capable of testing the closed AGD/PCSS transformation stack against the official benchmark suites used by leading systems in each target field.

## Rule

We do **not** claim SOTA from a local benchmark. A competitive claim requires:

1. the official benchmark implementation/rules;
2. the official workload/data/model;
3. the official metric;
4. the official validity/compliance procedure;
5. a same-hardware baseline where permitted;
6. AGD/PCSS execution under the same declared workload;
7. semantic/quality validation;
8. reproducible artifacts and hashes;
9. comparison against the published official result set.

The governing PCSS publication condition remains:

`PUBLISH := I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L`

## Matrix

| Field | Gold-standard target | Official source | What Speedup should compete on |
|---|---|---|---|
| HPC dense linear algebra | TOP500 / HPL | https://www.top500.org/project/linpack/ | HPL-compatible dense solve performance where AGD semantics permit a valid transformation |
| CPU general compute | SPEC CPU 2026 | https://www.spec.org/cpu2026/ | SPECspeed / SPECrate workloads, subject to SPEC licensing and reporting rules |
| GPU/HPC BLAS | NVIDIA cuBLAS/cuBLASLt | https://developer.nvidia.com/cublas | GEMM/BLAS throughput and end-to-end transformed workload cost on supported NVIDIA hardware |
| ML inference | MLPerf Inference | https://mlcommons.org/benchmarks/inference-datacenter/ | Official latency/throughput + quality constraints for selected models/scenarios |
| MLPerf reference implementations | MLCommons inference repository | https://github.com/mlcommons/inference | Reference-vs-AGD implementation comparison on identical benchmark definitions |
| Formal mathematics | Lean 4 / mathlib | https://lean-lang.org/ | Proof obligations: quotient descent, reconstruction, invariants, composition; never treat proof as timing evidence |

## Execution policy

Benchmark families are run **one at a time**, never as a single mixed campaign.

For every family create a self-contained certificate directory:

`benchmarks/runs/<family>/<version>/<scenario>/<run-id>/`

Required artifacts:

- official version/commit identifier
- official rules/checksum where available
- hardware fingerprint
- compiler/toolchain fingerprint
- exact command line
- baseline output
- AGD output
- correctness/quality output
- timing/throughput output
- quotient/reconstruction/invariant certificate
- raw logs
- manifest hash
- comparison against official results
- PCSS evidence state

## Licensing / distribution

Do **not** commit proprietary or licensed benchmark payloads to this repository when redistribution is prohibited.

SPEC CPU is licensed software; the repository may contain an installer/check script and provenance record, while the user obtains the suite from SPEC. CUDA/cuBLAS is distributed by NVIDIA as part of the CUDA Toolkit/HPC SDK; use the locally installed official toolkit rather than redistributing NVIDIA binaries.

Public source suites such as HPL and MLPerf reference code may be cloned at pinned commits by the bootstrap tooling.

## Competitive discipline

A result is not called "SOTA" merely because it beats a local baseline.

Use these labels:

- `OFFICIAL_REPRODUCTION`
- `SAME_HARDWARE_COMPARISON`
- `OFFICIAL_RESULT_COMPARISON`
- `COMPETITIVE_ON_BENCHMARK`
- `UNOFFICIAL_LOCAL_RESULT`
- `QUARANTINED`

"Dominance" is reserved for a benchmark-defined comparison in which the metric, workload, quality constraints, hardware class, and rules make the comparison valid.
