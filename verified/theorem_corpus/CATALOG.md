# batmeezy918 theorem corpus — Speedup intake

**Assembled:** 2026-09-16  
**Governing law:** `CLAIM_STRENGTH <= EVIDENCE_STRENGTH`  
**This folder is an archive, not a live Lean target.**  
Do not compile these copies with Speedup `lean4/` CI. The original CI lane that accepted each file is recorded below.

---

## 1. Speedup repository — structure

Speedup is a **Proof-Carrying Speedup Scheduler (PCSS)**, not a general math library.

```
CONSTITUTION.md / CLAIM_POLICY.md / PROTOCOL.md / SPECIFICATIONS.md
lean4/                  formal obligations (core + chronofold lane + Mathlib lane)
candidate/theorems/     CT-001..004 candidate statements (not yet VERIFIED)
evidence/               certificates, COCO occurrences, ledgers
benchmarks/             gold-standard matrix (HPL/SPEC/MLPerf/COCO intent)
verified/               only for artifacts that pass PUBLISH
governor / executor / publisher / formal_gap_isolator
```

Publication predicate:

```
PUBLISH := I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L
```

Integrity, reproducibility, forward quotient, reverse reconstruction, invariants, performance evidence, Lean.

### Novel math that is actually encoded

What is new *as a constructed stack* (not an automatic scientific-novelty claim):

1. **Observable quotient as the acceptance object.**  
   Equivalence is `Q(E_cand) = Q(E_base)`, not implementation identity.

2. **Bidirectional obligation.**  
   Forward intertwining `π ∘ T = T̄ ∘ π` is incomplete without a section `π ∘ σ = id` and `π ∘ Tⁿ ∘ σ = T̄ⁿ`.

3. **Declared-work factorization, not complexity-class collapse.**  
   GEMM instance: `W(qr,qs,k) = q² W(r,s,k)`, so `1024=4·256` gives exact `16×` Nat work reduction. Runtime is a separate object.

4. **Fail-closed publication.**  
   Lean `lean=false` is not publishable. Formal closure does not imply wall-clock.

5. **Family-local AGD collapse (FECU).**  
   Same declared observables + strictly less declared work + reconstruction. Explicitly *not* `P=NP`.

Article 10 of the constitution forbids inferring scientific novelty from architecture alone.

---

## 2. Profile scan — where Lean lives

| Repo | Role | Green Lean CI? |
|---|---|---|
| `batmeezy918/chronofold` | AGD / ChronoFold library (`src/Chronofold/*`) | **Yes** — CFPC Lean CI v2 `lake build` + no-sorry scan on `main` (incl. FECU, run 354 / merge 69a544f) |
| `batmeezy918/Speedup` | PCSS + isolated Lean kernels | **Partial** — GODS/ChronoFoldProof historically green (runs 30, 33). Later coupling files made `chronofold-lean4.yml` red on current `main` |
| `batmeezy918/OIC-Core-Calculus` | OIC kernel | **Yes** — `lean_verify.yml` and Lean Action CI success on `main` |
| `batmeezy918/Testsuite` | SNAP / Mathlib experiment | Not treated as green kernel corpus |
| Other 50+ repos | sensors, apps, empty scaffolds | No Lean kernel corpus |

Disabled / root-level ChronoFold files are **not** the production gate. The production gate is `src/Chronofold.lean` imports + `lake build`.

---

## 3. Green theorem registry

See INDEX.json for hashes. Attached kernel proofs live under `proofs/`.

ChronoFold production library (green): AgdCore, AgdClosure, AgdIterate, AgdBidirectional, AgdOperationalQuotient, AgdFecu, AgdRank, AgdMultiOmega, AgdClassGraph, AgdInvariantSafety, AgdUniversal, AgdFibreClosure, AgdMeasurement, AgdSicConstitutional, AgdMaximalConstitutionalOperationalClosure, AgdDerivedComputationalDomain, ConstitutionalKernelT0, Coqc*, CvrPhase0, AutoOmega, SIM2XR, EmvConstitution.

Speedup historically green kernels: GODSQuotientClosure, ChronoFoldProof, LinearQuotientProof, AGDGemmWork, AGDGemmProjection, AGDGemmReconstruction, AGDMaximallyTypedClaim, PCSSCertificate.

OIC green: Compose_assoc, IdOp units, derive_sound, bidirectional_closure, empty_corpus_always_boundary, elevation_requires_provenance, authorized_implies_provenance, rcc_coherent_implies_realized.

---

## 4. Benchmark scores (as recorded — not upgraded)

### Declared GEMM work model (formal Nat, not wall-clock)

| Quantity | Value | Status |
|---|---|---|
| W_full(1024,1024,1024) | 2,147,483,648 | proved |
| W_red(256,256,1024) | 134,217,728 | proved |
| ratio | 16 | proved |
| runtimeRatio 1596/100 vs work 16 | unequal | proved distinct |

### Official-COCO occurrence 2026-09-08T203000Z (surrogate, NOT cocoex)

| Function | CMA best_f | S6-AGD best_f | Winner | invariant_pass |
|---|---|---|---|---|
| sphere f001 | 80.882114 | 84.882100 | CMA | true |
| ellipsoid f002 | 5.568252 | 4,000,000.000006 | CMA | true |
| rastrigin f003 | 5.003124 | 7.979835 | CMA | true |

CMA won all three. S6 rejected 194/200 evals. Class: unofficial surrogate, not VERIFIED speedup.

HPL / SPEC / cuBLAS / MLPerf: targets only, no official captured SOTA result in-repo.
