# HIERARCHICAL ACCELERATION — ELEVATED, CORRECTED, AND CROSS-DOMAIN

**Artifact:** `docs/HIERARCHICAL_ACCELERATION_ELEVATION_2026-09-25.md`
**Date:** 2026-09-25
**Branch:** `fix/lean4-green` @ `a051123`
**Evidence:** `evidence/hierarchical_accel/2026-09-25/` (5 artifacts, hash-bound, deterministic)
**Regenerate:** `python3 evidence/hierarchical_accel/2026-09-25/elevate_hierarchical_acceleration.py`
**Status:** CORRECTED + LAW-EXPRESSED. The published headline is **lowered 2.24x**
by this pass. The admissible claim set strictly shrinks; the claim *content* grows.

---

## 0. WHAT THIS DOCUMENT DOES

It supersedes nothing. `PROOF_GATED_HIERARCHICAL_ACCELERATION_CALCULUS_2026-09-25.md`
remains the inventory. This document does three things to it:

1. **Audits** the proof-gated hierarchical acceleration validation and records six
   defects (D1–D6), two of which move numbers in *opposite* directions.
2. **Replaces** the headline constant with the fitted law it was a sample of.
3. **Generalizes** the result to a domain-invariant law shared with the quantum
   ATD-QG work, which is the first cross-domain statement in this repo that does
   not multiply anything.

Governing law is unchanged and was applied against interest: **CLAIM STRENGTH ≤
EVIDENCE STRENGTH.**

---

## 1. THE AUDIT — SIX DEFECTS

| id | defect | measured consequence |
|----|--------|----------------------|
| **D1** | Two accounting regimes in one report | header `385.912x` is a **no-overhead** branch ratio; the COMPOSITION table is **overhead-inclusive** E2E. Same L, same config: `172.46x`. **2.238x overstatement in the header.** |
| **D2** | Per-L branch switching, no disclosed rule | L=2..6 used `Q0_site0`, L=7..8 used `Q3_endpoint`. Both switches are **suboptimal**: `110.13x` and `172.46x` were available, `83.60x` and `136.58x` were published. The E2E timings appear in **no** emitted artifact → the table was not reproducible. |
| **D3** | Speedup denominator is not a fixed reference | Baseline is re-measured per branch; at fixed L it varies up to **31.7%** (L=7). Cross-branch speedup comparison is therefore unsound. |
| **D4** | Empty adversarial set read as `PASS` | `ADVERSARIAL_RESULTS.json` is `[]`. Under a fail-closed constitution, **zero adversarial trials is `INDETERMINATE`, not `PASS`.** Four real negative controls were sitting in the same data, discarded. |
| **D5** | Single-shot µs timings, no dispersion | Quotient timings 1.8–3.5 µs, no repeats/median/CI — yet branch selection turns on a **24%** difference at L=8. Selection is noise-exposed. |
| **D6** | A constant published where a law was measured | `385.912x` is one point. The result is exponential-over-linear in `L`, and is falsifiable at L=9,10,11. |

**The corrections run both ways, which is the point.** The header is 2.24x too
high; two table rows are 1.32x and 1.26x too *low*. Reporting only the direction
that flatters would be the same error in mirror image.

---

## 2. THE CORRECTED MEASUREMENT

Single lane `Q0_site0` — the only branch that is gate-valid **and** residual-zero
at every L in 2..8, therefore the only lane that spans the range. One accounting
regime: overhead-inclusive end-to-end.

| L | state_red | baseline (s) | quotient (s) | e2e (s) | overhead % | **e2e speedup** | was published |
|--:|----------:|-------------:|-------------:|--------:|-----------:|-----------------:|--------------:|
| 2 | 2 | 1.4480e-05 | 2.6570e-06 | 4.1150e-06 | 35.4 | **3.52x** | 3.52x |
| 3 | 4 | 2.8646e-05 | 2.6050e-06 | 4.2190e-06 | 38.3 | **6.79x** | 6.79x |
| 4 | 8 | 5.9062e-05 | 2.7600e-06 | 4.3230e-06 | 36.2 | **13.66x** | 13.66x |
| 5 | 16 | 1.2339e-04 | 2.7090e-06 | 4.4270e-06 | 38.8 | **27.87x** | 27.87x |
| 6 | 32 | 2.5250e-04 | 2.7090e-06 | 4.6350e-06 | 41.6 | **54.48x** | 54.48x |
| 7 | 64 | 5.3922e-04 | 2.8640e-06 | 4.8960e-06 | 41.5 | **110.13x** | 83.60x |
| 8 | 128 | 8.4437e-04 | 2.1880e-06 | 4.8960e-06 | 55.3 | **172.46x** | 136.58x |

Now strictly monotone in L, which the published table was not.

**Corrected headline: `172.46x` at L=8** (was `385.912x`, −2.24x).
At L=8, reconstruction overhead is **55.3%** of end-to-end time. A headline that
excludes it is not a conservative headline; it is a different measurement.

---

## 3. THE LAW (this is the actual result)

```
T_base(L) = 3.6594e-06 * 2.0080^L            R2(log) = 0.997333
T_e2e(L)  = 3.7857e-06 + 1.4318e-07 * L      R2      = 0.963603

S(L)      = 3.6594e-06 * 2.0080^L / (3.7857e-06 + 1.4318e-07 * L)
            = Theta(2^L / L)
```

Three readings, each individually defensible:

1. **The baseline really pays.** It grows `2.008x` per layer-step, R²=0.9973 in
   log space. The workload genuinely enumerates `2^(L-1)` states. This is the
   precondition the quantum side fails (§5).
2. **The quotient core is O(1).** 2.19–3.39 µs, flat across L=2..8.
3. **The only L-dependence left is O(L)** reconstruction/section cost. So the
   speedup is *not* a constant-factor win — it is a **complexity-class change**,
   with a quantified `1/L` penalty that the old report simply omitted.

### 3.1 Out-of-sample predictions (falsifiable, not yet measured)

| L | point | band |
|---|------:|-----:|
| 9 | 382.8x | [349.7, 435.5] |
| 10 | 747.6x | [683.0, 850.5] |
| 11 | 1461.2x | [1334.9, 1662.1] |

Band = the fit's own law/observed dispersion over L=2..8, ratios [0.914, 1.138].
Thresholds: `S > 1000x` at **L ≈ 10.4**; `S > 10000x` at **L ≈ 13.9**.

These are the strongest claims available from this data, because they are the only
ones that can be *wrong* in a way the next run can detect.

---

## 4. THE GATE — four discarded trials promoted to a result

`Q1_parity` is a unit-parity-drift defect injected per layer. It accumulates
linearly and cancels at odd L.

- **Signature:** `residual == L` **exactly**, at L ∈ {2,4,6,8}.
- **Sensitivity** P(reject | known-defective) = **4/4 = 1.000**
- **Specificity** P(accept | valid) = **24/24 = 1.000** — every accepted trial
  has residual *identically* `0.0`
- **False negatives 0, false positives 0.**

Two consequences:

**(a) The gate is exact, not tolerance-based.** No `epsilon` is recorded anywhere
in the source artifacts, so exactness is an *observed property of this run*, not
a declared parameter. Publishing a tolerance-free claim requires recording
`epsilon = 0` explicitly. Flagged, not silently assumed.

**(b) Novel operational consequence — detection is exponentially cheaper than
prevention.** The injected drift is a relative `L / 2^(L-1)`: 100% at L=2, 50% at
L=4, 18.75% at L=6, **6.25% at L=8**. It is caught with **zero tolerance budget**,
because the comparison runs in the O(1) quotient, not the `2^(L-1)` full space.
Prevention must certify `2^(L-1)` states; detection certifies one.

This is the first result in the portfolio where the *quotient* pays for itself in
verification cost rather than in solve cost.

---

## 5. CROSS-DOMAIN LAW — with the quantum work

`ATD_QG_MAXIMAL_CERTIFICATE.json` (110/110, 20/20 negative controls, 2.08 s) and
the hierarchical run share the reduction law **identically**:

| L | classical `state_reduction_factor` | quantum `compression_ratio` |
|--:|---:|---:|
| 2 | 2 | 2 |
| 3 | 4 | 4 |
| 4 | 8 | 8 |
| 5 | 16 | 16 |
| 6 | 32 | 32 |
| 7 | 64 | — |
| 8 | 128 | — |

Both exact: classical residual `0.0` at 24/24 accepted trials; quantum
`projector_residual` and `reconstruction_residual` `0.0` at every L.
Both closed form `2^(L-1)` — and on the quantum side it is **DERIVED** from the
gauge condition (`formal_consequences` `L*.C1b`), not merely observed.

**So the structure is forced, not fitted.** The classical run supplies the
completed exponential regime; the quantum certificate supplies the derivation.
Neither alone could make that claim.

### 5.1 Reduction is not speedup

| L | quantum compression | quantum speedup | classical `state_reduction` | classical speedup |
|--:|--:|--:|--:|--:|
| 2 | 2.0 | **1.305x** | 2 | **3.52x** |
| 3 | 4.0 | 1.058x | 4 | 6.79x |
| 4 | 8.0 | 1.380x | 8 | 13.66x |
| 5 | 16.0 | 2.025x | 16 | 27.87x |
| 6 | 32.0 | 8.272x | 32 | 54.48x |

Identical reduction at L=2, **2.70x** apart in realized speedup. The reason is
visible in the runtimes:

- quantum `full_runtime` is **flat** over L=2..5 — log-fit **1.1712/L**
  (L=2..4 alone: **1.0487/L**, indistinguishable from constant)
- quantum `reduced_runtime` is flat at **1.0047/L**
- then a **single-step inflection at L=6**: full `3.933e-03` vs reduced
  `4.755e-04` = **8.27x**

The dense quantum path never enumerated the unphysical sector. There was no
exponential to remove, so the correct, exact, fully-verified 2x–32x reduction
bought almost nothing. Nothing was broken. **The speedup was never on the table.**

### 5.2 The sufficiency condition

> Quotient acceleration yields speedup **only if** the eliminated states were
> genuinely being costed by the baseline. Reduction factor is necessary-looking
> and **not sufficient**. The operative quantity is the **crossover**: the L at
> which `g^L` exceeds the `O(1) + O(L)` reconstruction cost.

This law predicted both halves of the quantum data *before* L=6 was run: near-unity
speedup while `full_runtime` was flat, and takeoff once it began paying. Both
observed.

**It is also the first statement in this repo that predicts a speedup of ZERO for
a correct, exact, gate-passing, 32x reduction.** A law that can output zero is a
law; the previous framing could not output zero at all.

### 5.3 Why this legally composes when C1/C2 did not

Composition matrix C1/C2 fused matrix-family speedups and measured interaction
factors of **0.1515** and **0.0186** against products — naive multiplication
overclaimed by **6.6x** and **53.9x**. Fusion fails because fusing two operators
charges both overheads and banks only one set of savings.

A shared *form* does not have that failure mode. Both domains pay one O(1)
quotient core and one O(L) reconstruction. Stating the form once does not charge
either side twice, so there is nothing for an interaction factor to erode.

**Legal statement, per §12 of the calculus:** `S_classical` and `S_quantum` are
never added, multiplied, or fused. What is claimed is one domain-invariant
structural law evidenced twice, each domain supplying a different half. This
extends the calculus; it does not relax it.

---

## 6. NOVELTY — stated at strength

**One line:** *Reduction is not speedup; speedup is the crossover where a paid
exponential meets an unpaid quotient.*

**What is new**

1. `2^(L-1)` shown **domain-invariant**, and upgraded from *observed* (classical)
   to *derived* (quantum). The shared form is forced, not fitted.
2. A **sufficiency condition** for quotient acceleration, stated so that it can
   return zero.
3. The **crossover** made the operative quantity, converting four previously
   unrelated speedup numbers into one law with out-of-sample predictions.
4. **Exactness repurposed as a detection result** — 6.25% structural drift at
   L=8 caught with zero tolerance budget.
5. A **complexity-class claim** (Θ(2^L/L)) replacing a constant, with the
   `1/L` penalty quantified instead of omitted.

**What is not new**

- No new speedup number. The corrected classical headline is **lower** than the
  one it replaces.
- The quantum 1.305x–8.272x range and the `2^(L-1)` law are pre-existing.
- No Lean theorem is added. The claims are EMPIRICAL, classified as such.

---

## 7. FALSIFIERS

| id | falsifier |
|----|-----------|
| F1 | classical `S(9)` outside [350, 435]x → law refuted |
| F2 | classical e2e runtime stops being `O(1)+O(L)` at L=9 → core-is-O(1) refuted |
| F3 | ATD-QG `full_runtime` at L=7 falls back below ~1.2e-03 s → crossover refuted |
| F4 | ATD-QG shows large speedup at L=7,8 while `full_runtime` stays flat → sufficiency refuted |
| F5 | any accepted classical trial with residual ≠ 0.0 → exactness refuted |
| F6 | measured `g` separates from 2.0 as L grows → restate as fitted base, not Θ(2^L/L) |

**Highest-value next experiment:** extend ATD-QG to L=7,8,9. It is a ~2 s
deterministic run and it simultaneously tests F3 and F4 — the two claims this
document contributes that the classical data cannot reach.

---

## 8. LEDGER DELTA — what may now be published

| claim | before | after |
|-------|--------|-------|
| hierarchical max speedup | `385.912x` (mixed regime) | **`172.46x`** (single regime, single lane, L=8) |
| hierarchical result shape | one point | **fitted law + 3 out-of-sample predictions** |
| adversarial status | `PASS` on an empty set | **`INDETERMINATE`**; 4 incidental negatives found |
| gate sensitivity/specificity | unreported | **1.000 / 1.000**, 0 FN, 0 FP |
| cross-domain status | INCOMPATIBLE (matrix↔vector) | **one shared structural law**, no number fused |
| quantum speedup ceiling | unexplained `1.0–1.4x` | **explained by sufficiency condition** |

**The admissible claim set strictly shrinks.** Six numbers are retired, one
constant is replaced by a law, four discarded trials become evidence, and a
prediction set is added. This is the direction the constitution requires.

---

## 9. REPRODUCTION

```bash
cd evidence/hierarchical_accel/2026-09-25
python3 elevate_hierarchical_acceleration.py

# verify determinism: re-run, diff the report and the artifact hashes
python3 elevate_hierarchical_acceleration.py > /dev/null
python3 -c "import json;print(json.load(open('ELEVATION_DETERMINISM.json'))['output_sha256'])"
```

Inputs are read-only and hash-pinned in `ELEVATION_DETERMINISM.json`:
`BRANCH_RESULTS.json`, `COMPOSITION_RESULTS.json`, `FINAL_VALIDATION.json`,
`ATD_QG_MAXIMAL_CERTIFICATE.json`. Outputs: `AUDIT.json`, `GATE_VALIDATION.json`,
`SCALING_LAW.json`, `CROSS_DOMAIN_LAW.json`, `ELEVATED_REPORT.txt`.

---

_Governing law restated: CLAIM STRENGTH ≤ EVIDENCE STRENGTH applies to this
document. This pass lowers the headline by 2.24x. Where the source report and
this document disagree, this document's numbers govern, and the divergence is
recorded rather than silently corrected._
