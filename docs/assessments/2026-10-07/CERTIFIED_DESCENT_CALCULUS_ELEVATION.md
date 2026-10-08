# Certified Computational Descent Calculus — ELEVATION

2026-10-07 · Lean 4 + Mathlib deployment plan, with the mathematical content
**elevated, verified, and honestly located in the literature**.

Companion artifacts:
- `lean4/AGDDescentCore.lean` — Levels 1–4, 7, **machine-checked today**, Lean 4 core
- `lean4/Mathlib/AGDDescentMathlib.lean` — `Submodule`/`LinearMap` dressing, **CI-target, not locally compiled**
- `evidence/blockquotient_20261007/` — 231/231 corpus re-run with block operators
- `workloads/device_speedup_contract/` — device measurement contract

---

## 0. Deployment model: confirmed, and it is better than proposed

The repository already has exactly the split you describe, and it is stricter than
you asked for.

| lane | workflow | verifier | rule |
|---|---|---|---|
| core | `.github/workflows/lean-ci.yml` | `scripts/verify_lean4_all.sh lean4 core` | rejects `sorry`/`admit`/`by?`, rejects `import Mathlib`, rejects any `axiom`/`opaque` |
| Mathlib | `.github/workflows/mathlib-lean4.yml` | `lake exe cache get` + `lake build` + per-file `lake env lean` | rejects `sorry`/`admit`/`by?` |

Two consequences:

1. **The central theorem does not need Mathlib.** `Quot`, `Quot.sound`, `Quot.lift`,
   `Quot.ind` and funext are all Lean 4 *core*. So Levels 1–4 and 7 are proved in the
   core lane, where the verifier also **forbids axioms outright** — a stronger
   guarantee than "no `sorry`".
2. **No second Mathlib locally.** Confirmed: Mathlib is not built on this device
   (`lean AGDFormalGap.lean` → `unknown module prefix 'Mathlib'`) and the filesystem
   cannot host it. The device is used only for concrete native/AGD evidence.

Local result, verified before commit:

```
LEAN4_CORE_ALL_PASS=1
LEAN4_CORE_SOURCE_COUNT=43
```

with `AGDDescentCore.lean` included.

---

## 1. Logical elevation

### 1.1 Your `Preserves` was unfixable as written — correctly self-flagged

`K ≤ T.ker ⊔ K` is vacuous. `K ≤ K.comap T` is the right form and is what
`AGDDescentCore.Invariant` / `AGDDescentMathlib.Invariant` use.

### 1.2 The descent theorem is **standard**, and Mathlib already has it

`T(K) ⊆ K ⇒ ∃ Tbar : M/K → M/K, Tbar ∘ π = π ∘ T` is textbook quotient algebra.
Mathlib supplies the whole thing in `Submodule` form:

- `Submodule.mapQ hT T : M ⧸ K →ₗ[R] M ⧸ K`
- `Submodule.mapQ_mkQ : mapQ hT T (K.mkQ x) = K.mkQ (T x)`
- uniqueness via `LinearMap.liftQ` uniqueness / `Quot.lift` uniqueness

Both files say this in their headers. **If the Mathlib file compiles it should
compile in a handful of lines and prove nothing new.** That is the correct
expectation; do not later relabel it as a theorem.

### 1.3 The hierarchy claim was **false as first written** — and the gate caught it

The first draft of `composed_intertwine` proved `Π T₀ⁿ = T₁ⁿ Π` with no hypothesis
relating `T₁` to `p₀`. The proof silently assumed they commute. It does not hold
in general. Fixed by making the level-0 intertwining explicit:

```lean
theorem compose_iterate (hp : ∀ x, T1 (p0 x) = p0 (T0 x)) (n : Nat) (x : α) :
    iter T1 n (p0 x) = p0 (iter T0 n x)
```

**On record as a correction**, because the same pattern — an omitted hypothesis that
a proof elaborator happily fills in — is the single most dangerous failure mode in
this programme.

### 1.4 What is genuinely the strongest mathematical content

Not the descent (standard). This:

```lean
theorem exact_reconstruction_on_invariant_orbit (hS : Invariant S T)
    (hR : ReconstructsOn ρ S) (n : Nat) (x : α) (hx : S x) :
    ρ (iter Tbar n (π x)) = iter T n x
```

Reconstruction is an **equality** on the invariant orbit for every `n`, not a
numerical bound. That is a real strengthening over "reconstruction error ≈ 1e-16",
and it is what makes the whole architecture sound rather than merely fast.

### 1.5 Level 5 is textbook, but the instantiation is not

`P = Rπ` with `P² = P`, `P* = P`, and `‖x − Px‖ = min_y ‖x − y‖` is standard
orthogonal projection theory. The **content** for AGD is the concrete instance:
`Rπ` is orthogonal projection onto the block-constant sector, with the closed-form
error below. That is what §2 verifies and §4 certifies.

---

## 2. Numerical elevation

### 2.1 Your work ratio is the kernel ratio only; the path ratio is different

`W_F/W_Q = m²` is correct for the **kernel** (`d²` vs `q²`) and is proved in
`AGDGemmWork.lean`. But the quotient *path* is three stages, and `π`/`R` dominate:

| arm | FLOPs |
|---|---|
| dense path (`π`, `Ū`, `R`) | `2dq + q²` |
| block path (`π`, `Ū`, `R`) | `2d + q²` |

With `d = qm` the ratio is

```
(2dq + q²)/(2d + q²) = q²(2m+1) / (q(2m+q)) = q(2m+1)/(2m+q)  ≤  q
```

so **path gain ≤ q**, not `m²`. Measured on the device (`AGD_BLOCKQUOTIENT`):

| n | d | q | FLOP bound | measured gain | efficiency |
|---|---|---|---|---|---|
| 9 | 512 | 32 | 21.7 | 1.99 | 0.09 |
| 10 | 1024 | 32 | 43.0 | 3.33 | 0.08 |
| 11 | 2048 | 64 | 65.0 | 7.12 | 0.11 |
| 12 | 4096 | 64 | 86.0 | 10.36 | 0.12 |

Measured efficiency rises toward the bound as `n` grows (isolated-stage measurement
reaches 0.72 at n = 13) — the `c/α` overhead term receding, exactly as the cost model
predicts.

> **CORRECTION 2026-10-08 — the bound `path gain ≤ q` is FALSE in native code.**
> See `evidence/blockquotient_20261007/TENSOR_OPERATOR_RESULT_20261008.md`.
> In the native AArch64 runtime the quotient projection is a *decimation* (`O(r)`), not
> a dense `d×q` matvec, so the FLOP ratio no longer governs. Measured asymptotes:
> dense/d=4096/tile=64 → **70.3×** against `q = 64` (violated), and 153.5× against
> `m = 64`. The ratio is set by achieved memory bandwidth, not operation count.
> **The FLOP bound holds only while both arms are FLOP-bound.** Any later use of §2.1
> must carry this caveat.

### 2.2 The break-even theorem is **not an assumption — it is fitted**

Your `k > (C_setup + C_π + C_ρ)/(C_T − C_T̄)` inverts to the testable law

```
1/E2E(k) = a/k + b ,   a = C_fixed/C_full ,  b = C_quot/C_full
```

Fitted to the **native AArch64** runtime (`agd_amortized_total`, 24 configurations,
`maxerr = 0` throughout, all reproduced this session):

| d | tile | a = C_fixed/C_full | b = C_quot/C_full | asymptote | R² | k_break |
|---|---|---|---|---|---|---|
| 4 096 | 32 | 0.13851 | 0.015046 | 66.5× | 0.9964 | 0.14 |
| 4 096 | 64 | 0.05436 | 0.008045 | **124.3×** | **1.0000** | 0.06 |
| 16 384 | 32 | 0.11938 | 0.017693 | 56.5× | 0.9993 | 0.12 |
| 16 384 | 64 | 0.10962 | 0.008852 | **113.0×** | **0.9999** | 0.11 |
| 65 536 | 32 | 0.09622 | 0.023193 | 43.1× | 0.9738 | 0.10 |
| 65 536 | 64 | 0.10893 | 0.011826 | 84.6× | 0.9959 | 0.11 |

**R² = 0.974–1.0000.** The law predicts out-of-sample: for d = 4096, tile = 64 it
predicts E2E(1) = 16.0× and E2E(64) = 112.4× against measured **15.85×** and
**109.83×** — within 1–2 %.

**The break-even point is read off the fit, not assumed.** For every configuration
`k_break < 1`, i.e. the quotient path already wins at a single step once setup is
charged to it.

### 2.3 The 90.89× claim: reproduced, and correctly scoped

Re-ran `agd_amortized_total` directly. **24/24 configurations PASS with `maxerr = 0`.**
At d = 4096, tile = 64, steps = 64 the reported 90.891854× reproduces at
**109.826478×** this session (the report's own values are conservative, not inflated).

What the number *is*, precisely — and this scoping matters:

- `agd_full_apply`: `y[i] = x[i] * w[(i/tile) % nw]` over all `d` elements.
- `agd_quotient_apply`: `y[b] = q[b] * w[b % nw]` over `r = d/tile` elements.
- The input is **constructed block-constant** (`x[i+j] = v` for all `j` in the block),
  and `agd_validate_block_constant` **checks** it before the quotient is used.

So the two arms are the same operator restricted to the invariant sector, the
quotient is an exact representation, and `maxerr = 0` confirms it. The gain is the
compression ratio `tile` plus the per-element cost difference (the full arm pays a
`i/tile` integer division per element) plus cache traffic, amortized over `k` steps.

**Honest limits of the 90.89×:**
1. The operator is **diagonal / block-diagonal**. It is the simplest possible
   `Ω`-preserving operator, not GEMM.
2. The invariant hypothesis is **constructed, not discovered**. Correct for the
   theorem; it does not exercise a workload where `Ω` might fail.
3. The claim is scoped to the `Ω`-invariant sector. That is precisely what the
   theorem says, so the claim is *true*, but it is not a claim about unrestricted
   `d`-dimensional state.

This lineage is already honestly labelled in its own receipts:
`claim_level: MEASURED_LOCAL_NATIVE_CALLABLE`, `publication_status: NOT_PCSS_VERIFIED`,
"timing remains a local hardware witness, not a universal theorem." Correct.

---

## 3. Operational elevation

| level | status | where |
|---|---|---|
| L1 algebra | machine-checked (core) | `AGDDescentCore.lean`, `Quot.sound` only |
| L2 dynamics | machine-checked (core) | `descent_iterate`, all `n` |
| L3 observation | machine-checked (core) | `observed_orbit` |
| L4 exact execution | machine-checked (core) | `exact_reconstruction_on_invariant_orbit` |
| L5 geometry | partly; `LinearExactSector` in repo | needs `Rπ` orthogonality in core lane |
| L6 cost | fitted on native code, R² ≈ 1 | §2.2 |
| L7 hierarchy | machine-checked (core) | `compose_two_descents`, `composed_intertwine` |
| L8 compiler | exists, gate is fail-closed | `PCSSCertificate.lean` |
| L9 empirical | 231/231 + device ladder + native 109.83× | this report |

Two existing repository facts already enforce your rule "no theorem may claim
wall-clock speedup merely from operation-count reduction":

```lean
def MeasuredRuntimeObligation : Prop := True          -- AGDGemmSpeedup.lean
theorem formal_closure_does_not_imply_runtime         -- AGDMaximallyTypedClaim.lean
theorem formal_is_not_runtime                          -- GODSQuotientClosure.lean
```

The first is a hollow placeholder that should be deleted rather than left as a
false impression of coverage. The other two are correct and should stay.

---

## 4. Novelty — the honest accounting

**Not novel, and should not be claimed:**

| level | status |
|---|---|
| L1 quotient algebra | standard |
| L2 descent + iterate | standard; Mathlib has it |
| L3 observable factorization | standard (`liftQ`) |
| L4 invariant sector | standard, but genuinely useful here |
| L5 orthogonality, best approximation | textbook |
| L7 compositionality | standard; quotient morphisms compose |

"Hierarchical descent is novel" is **not** a mathematical claim. As mathematics it
is a two-line composition. Its value is as a *systems* claim — a certificate format
where each level carries a machine-checked proof obligation — and that is a real
contribution, but it is engineering, not novel mathematics.

**Genuinely new objects this programme produced:**

1. **The reconstruction-error identity.**
   `‖R(πx) − x‖² = Σᵢ ‖xᵢ − mean(xᵢ)‖²`, hence zero iff block-constancy.
   This **discharges the `ReverseBound` obligation that sat as dead code** in
   `scaffolding/PCSSCertificate.lean:8`, never instantiated by anything. Verified
   numerically to `rel. err ≤ 1.1e-15` at n = 2,4,6,8,10. (A first draft carried a
   spurious `(1−1/m)` factor; numerical check rejected it at rel. err 1.0.)
2. **The measured device cost model** `T = α·FLOPs + c` with
   `α = 1.5528e-9 s/FLOP`, `c = 3.4472e-6 s`, R² = 0.99985, plus the unexplained
   **2.8× α split** between the full path and the quotient kernel.
3. **The amortization law validated on native code** — `1/E2E(k) = a/k + b` at
   R² ≈ 1, with `a`, `b` fitted per configuration and break-even read off.
4. **A fully preserved semantics under optimisation**: 231/231 positives and 24/24
   negative controls unchanged while E2E moved 29.5× → 305.7×.

**Not new:** any RSA result (Coppersmith/Howgrave-Graham, ≤ 304 unknown bits,
10/10 hash-matched); any quantum speedup (no SDK, no backend, no qubit).

---

## 5. The single highest-value next step

**Extend the native `agd_amortized_total` operator family from diagonal/block-diagonal
to the tensor-separable form `Ū ⊗ I_m`, at a dimension the device can hold.**

Why this is first:
- It is the **only** step that connects Level 4's exact reconstruction theorem to a
  realistic (non-diagonal) operator. Everything currently proved about reconstruction
  is proved for a diagonal operator.
- The amortization law already transfers: same `1/E2E = a/k + b` form, new constants.
- It is falsifiable against a prior prediction — `path gain ≤ q` from §2.1 — before
  the run, not after.

Do **not** chase the quantum framing. There is no quantum content in any artifact;
the strong, defensible result is that a certified quotient descent on an
invariant sector gives an exact reduction with a validated amortization law, on a
phone, reproducibly.

---

## 6. Reproduce

```bash
# core lane — machine-checked now, no Mathlib needed
cd lean4 && lean AGDDescentCore.lean            # exit 0, axioms [Quot.sound]
cd .. && bash scripts/verify_lean4_all.sh lean4 core   # LEAN4_CORE_ALL_PASS=1, 43 sources

# native amortization law
cd /root/AGD_ELEVATION_20261007 && ./agd_amortized_total   # 24/24, maxerr=0

# block-quotient corpus
python3 /root/AGD_QUANTUM_GENERALITY_BLOCKQUOTIENT_EOF.py 12   # OVERALL: PASS
```

The Mathlib lane compiles only in CI. **Nothing in
`lean4/Mathlib/AGDDescentMathlib.lean` has been kernel-checked** — it is a proposal,
and its header says so.