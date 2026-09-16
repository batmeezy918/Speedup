#!/usr/bin/env python3
"""PCSS Phase 0 repository audit.

Builds evidence/repository_inventory.json, a machine-readable inventory of
every tracked artifact in the repository together with its role, producer/
consumer relationships, certificate obligations, gates exercised, current
evidence status, and current claim strength.

This generator NEVER invents evidence: status/claim fields come from the
curated audit table below, which reflects what is actually in the tree as
of the audit, plus computed metadata (sha256, size, git state).
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ROLE_SPEC = "SPECIFICATION"
ROLE_EXEC = "EXECUTION"
ROLE_MEAS = "MEASUREMENT"
ROLE_QUOT = "QUOTIENT"
ROLE_RECON = "RECONSTRUCTION"
ROLE_INV = "INVARIANT"
ROLE_FORMAL = "FORMALIZATION"
ROLE_VERIF = "VERIFICATION"
ROLE_PUB = "PUBLICATION"
ROLE_LEDGER = "LEDGER"
ROLE_ANALYS = "ANALYSIS"
ROLE_HIST = "HISTORICAL"
ROLE_CONFIG = "CONFIGURATION"
ROLE_DOC = "DOCUMENTATION"
ROLE_EVID = "EVIDENCE"
ROLE_ISOL = "ISOLATION"

STATUS_NA = "N/A"
STATUS_CANDIDATE = "CANDIDATE"
STATUS_STRONG_LOCAL = "STRONG_LOCAL"
STATUS_FORMAL_PARTIAL = "FORMAL_PARTIAL"
STATUS_VERIFIED = "VERIFIED"
STATUS_QUARANTINED = "QUARANTINED"
STATUS_HISTORICAL = "HISTORICAL"
STATUS_OBSERVATIONAL = "OBSERVATIONAL"
STATUS_OPEN = "OPEN"
STATUS_SCAFFOLD = "SCAFFOLD"

CLAIM_NONE = "NONE"
CLAIM_CANDIDATE = "CANDIDATE"
CLAIM_STRONG_LOCAL = "STRONG_LOCAL"
CLAIM_FORMAL_PARTIAL = "FORMAL_PARTIAL"
CLAIM_VERIFIED = "VERIFIED"

G_I = "I"
G_R = "R"
G_Q = "Q"
G_QINV = "Q^-1"
G_OM = "Omega"
G_X = "X"
G_L = "L"

# role, purpose, inputs, outputs, deps, producer, consumer, cert_produced,
# cert_consumed, hash_req, gates, evidence_status, claim_strength, note
TABLE = {
    "CONSTITUTION.md": (ROLE_SPEC, "Governing constitution; defines AUTHORITATIVE gates I,R,Q,Q^-1,Omega,X,L and PUBLISH law.", [], [], [], "PCSS law", "all programs", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "canonical law"),
    "CLAIM_POLICY.md": (ROLE_SPEC, "Claim strength lattice and monotone promotion rules.", [], [], [], "PCSS law", "publisher, governor", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "monotone lattice"),
    "IMPLEMENTATION.md": (ROLE_SPEC, "Implementation spec: pipeline, directory contract, hash chain, bidirectional quotient, oblig generation, failure codes.", [], [], [], "PCSS law", "implementers", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "v1.0 spec"),
    "PROTOCOL.md": (ROLE_SPEC, "Execution/evidence transition protocol.", [], [], [], "PCSS law", "runners", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "protocol"),
    "README.md": (ROLE_DOC, "Repository overview; publication law restated.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "overview"),
    "RECURSIVE_SPEEDUP_CONSTITUTION.md": (ROLE_SPEC, "Recursive composition law: S_i not multiplied for composed claims; K_12 diagnostic.", [], [], [], "PCSS law", "composition benchmarks", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "recursive extension of law"),
    "REMOTE_TERMUX_PROTOCOL.md": (ROLE_SPEC, "Remote/Termux execution protocol.", [], [], [], "PCSS law", "remote runners", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "transport protocol"),
    "RUNBOOK.md": (ROLE_DOC, "Operator runbook.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "runbook"),
    "SPECIFICATIONS.md": (ROLE_SPEC, "Additional specifications corpus.", [], [], [], "PCSS law", "implementers", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "spec corpus"),
    "LICENSE": (ROLE_CONFIG, "License.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "no claims"),
    "requirements.txt": (ROLE_CONFIG, "Python dependency pins for COCO/NumPy lanes.", [], [], [], "CI", "CI", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "dependency pins"),
    ".gitignore": (ROLE_CONFIG, "Ignore rules (olean/ilean/.lake).", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "build artifacts ignored"),
    "publisher/gate.py": (ROLE_PUB, "Fail-closed gate predicate evaluator. Read-only; does NOT copy artifacts.", ["certificate.json"], ["exit code + gate list"], [], "PCSS law", "strict_gate", "decision", "certificate.json", ["certificate hash"], [G_I, G_R, G_Q, G_QINV, G_OM, G_X, G_L], STATUS_NA, CLAIM_NONE, "predicate library; promotion authority moved to publisher/strict_gate.py (mission phase 1)"),
    "publisher/manifest.py": (ROLE_SPEC, "Canonical deterministic JSON canonicalize + SHA256 helper.", ["manifest.json"], ["sha256"], [], "PCSS law", "runner, strict_gate", "scenario hash", "manifest", ["scenario hash"], [], STATUS_NA, CLAIM_NONE, "canonical hash helper"),
    "scripts/repository_inventory.py": (ROLE_ANALYS, "Phase 0 inventory generator.", ["repo tree"], ["evidence/repository_inventory.json"], [], "audit", "operators", "none", "none", ["output hash"], [], STATUS_OBSERVATIONAL, CLAIM_NONE, "audit tool (new)"),
    "scripts/pcss_native_runner.py": (ROLE_EXEC, "Canonical unified speedup runner: manifest validation, scenario hashing, source/environment fingerprinting, warmup, baseline/candidate execution, raw timing/output/resource capture, direct speedup, artifact hashing, native evidence emission.", ["scenario manifest", "--output"], ["native evidence dir"], ["publisher.manifest"], "operator", "engines + strict_gate", "raw native evidence", "scenario manifest", ["scenario/source/input/environment/trace hashes"], [G_I, G_R, G_X], STATUS_NA, CLAIM_NONE, "canonical runner (new); must NOT manufacture Q, Q^-1, Omega, L"),
    "engines/__init__.py": (ROLE_EXEC, "Engine package marker.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "package"),
    "engines/quotient.py": (ROLE_QUOT, "Canonical forward quotient engine: equivalence relation, projection Q, forward semantic preservation, observable equivalence check; never promotes.", ["baseline trace", "candidate trace", "scenario"], ["quotient evidence"], ["publisher.manifest"], "runner", "strict_gate", "quotient evidence", "traces", ["quotient hash"], [G_Q], STATUS_NA, CLAIM_NONE, "engine (new)"),
    "engines/reconstruction.py": (ROLE_RECON, "Canonical reverse reconstruction engine: R:O->E, reconstruction distance d(R(Q(e)),e)<=epsilon, max/mean error, coverage; independent of quotient.", ["quotient evidence"], ["reconstruction evidence"], [], "runner", "strict_gate", "reconstruction evidence", "quotient evidence", ["reconstruction hash"], [G_QINV], STATUS_NA, CLAIM_NONE, "engine (new)"),
    "engines/invariant.py": (ROLE_INV, "Canonical invariant engine: Omega(e_candidate) vs Omega(e_baseline), declared relation only; no silent substitution.", ["traces", "scenario invariant def"], ["invariant evidence"], [], "runner", "strict_gate", "invariant evidence", "traces", ["invariant hash"], [G_OM], STATUS_NA, CLAIM_NONE, "engine (new)"),
    "engines/performance.py": (ROLE_MEAS, "Canonical performance engine: median/p95/p99, repetitions/warmups, variance/uncertainty, direct speedup = baseline/candidate; never multiplies isolated speedups.", ["raw timings"], ["performance evidence"], [], "runner", "strict_gate", "performance evidence", "raw timings", ["performance hash"], [G_X], STATUS_NA, CLAIM_NONE, "engine (new)"),
    "engines/attribution.py": (ROLE_ANALYS, "Speedup attribution: work reduction vs implementation overhead vs reconstruction/construction cost vs wall-clock; states exactly which quantity is measured.", ["performance evidence", "scenario"], ["attribution report"], [], "runner", "analysis", "attribution report", "scenario", [], [G_X], STATUS_NA, CLAIM_NONE, "engine (new)"),
    "engines/linear_exact.py": (ROLE_EXEC, "Exact invariant-sector reference workload (block-constant diagonal propagation): T, Tbar, pi, sigma, obs; supports N up to 1M-dimensional.", ["python numpy"], ["traces"], ["numpy"], "runner", "engines", "raw output", "scenario", ["trace hashes"], [], STATUS_NA, CLAIM_NONE, "reference workload (new)"),
    "schemas/pcss_certificate.schema.json": (ROLE_SPEC, "Canonical PCSS certificate schema v2 binding run_id, scenario/scenario_hash, source/input/environment hashes, baseline/candidate trace hashes, quotient/reconstruction/invariant/performance/lean hashes, toolchain, parameters, seed, tolerance, metric, repetitions, warmups, measurement, speedup, uncertainty, gate results, claim boundary.", [], [], [], "PCSS law", "strict_gate", "schema", "certificate.json", [], [], STATUS_NA, CLAIM_NONE, "canonical schema (new); rejects unexplained PASS"),
    "schemas/pcss_scenario.schema.json": (ROLE_SPEC, "Canonical scenario manifest schema v1: workload, object, baseline/candidate impl, quotient/reconstruction/invariant defs, parameters, dimensions, repetitions, warmup policy, timing source, seed, expected observables, environment.", [], [], [], "PCSS law", "runner", "schema", "scenario manifest", [], [], STATUS_NA, CLAIM_NONE, "scenario schema (new)"),
    "publisher/strict_gate.py": (ROLE_PUB, "SINGLE authoritative publication decision. Validates against canonical schema, recomputes all bound hashes, requires non-empty evidence for every declared gate (no unexplained PASS), requires Lean gate backed by verifier artifact, yields PUBLISH or QUARANTINE (exit code).", ["certificate.json", "evidence tree"], ["publication decision"], ["jsonschema-free strict checks", "publisher.manifest", "publisher.gate"], "verification", "ledger", "publication decision", "certificate.json", ["all certificate-bound hashes"], [G_I, G_R, G_Q, G_QINV, G_OM, G_X, G_L], STATUS_NA, CLAIM_NONE, "canonical publisher (new); sole promotion authority"),
    "publisher/evidence_lib.py": (ROLE_PUB, "Certificate assembly/verification helpers shared by runner and strict gate.", [], [], [], "", "", "certificate parts", "certificate.json", [], [], STATUS_NA, CLAIM_NONE, "helpers (new)"),
    "scenarios/linear_exact_diag_1M.json": (ROLE_SPEC, "Canonical million-dimensional exact invariant-sector scenario (Phase 16).", [], [], [], "operator", "runner", "scenario hash", "scenario manifest", [], [], STATUS_NA, CLAIM_NONE, "reference benchmark scenario (new)"),
    "scenarios/discovery_admissibility.json": (ROLE_SPEC, "Canonical admissible-quotient discovery scenario (Phase 17).", [], [], [], "operator", "discovery engine", "scenario hash", "scenario manifest", [], [], STATUS_NA, CLAIM_NONE, "discovery scenario (new)"),
    "engines/discovery.py": (ROLE_QUOT, "Admissible quotient discovery: given state space, transition, observables, invariants, discover equivalence classes; returns NO_ADMISSIBLE_QUOTIENT instead of forcing reduction; candidate classes validated by forward closure, reconstruction, invariant, observable preservation.", ["scenario", "workload model"], ["candidate quotient + validation report"], [], "runner", "refinement", "candidate quotient evidence", "scenario", [], [G_Q, G_QINV, G_OM], STATUS_NA, CLAIM_NONE, "discovery engine (new)"),
    "engines/refinement.py": (ROLE_QUOT, "Refinement loop: candidate quotient -> counterexample -> split class -> revalidate; records initial partition, refinement sequence, final partition, termination evidence.", ["candidate quotient"], ["refined quotient + refinement journal"], [], "discovery", "runner", "refinement journal", "candidate quotient", [], [G_Q, G_QINV, G_OM], STATUS_NA, CLAIM_NONE, "refinement engine (new)"),
    "tests/test_strict_gate.py": (ROLE_VERIF, "Negative/falsification tests for strict_gate (Phase 14): rejects quotient without semantic preservation, reconstruction failure, invariant failure, hash mismatch, tampering, missing artifacts/proof, wrong tolerance, etc.", [], ["test report"], ["publisher.strict_gate", "scripts.pcss_native_runner"], "tests", "CI", "test evidence", "fixtures", [], [G_I, G_R, G_Q, G_QINV, G_OM, G_X, G_L], STATUS_NA, CLAIM_NONE, "negative suite (new)"),
    "tests/test_runner_e2e.py": (ROLE_VERIF, "End-to-end scenario->runner->engines->strict_gate->ledger positive and per-gate negative variants (Phase 20).", [], ["run dirs"], ["as tests/test_strict_gate"], "tests", "CI", "e2e evidence", "scenario", [], [G_I, G_R, G_Q, G_QINV, G_OM, G_X, G_L], STATUS_NA, CLAIM_NONE, "e2e suite (new)"),
    "tests/fixtures/": (ROLE_ISOL, "Negative fixture set retained under quarantine.", [], [], [], "tests", "tests", "quarantined fixtures", "fixtures", [], [], STATUS_QUARANTINED, CLAIM_NONE, "fixture corpus (new)"),
    "test_runner.py": None,  # placeholder unused
    "scripts/verify_and_publish.sh": (ROLE_PUB, "Shell wrapper requesting strict gate + optional Lean build before publication.", ["certificate path"], [], [""], "operator", "CI", "none", "certificate.json", [], [G_L], STATUS_NA, CLAIM_NONE, "must route through strict_gate (Phase 1)"),
    "scripts/verify_lean4_all.sh": (ROLE_VERIF, "Canonical repository-wide Lean entry point: discovers every Lean source in lane, rejects sorry/admit/by?, rejects Mathlib imports in core lane, respects lean-toolchain, resolves dependency ordering over passes, compiles each source, fails on any failure, emits source hashes.", ["lean4 root", "mode"], ["compile results + source hashes"], ["elan/lean/lake"], "CI", "strict_gate", "lean verification artifact", "lean sources", ["source hashes"], [G_L], STATUS_NA, CLAIM_NONE, "canonical Lean verifier"),
    "scripts/evidence_to_lean.py": (ROLE_FORMAL, "Generates Lean obligations from a certificate. NOT an assertion of empirical gates: encodes declared hashes and obligation surface; must not be used as proof of gates.", ["certificate.json", "output.lean"], ["generated Lean obligation"], ["publisher.manifest"], "verification", "Lean pipeline", "obligation file", "certificate.json", ["scenario/source/certificate hashes"], [G_L], STATUS_NA, CLAIM_NONE, "obligation generator; gate evidence must come from real verification artifact (Phase 5-8 compliance mandatory)"),
    "lean4/lakefile.lean": (ROLE_CONFIG, "Lake package declaration for lean4 core lane.", [], [], ["Lake"], "", "lake", "none", "none", [], [G_L], STATUS_NA, CLAIM_NONE, "build wiring"),
    "lean4/lean-toolchain": (ROLE_CONFIG, "Toolchain pin for core lane.", [], [], [], "", "", "none", "none", [], [G_L], STATUS_NA, CLAIM_NONE, "leanprover/lean4:v4.29.0"),
    "lean4/PCSSCertificate.lean": (ROLE_FORMAL, "PCSS certificate predicates: EvidenceCertificate, ClaimStrength, publishable (requires all 7 gates), lean_false_not_publishable, strongestUnverified. Core-only.", [], [], [""], "formal", "strict_gate", "Lean predicates", "certificate", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "formal gate predicates"),
    "lean4/AGDGemmWork.lean": (ROLE_FORMAL, "Operation-count model: fullWork/quotientWork identities.", [], [], [], "formal", "Lean pipeline", "work identities", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "work-model theorems"),
    "lean4/AGDGemmProjection.lean": (ROLE_FORMAL, "Procession/intertwining iterate theorems over AGD state.", [], [], [], "formal", "Lean pipeline", "projection theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "projection theorems"),
    "lean4/AGDGemmReconstruction.lean": (ROLE_FORMAL, "Reverse reconstruction/section theorems.", [], [], [], "formal", "Lean pipeline", "reconstruction theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "reconstruction theorems"),
    "lean4/AGDGemmSpeedup.lean": (ROLE_FORMAL, "Speedup boundary theorems linking work model to projection/reconstruction.", [], [], ["AGDGemmWork", "AGDGemmProjection", "AGDGemmReconstruction"], "formal", "Lean pipeline", "speedup boundary theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "speedup-boundary theorems"),
    "lean4/AGDMaximallyTypedClaim.lean": (ROLE_FORMAL, "Intertwining, iterate, section, observable preservation, work ratio, runtime/work distinctness; core-only.", [], [], [], "formal", "Lean pipeline", "formal closure theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "maximal typed claim surface"),
    "lean4/GODSQuotientClosure.lean": (ROLE_FORMAL, "First-principles GODS quotient closure kernel. Core-only.", [], [], [], "formal", "Lean pipeline", "gods descend/recursive descent theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "GODS kernel"),
    "lean4/LeanSpeedup.lean": (ROLE_FORMAL, "Aggregating module importing core AGD stack.", [], [], list("PCSSCertificate"), "formal", "Lean pipeline", "aggregate import", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "aggregator"),
    "lean4/SpeedupExactInvariant.lean": (ROLE_FORMAL, "Exact invariant-sector semantics on AGD vocabulary. Core-only.", [], [], [], "formal", "Lean pipeline", "invariant sector theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "exact invariant sector"),
    "lean4/SpeedupLean.lean": (ROLE_FORMAL, "Aggregating import module.", [], [], [], "formal", "Lean pipeline", "aggregate import", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "aggregator"),
    "lean4/chronofold/lean-toolchain": (ROLE_CONFIG, "Toolchain pin (stable).", [], [], [], "", "", "none", "none", [], [G_L], STATUS_NA, CLAIM_NONE, "not canonical-pinned (v4.29.0 canonical)"),
    "lean4/chronofold/lakefile.lean": (ROLE_CONFIG, "ChronoFold lake package.", [], [], [], "formal", "lake", "none", "none", [], [G_L], STATUS_NA, CLAIM_NONE, "build wiring"),
    "lean4/chronofold/ChronoFoldProof.lean": (ROLE_FORMAL, "ChronoFold literal proof surface.", [], [], [], "formal", "Lean pipeline", "literal theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "chronofold proofs"),
    "lean4/chronofold/ExactQuotientClosure.lean": (ROLE_FORMAL, "Exact quotient closure theorems (intertwining, section, observable factorization, iterate closure).", [], [], [], "formal", "Lean pipeline", "exact closure theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "exact closure"),
    "lean4/chronofold/GODSQuotientClosure.lean": (ROLE_FORMAL, "GODS quotient closure (chronofold namespace).", [], [], [], "formal", "Lean pipeline", "GODS theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "GODS chronofold variant"),
    "lean4/chronofold/LinearQuotientProof.lean": (ROLE_FORMAL, "Linear quotient proof surface.", [], [], [], "formal", "Lean pipeline", "linear quotient theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "linear quotient"),
    "lean4/chronofold/ProgressTargetCoupling.lean": (ROLE_FORMAL, "Progress-Target Coupling: Nat-valued defect descent reaches target; literal transfer + reconstruction transfer.", [], [], [], "formal", "Lean pipeline", "progress/target theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "progress-target coupling"),
    "lean4/chronofold/WeakCouplingBound.lean": (ROLE_FORMAL, "Weak-coupling finite-horizon bound at the algebraic recurrence boundary (Nat recurrence, explicit assumptions; normed-space instantiation separate).", [], [], [], "formal", "Lean pipeline", "weak coupling bound", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "weak coupling boundary; real-analysis instantiation OPEN"),
    "lean4/linear/LinearQuotientProof.lean": (ROLE_FORMAL, "Linear quotient proof surface.", [], [], [], "formal", "Lean pipeline", "linear quotient theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "linear quotient"),
    "lean4/scaffolding/PCSSCertificate.lean": (ROLE_FORMAL, "Scaffold of quotient/forward/reverse surface (not promoted).", [], [], [], "formal", "Lean pipeline", "none", "none", [], [], STATUS_SCAFFOLD, CLAIM_NONE, "scaffold only"),
    "lean4/workflow_isolation/MaximalPreLean.lean": (ROLE_FORMAL, "Pre-Lean objects: quotient model, intertwining, reconstruction, observability, iterate; modeled GEMM work identities and runtime binding honesty boundary.", [], [], [], "formal", "Lean pipeline", "pre-Lean theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "workflow isolation layer"),
    "lean4/workflow_isolation/README.md": (ROLE_DOC, "Workflow isolation explanation.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "documentation"),
    "lean4/ProvenAgd/AGDTheoremSeries.lean": (ROLE_FORMAL, "Port of THM_000101..THM_000205 series over Nat/generic core types.", [], [], ["AGDMaximallyTypedClaim"], "formal", "Lean pipeline", "theorem series", "none", [], [G_L], STATUS_OPEN, CLAIM_NONE, "BLOCKS canonical Lean lane: does not compile on Lean 4.29 (Phase 12). Must be fixed or quarantined."),
    "lean4/ProvenAgd/ConstitutionalKernel.lean": (ROLE_FORMAL, "ProvenAgd constitutional kernel.", [], [], ["AGDMaximallyTypedClaim"], "formal", "Lean pipeline", "kernel theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "ProvenAgd kernel"),
    "lean4/ProvenAgd/CorrectByConstructionSearch.lean": (ROLE_FORMAL, "Correct-by-construction search formal surface.", [], [], [], "formal", "Lean pipeline", "search theorems", "none", [], [G_L], STATUS_FORMAL_PARTIAL, CLAIM_NONE, "ProvenAgd search"),
    "lean4/Mathlib/lakefile.lean": (ROLE_CONFIG, "Mathlib lane lake package.", [], [], [], "formal", "lake", "none", "none", [], [G_L], STATUS_NA, CLAIM_NONE, "mathlib lane (dependency-heavy; not core)"),
    "lean4/Mathlib/lean-toolchain": (ROLE_CONFIG, "Mathlib lane toolchain pin v4.29.0.", [], [], [], "", "", "none", "none", [], [G_L], STATUS_NA, CLAIM_NONE, "mathlib toolchain"),
    "lean4/Mathlib/MathlibProof.lean": (ROLE_FORMAL, "Mathlib-lane proof surface.", [], [], ["Mathlib"], "formal", "Lean pipeline", "mathlib proofs", "none", [], [G_L], STATUS_OPEN, CLAIM_NONE, "requires Mathlib dependency build; canonical core lane must not depend on it"),
    "lean4/Mathlib/SpeedupMathlib.lean": (ROLE_FORMAL, "Mathlib speedup formalization.", [], [], ["Mathlib"], "formal", "Lean pipeline", "mathlib speedup theorems", "none", [], [G_L], STATUS_OPEN, CLAIM_NONE, "Mathlib-lane only; see MathlibMathlibProof"),
    "candidate/README.md": (ROLE_DOC, "Candidate area description.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "candidate area"),
    "candidate/lean4/README.md": (ROLE_DOC, "Candidate lean area description.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "candidate lean area"),
    "verified/README.md": (ROLE_DOC, "Verified area description.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "verified area doc"),
    "verified/lean4/README.md": (ROLE_DOC, "Verified lean area description.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "verified lean area doc"),
    "verified/sim2xr/2026-09-08/CLAIM.md": (ROLE_HIST, "Exact invariant-sector speedup claim summary: d=256..65536, r=2..32, max 168.14x, median 4.09x.", [], [], [], "historical", "audit", "claim statement", "certificate + witness", [], [G_Q, G_QINV, G_OM, G_X], STATUS_STRONG_LOCAL, CLAIM_STRONG_LOCAL, "NOT VERIFIED: lean gate false in attached certificate (Phase 15: every empirical artifact honest class)"),
    "verified/sim2xr/2026-09-08/bidirectional_witness.json": (ROLE_EVID, "Five bidirectional witnesses with residuals and measured speedups.", [], [], [], "historical", "certificate", "witness", "certificate", ["certificate hash"], [G_Q, G_QINV, G_OM, G_X], STATUS_STRONG_LOCAL, CLAIM_STRONG_LOCAL, "reconstruction/task/intertwining residuals all reported == 0; wall-clock speedups measured locally; NOT Lean-bound"),
    "verified/sim2xr/2026-09-08/pcss_certificate.json": (ROLE_EVID, "PCSS certificate for sim2xr run with gates.integrity..performance true but lean=false.", [], [], [], "historical", "strict_gate", "certificate", "certificate", ["certificate sha256"], [G_I, G_R, G_Q, G_QINV, G_OM, G_X], STATUS_STRONG_LOCAL, CLAIM_STRONG_LOCAL, "lean false => strict publication law forces QUARANTINE for VERIFIED status (Phase 15)"),
    "evidence/ledger/SCREENING_2026-09-08T191800Z.json": (ROLE_LEDGER, "Screening ledger entry.", [], [], [], "ledger", "audit", "ledger entry", "none", [], [G_I], STATUS_OBSERVATIONAL, CLAIM_NONE, "screen ledger"),
    "evidence/ledger/SCREENING_2026-09-08T191800Z.md": (ROLE_LEDGER, "Screening ledger prose.", [], [], [], "ledger", "audit", "none", "none", [], [], STATUS_OBSERVATIONAL, CLAIM_NONE, "screen ledger prose"),
    "evidence/schema/certificate.schema.json": (ROLE_SPEC, "V1 certificate schema. Missing the canonical binding fields of Phase 2 (environment_hash present but no scenario/run binding, no lean_hash, no claim boundary, additionalProperties true).", [], [], [], "PCSS law", "gate", "schema", "certificate.json", [], [], STATUS_NA, CLAIM_NONE, "superseded by schemas/pcss_certificate.schema.json (retained; strict gate requires canonical schema)"),
    "evidence/schema/evidence.schema.json": (ROLE_SPEC, "V1 evidence schema.", [], [], [], "PCSS law", "gate", "schema", "evidence.json", [], [], STATUS_NA, CLAIM_NONE, "evidence schema"),
    "evidence/normalized/INDEX.md": (ROLE_DOC, "Normalized index.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "index"),
    "evidence/normalized/coco-deterministic/certificate.json": (ROLE_EVID, "COCO determinism certificate: double-run equality, not speedup.", [], [], [], "historical", "strict_gate", "certificate", "scenario", ["certificate hash"], [G_R], STATUS_STRONG_LOCAL, CLAIM_NONE, "determinism contract only"),
    "evidence/normalized/coco-deterministic/scenario.json": (ROLE_EVID, "Determinism scenario manifest.", [], [], [], "historical", "runner", "scenario", "manifest", ["scenario hash"], [], STATUS_NA, CLAIM_NONE, "scenario"),
    "evidence/normalized/coco-head-to-head/certificate.json": (ROLE_EVID, "COCO head-to-head certificate; Lean binds only declared classification counts.", [], [], [], "historical", "strict_gate", "certificate", "scenario", ["certificate hash"], [G_R, G_Q], STATUS_STRONG_LOCAL, CLAIM_NONE, "bounded classification counts"),
    "evidence/normalized/coco-head-to-head/scenario.json": (ROLE_EVID, "Head-to-head scenario manifest.", [], [], [], "historical", "runner", "scenario", "manifest", ["scenario hash"], [], STATUS_NA, CLAIM_NONE, "scenario"),
    "evidence/normalized/vault-canonical-decider-20260531T112101Z/certificate.json": (ROLE_EVID, "Vault canonical decider certificate.", [], [], [], "historical", "strict_gate", "certificate", "scenario", [], [], STATUS_CANDIDATE, CLAIM_NONE, "certificate"),
    "evidence/normalized/vault-canonical-decider-20260531T112101Z/scenario.json": (ROLE_EVID, "Vault decider scenario manifest.", [], [], [], "historical", "runner", "scenario", "manifest", [], [], STATUS_NA, CLAIM_NONE, "scenario"),
    "evidence/official-coco/ARCHITECTURE.md": (ROLE_DOC, "Official COCO architecture note.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "doc"),
    "evidence/official-coco/OCCURRENCE.md": (ROLE_DOC, "Official COCO occurrence summary.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "doc"),
    "evidence/official-coco/OPTIMIZER_MATRIX.json": (ROLE_ANALYS, "Optimizer matrix; marked OFFICIAL_HARNESS_NOT_YET_FULL_CAPTURE.", [], [], [], "analysis", "audit", "none", "none", [], [], STATUS_OPEN, CLAIM_NONE, "non-claim status recorded"),
    "evidence/official-coco/projected_s6_coco_harness.py": (ROLE_EXEC, "Projected S6 COCO harness (fetches chronofold benchmark source).", ["--self-test", "--run-id", "--dimensions", "--budget", "--seed", "--output-dir"], ["run dir with manifest + report"], ["cocoex", "cma", "numpy", "psutil"], "CI", "evidence", "manifest + summary", "scenario", ["run dir hash"], [G_R], STATUS_OBSERVATIONAL, CLAIM_NONE, "official harness; does not manufacture quotient/reconstruction"),
    "evidence/official-coco/occurrence-2026-09-08T192500Z/certificate.json": (ROLE_EVID, "Early occurrence certificate.", [], [], [], "historical", "strict_gate", "certificate", "scenario", [], [], STATUS_CANDIDATE, CLAIM_NONE, "early occurrence"),
    "evidence/official-coco/occurrence-2026-09-08T192500Z/smoke_results.json": (ROLE_EVID, "Smoke results.", [], [], [], "historical", "analysis", "smoke result", "none", [], [], STATUS_OBSERVATIONAL, CLAIM_NONE, "smoke data"),
    "evidence/official-coco/occurrence-2026-09-08T195400Z/certificate.json": (ROLE_EVID, "Occurrence certificate.", [], [], [], "historical", "strict_gate", "certificate", "scenario", [], [], STATUS_CANDIDATE, CLAIM_NONE, "occurrence"),
    "evidence/official-coco/occurrence-2026-09-08T195400Z/summary.json": (ROLE_EVID, "Summary.", [], [], [], "historical", "analysis", "summary", "none", [], [], STATUS_OBSERVATIONAL, CLAIM_NONE, "summary data"),
    "evidence/official-coco/occurrence-2026-09-08T203000Z/OCCURRENCE.md": (ROLE_DOC, "Occurrence prose.", [], [], [], "historical", "analysis", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "prose"),
    "evidence/official-coco/occurrence-2026-09-08T203000Z/certificate.json": (ROLE_EVID, "Occurrence certificate.", [], [], [], "historical", "strict_gate", "certificate", "scenario", [], [], STATUS_CANDIDATE, CLAIM_NONE, "occurrence"),
    "evidence/official-coco/occurrence-2026-09-08T203000Z/summary.json": (ROLE_EVID, "Summary.", [], [], [], "historical", "analysis", "summary", "none", [], [], STATUS_OBSERVATIONAL, CLAIM_NONE, "summary data"),
    "evidence/official-coco/sandbox-run-20260910/": (ROLE_EVID, "Sandbox run (manifest, environment, benchmark_summary, replay report, final report).", [], [], [], "historical", "analysis", "run evidence", "manifest", ["run dir hash"], [G_R], STATUS_OBSERVATIONAL, CLAIM_NONE, "sandbox run evidence; not a verified claim"),
    "evidence/official-coco/sim2xr_agd_gapfill.md": (ROLE_HIST, "Gap-fill analysis of sim2xr/AGD relation.", [], [], [], "historical", "audit", "none", "none", [], [], STATUS_HISTORICAL, CLAIM_NONE, "gap analysis"),
    "evidence/optimizer/HISTORICAL_RESULTS.md": (ROLE_HIST, "Historical optimizer results inventory.", [], [], [], "historical", "audit", "none", "none", [], [], STATUS_HISTORICAL, CLAIM_NONE, "historical results"),
    "evidence/optimizer/SOURCE_STATUS.md": (ROLE_HIST, "Source/evidence status for optimizer results.", [], [], [], "historical", "audit", "none", "none", [], [], STATUS_HISTORICAL, CLAIM_NONE, "source status"),
    "evidence/quarantine/INDEX.md": (ROLE_DOC, "Quarantine index.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "quarantine index"),
    "evidence/snap/HISTORICAL_CORPUS_INDEX.md": (ROLE_HIST, "SNAP optimizer evidence corpus index.", [], [], [], "historical", "audit", "none", "none", [], [], STATUS_HISTORICAL, CLAIM_NONE, "historical corpus"),
    "evidence/snap/README.md": (ROLE_DOC, "SNAP area readme.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "readme"),
    "evidence/snap/cmaes_benchmark_manifest.md": (ROLE_SPEC, "CMA-ES benchmark manifest (prose).", [], [], [], "historical", "runner", "none", "none", [], [], STATUS_HISTORICAL, CLAIM_NONE, "prose manifest"),
    "evidence/telemetry/runtime/ledger.jsonl": (ROLE_LEDGER, "COCI telemetry witness ledger (local on-device executions).", [], [], [], "governor", "audit", "witness ledger", "none", [], [G_I], STATUS_OBSERVATIONAL, CLAIM_NONE, "on-device observability ledger"),
    "evidence/telemetry/runtime/snapshots/snapshot-20260912T012529Z-1aa98cc7.json": (ROLE_EVID, "Runtime telemetry snapshot.", [], [], [], "governor", "audit", "snapshot", "none", [], [], STATUS_OBSERVATIONAL, CLAIM_NONE, "telemetry snapshot"),
    "evidence/templates/CF_QRT_CANONICAL_RUNTIME_CERTIFICATE_v1.1.md": (ROLE_SPEC, "Canonical quotient-runtime certificate template v1.1.", [], [], [], "PCSS law", "certificate authors", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "template"),
    "evidence/templates/CF_QRT_CANONICAL_RUNTIME_CERTIFICATE_v1.1_INSTANCE_20260910.md": (ROLE_EVID, "Instantiated runtime certificate instance (2026-09-10).", [], [], [], "historical", "audit", "instance cert", "certificate", [], [], STATUS_CANDIDATE, CLAIM_NONE, "instance"),
    "evidence/unofficial/ISOLATION.md": (ROLE_DOC, "Unofficial isolation note.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "isolation note"),
    "evidence/unofficial/certificate.json": (ROLE_EVID, "Unofficial optimizer isolation certificate; all gates false; QUARANTINED.", [], [], [], "historical", "strict_gate", "certificate", "none", [], [G_I, G_R, G_Q, G_QINV, G_OM, G_X, G_L], STATUS_QUARANTINED, CLAIM_NONE, "quarantined by explicit false gates"),
    "executor/scenario/manifest.example.json": (ROLE_SPEC, "Example scenario manifest (v1).", [], [], [], "PCSS law", "runner", "scenario hash", "manifest", [], [], STATUS_NA, CLAIM_NONE, "example manifest; superseded by schemas/pcss_scenario.schema.json"),
    "formal/theorem_escalation/2026-09-11/StableConstitutionalQuotient.lean": (ROLE_FORMAL, "Greatest stable constitutional quotient SCAFFOLD (spec only, no proof).", [], [], [], "formal", "Lean pipeline", "none", "none", [], [], STATUS_SCAFFOLD, CLAIM_NONE, "explicit scaffold; not verified"),
    "formal/theorem_escalation/2026-09-11/THEOREM_QUEUE.yaml": (ROLE_SPEC, "Theorem escalation queue.", [], [], [], "formal", "implementers", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "queue"),
    "formal/theorem_escalation/2026-09-11/README.md": (ROLE_DOC, "Escalation readme.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "readme"),
    "formal/theorem_escalation/2026-09-11/OPERATIONAL_EFFECTS.md": (ROLE_SPEC, "Operational effects mapping contract for theorem promotion.", [], [], [], "PCSS law", "implementers", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "promotion contract"),
    "governor/COCI_GOVERNOR.md": (ROLE_SPEC, "COCI governor spec.", [], [], [], "PCSS law", "governor", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "spec"),
    "governor/coci_governor.py": (ROLE_LEDGER, "COCI observational witness governor: hashes changed files, appends hash-linked JSONL; does not execute or promote.", ["root"], ["governor ledger JSONL"], [], "operator", "audit", "witness ledger", "none", ["event hash chain"], [G_I], STATUS_OBSERVATIONAL, CLAIM_NONE, "witness governor"),
    "skills/coci-governor/SKILL.md": (ROLE_DOC, "Invocation skill doc.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "skill doc"),
    ".opencode/skills/coci-governor/SKILL.md": (ROLE_DOC, "Mirror skill doc.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "skill doc mirror"),
    "speedup/historical_closure/2026-09-08/README.md": (ROLE_HIST, "Historical closure corpus readme.", [], [], [], "historical", "audit", "none", "none", [], [], STATUS_HISTORICAL, CLAIM_NONE, "historical corpus"),
    "speedup/historical_closure/2026-09-08/SPEEDUP_CLOSURE_20260908.md": (ROLE_HIST, "Honest closure status of historical speedup claims (17.544277x SIM2XR validated; GS254/others quarantined or pending).", [], [], [], "historical", "audit", "none", "none", [], [], STATUS_HISTORICAL, CLAIM_NONE, "keeps claim_strength <= evidence_strength; canonical history"),
    "speedup/historical_closure/2026-09-08/closure_matrix.json": (ROLE_HIST, "Machine-readable closure matrix of historical claims.", [], [], [], "historical", "audit", "closure matrix", "none", ["matrix hash"], [], STATUS_HISTORICAL, CLAIM_NONE, "historical claims not elevated"),
    "speedup/historical_closure/2026-09-08/artifact_hashes.sha256": (ROLE_HIST, "SHA256 of historical closure artifacts.", [], [], [], "historical", "audit", "hash set", "closure artifacts", ["artifact hashes"], [G_I], STATUS_HISTORICAL, CLAIM_NONE, "hash set"),
    "speedup/historical_closure/2026-09-08/PROOF_CARRYING_HASHES_20260908.sha256": (ROLE_HIST, "Proof-carrying hashes for closure corpus.", [], [], [], "historical", "audit", "hash set", "closure corpus", ["artifact hashes"], [G_I], STATUS_HISTORICAL, CLAIM_NONE, "hash set"),
    "speedup/historical_closure/2026-09-08/SIM2XR_FIRST_PRINCIPLES_STABILITY.json": (ROLE_HIST, "SIM2XR first-principles stability record.", [], [], [], "historical", "audit", "stability record", "none", [], [], STATUS_HISTORICAL, CLAIM_NONE, "stability record"),
    "speedup/historical_closure/2026-09-08/SIM2XR_FIRST_PRINCIPLES_STABILITY.md": (ROLE_HIST, "SIM2XR stability prose.", [], [], [], "historical", "audit", "none", "none", [], [], STATUS_HISTORICAL, CLAIM_NONE, "stability prose"),
    "speedup/historical_closure/2026-09-08/SIM2XR_TARGET_20260908T201616Z.log": (ROLE_HIST, "SIM2XR target rerun log.", [], [], [], "historical", "audit", "log", "none", [], [], STATUS_HISTORICAL, CLAIM_NONE, "run log"),
    "speedup/historical_closure/2026-09-08/SIM2XR_target_report.json": (ROLE_HIST, "SIM2XR target rerun report (7 repeats, median 17.544277x).", [], [], [], "historical", "audit", "report", "none", ["report hash"], [G_X], STATUS_HISTORICAL, CLAIM_NONE, "local measured rerun retained"),
    "speedup/historical_closure/2026-09-08/GS254_target_gate.log": (ROLE_HIST, "GS254 gate log (BLOCKED_PENDING_SEMANTIC_WITNESS).", [], [], [], "historical", "audit", "log", "none", [], [G_Q], STATUS_HISTORICAL, CLAIM_NONE, "blocked by semantic witness"),
    "speedup/historical_closure/2026-09-08/GS254_FIRST_PRINCIPLES_BLOCK_CLOSURE.md": (ROLE_HIST, "GS254 first-principles block closure prose.", [], [], [], "historical", "audit", "none", "none", [], [], STATUS_HISTORICAL, CLAIM_NONE, "block record"),
    "speedup/historical_closure/2026-09-08/Omega_v63_target_partial.md": (ROLE_HIST, "Omega v6.3 partial rerun; NOT validated as stable speedup.", [], [], [], "historical", "audit", "none", "none", [], [], STATUS_HISTORICAL, CLAIM_NONE, "correct factoring; unstable ratio"),
    "docs/AGD_OPT_1_Frozen_Architecture_2026-09-10.md": (ROLE_DOC, "Frozen architecture note for AGD-OPT-1.", [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE, "frozen architecture doc"),
    ".github/workflows/pcss-verification.yml": (ROLE_VERIF, "Canonical PCSS verification workflow: structure, gate fail-closed test, Lean install + PATH, lake build, repository-wide Lean verification, proof identities.", [], [], [], "CI", "repo", "CI verification artifact", "none", [], [G_I, G_R, G_Q, G_QINV, G_OM, G_X, G_L], STATUS_NA, CLAIM_NONE, "must additionally call strict_gate negative + schema/scenario validation (Phase 13)"),
    ".github/workflows/lean-ci.yml": (ROLE_VERIF, "Lean verification lane (core).", [], [], [], "CI", "repo", "Lean artifact", "none", [], [G_L], STATUS_NA, CLAIM_NONE, "invokes canonical verifier; verify consistency"),
    ".github/workflows/chronofold-lean4.yml": (ROLE_VERIF, "ChronoFold-specific Lean lane.", [], [], [], "CI", "repo", "Lean artifact", "none", [], [G_L], STATUS_NA, CLAIM_NONE, "sub-lane; keeps repo-wide interpretation honest"),
    ".github/workflows/mathlib-lean4.yml": (ROLE_VERIF, "Mathlib lane build.", [], [], [], "CI", "repo", "Mathlib build artifact", "none", [], [G_L], STATUS_OPEN, CLAIM_NONE, "Mathlib-lane only; never used to claim core verification"),
    ".github/workflows/official-coco-registered.yml": (ROLE_VERIF, "Official COCO/BBOB registered run; explicit that publication gate remains closed.", [], [], [], "CI", "evidence", "COCO run evidence", "none", [], [G_R], STATUS_OBSERVATIONAL, CLAIM_NONE, "registered harness"),
    ".github/workflows/projected-s6-coco.yml": (ROLE_VERIF, "Projected S6 COCO pipeline w/ manifest post-checks.", [], [], [], "CI", "evidence", "COCO run evidence", "manifest", [], [G_R], STATUS_OBSERVATIONAL, CLAIM_NONE, "projected harness"),
    ".github/workflows/proof-gated-speedup.yml": (ROLE_VERIF, "Proof-gated speedup workflow (gate.py path).", [], [], [], "CI", "publisher", "gate validation", "certificate", [], [G_I, G_R, G_Q, G_QINV, G_OM, G_X, G_L], STATUS_NA, CLAIM_NONE, "MUST route through publisher/strict_gate.py (Phase 1 rule: single authoritative publisher)"),
}

# Paths that exist but are not individually curated are classified by the
# directory-level defaults below.
DIR_DEFAULTS = {
    "evidence/telemetry/": (ROLE_EVID, "On-device telemetry artifacts (runtime only tracked).", STATUS_OBSERVATIONAL, CLAIM_NONE),
}


def canonical_sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_state(repo: Path) -> dict:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain=v1", "-z"],
            capture_output=True, text=True, timeout=20,
        ).stdout
        fields = out.split("\0") if out else []
        modified, untracked = set(), set()
        it = iter(fields)
        for f in it:
            if not f:
                continue
            flag = f[0:2]
            if flag == "??":
                untracked.add(f[3:])
            else:
                modified.add(f[3:].split(" -> ")[-1])
        return {"modified": sorted(modified), "untracked": sorted(untracked)}
    except Exception:
        return {"modified": [], "untracked": []}


def main() -> int:
    git = git_state(ROOT) if (ROOT / ".git").exists() else {}

    entries = []
    all_paths = [str(p.relative_to(ROOT)) for p in sorted(ROOT.rglob("*")) if p.is_file()]
    all_paths = [p for p in all_paths if ".git/" not in p and "__pycache__" not in p
                 and not p.endswith(".olean") and not p.endswith(".ilean")]

    for rel in all_paths:
        p = ROOT / rel
        info = TABLE.get(rel)
        if info is None:
            # directory default matching
            for prefix, (role, purpose, status, claim) in DIR_DEFAULTS.items():
                if rel.startswith(prefix):
                    info = (role, purpose, [], [], [], "", "", "none", "none", [],
                            [], status, claim, "directory default classification")
                    break
        if info is None:
            info = (ROLE_CONFIG, "Unclassified artifact (audit gap; classify before next promotion).",
                    [], [], [], "", "", "none", "none", [], [], STATUS_NA, CLAIM_NONE,
                    "unclassified")
        (role, purpose, inputs, outputs, deps, producer, consumer,
         cert_prod, cert_cons, hash_req, gates, status, claim, note) = info

        extra = {}
        if rel in git.get("modified", []):
            extra["git_state"] = "modified"
        if rel in git.get("untracked", []):
            extra["git_state"] = "untracked"

        entries.append({
            "path": rel,
            "language": _language(rel),
            "role": role,
            "purpose": purpose,
            "inputs": inputs,
            "outputs": outputs,
            "dependencies": deps,
            "producer": producer,
            "consumer": consumer,
            "certificate_produced": cert_prod,
            "certificate_consumed": cert_cons,
            "hash_requirements": hash_req,
            "pcss_gates_exercised": gates,
            "evidence_status": status,
            "claim_strength": claim,
            "size_bytes": p.stat().st_size,
            "sha256": file_sha256(p),
            "note": note,
            **extra,
        })

    # Phase 0 synthesis: duplicates / obsolete / bypass paths observed.
    synthesis = {
        "governing_documents": [
            "CONSTITUTION.md", "CLAIM_POLICY.md", "IMPLEMENTATION.md",
            "RECURSIVE_SPEEDUP_CONSTITUTION.md", "PROTOCOL.md", "SPECIFICATIONS.md",
        ],
        "duplicate_or_parallel_paths": [
            {
                "paths": ["publisher/gate.py", ".github/workflows/proof-gated-speedup.yml"],
                "issue": "Multiple programs/CI lanes claim publication authority.",
                "resolution": "Phase 1+: single authoritative publisher/strict_gate.py; gate.py demoted to read-only predicate. proof-gated-speedup.yml must route through strict_gate.py.",
            },
            {
                "paths": [".github/workflows/lean-ci.yml", ".github/workflows/chronofold-lean4.yml"],
                "issue": "Two Lean lanes with identical role but different scanned roots.",
                "resolution": "Phase 12+: both MUST invoke scripts/verify_lean4_all.sh with explicit root; repository-wide lane is lean4 (core). chronofold lane remains sub-lane but compiles a subset - never claim repository-wide.",
            },
        ],
        "obsolete_or_superseded": [
            {
                "paths": ["evidence/schema/certificate.schema.json"],
                "issue": "V1 schema lacks canonical Phase-2 binding fields and gate evidence requirements.",
                "resolution": "Superseded by schemas/pcss_certificate.schema.json; retained for history.",
            },
            {
                "paths": ["executor/scenario/manifest.example.json"],
                "issue": "V1 example manifest not conformant to canonical scenario schema.",
                "resolution": "Superseded by scenarios/*.json + schemas/pcss_scenario.schema.json; retained as historical example.",
            },
            {
                "paths": ["lean4/ProvenAgd/AGDTheoremSeries.lean"],
                "issue": "Does not compile under canonical Lean 4.29 (blocks Phase 12 lane).",
                "resolution": "Fix or quarantine; do not claim repository-wide Lean pass while it is broken.",
            },
        ],
        "bypass_or_gap_paths": [
            {
                "paths": ["scripts/evidence_to_lean.py"],
                "issue": "Current generator emits gate booleans as axioms; if consumed as proof of gates this would be unconditional promotion.",
                "resolution": "Obligation generation must carry declared hashes and obligations; gate evidence L must come from a real compiled Lean artifact (verify_lean4_all.sh).",
            },
            {
                "paths": ["verified/sim2xr/2026-09-08/pcss_certificate.json"],
                "issue": "Certificates located in verified/ but gates.lean=false; publication law => not VERIFIED as a dashboard-green gate.",
                "resolution": "Retained with STRONG_LOCAL status; strict_gate returns QUARANTINE for VERIFIED promotion until Lean gate closes.",
            },
            {
                "paths": ["speedup/historical_closure/2026-09-08/"],
                "issue": "No canonical runner exists in-repo; historical claims depending on unavailable runners are PENDING_RERUN.",
                "resolution": "Phase 4+ canonical runner scripts/pcss_native_runner.py makes every future speedup traceable end-to-end.",
            },
        ],
    }

    counts = {}
    for e in entries:
        counts[e["role"]] = counts.get(e["role"], 0) + 1
    status_counts = {}
    for e in entries:
        status_counts[e["evidence_status"]] = status_counts.get(e["evidence_status"], 0) + 1

    doc = {
        "schema": "PCSS-REPOSITORY-INVENTORY-1.0",
        "generated_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        .isoformat(timespec="seconds").replace("+00:00", "Z"),
        "repository": "batmeezy918/Speedup",
        "inventory_sha256": None,
        "entries": entries,
        "summary": {
            "total_files": len(entries),
            "by_role": counts,
            "by_evidence_status": status_counts,
            "bypass_or_gap_paths": synthesis["bypass_or_gap_paths"],
            "duplicate_or_parallel_paths": synthesis["duplicate_or_parallel_paths"],
            "obsolete_or_superseded": synthesis["obsolete_or_superseded"],
            "governing_documents": synthesis["governing_documents"],
        },
    }
    canonical = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
    doc["inventory_sha256"] = hashlib.sha256(canonical).hexdigest()

    out = ROOT / "evidence" / "repository_inventory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(entries)} entries, {doc['inventory_sha256']})")
    return 0


def _language(rel: str) -> str:
    if rel.endswith(".py"):
        return "python"
    if rel.endswith(".sh"):
        return "bash"
    if rel.endswith(".lean"):
        return "lean4"
    if rel.endswith(".jl"):
        return "julia"
    if rel.endswith(".json"):
        return "json"
    if rel.endswith(".jsonl"):
        return "jsonl"
    if rel.endswith(".yml"):
        return "yaml"
    if rel.endswith(".yaml"):
        return "yaml"
    if rel.endswith(".md"):
        return "markdown"
    if rel.endswith(".sha256") or "@" in rel:
        return "hashtext"
    if rel.endswith(".txt"):
        return "text"
    if rel.endswith(".log"):
        return "text-log"
    return "other"


if __name__ == "__main__":
    sys.exit(main())