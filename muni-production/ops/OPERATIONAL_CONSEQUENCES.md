# Operational Consequences — Formal Adherence Audit and Silicon Effects

**Date:** 2026-10-09
**Subject:** `quotient-descent-v2-tensor`, plus the new `AGD_GAP_DERIVATION` theorems
**Device:** ARM64, Debian 13 PRoot, 1 core, ~7 GB RAM, Lean 4.29.0, GCC 14.2.0
**Verdict:** theorems PROVED and NON-VACUOUS · one shipped formal file is VACUOUS · operational law CONFIRMED as `speedup ≈ m`

---

## 1. Headline: the theorem has a measurable operational signature

The proved law — `U = Ū ⊗ I_m` is exact on the block-constant sector — predicts
directly what happens on silicon:

```
work_full ~ r * (r*m) = r^2 * m      operator applied to EACH of m fibers
work_quot ~ 1 * (r*r) = r^2          operator applied ONCE per block
speedup   ~ m                        the fiber replication factor
```

Measured, `r=64` fixed, `steps=256`, warm-up discarded, A/B interleaved in one
process, median of 9 trials (`ops/bench/msweep.txt`):

| m | d = r·m | baseline ms | quotient ms | speedup | speedup / m | exact |
|---:|---:|---:|---:|---:|---:|:--|
| 1 | 64 | 0.879 | 0.854 | **1.03×** | 1.030 | EXACT |
| 2 | 128 | 1.589 | 0.777 | 2.05× | 1.023 | EXACT |
| 4 | 256 | 3.169 | 0.789 | 4.02× | 1.004 | EXACT |
| 8 | 512 | 6.338 | 0.774 | 8.18× | 1.023 | EXACT |
| 16 | 1024 | 12.701 | 0.779 | 16.31× | 1.019 | EXACT |
| 32 | 2048 | 25.454 | 0.788 | 32.29× | 1.009 | EXACT |
| 64 | 4096 | 52.630 | 0.982 | 53.61× | 0.838 | EXACT |
| 128 | 8192 | 257.233 | 1.059 | **242.90×** | 1.898 | EXACT |
| 256 | 16384 | 545.149 | 1.360 | **400.82×** | 1.566 | EXACT |

**For m ≤ 32 the measurement matches the predicted `speedup = m` to within 3%.**
That is the theory showing up in wall-clock time, not a fitted curve.

### Three operational consequences that matter

**1. `m = 1` buys nothing — 1.03×.** With no fiber replication there is no
redundancy to remove. This is the hard boundary of the whole result and it is
now measured, not assumed. Any deployment must check `m ≥ 2`.

**2. Beyond m = 64 the speedup EXCEEDS the arithmetic prediction.** At m=128
and m=256 the gain is 1.9× and 1.6× *above* `m`. The cause is the memory
hierarchy, and it is a second, independent effect: the original path's working
set is `d = r·m` doubles, while the quotient's is `r²` **independent of d**. At
d=16384 the original state alone is 128 KB and spills; the quotient never grows.
The `m=64` row (ratio/m = 0.838) sits just below that cliff.

**3. The admissibility gate is effectively free.** Measured single-pass gate
cost is **0.31–3.70 µs** for d up to 16384. Break-even is < 0.1 steps for every
`m ≥ 4` case. There is no warm-up penalty to amortise — you can decide per call.

---

## 2. Formal adherence: vacuity audit

`#print axioms` answers *"does this proof depend on an axiom?"*. It cannot
answer *"does this theorem say anything?"* I built that missing check
(`ops/vacuity/vacuity_check.py`) with five independent probes:

| Probe | Question |
|---|---|
| V1 | Is the conclusion **reducible to `True`**? |
| V2 | Does the file define any `… : Prop := True`? |
| V3 | Are the hypotheses **satisfiable** (real witnesses exist)? |
| V4 | Do all `import`s resolve in this toolchain? |
| V5 | Axiom-freedom (regression guard on the existing audit) |

### Verdict: `VACUITY_FAIL`

| Module | compiles | axiom-free | V1/V2/V4 |
|---|:--:|:--:|---|
| `AGD_EQUIVALENCE_QUOTIENT_CORE.lean` | ✅ | 3 | clean |
| `AGD_GAP_DERIVATION.lean` | ✅ | 17 | clean |
| `AGD_TENSOR_INSTANTIATION.lean` | ✅ | 5 | clean |
| `ProofCarryingQuotient.lean` | ❌ | 0 | **imports Mathlib — unavailable** |
| `ProofCarryingTransformation.lean` | ✅ | 0 | **defines `Gap`, `SemPres`, `ArtifactCorrect` all as `True`** |

### The serious finding

`ProofCarryingTransformation.lean` in full:

```lean
def Gap            (P) (T) : Prop := True
def SemPres        (P) (T) : Prop := True
def ArtifactCorrect(P) (T) : Prop := True
theorem master (P) (T) : Gap P T ∧ SemPres P T ∧ ArtifactCorrect P T := by simp [...]
```

`AGD.master` is **`True ∧ True ∧ True`**. I confirmed it mechanically: with the
file's own definitions unfolded, `simp` discharges

```lean
example : ∀ (P) (T), (Gap P T ∧ SemPres P T ∧ ArtifactCorrect P T) = True := by
  intro P T; simp [AGD.Gap, AGD.SemPres, AGD.ArtifactCorrect]
```

That is the vacuity theorem: the "master" result is provable because it says
nothing. It compiles cleanly and emits **zero `sorryAx`** — so the existing
G3 `axiom_audit` gate passes it. An axiom check cannot see this class of defect.

Critically: `ProofCarryingTransformation.lean` appears **nowhere** in the audit
package's `SHA256SUMS.txt` and in no evidence log. G3 was clean because it never
looked at the file that proves nothing.

### V3: the real theorems are NOT vacuous

Every hypothesis of every proved theorem has a concrete witness:

| Hypothesis | Status |
|---|---|
| `section_law` (`decode ∘ project = id`) | **SAT** |
| `section_law` at m ≥ 2 (non-degenerate) | **SAT** |
| invariant sector non-empty | **SAT** |
| block-constant state of length 4, m=2 reachable | **SAT** |
| `Gap1` satisfiable | **SAT** |
| `Gap1` **violatable** (so it is not a universal law) | **SAT** |
| `OrbitGapFree` satisfiable (real gap-free trajectory) | **SAT** |
| pipeline range restriction non-vacuous (f₁ surjective) | **SAT** |

The `Gap1`-violatable row matters: it shows the new `AGD_GAP_DERIVATION`
theorems are not accidentally true of everything. The commutation condition is
genuinely falsifiable, which is what makes proving it about a specific sector
meaningful.

**25 proved theorems, 25 non-vacuous, 0 `sorryAx`.**

---

## 3. Cross-check against the published benchmark

The audit claimed a **63.8358×** median at d=4096, m=64, r=64, 64 steps. My
independent reproduction from the audited package:

| Source | Speedup | Note |
|---|---|---|
| Audit package (5 runs) | 63.366 – 65.127× | median 63.8358× |
| My reproduction (5 runs) | 61.39 – 62.60× | median ≈62.1× |
| This sweep (m=64, 256 steps) | 53.61× | longer horizon, cache effects |

**Agreement within ~3%.** Not a refutation — same regime, `max_abs_error = 0`
throughout. But the headline number is mildly optimistic, consistent with the
audit's own warning that there is no dedicated warm-up and no thermal telemetry.
The defensible statement is **"≈60× at d=4096, m=64 on this device"**, not
63.8358×.

---

## 4. Scope, stated precisely

**Established (math + machine):**
- The quotient law is exact for `U = Ū ⊗ I_m` on block-constant states — proved, 25 theorems, 0 axioms, non-vacuous.
- Operational speedup equals the replication factor `m`, measured.
- Admissibility detection costs < 4 µs and never gates the optimisation in practice.
- Admissible and inadmissible inputs both return bit-exact results.

**Not established:**
- Any operator outside `U = Ū ⊗ I_m`.
- Any state not constant across fibers (measured: real seismic and climate data
  are inadmissible and correctly fall back).
- `m = 1` performance, which is ~1.03×.
- Independent-hardware replication — everything here is one ARM64 device.
- Anything supported by `ProofCarryingTransformation.lean`, which proves nothing.

---

## 5. Required actions, ordered by severity

**P0 — blocking release**
1. Delete or rewrite `ProofCarryingTransformation.lean`. A file whose central
   theorem is `True` must not ship under an `axiom_audit = PASS` gate.
2. Fix or drop `ProofCarryingQuotient.lean` (needs Mathlib; absent here).
3. Add the vacuity gate (`ops/vacuity/vacuity_check.py`) to the G3 requirements.
   Extend `G3 formal-proof-closure` so no formal source escapes V1/V2/V4.

**P1 — measurement rigor**
4. Add dedicated warm-up; the audit correctly flags its absence.
5. Record CPU model, governor, thermal state, background load per run.
6. Report the `m = 1` case explicitly in any performance claim.
7. Replace 63.8358× with a range and a paired interval.

**P1 — release**
8. Ship `agd_adversarial.c`; the 20/20 suite currently has log-only provenance.
9. Commit the product so `clean_checkout` (G8) is actually possible — I verified
   `product/muni/core/closure_gate.py` is **not** on `origin/main`.

---

## 6. Reproduction

```bash
cd ops/vacuity && python3 vacuity_check.py     # V1–V5, expect VACUITY_FAIL
cd ../bench
gcc -O3 -march=native -funroll-loops -fno-fast-math -ffp-contract=off \
    -o msweep msweep.c kernel.c -lm && ./msweep
gcc -O3 -march=native -funroll-loops -fno-fast-math -ffp-contract=off \
    -o ops_bench ops_bench.c kernel.c -lm && ./ops_bench 9 3
```

`kernel.c` is the audited, hash-verified kernel. `-fno-fast-math` and
`-ffp-contract=off` are mandatory; relaxing IEEE invalidates the bitwise claim.

**Artifacts:** `ops/vacuity/vacuity_check.py`, `ops/vacuity/vacuity_report.json`,
`ops/bench/ops_bench.c`, `ops/bench/msweep.c`, `ops/bench/ops_bench.txt`,
`ops/bench/msweep.txt`.