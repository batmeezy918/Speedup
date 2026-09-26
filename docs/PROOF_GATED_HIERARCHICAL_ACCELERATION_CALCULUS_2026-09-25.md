# PROOF-GATED HIERARCHICAL ACCELERATION CALCULUS

**Artifact:** `docs/PROOF_GATED_HIERARCHICAL_ACCELERATION_CALCULUS_2026-09-25.md`
**Date:** 2026-09-25
**Branch:** `fix/lean4-green` @ `a051123`
**Status:** FORMAL-AND-EMPIRICAL-BOUNDED — every claim below is classified by
evidence strength; nothing is promoted beyond its certificate.

---

## 0. GOVERNING LAW

**CLAIM STRENGTH <= EVIDENCE STRENGTH.**

For every operator `O_i` in the hierarchy the only legally publishable statement is:

```
S_i = T_before_i / T_after_i          (same workload, same machine, same unit)
S_total = T_baseline / T_final         (authoritatively measured end-to-end)
```

- Layer speedups are multiplied **only** as a *conditional compositional bound*
  when the pair is explicitly certified composable (see Composition Matrix, §7).
- The product of isolated ratios is **never** a claim; it is a conjecture to be
  refuted computationally (`modeled_product_is_NOT_measured = true` everywhere).
- A theorem whose dependency graph contains axioms (`Quot.sound`, `propext`,
  `Classical.choice`, `native_decide`) is **not** called axiom-free.
- Empirical numbers are bound to the exact scenario, machine, and artifact hash
  in which they were measured. No universal applicability is assumed.

---

## 1. DECLARED GLOBAL OPERATOR CHAIN

Verification order is applied right-to-left:

```
psi_final = O_total psi_initial

O_total = T ∘ S ∘ M ∘ K ∘ E ∘ U ∘ R ∘ Q ∘ A
```

| # | Layer | Operator | Meaning | Primary certified payload |
|---|-------|----------|---------|---------------------------|
| 1 | ADMISSIBILITY | `A` | gate: claim admitted iff evidence law holds | PCSS.gate manifest, strict_gate.py fail-closed |
| 2 | QUOTIENT / STATE-SPACE | `Q` | quotient projection onto invariant subspace | matrix n=512 tile=16 → quotient 256:1, block-constancy |
| 3 | REPRESENTATIONAL EQUIVALENCE | `R` | section + reconstruction; reverse faithfulness | QMULT-02 14.9469x, AQGE-02 9.7841x |
| 4 | ALGORITHMIC (UNFOLDING) | `U` | quotient-path interpreter replaces barrier-expanded pipeline | unfold v2, median 485.7x |
| 5 | SIM2XR EQUIVALENCE-PRESERVING | `E` | equivalence-faithful kernel, exact decomposition | equivalence_faithful 18.886x |
| 6 | KERNEL | `K` | operator kernel in reduced coordinates | SIM2XR oracle merge 15.143x; AGD-GEMM 13.2075x |
| 7 | MICROKERNEL | `M` | packed/SIMD microkernel | C-cluster SIMD v6 8x8, 3.499x |
| 8 | SILICON | `S` | realized execution artifact on A78-class silicon | EMPIRICAL_SILICON_CLOSURE runs (NOT published) |
| 9 | TELEMETRY / PHYSICAL VALIDATION | `T` | physical validation probe | threadlock, SIC, ATD/QG, COCO (negative) |

**Reading discipline.** The chain is a *declared certification order*. Each
operator contributes a speedup `S_i` only in its own timing domain; the only
number that is legally published as an end-to-end speedup is the natively
measured `S_total`. Multiplicative composition across operators is permitted
only where §7 certifies the pair as composable.

---

## 2. INVENTORY A — ADMISSIBILITY OPERATOR `A`

| item | Entry |
|------|-------|
| Gate law | `PUBLISH := I ∧ R ∧ Q ∧ Q⁻¹ ∧ Ω ∧ X ∧ L` (PCSS strict gate, 7 gates) |
| Reference | `CONSTITUTION.md`, `CLAIM_POLICY.md`, `PROTOCOL.md`, `SPECIFICATIONS.md` |
| Enforcer | `publisher/strict_gate.py` (fail-closed; SHA256-verified sources) |
| Citation source | `evidence/ledger/claims.jsonl` — 31 lines, all valid |
| FORMAL status | Lean modules `PCSSCertificate.lean`, `PCSS.publishable` (0 axioms) |
| EMPIRICAL status | 2026-09-23..25 certificates all report `lean=true, publish=true`, 7 gates true |
| Precondition | artifact SHA256 matches on-disk evidence; certificate JSON schema valid |
| Postcondition | claim is admitted to `evidence/ledger/claims.jsonl` with hash-bound citation |
| Invariant preserved | CLAIM_STRENGTH <= EVIDENCE_STRENGTH |
| Known limitations | gate checks hash + presence, not semantic content of the claim text |
| Composability | operator with itself: `A∘A = A` (idempotent precondition gate; S=1, no speedup) |

---

## 3. INVENTORY B — QUOTIENT / STATE-SPACE REDUCTION `Q`

Domain: matrix `n=512`, tile `16`, block-constancy, `R^{512x512}`.

| item | Entry |
|------|-------|
| Certified artifacts | `verified/sim2xr/2026-09-23-qmult02/pcss_certificate.json` (14.9469x), `.../aqge02` (9.7841x), `.../agd` (13.2075x) |
| Lean grounding | `chronofold/ExactQuotientClosure.lean` (8 decl, **0 axioms**), `AGDGemmProjection.lean` (17 decl, 16 clean) |
| Key theorems | `AGD.projection_iterate` (0 axioms), `AGDGemmProjection.projection_iterate` (0 axioms), `AGDGemmProjection.projection_closure` (0 axioms) |
| Quotient ratio | 256:1 matrix-index reduction under block-constancy (512²/32²) |
| FORMAL status | projective quotient law holds axiom-free in `chronofold/ExactQuotientClosure.lean` |
| EMPIRICAL status | VERIFIED (certified, gate 7/7) — quotient gate `Q` true in all certs |
| Residual/error | quotient reconstruction closure max err ≈ 8.113e-14 (equivalence run) |
| Timing boundary | operator-level: wall-clock in reduced coordinates only |
| Benchmark config | scenario `qmult02-quotient-gemm-2026-09-23`; run `pcss-run-1790176150` |
| Provenance/hash | cert `dae687ae…` (qmult02); lean artifact `ba616dce…` (25-source core) |
| Composability | matrix↔matrix family: COMPOSABLE with `R` and `K` (trajectory_deepening, §7) |

---

## 4. INVENTORY C — REPRESENTATIONAL EQUIVALENCE `R`

| item | Entry |
|------|-------|
| Meaning | section `σ`, reconstruction `ζ`, reverse faithfulness `ζ∘σ = id` on reduced domain |
| Certified payload | QMULT-02 14.9469x; AQGE-02 9.7841x; AGD-GEMM 13.2075x |
| Lean grounding | `AGDGemmReconstruction.lean` — `section_injective` (0 ax), `section_is_right_inverse` [Quot.sound], `reconstruction_closure` [Quot.sound] |
| Repres. equivalence | `AGD.section_right_inverse` [Quot.sound]; `reconstructed_iterate` (0 ax) |
| FORMAL status | section right-inverse is proved under `Quot.sound` (standard quotient axiom — disclosed, not hidden) |
| EMPIRICAL status | VERIFIED; `R` gate true in all composed certificates |
| Residual/error | equivalence faithful: closure max 1.338e-12, task max 1.493e-12, unfold max 1.367e-15 |
| Timing boundary | one-time projection + reconstruction cost amortized over `≥k` operator steps (break-even k=0.642 for C1) |
| Composability | CP: `R ∘ Q` trajectory-deepening composable on matrix family (§7) |

---

## 5. INVENTORY D — ALGORITHMIC ACCELERATION (UNFOLDING) `U`

| item | Entry |
|------|-------|
| Meaning | `unfold_bench2.py` — quotient-path interpreter vs dense unpacked pipeline |
| Certified artifact | `verified/sim2xr/2026-09-25-unfold_bench2/pcss_certificate.json` — **485.714x** median |
| lean binding | `lean_hash` = `3ba56a0b…` (`evidence/lean4/lean_core_all_20260925.log`, 26 sources, pass) |
| Empirical detail | per-N medians: 2000→76x, 5000→150x, 10000→490x, 25000→830x, 50000→2891x |
| Performance evidence | run-dir: baseline median 34,000,000 ns vs candidate 70,000 ns → 485.71x |
| Invariant evidence | baseline_signature 39514, candidate_signature 3880; checks_avoided ≤ 39,514; obj_ratio ≤ 3,880 |
| FORMAL status | closure/equivalence language green; interpreter identity itself is EMPIRICAL (no Lean theorem of BFS interpreter equality — see Gap Ledger §9) |
| EMPIRICAL status | VERIFIED (gate 7/7), BFS_ok 3/3 seeds both sides |
| Flag (reconcile) | range "193x–7011x" **does not appear in any artifact**; certified range is 76x–2891x. Bound `E_new` accordingly. |
| Timing boundary | solve-time ratio, same N, both pipelines succeed |
| Composability | compiler pipeline is its own timing domain; must not be composed with matrix-family certs (§7 INCOMPATIBLE) |

---

## 6. INVENTORY E — SIM2XR EQUIVALENCE-PRESERVING ACCELERATION `E`

| item | Entry |
|------|-------|
| Meaning | gaussian-spectrally-separated equivalence-faithful decomposition |
| Certified artifact | `verified/sim2xr/2026-09-25-equivalence_faithful/pcss_certificate.json` — **18.886x** |
| Empirical detail | 122 scenarios, d ∈ {64..1024}, r ∈ {2,4,8}, 5 trials each, all PASS |
| Error bound | max err ≤ 1.493e-12 ≪ 1e-10 tolerance |
| Lean grounding | `SIM2xrEquivalenceClosure.lean` — 8 decl, **0 axioms** (newest closure module) |
| Kernel payload | SIM2XR oracle merge `verified/sim2xr/2026-09-23-sim2xr` — 15.143x |
| But | kernel median differs by domain; do not merge equivalences across d |
| FORMAL status | equivalence-faithful closure proved axiom-free for the closure law |
| EMPIRICAL status | VERIFIED (gate 7/7) |
| Audit-transcript note | 333/333 PASS at median ~63x / max ~5321x exists **only** in `/tmp/opencode/audit/equiv_faithful.pty.log` (d ≤ 2048). This is a reproducibility audit, **not** a published certificate — classify as REPRODUCED, not VERIFIED. |
| Composability | vector domain ↔ matrix domain: INCOMPATIBLE (no certified morphism, §7) |

---

## 7. INVENTORY F+G — KERNEL `K` AND MICROKERNEL `M`

| Kernel payload | source | speedup | status |
|----------------|--------|---------|--------|
| QMULT-02 quotient kernel | `verified/sim2xr/2026-09-23-qmult02` | 14.9469x | VERIFIED |
| AQGE-02 quotient kernel | `verified/sim2xr/2026-09-23-aqge02` | 9.7841x | VERIFIED |
| AGD-GEMM exact kernel | `verified/sim2xr/2026-09-23-agd` | 13.2075x | VERIFIED (README "5.02x" is stale; cert authoritative) |
| SIM2XR oracle merge | `verified/sim2xr/2026-09-23-sim2xr` | 15.143x | VERIFIED |
| 2026-09-15 kernel | `verified/sim2xr/2026-09-15` | 7.153x | VERIFIED |
| C-cluster SIMD v6 8x8 | `verified/sim2xr/2026-09-23-C` (= default dir, byte-identical) | 3.499x | VERIFIED |
| apollo-sc | `verified/sim2xr/2026-09-23-apollo-sc` | 3.263x | **REFUTED** — ledger line 16 quarantine: baseline/candidate identical SHA256; do not promote |
| AGD "6.26x" micro/SIMD | fans/silicon | — | **REFUTED** — no surviving certificate |

Lean grounding for `M`: `AGDGemmSpeedup.lean` — `speedup_stack_closure`
[propext + 9 native_decide]; `measured_runtime_is_not_a_work_theorem`
[native_decide] — explicitly keeps the work-model theorem distinct from a
runtime claim (design honesty, `AGDGemmSpeedup.measuredHundredths` etc.).

**Interaction factor law (measured, §8):**
- C1 (QMULT∘AQGE): S_cert = 22.1545x vs product 146.24x → I1=0.1515 (6.6x overclaim)
- C2 (3-way):         S_cert = 35.8222x vs product 1931.49x → I3=0.0186 (53.9x overclaim)
- `modeled_product_is_NOT_measured = true` — certified in `composition_certificate.json`.

---

## 8. INVENTORY H — SILICON REALIZATION `S`  (EMPIRICAL ONLY, NOT PUBLISHED)

From `evidence/final/2026-09-23/EMPIRICAL_SILICON_CLOSURE*` (aarch64 A78-class, all with `lean=false, publish_satisfied=false`):

| run | S_silicon | note |
|-----|-----------|------|
| QMULT S_SANDBOX | 19.99x @ N=1024 r=64 | battery 21/21 |
| AQGE S_native | 72.07x | native build |
| composed S | 69.41x | native |
| (AB)^6 stay-in-Q | 457.1x | telemetry of Q-reduced trajectory |
| SIM2XR pipeline | 18.66x | oracle-exact |
| SIM2XR single-shot construct-incl. | 0.73–0.83x | refuted construction-overhead claim |
| SIM2XR discovery-incl. | 0.02–0.18x | — |
| AGD E2E | 1.285–2.273x | modest, honest |
| AGD micro | 4.51x | SIMD-bound |

Classification: **REPRODUCED (empirical layer)**, never published. Former
"6.26x" and "apollo-sc 3.263x" silicon claims are REFUTED.

---

## 9. INVENTORY I — TELEMETRY / PHYSICAL VALIDATION `T`

| probe | result | classification |
|-------|--------|----------------|
| threadlock v4 | passed=30000, closure_rate 1.0, max_reconstruction_error 0.0 | VERIFIED (ledger line 21) |
| SIC ensemble | A recon 1.92e-16, Ainv 3.69e-16, E2−K2 4.485e-15, commutator 0.0; max_abs_R1 0.0 | REPRODUCED |
| ATD/QG | 110/110 pass, 20/20 negative controls, wall 2.08s (retained-residency ~1.05–1.31x) | **WORKBENCH-ONLY** (`/root/ATD_QG_MAXIMAL_RESULTS`, NOT in repo; no ledger entry) |
| COCO occurrence 2026-09-08T203000Z | s6_mean_best_f 1,333,364 vs cma 30.48; counts CMA_ONLY=3, S6_ONLY=0 | **NEGATIVE** — S6 does not beat CMA; surrogate-only (`NOT cocoex`), publication gate remains cocoex 2.8.2 |
| nonlinear eod v5 | 120 rows PASS, max err 0.0269942 < EPS 0.05 | VERIFIED-row; **flag:** ledger note says "121/121" but machine claims `gates:120` — internal inconsistency, machine value 120 is authoritative |

---

## 10. INVENTORY J — FORMAL LEAN MODULE INVENTORY (26 sources, `a051123`)

Fresh axiom dump of every declaration (`lake env lean` per module, `#print axioms`, logged at `evidence/lean4/lean_core_axiom_dump_20260925.log`; full output in `lean4`).

| module | decls | clean | axiomatic |
|--------|------:|------:|----------:|
| AGDGemmProjection | 17 | 16 | 1 |
| AGDGemmReconstruction | 9 | 6 | 3 |
| AGDGemmSpeedup | 7 | 2 | 5 |
| AGDGemmWork | 21 | 5 | 16 |
| AGD (MaximallyTypedClaim) | 48 | 31 | 17 |
| GODSQuotientClosure | 40 | 19 | 21 |
| HPL_AGD_01_Obligations | 12 | 3 | 9 |
| PCSSCertificate | 6 | 6 | 0 |
| ProvenAgd/AGDTheoremSeries | 31 | 30 | 1 |
| ProvenAgd/ConstitutionalKernel | 27 | 27 | 0 |
| ProvenAgd/CorrectByConstructionSearch | 11 | 11 | 0 |
| SIM2xrEquivalenceClosure | 8 | 8 | 0 |
| SpeedupExactInvariant | 4 | 4 | 0 |
| chronofold/ChronoFoldProof | 13 | 13 | 0 |
| chronofold/ExactQuotientClosure | 8 | 8 | 0 |
| chronofold/GODSQuotientClosure | 22 | 11 | 11 |
| chronofold/LinearQuotientProof | 12 | 12 | 0 |
| chronofold/ProgressTargetCoupling | 12 | 10 | 2 |
| chronofold/WeakCouplingBound | 3 | 1 | 2 |
| linear/LinearQuotientProof | 12 | 12 | 0 |
| scaffolding/PCSSCertificate | 5 | 5 | 0 |
| workflow_isolation/MaximalPreLean | 12 | 12 | 0 |
| LeanSpeedup / SpeedupLean / scratch | 0-6 decl | — | — |

**Totals: 340 declarations inventoried; 252 axiom-free, 88 with disclosed
axiom dependencies.**

Axiom set appearing across the core (all standard Lean kernel constants —
none are `sorry`/`admit`; toolchain `leanprover/lean4:v4.29.0`):
`Quot.sound`, `propext`, `Classical.choice`, `native_decide` (`ax_1`, `ax_1_1`).

Note: theorem set described as "206 across 28 files" in earlier scratch notes
was a count of theorem/lemma keywords; the declaration-level dump (340) is the
authoritative inventory here.

---

## 11. INVENTORY K — CERTIFICATE / PROVENANCE INVENTORY

| artifact dir | cert speedup | hash anchor | gate | status |
|--------------|-------------|-------------|------|--------|
| verified/sim2xr/2026-09-25-equivalence_faithful | 18.886x | lean 3ba56a0b… | 7/7 | VERIFIED |
| verified/sim2xr/2026-09-25-unfold_bench2 | 485.714x | lean 3ba56a0b… | 7/7 | VERIFIED |
| verified/sim2xr/2026-09-23-qmult02 | 14.9469x | lean ba616dce… | 7/7 | VERIFIED |
| verified/sim2xr/2026-09-23-aqge02 | 9.7841x | lean ba616dce… | 7/7 | VERIFIED |
| verified/sim2xr/2026-09-23-agd | 13.2075x | lean ba616dce… | 7/7 | VERIFIED |
| verified/sim2xr/2026-09-23-sim2xr | 15.143x | lean ba616dce… | 7/7 | VERIFIED |
| verified/sim2xr/2026-09-23-C (+ default, byte-identical) | 3.499x | — | 7/7 | VERIFIED |
| verified/sim2xr/2026-09-15 | 7.153x | — | 7/7 | VERIFIED |
| verified/sim2xr/2026-09-08 | CLAIM + witness (no lean) | — | lean=false | STRONG_LOCAL (not published) |
| verified/composition/2026-09-23/C1 | 22.1545x | interaction 0.1515 | 7/7 | VERIFIED |
| verified/composition/2026-09-23/C2 | 35.8222x | interaction 0.0186 | 7/7 | VERIFIED |

Lean lane: 25-source core hash `ba616dce…` (2026-09-23 certs), 26-source core
hash `3ba56a0b…` (2026-09-25 certs). CI green at `a051123`: Lean4
Verification (chronofold), Lean 4 Verification (`LEAN4_CORE_ALL_PASS=1`),
Proof-Gated Speedup, Official COCO (not cocoex).

---

## 12. INVENTORY L — COMPOSITION MATRIX (certified pairs only)

Source: `evidence/composition/2026-09-23/composition_matrix.csv` (7 rows) + interaction facts.

| A | B | class | composition_type | evidence |
|---|---|-------|------------------|----------|
| QMULT-02 | AQGE-02 | COMPOSABLE | trajectory_deepening (same Tbar, stay-in-Q 8+6=14 steps, single Q+R) | C1 = 22.1545x |
| QMULT-02 | AGD-GEMM | COMPOSABLE | trajectory_deepening (16 steps) | C2 family |
| AQGE-02 | AGD-GEMM | COMPOSABLE | trajectory_deepening (14 steps) | C2 family |
| QMULT-02 | SIM2XR | INCOMPATIBLE | representation_mismatch matrix↔vector; no certified morphism | — |
| AQGE-02 | SIM2XR | INCOMPATIBLE | same | — |
| AGD-GEMM | SIM2XR | INCOMPATIBLE | same | — |
| SIM2XR | QMULT-02 | INCOMPATIBLE | same | — |

**Composition discipline:**
- Composable pairs fuse into a single operator `O_C = σ ∘ Tbar^n ∘ π` with *one*
  projection and *one* reconstruction; speedup is the **native measurement**
  (22.1545x / 35.8222x), never the product (146.24x / 1931.49x).
- Cross-domain (matrix↔vector, matrix↔compiler) speedups are **never** added,
  multiplied, or fused. `S_total` is only the natively measured end-to-end ratio.

---

## 13. INVENTORY M — REFUTATIONS / NEGATIVES (must be preserved)

1. **[apollo-sc 3.263x]** REFUTED — `evidence/ledger/claims.jsonl` line 16:
   baseline and candidate traces are SHA256-identical.
2. **[AGD 6.26x]** REFUTED — no surviving certificate; silicon closure shows
   honest AGD E2E 1.285–2.273x.
3. **[SIM2XR single-shot construction]** REFUTED — 0.73–0.83x (slower).
4. **[COCO]** NEGATIVE — S6 loses to CMA on surrogate (`NOT cocoex`).
5. **[product composition]** REFUTED as claims — interaction 0.1515 / 0.0186,
   6.6x and 53.9x overclaim vs products.
6. **[unfold "193x–7011x"]** NOT FOUND — certified range 76x–2891x.
7. **[agile "121/121"]** flag — machine value 120.

---

## 14. INVENTORY N — GAP LEDGER `E_new → H → Lean → T_new`

Every empirically-only or refuted claim is assigned a repair path to a formal
hypothesis `H`, a Lean obligation, and a target telemetry gate `T_new`.

| E_new (claim) | status | H (hypothesis) | Lean obligation | T_new (gate) |
|---------------|--------|----------------|-----------------|--------------|
| unfold v2 485.7x | VERIFIED(emp) | quotient-path interpreter ≡ dense pipeline on all N | `interpreter_identity`: ∀N steps, quotient BFS result equals dense result | BFS_ok both sides at N=100000 |
| equivalence 333/333 @ max 5321x | REPRODUCED(audit) | 63x median extends to d≤2048 | `SIM2xR.equivalence_closure_high_dim`: closure at d>1024 | publish a d≤2048 certificate |
| nonlinear eod "121/121" | VERIFIED(120) | exactly 120 gate-constrained systems | reconcile note vs machine value | single-source count field |
| ATD/QG 110/110 | WORKBENCH | retained-residency holds on repo CI host | repackage + hash into verified/ | repo-host rerun battery 21/21 |
| SIM2XR oracle 15.143x | VERIFIED | kernel median domain-stable | `equivalence_kernel_closure` over r∈{8} | publish oracle merge cert at d≤512 |
| COCO S6 | NEGATIVE | no complexity-collapse claim from S6 | none (suppressed) | gate: cocoex 2.8.2 real function set |
| silicon S runs | REPRODUCED | silicon realization matches model | `silicon_closure_formal`: silicon S ≤ model S bounds | publish on native build after gates |
| composed C1/C2 | VERIFIED | interaction <1 quantified | trajectory-deepening lemma for ≥2 steps | keep x overclaim < 2 on future stacks |

---

## 15. `psi_final` — CLOSED-FORM SUMMARY

Applying the discipline of §0–§1 to the verified portfolio:

```
psi_final = (T ∘ S ∘ M ∘ K ∘ E ∘ U ∘ R ∘ Q ∘ A) psi_initial
```

The **only** legally composed, certified end-to-end result in the matrix
domain is the trajectory-deepened quotient stack:

```
S_total(matrix, QMULT∘AQGE∘AGD) = C2 = 35.8222x        (native, 7/7 gates)
S_total(matrix, QMULT∘AQGE)      = C1 = 22.1545x        (native, 7/7 gates)
S_total(component) = {14.9469, 9.7841, 13.2075, 15.143}x  (isolated, certified)
S_total(SIM2XR kernel median)    = 18.886x              (vector domain)
S_total(unfold v2 median)        = 485.7x               (compiler domain)
```

Product bounds are **conditional and supressed**: e.g. `14.95×9.78×13.21 =
1931.49x` is refuted (measured 35.82x, interaction 0.0186). No cross-domain
number is claimable. The "complexity collapse" claim is therefore scoped to
the trajectory-deepening matrix family and is **measured, not multiplied**.

---

## 16. REPRODUCTION COMMANDS (from clean worktree)

```bash
# Lean toolchain
elan default leanprover/lean4:v4.29.0

# Full Lean core verification (26 sources) — same lane as CI "Lean 4 Verification"
cd lean4 && lake build
bash ../scripts/verify_lean4_all.sh lean4

# Axiom inventory (module-granular, as used to produce this artifact)
export LEAN_PATH="$PWD/.lake/build/lib/lean:$PWD"
for f in <module>.lean; do lake env lean "$f"; done   # #print axioms per module

# Certified scenario reruns (run-dirs hold scenario.json)
python3 sim2xr_equivalence_faithful_runner.py --config evidence/runs/chronicle-2026-09-25/equivalence_faithful_gaussian/scenario.json
python3 unfold_bench2.py --config evidence/runs/chronicle-2026-09-25/unfold_bench2/scenario.json

# Publication gate (fail-closed) and ledger append
python3 scripts/compose_certificate.py --manifest <verified-dir>    # relocatable verified dir
python3 publisher/strict_gate.py --verify <certificate.json>        # 7 gates, SHA256-bound
```

All certificates cited above are on branch `fix/lean4-green` @ `a051123`
(even if a header above, e.g. 25-source core hash, predates it).

---

_Governing law restated: CLAIM STRENGTH <= EVIDENCE STRENGTH applies to this
document itself. Where an empirical number cited in a prior brief diverges from
a certificate (e.g. README "2.5x/5.02x" vs certs 14.95x/13.21x), the certificate
is authoritative and the divergence is flagged, never silently corrected._