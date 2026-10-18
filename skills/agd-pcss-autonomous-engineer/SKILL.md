# AGD-PCSS Autonomous Engineer Skill

Operational contract for any agent (human or AI) running autonomous engineering
loops against the batmeezy918/Speedup repository. Complements AGENT.md — this
file is the *execution* contract; AGENT.md remains the *evidence* contract.

Governing invariant (never relax):

    CLAIM_STRENGTH <= EVIDENCE_STRENGTH

Publication transition (Constitution Article 9):

    PUBLISH <=> I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L

Any false or unknown predicate => QUARANTINE. No silent promotion.

---

## 1. Canonical Wiring (do not rediscover)

- Repository: batmeezy918/Speedup, branch main, pinned commit SHA recorded per run.
- Canonical executor: scripts/pcss_native_runner_v2.py
  - Hashes source + input files, warmups, repeats, determinism check
    (exit_code + stdout_sha256 + stderr_sha256), median speedup, fail-closed
    non-publishable certificate.
- Sister scripts: scripts/pcss_native_runner.py (v1), scripts/evidence_to_lean.py,
  scripts/execute_quarantine_gates.py, scripts/verify_lean4_all.sh,
  scripts/verify_and_publish.sh, scripts/validate_claim_registry.py,
  scripts/test_pcss_gates.py, scripts/test_pcss_gate_matrix.py,
  scripts/qkxr_direct_comparison.py.
- Publisher: publisher/strict_gate.py (sole publication authority).
- Governor: governor/coci_governor.py, governor/formal_gap_isolator.py,
  governor/formal_gap_ledger.py, governor/recursive_speedup_ledger.py,
  governor/close_sim2xr_formal_gap.py.
- Formal gap isolator: formal_gap_isolator/gap_isolator.py.
- Evidence-to-Lean compiler: scripts/evidence_to_lean.py.
- Termux remote execution: REMOTE_TERMUX_PROTOCOL.md (handshake, timing
  separation, artifact contract, proof handoff).
- Merchant assurance benchmark: merchant_assurance_benchmark_v2.py
  (LOCAL_REFERENCE_ORACLE_ONLY; network_equivalence=UNPROVEN).
- Native C kernels: muni-production/muni/kernel.c, muni-production/ops/bench/*.
- Native C++ towers: benchmarks/qkxr_tower_native.cpp,
  benchmarks/qkxr_tower_native_v5.cpp.
- Lean specimens: lean4/AGDGemmSpeedup.lean, lean4/PCSS_NEON_N512.lean,
  muni-production/proof/*.lean.
- Evidence index: evidence/normalized/INDEX.md, evidence/ledger/*,
  verified/theorem_corpus/INDEX.json, claims/REGISTRY.json.
- CI workflows: .github/workflows/pcss-verification.yml,
  proof-gated-speedup.yml, formal-gap-governor.yml, muni-verify.yml,
  agd-cross-environment-witness.yml, and others.
- PCSS speedup template: PCSS_SPEEDUP_TEMPLATE/ (scenario, operators,
  measurement, validation, certificate, lean scaffold).

If a path is missing or moved, report it explicitly. Do NOT substitute a
guess. Do NOT silently relabel historical artifacts as current measurements.

---

## 2. Algorithmic Speed-Up Promotion Boundary

Speed-ups in this repository are ALGORITHMIC: the math holds whether a mind
or a machine computes it. Treat every candidate as an operator-level speed-up
to integrate into the PCSS gate path and CVR DAG, not merely a number to
reproduce.

### 2.1 Candidate classes

1. AGD quotient operators (projection π, reduced operator T̄, reconstruction σ).
   Formal work ratio: workRatio(fullWork 1024, quotientWork 256) = 16
   (lean4/AGDGemmSpeedup.lean, theorem canonical_workRatio). Measured wall on
   aarch64: 15.96x (measuredHundredths = 1596) — with an explicit theorem
   proving measured ≠ work_ratio×100. That separation is load-bearing.
2. NEON vector kernels (4x4 NEON FMA, FP32, N=512): scalar median
   319,142,604 ns vs NEON median 27,621,615 ns → 11.554x, 3/3 runs > 1
   (lean4/PCSS_NEON_N512.lean). NOT publishable: Q, Q⁻¹, Ω gates false.
3. SIM2XR retention: historical 16.5–17.6x across 5 repeats, hash match true,
   115,000 of 121,920 steps skipped (evidence/optimizer/HISTORICAL_RESULTS.md).
   HISTORICAL_ARTIFACT only until independently rerun.
4. MUNI C kernels: muni-production/muni/kernel.c + ops/bench (msweep,
   ops_bench) with Lean correspondence proofs
   (AGD_C_KERNEL_CORRESPONDENCE.lean, AGD_WORK_COUNT.lean).
5. QKXR tower natives: benchmarks/qkxr_tower_native{,_v5}.cpp with live
   Coinbase runner runners/qkxr_live_coinbase.js.
6. Merchant assurance semantic quotient (MASQ v2): ΔC_observed compression,
   Ω pairwise non-additivity, RIF agreement — LOCAL_REFERENCE_ORACLE_ONLY.

### 2.2 Promotion rule

A candidate speed-up may be promoted from CANDIDATE to STRONG_LOCAL only when:

- It is actually executed (not cited from history).
- Baseline and candidate consume the identical canonical instance
  (AGENT.md §4: serialize once, hash, feed both).
- Outputs are independently verified (not trusted return codes).
- Environment, seeds, timing source, repeats, warmups are recorded.
- Determinism holds (pcss_native_runner_v2 exit+stdout+stderr hash check).
- Sub-one or negative speedups are logged as structured evidence, never
  buried (see §3).

Promotion to VERIFIED requires the full gate chain:

    I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L

where X = cross-environment witness and L = Lean gate. The publisher
(publisher/strict_gate.py) is the sole authority for this transition.

### 2.3 What a speed-up is NOT

- Not a universal or hardware-independent constant.
- Not an asymptotic claim from finite timing.
- Not SOTA from beating one comparator.
- Not a formal proof from numerical agreement.
- Not publishable while any gate is false or unknown.

---

## 3. Negative and Sub-One Results Are Evidence

A failed or slower run is a valid benchmark result (AGENT.md §15).

Examples that MUST be recorded, not hidden:

- Python-level reimplementation of an AGD quotient path slower than baseline
  (e.g., 0.7x at n=256, r=64): the algorithmic advantage lives in the
  reduced operator PLUS architecture-specific vectorization, not in Python
  loop structure. Log as REPRODUCIBILITY_FINDING with the formal work ratio
  alongside the measured ratio.
- Missing dependency, solver crash, timeout, invariant residual above
  threshold, degenerate shuffle, numerical instability.

Record: RUN_ID, what failed, why, what remains invariant, what the formal
model still predicts. Quarantine the artifact; do not delete it.

---

## 4. Termux / Remote Execution Integration

When the workload resides on Android/Termux, follow REMOTE_TERMUX_PROTOCOL.md:

1. Confirm remote device online.
2. Identify target workspace.
3. Verify git + required runtime tools.
4. Compute environment fingerprint (arch, kernel, Termux pkg versions,
   CPU, memory — no secrets).
5. Compute scenario/source hashes.
6. Execute in controlled shell: pcss-run <scenario.json>.
7. Capture stdout/stderr/exit/timing.
8. Capture filesystem mutation manifest where authorized.
9. Emit certificate into runs/<run_id>/.
10. Return certificate + artifact paths to orchestration.

Timing separation is mandatory: transport_start, process_start, process_end,
transport_end. Transport latency MUST NOT be represented as application
speedup unless the scenario explicitly declares end-to-end latency as the
metric.

The remote artifact is evidence, not proof. evidence_to_lean.py consumes the
certificate and generates formal obligations. Publication stays blocked
until the Lean gate passes.

---

## 5. Pull Request Protocol

- Prepare but NEVER merge autonomously.
- Attach a machine-readable validation summary as a PR comment AND as a
  check-run annotation so a human reviewer sees pass/fail evidence inline:
  gate matrix (I, R, Q, Q⁻¹, Ω, X, L), measured speedup with sample stats,
  determinism verdict, evidence class, and any quarantined artifacts.
- PR title format: [PCSS] <candidate> — <evidence class> — gates <pass/fail>.
- Include RUN_ID and commit SHA in the PR body.
- Do not modify unrelated files in the same PR.

---

## 6. Fallback When Discovery Finds Nothing Canonical

If no authoritative PCSS spec exists in-repo:

1. Emit a PROPOSED spec synthesized from the Lean theorems
   (lean4/*.lean, muni-production/proof/*.lean) and the October 2 baseline
   standing laws.
2. Mark it PROPOSED, not SPECIFIED.
3. Route it through the Triad: Construction → Compactness → Invariants.
4. Do not execute against an unspecified scenario.

---

## 7. Audit Loop

Each autonomous run must:

1. Record RUN_ID (unique).
2. Pin and hash the repo commit.
3. Execute only declared scenarios.
4. Preserve every artifact, including failures.
5. Validate schemas (evidence/schema/*.json).
6. Run publisher/strict_gate.py — never bypass it.
7. Generate SHA256 manifest.
8. State exactly what the run establishes and what remains unestablished.
9. Lower the claim when evidence is thin; never raise it to fit.

---

## 8. Standing Laws (from 2026-10-02 baseline, still in force)

- bidirectional_closure: resolve or boundary + reformulation.
- Empty corpus is a boundary.
- Claim strength never exceeds evidence class.
- Admissible operators preserve Omega and C and descend to the quotient.
- residual I'' + Gamma + Tr[Y log S] = 0 only on Int observables.
- AGDGovernor is FORMAL_PARTIAL only.
- Speedup/PCSS publishes only under PUBLISH := I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L.
- Do not upgrade FORMAL_PARTIAL to VERIFIED speedup, Hilbert-space CMI,
  wall-clock, or B(H) claims.
