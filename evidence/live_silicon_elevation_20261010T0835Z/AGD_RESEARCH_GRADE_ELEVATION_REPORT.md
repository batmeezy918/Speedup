# AGD / MUNI / SIM2XR — Research-Grade Elevation Receipt

**Run ID:** live_silicon_elevation_20261010T0835Z  
**Execution date:** 2026-10-10 UTC  
**Target:** Moto G Power 5G (2024), Android 16, AArch64, Debian PRoot  
**Execution channel:** live Desktop Commander / RDC  
**Repository:** /root/Speedup  
**Repository revision at start:** a69eb477ea8eff1de7ee9574b54579c8809102e2  
**Scope:** invariant-state quotient descent for a tensor-separable operator; exactness, fallback, formal instantiation, applicability and novelty boundary.

## Executive result

The final v4 native build was measured on the phone with CPU affinity pinned to cores 4–7, using 7 trials x 5 repetitions at d=4096, r=64, m=64, 256 steps. Run-loop speedup was 69.013x; end-to-end speedup was 67.387x after including allocation, certificate/admissibility gate, plan creation, run, reconstruction, and cleanup. End-to-end median per-call times: full path 68.325552 ms; quotient path 1.013927 ms; max absolute error 0. The 95% bootstrap interval for the median paired E2E speedup across seven trial clusters was [66.641x, 67.852x]. The final adversarial suite passed 23/23 cases. On deliberately inadmissible input, the quotient was rejected and the original path used; E2E ratio of medians was 1.002x, with a paired-trial bootstrap interval spanning 1.0, so no fallback speedup is claimed. Other device processes were active, so this is real silicon evidence with affinity control, not a fully isolated laboratory benchmark.

A new Lean 4 core-lane theorem, AGDTensorSeparableInstantiation.lean, was added to the Lake roots and compiled in the full 44-source core-lane verification: LEAN4_CORE_ALL_PASS=1, LEAN4_CORE_SOURCE_COUNT=44. It proves exact reconstruction for all iterates of the tensor-separable/fiberwise operator on the block-constant sector. Its #print axioms output is [propext, Quot.sound]; the new file declares no axiom, opaque, sorry, admit, or native_decide. This is a proof of the exact algebraic model, not a formal refinement proof of the C/IEEE-754 binary. The wider repository is not axiom-free: the existing HPL_AGD_01 proof receipts include Classical.choice and a generated native_decide axiom; those are pre-existing, unrelated dependencies that must remain explicitly accounted for.

## Fresh silicon witness — final v4

- Device: TMRV08P5G, Android 16, AArch64, Debian PRoot kernel 6.17.0-PRoot-Distro; RDC connection was live for the run.
- Final native benchmark binary: evidence/live_silicon_elevation_20261010T0835Z/muni_v4_samples.
- Final adversarial binary: evidence/live_silicon_elevation_20261010T0835Z/agd_adversarial_v4_samples.
- Native binary SHA-256: 0e655a4ea40136b7d79f0eabfd773358778fd4bfa90796d160f468f943de315e.
- Adversarial binary SHA-256: 8f1abf4b2a9e67cc2c739553dd0f64734aa111d8ff9de929d3a18f73257056a5.
- Proof source SHA-256: eea5e18530087b654307429514e43b76274bf201fa356be1980aef2f0413d01e.
- Source manifest SHA-256 compiled into the binary: 39f50f330db8b6c020a21a6a86a3d99ea1683206f481bc79e81bd58d4f41162a.
- Workload: d=4096, r=64, m=64, steps=256; 7 trial clusters x 5 repetitions; CPU affinity pinned to cores 4–7. E2E arm order alternates across repetitions. Raw per-trial means are preserved in JSON.
- Run-loop-only median per call: full=68.475875 ms; quotient=0.992219 ms; 69.012892x. This excludes plan creation, certificate/admissibility gate, and reconstruction.
- End-to-end median per call: full path=68.325552 ms; quotient path=1.013927 ms; 67.387039x. This includes full-path allocations/copy/steps/cleanup versus quotient plan creation/gate/run/reconstruction/cleanup. max_abs_error=0.
- Deliberately inadmissible input: full path=68.649937 ms; guarded fallback=68.515438 ms; ratio of medians=1.001963x; max_abs_error=0; claim class=QUARANTINED_OPTIMISATION_NOT_APPLIED. The median paired-trial ratio is 1.000440x (95% bootstrap interval [0.999187x, 1.001963x]); no fallback speedup is claimed.
- Final adversarial result: ADVERSARIAL_SUITE=PASS passed=23 failed=0. New cases specifically verify that an unknown certificate state, mismatched semantic identity, a claimed CERTIFIED state without native binding, and a CERTIFIED state with a mismatched semantic identity all force fallback.
- Timing caveat: other device processes were active. CPU affinity was controlled, and E2E arm order was alternated, but the device was not isolated from all background work. Treat this as a real on-device witness, not a laboratory-grade confidence interval.
- The earlier v2 run's 65.437x number was run-loop-only and its milliseconds aggregated repetitions; it must not be described as end-to-end. The v3 run was an E2E measurement without raw trial samples. The v4 receipts are the final E2E witness with per-trial sample arrays and an exploratory bootstrap analysis.
- Receipts: muni_v4_admissible.txt/.json, muni_v4_inadmissible.txt/.json, adversarial_v4_samples.txt, benchmark_environment_v4.txt, timing_statistics.md, lean_core_verification.log, lean_core_hashes.sha256, source_manifest.sha256, source_manifest.digest.

## Engineering and provenance changes completed

1. Added AGDTensorSeparableInstantiation.lean to the Lake roots and full core verification.
2. Updated the native certificate to bind the algebraic model to the exact Lean proof-source hash; it explicitly says the C floating-point/compiler refinement is not kernel-proved.
3. Added a SHA-256 source manifest covering the Lean core, new instantiation, Lake roots, MUNI source, certificate source/header, and adversarial source. The manifest digest is emitted in the native text and JSON receipt.
4. Tightened the certificate gate: unknown states and unrecognized semantic identities fail closed. A CERTIFIED state cannot authorize the fast path unless the native-binding gate is exactly CERTIFIED_NATIVE_BINDING.
5. Tightened claim classification: MEASURED_LOCAL_NATIVE is emitted only for a fully CERTIFIED certificate with native binding. Current result remains FORMAL_PARTIAL_MEASURED_LOCAL.
6. Removed the hard-coded “19/19 adversarial pass” claim from the benchmark process; the benchmark now correctly says the suite is not run in-process and points to a separate receipt.
7. Added end-to-end timing that includes baseline allocations/copy/steps/cleanup and quotient plan creation/gate/run/reconstruction/cleanup. The harness reports run-loop-only and end-to-end numbers separately and alternates E2E arm order.
8. The benchmark now exits nonzero if exactness fails and rejects trials=0. The adversarial suite was expanded from 19 to 23 cases to test unknown states, stale semantic identity, and false claims of native certification.

## Concrete mathematical statement

Let the full state be x : Fin r -> Fin m -> Rat. Each of the m fibers has r coordinates. Let U : (Fin r -> Rat) -> Fin r -> Rat be any reduced-state update and define:

T(x)(i,j) = U (fun k => x(k,j)) (i)

Let lift(q)(i,j)=q(i), and project a full state to a representative fiber j0 by project(x)(i)=x(i,j0). The admissible sector is:

BlockConstant(x) := forall i j k, x(i,j)=x(i,k).

The Lean witness proves:
1. lift(project(x)) = x whenever BlockConstant(x).
2. T(lift(q)) = lift(U(q)).
3. BlockConstant(x) implies BlockConstant(T(x)).
4. For every natural n, lift(U^[n](project(x))) = T^[n](x) for every block-constant initial x.

This is exact algebraic equality, not a tolerance bound, for the mathematical model. It applies to arbitrary U as a function on the reduced state, including suitable repeated-fiber updates. It does not, by itself, prove that the C floating-point implementation is identical to this abstract model or that all applications satisfy the sector assumptions.

## Application transfer matrix — do not conflate theorem scope with benchmark scope

| Domain | Mathematical fit | What is actually demonstrated here | Next domain-specific gate |
|---|---|---|---|
| AI inference | A layer/update can fit if the same operator is applied independently across replicated fibers and the activation/update preserves that structure. | Generic operator theorem and a native linear operator witness only. No real neural model, token workload, accuracy evaluation, or end-to-end inference benchmark ran in this receipt. | Adapt a named model/layer; prove graph-level structure and activation closure; compare exact logits/output and latency against the same reference model. |
| Scientific simulation | Repeated state evolution fits if the discretized operator preserves the block-constant sector. | 256-step repeated operator evolution with exact output agreement. | Integrate a named physical discretization (not just a synthetic operator); validate conservation/stability invariants and reference trajectories. |
| Mobile computing | Fewer arithmetic operations and less repeated state traffic can reduce runtime and may reduce energy. | Fresh AArch64 phone execution and measured elapsed-time reduction. Energy was not measured. | Collect repeated cold/warm trials, thermal/frequency telemetry, CPU cycles, memory traffic, and energy if instrumentation permits. |
| Real-time systems | A gated fast path can help if both path semantics and execution-time bounds are established. | Empirical latency and fallback behavior only. No hard deadline or worst-case execution-time proof. Android scheduler/governor and interference are not controlled by this run. | Define deadline and criticality, bound gate + fast path + fallback, analyze WCET/interference, and test deadline misses under load. |
| Numerical solvers | An iterative solver fits only if its update map and initialization preserve the quotient sector and the reduced residual/solution map is equivalent. | Generic repeated operator, not CG/GMRES/Jacobi or a named solver. | Use a named solver; prove residual/solution equivalence and convergence assumptions; compare residual histories, stopping decisions, and solution error. |

## Novelty separation and prior-art boundary

The quotient construction, invariant-subspace reduction, abstract interpretation, and exact reconstruction principle are established mathematics. Neural-network compression via lumpability/formal methods and tensor-program optimization with equivalence/correction also exist. Runtime monitors, adaptive shielding, and fallback policies are also established engineering concepts.

Relevant prior art:
- “The quotient of an abstract interpretation” (Theoretical Computer Science, 1998), DOI 10.1016/S0304-3975(97)00137-0.
- PET: “Optimizing Tensor Programs with Partially Equivalent Transformations and Automated Corrections,” OSDI 2021; it discovers transformations and corrects outputs to restore equivalence.
- “Compressing neural networks via formal methods,” Neural Networks 178 (2024), article 106411; connects neural-network reduction with formal methods/lumpability and exact behavior preservation.
- “Abstraction and Refinement: Towards Scalable and Exact Verification of Neural Networks,” ACM TOSEM 33(5), 2024; established abstraction/refinement for exact NN verification.
- “Adaptive Shielding via Parametric Safety Proofs,” PACMPL (2025); prior work on runtime monitoring, safety proofs, and fallback behavior.
- Reduced-order modeling / invariant subspace methods are established in scientific computing, including projection-based ROMs and exact operator-inference work.

Therefore do NOT claim novelty for quotient math, invariant sectors, exact reconstruction, or formal optimization in general. The plausible contribution to test is the specific operational combination: an operator-bound certificate, explicit admissibility gate, in-object fallback, exact reconstruction witness, native ARM64 measurement, and provenance/claim-class policy. This remains a candidate systems contribution, not a verified first-in-field result; the current implementation still declares the invariant per family rather than deriving it automatically.

## Operational gaps that remain open

1. Concrete Lean instantiation must be connected to the exact C operator, build flags, and certificate identity; the new Lean theorem is an algebraic model witness, not a proof of compiler output.
2. Full core-lane verification completed successfully: LEAN4_CORE_ALL_PASS=1 across 44 Lean sources. Existing unused-variable/simp warnings remain; the broader axiom audit also reports dependencies in unrelated existing proofs, so the repository as a whole is not claimed axiom-free.
3. Automatic gap discovery for arbitrary source/IR is not implemented.
4. No end-to-end real transformer, PDE/HPCG workload, named numerical solver, or certified real-time deadline workload is included in this run.
5. Raw per-trial means and exploratory bootstrap intervals are now recorded. Remaining timing work: independent repeat sessions, cold/warm separation, thermal telemetry, broader device/workload replication, and stronger isolation from background processes.
6. Device storage reported 100% utilization with about 2.0 GB available. Avoid large builds/artifacts until space is recovered.
7. Prior experiments documented that a claimed universal speedup <= quotient factor bound was refuted, and an earlier baseline mismatch was quarantined. Do not revive those claims.

## Research conclusion

The strongest current evidence is a fresh, affinity-pinned on-device benchmark with 7 trial clusters and 5 repetitions each: the structured workload has a 64:1 arithmetic reduction, the full-call end-to-end median speedup was 67.387x at 256 steps, output error was zero, and the inadmissible path fell back at approximately 1.00x. The paired-trial bootstrap interval for admissible E2E speedup was [66.641x, 67.852x]; the fallback interval included 1.0. The final adversarial suite passed 23/23, including certificate-state and semantic-identity refusal cases. The new Lean theorem proves exact reconstruction for every iterate in the algebraic tensor-separable model, and the 44-source core lane passes. The native certificate remains FORMAL_PARTIAL because compiler/IEEE-754 refinement is not machine-proved. Next: repeat independent runs under lower background load; then instantiate named AI, scientific, and solver workloads and analyze real-time bounds before making domain-level claims.
