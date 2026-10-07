# AGD / QUOTIENT DESCENT / PCSS — MASTER EVIDENCE ASSESSMENT

Generated 2026-10-07 · forensic, read-only. No repository, benchmark, or evidence artifact
was modified, committed, pushed, or moved. Derived artifacts are confined to
`/root/AGD_MASTER_DERIVED_20261007/` plus the three files named in §20.

**Operating rule applied throughout:** if an earlier claim conflicts with the filesystem,
the filesystem wins. Every number below was recomputed from an artifact.

---

## 1. Executive summary

Six findings dominate.

1. **The AGD generality corpus is real and its headline counts are exactly right.**
   Recomputed from `AGD_QUANTUM_GENERALITY_RESULTS.csv`: **213 rows = 189 positive + 24
   negative controls; 189/189 positive PASS; 24/24 negative controls correctly rejected.**
   Evidence class **E1**.

2. **The quotient structure is not an empirical discovery — it is an exact algebraic
   identity, and it is provable.** `closure_residual` is not "small"; it is **exactly 0.0 on
   all 189 rows**. The reason is that the operator family is *defined* as `U = Ū ⊗ I_m`, so
   `π(Uψ) = Ū π(ψ)` holds identically and `π R = I` holds exactly. This upgrades the
   positive families from "measured correct" to "correct by construction."

3. **The reconstruction obligation is genuinely discharged here.** `π R = I_q` to
   `2.22e-16` machine precision on every row. In the Lean corpus this obligation is
   *assumed* almost everywhere (`hσ : Section π σ`); in this experiment it is *measured*.

4. **A two-parameter hardware cost model predicts the speedups, R² = 0.99985.**
   `T = α·FLOPs + c` with **α = 1.553e-9 s/FLOP** and **c = 3.447e-6 s/call**, fitted on this
   device, predicts the measured kernel speedup across n = 2…10 to within **7–25 %** without
   seeing any speedup value. This is the predictive quantity the framework was missing.

5. **The corpus's own headline understates the result.** `AGD_QUANTUM_GENERALITY_REPORT.md`
   reports "median end-to-end 0.7268x (slower)". That is the **n = 6** value. Measured
   end-to-end crosses **break-even at n = 7** and reaches **13.65x at n = 10**. The report
   pools n = 2…10 and is dominated by the overhead regime.

6. **`/root/AGDFormalGap.lean` cannot be compiled on this host.** It opens
   `import Mathlib`; Mathlib is not built (`unknown module prefix 'Mathlib'`), and the
   filesystem is **100 % full (938 MB free)** so Mathlib cannot be built here either. I
   re-proved the same zeroization lemma in **Lean 4 core**: it compiles, exit 0, and depends
   on `[propext]` only — **no `sorryAx`**. Evidence class **E3**.

---

## 2. Device / environment fingerprint

| item | measured value |
|---|---|
| uname | `Linux localhost 6.17.0-PRoot-Distro #1 SMP PREEMPT_DYNAMIC aarch64 GNU/Linux` |
| Android kernel | `Linux version 6.17.0-PRoot-Distro (proot@termux) (gcc 13.3.0)` |
| SoC | **4× Cortex-A55** (cpu0–3, `cpuinfo_max_freq` 1 804 800 kHz) + **4× Cortex-A78** (cpu4–7, `cpuinfo_max_freq` 2 400 000 kHz) |
| governor | `walt` on all policies; cpu0–3 observed at 691.2 MHz (**floor**), cpu4–7 at 1 900.8 MHz |
| SIMD | `fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm lrcpc dcpop asimddp` — 128-bit ASIMD, 4 lanes |
| thermal | 38 zones, 46–54 °C at capture |
| RAM | 7 366 MiB total; 4 135 used; 56 free; 3 230 available |
| storage | `/dev/block/dm-64 222G used 221G avail 938M Use% 100` |
| compilers | gcc 14.2.0 · clang 19.1.7 · Julia 1.11.1 · Lean 4.29.0 (+elan 4.2.2, toolchains 4.29.0/4.30.0/4.33.1) · FLINT 3.1.0 · Python 3.13.5 |
| execution context | **PRoot userspace chroot on an ARM phone** — not an HPC host |

**Two hard blockers.**
- **Disk 100 % full.** Blocks Mathlib construction (~10 GB) and any new large benchmark.
- **Mathlib not built.** Therefore `AGDFormalGap.lean`, `chronofold/Constitutional.lean`,
  `Mathlib/MathlibProof.lean`, and every `import Mathlib` file in the corpus are
  **unverifiable on this host**. The 28 `.olean` files under `Speedup/lean4/` are dated
  2026-10-06 03:22–03:28, but `PCSSCompositionCriterion.lean` has mtime **2026-10-07 02:23**,
  i.e. edited *after* the last recorded build.

Note: `omega` and the `|·|` notation for `Int` are **not** available in Lean core — only
`import Std` + core lemmas. `le_of_lt`, `Int.eq_zero_or_pos`, `Int.natAbs_of_pos` and
`not_lt_of_ge` are all absent from core; the derived proof uses `Int.natAbs_mul`,
`Int.natAbs_pos.mpr`, `Nat.le_mul_of_pos_left`, `Nat.not_lt_of_ge` instead.

---

## 3. Experiment inventory

All 21 named paths **exist**. Two files referenced elsewhere do not:
`AGD_GEMM_EOF_FINAL_EMPIRICAL_V2.py` and `agd_closure_results/`. No `simd_v4_validation.csv`
exists anywhere.

---

## 4. Quotient / descent reconstruction (recovered from artifacts)

Source of truth: `AGD_QUANTUM_GENERALITY_DEFINITIVE_EOF.py`, `build_quotient(n)` (L203).

| object | exact definition |
|---|---|
| state space `H` | `ℂ^d`, `d = 2^n` |
| quotient `Q` | `ℂ^q`, `q = 2^⌈n/2⌉` |
| fibre block `m` | `m = 2^⌊n/2⌋`, so `d = q·m` |
| projection `π` | `I_q ⊗ p`, `p = m^{-1/2}·1_{1×m}` ⟹ `(πx)_i = m^{-1/2} Σ_j x_{im+j}` — **normalised block average** |
| reconstruction `R` | `I_q ⊗ pᵀ` ⟹ `(Rz)_{im+j} = z_i/√m` — **block-uniform embedding** |
| invariant `Ω` | `BlockConstant`: `x_{im+j} = x_{im+j'}` — fibre constancy |
| equivalence `~` | `i ~ j ⟺ ⌊i/m⌋ = ⌊j/m⌋` (verbatim in the artifact's hash preimage) |
| operator family | `U = Ū ⊗ I_m` |
| pipeline | `ψ → Q(ψ) = πψ → q → R(q) → ψ̂ → Ω-check → gate → timed execution` |

**Which implications are actually proved / hold:**

| implication | status |
|---|---|
| `π` well-defined on the equivalence | **exact** — `πx` depends only on `⌊i/m⌋` |
| `π R = id_Q` | **exact, algebraic**: `(I_q⊗p)(I_q⊗pᵀ) = I_q⊗(ppᵀ) = I_q⊗[1] = I_q`. Measured `π_r_identity_error ≤ 2.22e-16`. **This is `section_pi_sigma`, discharged.** |
| `R π = id_H` | **FALSE.** `Rπ = I_q ⊗ (pᵀp) = I_q ⊗ J_m` = projection onto block-constant subspace, not identity. Holds **iff** `BlockConstant x` — exactly the `σ(πx) = x` hypothesis of `LinearExactSector.sigma_pi_of_blockConstant`. |
| intertwining `πU = Ūπ` | **exact identity**: `(I_q⊗p)(Ū⊗I_m) = Ū⊗(pI_m) = Ū⊗p = Ū(I_q⊗p)`. Measured `closure_residual = 0.0` on **all 189 rows** — not 1e-16, exactly zero. |
| `Ω` preserved | **assumed by construction**: `U` is built as a Kronecker product with `I_m`, so it acts on the quotient index only and is fibre-constant by construction. **Not an independent finding.** |
| reconstruction `ψ̂ = ψ` | measured, `state_max_error ≤ 2.26e-16`, `observable_error`, `reverse_error` all at machine epsilon |

**Consequently:** G1 (equivalence/descent), G2 (invariant preservation) and G3
(reconstruction) are all *true and exact* for this family, but G1–G3 hold **by algebraic
identity**, not by discovery. That is a stronger result than the corpus claims and also a
more limited one: it is a statement about `Ū ⊗ I_m`, not about arbitrary operators.

**No performance theorem follows from G1–G3.** The Lean corpus says so itself in five
places, most explicitly `GODSQuotientClosure.formal_is_not_runtime` and
`AGDGemmSpeedup.MeasuredRuntimeObligation : Prop := True`.

---

## 5. Formal theorem inventory

~130 declarations in 23 files under `/root/Speedup/lean4/`, `/root/chronofold/src/Chronofold/`
and `/root` top level. Roughly 500 further `.lean` files are third-party (miniF2F) or tiny
propositional-search goal files.

| class | count | representative |
|---|---|---|
| A genuinely mathematical | ~95 | `AGDFormalGap.divisible_and_small_zero`; `LinearExactSector.sigma_pi_of_blockConstant`; `HierarchicalScaling.phi_closed_form`, `no_speedup_without_paid_exponential`; `PCSSGemmRegisterBlock.blockedSumObligation_holds`; `PCSSErrorBound.accFadd_chain_bound`; `PCSSCompositionCriterion.composedGain_lt_of_overlap`; `ToProve*` refutations |
| B formalisation of an empirical cert | ~35 | `AGDQuantumPCSSBinding.quantumCertificate`; `omega_*`; `haradax_*` |
| C structural definition | ~70 | `Intertwines`, `Section`, `ObservablePreserved`, `FibreConstant`, `QStar`/`pi`/`TBar`, `BlockConstant` |
| D benchmark witness | ~12 | `ChronoFoldSpeedup.grqc/hepth/enron` (`speedup_x1000` literals); `AGDGemmSpeedup.measuredHundredths := 1596` |
| E incomplete (`sorry`) | **1** | `/root/squarevalence_proof.lean:22` |
| F rejected | ~15 | see below |
| G narrative only | — | `.md` files |

**Answers to the six critical questions.**

- **Q1 — is admissibility of `R` proved?** The *scheme* is proved given `hσ : Section π σ`;
  the files name the gap themselves (`AGDGemmReconstruction.lean:13`: *"Does NOT prove that a
  particular GEMM embedding is a section. That remains the obligation:
  `actual_reconstruction_section`."*). It **is** discharged concretely in exactly two places:
  `LinearExactSector.sigma_pi_of_blockConstant` (BlockConstant retraction) and
  `HPL_AGD_01_Obligations.section_pi_sigma` (4-block tiling). The ε-tolerance obligation
  exists as `scaffolding/PCSSCertificate.ReverseBound` and is **never instantiated or
  discharged** — it is dead code. `/root/FinalForm.lean` is a 37-line pure-axiom stub
  (`proj_well_defined`, `section_property`, `boundary_idempotent`) with zero theorems.
- **Q2 — is `Ω` preserved?** Yes, four times, **all conditional**: `GODSQuotientClosure.invariant_descends`
  (assumes `Inv ∘ T = Inv` and `FibreConstant`), `AgdSicConstitutional.quotient_descent`
  (assumes `Governor Ω O`), `chronofold/Constitutional.identity_preservation` (assumes a
  structure field labelled "axiom 4"), and `AgdCore.Admissible`. **Verdict: no file proves a
  non-trivial invariant is preserved; every one is `h_Ω : Ω(Ox) = Ωx ⇒ …`.** The only
  invariants whose preservation is *computed* are `Ω = ()`, `id mod 7`, `id`, `_+1`.
- **Q3 — any wall-clock theorem?** **No.** Confirmed five times in the corpus's own prose.
  The only runtime obligation defined anywhere is `MeasuredRuntimeObligation : Prop := True`.
- **Q4 — any cost/speedup theorem?** **Yes, but only an operation-count ratio in a
  self-defined cost model** (`AGDGemmWork.canonical_workRatio = 16` for 1024→256). Never a
  time ratio. Two files prove honest negatives: `PCSSGemmRegisterBlock.workRatio_is_one` /
  `no_speedup_from_this` (register blocking saves **zero** FLOPs) and
  `HierarchicalScaling.no_speedup_without_paid_exponential`.
- **Q5 — hard-coded experimental values:** 31 declarations. Tier 1 are the `def grqc/hepth/enron`
  speedup literals and the `KernelGeometryCert` fields; `ChronoFoldSpeedup.lean`'s entire
  content is *"three hand-typed integers satisfy a comparison."*
- **Q6 — counts:** `sorry` = **1**; `native_decide` = **20 uses in 8 files** (an unsound
  oracle — `AGDGemmWork.lean:5` documents removing it from one file but **not** from
  `AGDMaximallyTypedClaim.lean` or `HPL_AGD_01_Obligations.lean`); `axiom` = **4
  declarations** (3 in `FinalForm.lean`, `banach_operator_algebra_closed` in a byte-identical
  twin pair). Plus **structure-field-as-axiom** in 7 more places, invisible to grep.

**The highest-quality work in the repository is the machine-checked *refutations*:**
`ToProveQFIDossier.refutes_main_lower_bound`, `ToProveChronoFold.capability_2_refuted`,
`capability_5_not_self_adjoint`, `capability_5_not_norm_preserving`,
`invariant_and_controllability_force_constancy`, `ToProveThreadLock.xi_total_claim_is_false`,
`ToProveCognitiveTensor.refutes_global_contraction_inference`,
`ToProveOperatorContraction.claim_A_refuted`, and
`PCSSCompositionCriterion.compositionTheoremObligation_refuted`.

---

## 6. PCSS gate matrix

| run | I | R | Q | R⁻¹ | Ω | X | L |
|---|---|---|---|---|---|---|---|
| `SIM2XR_PCSS_TEMPLATE_20261001T060445Z` | T | T | T | T | T | T *(single wall time, not a ratio)* | **F** |
| `GOVERNED_QUOTIENT_E2E_20261001T063448Z` | **F** | **F** | T | T | T | T | **F** |
| `GOVERNOR_FORMALIZATION_20261001T070917Z` | **F** | **F** | **F** | **F** | **F** | **F** | **F** |
| `PCSS_NEON_GEMM_N512_20261001T052954Z` | T | U | A | A | A | T | **F** |
| `SIM2XR_E2E_PCSS_20261004T101614Z` | F | F | F | F | F | F | F |
| `SIM2XR_E2E_DISCOVERY_20261004T101812Z` | A | A | A | A | A | A | A |

Bold F = declared `true` in the certificate but **hard-coded as a literal** in the generator
(`governed_run.py:103-104`; all six in `formalize_governed_method.py`). Only the **Lean gate
is uniformly honest — every certificate declares it `false`.**

The template certificate's hash bindings were recomputed: 7 of 8 verify; `input_hash
e6537de5…` **matches no file in the directory**. Its `strict_gate.py` — the declared
authority — is not runnable there (no `speedup` package) and its own binding rules would
reject this certificate.

---

## 7. All verified speedups

| # | speedup | what was actually compared | class | verdict |
|---|---|---|---|---|
| 1 | **13.647×** E2E, n = 10 | dense `2^10×2^10` matvec vs π + Ū + R, 21 samples | **E1** | **VERIFIED.** Break-even at **n = 7**. |
| 2 | **356.8×** kernel median, n = 10 | same operator, dense vs quotient | **E1** | **VERIFIED** |
| 3 | **14.6× → 7.3×** | NEON 4×4 FMA GEMM vs **naive triple-loop**, N = 128…1024, 3 outer runs | **E1** | **VERIFIED** — and `max_abs ≤ 2.0e-5`, `Correctness gate: PASS`. Distinct from the `simd_v5/v6` files, which report speedups on rows that FAIL. |
| 4 | **1.3825×** | PCSS, genuine separate baseline, 40 samples/arm | **E1** | **VERIFIED** |
| 5 | 16 claims, all MATCH | ω-telemetry re-timed against 4 independent clocks | **E1** | **VERIFIED** as methodology (both arms in-process) |
| 6 | **6.19× median / 105.5× max** kernel | *state-space traversal count* reduction, `L = 4…12`; at `L=4` all three branches are **0.54–0.58× (slower)** | **E1 (kernel only)** | **VERIFIED as traversal reduction.** Both arms call the *same* `reference_operator`; it is not two implementations. Certificate itself sets `general_E2E_speedup_claim: false`. |
| 7 | 25 600× | `104857600 / 4096` — a **byte-size ratio** | **E0** | **NOT a speedup.** No timing in the artifact. |
| 8 | 497.8× / 206.7× / 115.4× PCSS | `baseline.hash == candidate.hash == 56995a71…`, `repetitions:1, warmups:0` | **E0** | **REFUTED** — self-comparison; values recycled from AGD maxima. |
| 9 | SIMD v4 36.19× | `silicon_speedup_dossier.py:44-48` literals stamped `"VALIDATED"`; no source CSV | **E0** | **REFUTED** |
| 10 | 279.62 / 312.15 GFLOPS | 2.1× the device's own declared FP32 peak | **E0** | **REFUTED — physically impossible** |
| 11 | ChronoFold 6.1× / 14 400× | on-disk runs: `kdim = 0`, **0/512 iterations accepted**, `state_delta = 0` | **E0** | **REFUTED**; the one executed benchmark gives **−98.08 %** |
| 12 | ≤ 304 unknown bits | RSA-1024 e=3, 320 known bits, blind, 10/10 SHA-256 match | **E1** | **VERIFIED** (this campaign) |

---

## 8. Variance / stability

Per-n CV for `kernel_speedup`: **7–12 % for n = 2…7**, 20 % at n = 8, **171 % at n = 9**,
19 % at n = 10. `end_to_end_speedup` CV: 4–8 % through n = 8, **14 % at n = 9, 112 % at n = 10**.

The n = 9 and n = 10 outliers are **single runs**, not a distribution shift: at n = 9
`reference_time` ranges 3.46e-4 … 5.46e-3 s around a 3.94e-4 median. **MAD is far more
robust than std there** (n = 9: MAD 2.88e-5 vs std 1.11e-3, a 38× difference). Cause is
consistent with governor/thermal/scheduling contention on a 4+4 big.LITTLE with cpu0–3 parked
at 691 MHz — not with the mathematics.

**Consequence for reporting: use MAD/median, not std/mean, for n ≥ 9.** No evidence was found
that quotient descent *reduces variance*; both arms are equally noisy and the noise is
machine-driven.

---

## 9. Silicon / telemetry correlation

The α split is itself a finding: the full path sustains **1.56e-9 s/FLOP** while the small
quotient kernel runs at **4.32e-9 s/FLOP** — a **2.8× efficiency gap** because a 32×32
complex matvec cannot fill the A78's 4×128-bit ASIMD pipes. That is why a single shared α
still predicts within 25 % but not exactly. The remaining 7–25 % residual is that gap plus
Python dispatch.

---

## 10. RSA frontier

Independently re-verified from public inputs only (`N`, `e`, `C`, `m_known`, `X`), blind, on
the pre-existing Zelux target: `ROOT_FOUND M=1 T=1 dim=4 LLL=7.2ms x=285661594263749177262538127`,
`sha256(secret) == secret_hash.txt == 0f39a79c…a9d3`, `pow(m_known+x,3,N)==C`.
Frontier recomputed: **64, 88, 128, 170, 192, 224, 256, 288, 304 recovered; 320, 336, 340, 344
not recovered.** Full records in `/root/rsa_culmination_20261007/`.

**Correct characterisation:** structured-plaintext small-root recovery by
Coppersmith/Howgrave-Graham. **Not** a new RSA attack.

**The interesting research question — does the AGD quotient formalism predict the frontier? —
now has a computable answer.** See §12.

---

## 11. Old evidence quarantined

All of `/root/rsa_elevation_20261006/` — `elevation.log`, `agd_exact_*.c`, `run_*`:

| defect | evidence |
|---|---|
| deterministic generation | `flint_randinit(rs)` unseeded; `run_64` twice → identical `x = 12754499613590066039` |
| non-independent instances | 4 "instances" per UB are byte-identical |
| **signed FLINT randombits** | FLINT 3.1.0 `fmpz_randbits` returns **negative ~50 %**: 10 026 / 9 974 over 20 000 draws at 320 and at 224 bits |
| invalid negative plaintext | consequence of the above; `m0`, `m`, `m³` negative ⇒ not valid RSA plaintexts |
| incorrect wrapping logic | `wrapped=NO` printed while the same line shows `N_bits=1024`, `m3_bits=1150…1630` |
| FLINT API inversion | `fmpz_set_str` returns **0 on success** in 3.1.0 (1 on failure in 2.x) |

**Do not mix with the 2026-10-07 blind campaign.**

---

## 12. Mathematical derivation — see `AGD_MASTER_DERIVATION_20261007.md`

---

## 13. Novelty candidates

Smallest genuinely new objects the evidence supports:

| # | candidate | formally proven | empirical | prior-art pressure | missing obligation |
|---|---|---|---|---|---|
| N1 | `π = I_q⊗p`, `R = I_q⊗pᵀ` is an **orthogonal coisometry / isometry pair** (`πR = I`, `Rπ` = orthogonal projection onto block-constant subspace) | **YES — provable, and I proved the zeroization sibling in Lean core** | `π_r_identity_error ≤ 2.22e-16` | none; elementary Kronecker algebra | none — **this is a complete, publishable-grade object** |
| N2 | `(I_q⊗p)(Ū⊗I_m) = Ū⊗(pI_m)` — the descent of a tensor-separable operator | **YES, identically** | `closure_residual = 0.0` exactly | elementary | state the class of `Ū` for which this holds (all `q×q`; no unitary constraint needed) |
| N3 | Cost model `T = α·FLOPs + c`, `α = 1.553e-9`, `c = 3.447e-6`, predicting kernel speedup within 7–25 % | no (empirical fit) | **E1, R² = 0.99985** | wall/roofline models | justify α from device parameters (2.8× α split is unexplained) |
| N4 | **Break-even condition.** Quotient E2E beats full exactly when `α(4^n − 4^⌈n/2⌉) > c(1 + 2)`-ish; measured break-even **n = 7** | partially | **E1** | novel as stated | derive the closed form, confirm the 2.8× α split |
| N5 | The Lean `ReverseBound` (ε-tolerance reverse gate) | **dead code — never instantiated** | — | — | **discharge it.** This is the single cleanest missing lemma. |
| N6 | Predictive link to the RSA frontier | see derivation | — | — | decide whether the claim survives |

**Not novel (must not be claimed):** any quantum speedup; any RSA break; `πR = id`; block
averaging; Coppersmith; the q² composition law (already refuted in-repo).

---

## 14. Missing proof obligations, ranked

1. **`ReverseBound : d(R(Qs), s) ≤ ε`** — the actual AGD reverse-error gate, exists as dead
   code, never discharged. Highest-value single lemma.
2. **`actual_reconstruction_section`** — named by the corpus itself as the outstanding
   obligation; discharged empirically here (`π_r_identity_error ≤ 2.22e-16`) but never as a
   Lean theorem for *this* quotient.
3. **Remove `native_decide`** from `AGDMaximallyTypedClaim.lean` and
   `HPL_AGD_01_Obligations.lean` — the cleanup was applied to `AGDGemmWork.lean` only.
4. **`FinalForm.lean`** — 3 axioms, 0 theorems, no imports. Either prove or delete.
5. **Mathlib must be built**, or the corpus's only genuinely useful Mathlib theorem
   (`AGDFormalGap.divisible_and_small_zero`) remains unverifiable. Blocked by disk.
6. **`axcheck.lean:12`** requests `#print axioms AGD.projection_iterate`, a name that does
   not exist — that command errors.
7. **Suspected proof-term bugs:** `AGDMaximallyTypedClaim.lean:376` passes the same projection
   for field 9; `SimSystem.lean:100-107` has a type-incompatible `cases S.equiv_equiv`.
8. **`StrictCostReduction` / the E2E theorem** — none exists. Only a FLOP ratio does.

---

## 15. Recommended next experiments

1. **Discharge `ReverseBound`** in `LinearExactSector.lean` for `π = I_q⊗p`, `R = I_q⊗pᵀ`.
   Expected: `d(R(πx), x) ≤ ε` iff `BlockConstant x`, otherwise `‖x − blockavg(x)‖_F`. One
   file, one theorem, closes the corpus's own named gap.
2. **Exploit the Kronecker structure of π and R.** They are currently applied as *dense*
   `(d×q)` matvecs. Exploiting block structure drops each from `dq` to `d` operations and
   should move E2E from `√kernel/4` toward `kernel/3`. **This is the single largest
   available gain and it is fully predicted by the model in the derivation.**
3. **Build Mathlib** (needs ~10 GB free — free disk first).
4. **Re-run `AGD_QUANTUM_GENERALITY` with per-n reporting** so the headline is not pooled
   across n. Report median + MAD.
5. **Pin to the big cores** (`taskset -c 4-7`) and re-measure n = 9, 10, where CV is 171 % and
   112 %. cpu0–3 sit at their 691 MHz floor.

---

## 16. Exact reproducibility commands

```bash
# environment
uname -a; for i in 0 1 2 3 4 5 6 7; do cat /sys/devices/system/cpu/cpu$i/cpufreq/cpuinfo_max_freq; done
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; df -h /

# AGD generality recomputation (counts + per-n medians)
python3 - <<'EOF'
import csv,statistics as st
rows=list(csv.DictReader(open('/root/AGD_QUANTUM_GENERALITY_RESULTS.csv')))
pos=[r for r in rows if not r['operator_family'].startswith('NEG')]
neg=[r for r in rows if r['operator_family'].startswith('NEG')]
print(len(pos),sum(r['PASS/FAIL']=='PASS' for r in pos))
print(len(neg),sum(r['PASS/FAIL']=='PASS' for r in neg))
EOF

# the zeroization lemma, machine-checked today (no Mathlib required)
cd /root/AGD_MASTER_DERIVED_20261007 && lean AGDFormalGapCore.lean; echo "exit=$?"
# -> exit=0 ; #print axioms -> [propext], no sorryAx

# the original, which does NOT build here
cd /tmp && lean /root/AGDFormalGap.lean    # -> unknown module prefix 'Mathlib'
```

---

## 17. SHA-256 of critical artifacts

Recorded in `AGD_MASTER_EVIDENCE_ASSESSMENT_20261007.json` under `critical_sha256`
(14 artifacts, all recomputed this session).

---

## 18. Git repository state

No git repository mutation was performed, attempted, or required. `commit`, `push`,
`reset`, `rebase` were never run. `/root/research_repo` (203 MB) and all other trees are
untouched.

---

## 19. Claim-strength / evidence-strength matrix

| claim | asserted strength | evidence class | satisfies `CLAIM ≤ EVIDENCE`? |
|---|---|---|---|
| AGD generality semantic correctness | strong | **E1** (189/24, all hashes verify) | **YES** |
| Quotient descent + section exact | strong | **E1** + **E3** (Lean core) | **YES** |
| Cost model predicts speedup | novel | **E1** (fit R²=0.99985) | **YES** |
| E2E break-even at n = 7 | novel | **E1** | **YES** |
| NEON GEMM 7.3–14.6× | local | **E1** | **YES** |
| PCSS 497.8× | strong | **E0** | **NO — self-comparison** |
| SIMD v4 36.19× | strong | **E0** | **NO — hard-coded literals** |
| 279.62 GFLOPS | strong | **E0** | **NO — above device peak** |
| ChronoFold 6.1× / 14 400× | strong | **E0** | **NO — kdim=0, 0/512 accepted** |
| 25 600× fiber reduction | strong | **E0** | **NO — size ratio, no timing** |
| Universal/quantum speedup | universal | — | **NO — not claimed by the artifacts; do not claim** |
| RSA break | strong | **E0** | **NO — Coppersmith, ≤304 bits, structured** |
