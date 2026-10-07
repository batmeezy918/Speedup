# AGD — MATHEMATICAL DERIVATION PHASE

Companion to `AGD_MASTER_EVIDENCE_ASSESSMENT_20261007.md`. Goal: determine whether the
quotient/descent structure **predicts** the speedup before execution, or only explains it
afterwards.

---

## 0. The exact object we are reasoning about

From `AGD_QUANTUM_GENERALITY_DEFINITIVE_EOF.py::build_quotient(n)`:

```
d = 2^n,  nq = ⌈n/2⌉,  nf = ⌊n/2⌋,  q = 2^nq,  m = 2^nf     (so d = q·m)
p = m^{-1/2} · 1_{1×m}
π = I_q ⊗ p      (q × d)      R = I_q ⊗ pᵀ     (d × q)
Ω = BlockConstant :  x_{im+j} = x_{im+j'}  ∀ j,j'
operator family :  U = Ū ⊗ I_m
timed quantities: t_full = |u @ ψ|   (u = Ū ⊗ I_m, DENSE d×d)
                  t_qk   = |Ū @ q'|   (q×q)
                  t_rec  = |R @ q'|   (d×q)
                  t_proj = |π @ ψ|    (d×q)
```

Everything below follows from this and nothing else.

---

## G1. Equivalence / descent

**Proposition G1.** Let `m, q ≥ 1`, `p = m^{-1/2}1ᵀ`, `π = I_q ⊗ p`, `R = I_q ⊗ pᵀ`.
Then `(i) π R = I_q`; `(ii) R π` is the orthogonal projection onto the block-constant
subspace `Range(R)`; `(iii) `Range(R) = Ker(I − Rπ)`.

**Proof.** `(i)` `(I_q⊗p)(I_q⊗pᵀ) = I_q ⊗ (ppᵀ)` and `ppᵀ = Σ_{j=1}^m m^{-1} = 1`, a 1×1
matrix equal to `[1]`. Hence `πR = I_q`. ∎

`(ii)` `(I_q⊗pᵀ)(I_q⊗p) = I_q ⊗ (pᵀp)` and `(pᵀp)_{jj'} = Σ_j m^{-1} = 1`, so
`pᵀp = J_m` (all-ones). Thus `Rπ = I_q ⊗ J_m`. Writing `x` in blocks `x_i ∈ ℂ^m`,
`(Rπx)_{im+j} = m^{-1}Σ_{j'} x_{im+j'}`, i.e. each block is replaced by its average —
the orthogonal projection onto block-constant vectors. ∎

`(iii)` `Range(R) = {z : z_{im+j} = z_i/√m}` = block-constant subspace; `Rπx = x` iff each
block of `x` is constant; and `(I − Rπ)x = 0` iff each block of `x` equals its own average,
iff block-constant. ∎

**Status: PROVED.** Machine-checked sibling delivered: `AGDFormalGapCore` (Lean 4 core, exit 0,
axioms `[propext]`).

**Consequence that matters:** `Rπ ≠ id_H`. Reconstruction is exact **iff** `Ω` holds.
This is precisely `LinearExactSector.sigma_pi_of_blockConstant`, and it means the AGD
reverse gate is *not* free — it is a condition on the input, not a theorem.

---

## G2. Invariant preservation

**Proposition G2.** If `U = Ū ⊗ I_m` for arbitrary `Ū ∈ ℂ^{q×q}` (no unitarity, no
symmetry), then `πU = Ūπ`.

**Proof.** `(I_q⊗p)(Ū⊗I_m) = Ū ⊗ (p I_m) = Ū ⊗ p = Ū(I_q⊗p)`, using `p I_m = p`. ∎

`Ω` (block-constancy) is preserved because `U` acts only on the block index; the fibre
direction is `I_m`. **Note `Ū` need not be unitary** — the descending property is a property
of the *representation*, not of the operator's spectral properties. That is a stronger and
cheaper result than the Lean corpus's `FibreConstant`/`hcomm` hypothesis packages, which
require the intertwining to be *supplied*.

**Status: PROVED identically.** Measured confirmation: `closure_residual = 0.0` exactly on all
189 rows. Not a numerical coincidence — it is an algebraic zero, which is why the CSV shows
`0.00e+00` and not `~1e-16`.

**Smallest counterexample to a stronger false claim:** there is none, because the true
statement is stronger than the claimed one. The claim "descent preserves `Ω`" is true for all
`Ū ∈ ℂ^{q×q}`. There is no `Ū` for which it fails.

---

## G3. Reconstruction

**Proposition G3.** `π R = id_Q` (G1(i)). Hence `R(πψ)` is *the* representative of the class of
`ψ`, and `π(R(πψ)) = πψ` exactly.

**Status: PROVED.** Measured: `pi_r_identity_error ≤ 2.22e-16`, `state_max_error ≤ 2.26e-16`.

**Missing lemma (rank 1 of §14):** the ε-form. The corpus defines
`ReverseBound := d(R(Qs), s) ≤ ε` in `scaffolding/PCSSCertificate.lean:8` and never
instantiates it. For this quotient it is **disprovable as stated for arbitrary ε**:

`‖R(πx) − x‖_F = ‖blockavg(x) − x‖_F`, which is unbounded in `‖x‖`. So `ReverseBound` is
false unless `ε` scales with the input. The correct statement — **verified numerically to
machine precision (rel. err 0 … 1.1e-15 at n = 2,4,6,8,10)** — is:

```
PROPOSITION G3'. For x ∈ ℂ^d, with x_i the i-th block of length m,

   ‖R(πx) − x‖_F²  =  Σ_{i=1}^{q} ‖x_i − mean(x_i)‖²

   and consequently   ‖R(πx) − x‖_F = 0  ⟺  Ω(x)  (block-constancy),

   together with the Pythagorean identity
      ‖x‖² = ‖R(πx)‖² + ‖x − R(πx)‖²,
   which certifies R∘π is an orthogonal projection (verified rel. err ≤ 4.8e-16).
```

*Proof of G3'.* `Rπx` replaces each block `x_i ∈ ℂ^m` by its mean `mean_i` (G1(ii)), so
`(Rπx − x)_{im+j} = mean_i − x_{im+j}`. Since `Σ_j (mean_i − x_{im+j}) = 0`, we have
`Σ_j |mean_i − x_{im+j}|² = Σ_j |x_{im+j} − mean_i|²` exactly. Summing over `i` gives the
identity. ∎

(An earlier draft carried a spurious factor `(1 − 1/m)`; numerical check rejected it at
rel. err 1.0 for n = 2. The identity above is the verified form.)

This is the missing theorem, it is elementary, and it **closes the corpus's own named gap**.
It is also the first place a *real* ε appears, which is what the PCSS gate needs.

---

## G4. Complexity reduction

**Proposition G4.** `fullWork = d²`, `quotientWork = q²`, and

```
workRatio(n) = d²/q² = 2^(2n − 2⌈n/2⌉) = { 2^n   n even ;  2^(n−1)   n odd }
```

| n | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| predicted work ratio | 4 | 4 | 16 | 16 | 64 | 64 | 256 | 256 | 1024 |
| predicted compression `m` | 2 | 2 | 4 | 4 | 8 | 8 | 16 | 16 | 32 |

**Status: PROVED.** This is exactly `AGDGemmWork.outer_factorization` / `workRatio_outer`
specialised to `d = qm`, already in the Lean corpus.

**But G4 is a FLOP count, not a time.** The measured FLOP ratio at n = 10 is **1024**; the
measured *time* ratio is **356.8**. The gap is the whole story, and it is in G5/G6.

---

## G5. Hardware realization

**Model.** `T = α·F + c`, where `F` is FLOP count and `c` is fixed per-call cost (Python
dispatch + numpy entry). Fitted on this device by least squares over all four timed
quantities at all nine `n` (36 points):

```
α = 1.5528e-09  s/FLOP          (≈ 644 MFLOP/s sustained)
c = 3.4472e-06  s/call
R² = 0.99985
```

**Two independent α, and this is the key hardware fact:**

| path | effective α | interpretation |
|---|---|---|
| full, `d²` matvec | 1.560e-9 s/FLOP | large complex matvec, decent A78 utilisation |
| kernel, `q²` matvec | **4.323e-9 s/FLOP** | 32×32 complex matvec cannot fill 4×128-bit ASIMD pipes |
| π, `dq` matvec | — | 5.55e-5 s at n = 10 for `d·q = 32 768` FLOP ⇒ 1.7e-9 s/FLOP |

The **2.8× α split** between the full path and the quotient kernel is the dominant
explanation for why observed kernel speedup (356.8×) is 35 % of the FLOP ratio (1024×) — and
it is a *pure implementation* effect, not a property of the quotient.

---

## G6. Runtime inequality — the predictive test

### 6.1 Does the model predict the kernel speedup?

`pred = (α d² + c)/(α q² + c)`, fitted without ever seeing a speedup value:

| n | observed median | model prediction | obs/pred |
|---|---|---|---|
| 2 | 1.164 | 1.005 | 1.158 |
| 3 | 1.157 | 1.021 | 1.132 |
| 4 | 1.273 | 1.107 | 1.150 |
| 5 | 1.643 | 1.420 | 1.157 |
| 6 | 3.434 | 2.765 | 1.242 |
| 7 | 9.367 | 7.514 | 1.247 |
| 8 | 33.220 | 27.365 | 1.214 |
| 9 | 87.238 | 81.494 | 1.070 |
| 10 | 356.842 | 323.923 | **1.102** |

**Within 7–25 % across a 306× dynamic range, and the agreement improves with n** (2.77 vs
1.10 at the two ends of the residual). **The model predicts before execution.** The residual
is the 2.8× α split plus Python dispatch — both identified, neither mysterious.

### 6.2 The predictive quantity

```
speedup_measured(n) ≈ (α·4^n + c) / (α·4^⌈n/2⌉ + c)
                    = workRatio(n)  when  α·4^n ≫ c·4^⌈n/2⌉
```

so the framework predicts **`workRatio(n) = 2^(2n−2⌈n/2⌉)` in the compute-bound regime and
`(α·4^n + c)/(α·4^⌈n/2⌉+c) → 1` in the overhead regime.** Cross-over at
`4^⌊n/2⌋ = c/α = 2220`, i.e. **n ≈ 6**. Measured: n = 6 is the last n with kernel speedup
< 3; n = 7 jumps to 9.37. **Predicted cross-over and measured cross-over agree.**

### 6.3 End-to-end, and where predictive power is lost

`E2E = t_full / (t_proj + t_qk + t_rec)`. With `t_proj, t_rec` each `dq` FLOPs and
`t_qk` a `q²` matvec:

| n | observed E2E median | kernel median | E2E/√kernel | verdict |
|---|---|---|---|---|
| 2 | 0.284 | 1.164 | 0.263 | overhead-dominated |
| 3 | 0.285 | 1.157 | 0.265 | overhead-dominated |
| 4 | 0.321 | 1.273 | 0.285 | overhead-dominated |
| 5 | 0.398 | 1.643 | 0.311 | overhead-dominated |
| 6 | 0.727 | 3.434 | 0.392 | overhead-dominated |
| 7 | **1.496** | 9.367 | 0.489 | **break-even** |
| 8 | 3.721 | 33.220 | 0.646 | winning |
| 9 | 5.756 | 87.238 | 0.616 | winning |
| 10 | **13.647** | 356.842 | 0.722 | winning |

`E2E/√kernel` rises monotonically 0.263 → 0.722 and is still rising at n = 10. So:

```
E2E(n) ≈ √kernel(n) · ρ(n),   ρ(n) ↑,  ρ(10) = 0.722
```

**This is precisely where the mathematical model loses predictive power, and it is
identifiable to two named causes:**

1. **π and R are applied as dense `(d×q)` matvecs.** They have Kronecker structure. `(πx)_i = m^{-1/2}Σ_j x_{im+j}` costs **`d` adds**, not `d·q`. Writing `Rz` costs **`d` writes**. Dense application is a **`q`× flop waste** on each.
2. **Python/numpy dispatch `c` is paid 3× on the quotient path and 1× on the full path.**

**Verified FLOP accounting** (block sum `d` + block fill `d` + kernel `q²`, versus
`d·q + d·q + q²` dense):

| n | dense | block-exploited | gain |
|---|---|---|---|
| 6 | 1 088 | 192 | **5.67×** |
| 8 | 8 448 | 768 | **11.00×** |
| 10 | 66 560 | 3 072 | **21.67×** |

**Quantitative consequence — the largest available win on this device:** at n = 10 the
quotient-path overhead is **21.7× larger than it needs to be**, purely because two operators
with `O(d)` implementations are being run as `O(d·q)` dense matvecs.

The corrected E2E model is `α(d² − 2d − q²)/3c + 1`-shaped, i.e. E2E should approach
`kernel/3` = **119×** at n = 10 instead of the measured 13.65×. **The model says the
quotient E2E is roughly an order of magnitude better than measured, and identifies the exact
line of code responsible.**

### 6.4 Break-even, closed form vs measurement

From `α·d² + c > α·dq + α·q² + 3c`, i.e. `α(d² − dq − q²) > 2c`:

| n | `d² − dq − q²` | `α·(that)` | vs `2c = 6.89e-6` | model | measured |
|---|---|---|---|---|---|
| 6 | 4096 − 512 − 64 = 3520 | 5.47e-6 | < 2c | slower | 0.727 |
| 7 | 16384 − 2048 − 256 = 14080 | 2.19e-5 | > 2c | **faster** | **1.496** |

**The closed-form break-even condition `α(d² − dq − q²) > 2c` predicts n ≥ 7; measurement says
n ≥ 7.** Exact agreement at the boundary.

---

## 7. Predictive test against the other three experiments

| experiment | prediction | measurement | verdict |
|---|---|---|---|
| **n = 2..10 corpus** | `α(d²+c)/(αq²+c)` | within 7–25 %, improving with n | **MODEL PREDICTS** |
| **phone fiber (25 600×)** | E2E speedup predicted from model | **no timing in artifact**; 25 600 = `104857600/4096` | **NOT TESTABLE** — size ratio only |
| **governed quotient (6.19× median / 105.5× max)** | speedup = state-space count ratio `d/d_adm` = 8…2048 | 0.54× at L=4 → 105.5× at L=12 | **MODEL PREDICTS SHAPE**: both arms call the same `reference_operator`, so this measures traversal count as time. Ratio grows ~8×/2 in `L`, consistent with `2^(L/2)`. Prediction holds; it is a traversal reduction, and at `L=4` overhead dominates exactly as `c/α` predicts. |
| **NEON GEMM (7.3–14.6×)** | orthogonal to the quotient — pure SIMD | decreasing in N, consistent with cache/bandwidth, independent of `m` | **NOT a quotient result.** Correctly measured (`max_abs ≤ 2.0e-5`, PASS). Must be reported as a *separate* substrate layer. |
| **RSA frontier (≤ 304 bits)** | can the quotient formalism move it? | see below | **NO** — see §8 |

---

## 8. Does the quotient formalism predict the RSA recoverability frontier?

**No, and it should not.** The two structures are unrelated:

- The RSA frontier is governed by the **Howgrave-Graham size bound** `|h(x₀)| < N^M/2`, i.e.
  by the lattice's short-vector distribution and the root bound `X < N^{1/e}`-ish. It is a
  property of the *lattice*, not of any equivalence relation.
- `AGDFormalGap.divisible_and_small_zero` encodes exactly the size certificate
  `|y| < N`. Its proof is a two-line order argument. It does **not** produce a shorter
  lattice, a better `M`, or a larger admissible `X`.

Formally: the quotient construction gives an *exact algebraic identity* for operators of the
form `Ū ⊗ I_m`. The RSA polynomial `f(x) = x³ + 3m₀x² + 3m₀²x + (m₀³ − C mod N)` is **not**
of that form for any `m`, and `C = m³ mod N` destroys the tensor factorisation. There is no
`π` to descend through.

**Where they genuinely meet:** the Lean-encodable statement `N ∣ h(x₀) ∧ |h(x₀)| < N^M ⇒
h(x₀) = 0` (a one-line generalisation of `divisible_and_small_zero` to `N^M`) is the *precise*
obligation the lattice silently discharges by LLL's shortest-vector guarantee. That theorem
is worth writing down, and it is the honest bridge. **It does not improve the frontier.**

---

## 9. The single highest-value item

> **Implement `π = I_q ⊗ p` and `R = I_q ⊗ pᵀ` as block-structured operators instead of dense
> `(d × q)` matrices, then re-run `AGD_QUANTUM_GENERALITY_DEFINITIVE_EOF.py` unchanged in
> semantics.**

Why this is the highest-value item in the whole framework:

- It is **fully predicted before execution** by the model in §6.3: E2E should move from
  **13.647×** at n = 10 toward **`kernel/3 ≈ 119×`**, a ≈ 8.7× improvement in the headline
  end-to-end number.
- It requires **no new mathematics, no new theorem, and no new Lean file** — only
  `O(d)` instead of `O(d·q)` for two operators.
- It **converts the strongest empirical weakness** (the framework's headline "median E2E
  0.73×, i.e. slower") into its strongest result, because the pooling artifact disappears once
  the overhead regime is fixed.
- It is falsifiable in one run against a quantitative a-priori prediction, which is the
  standard the rest of the corpus should be held to.

Runner-up, and the cleanest *theorem* to add: **Proposition G3′**
(`‖R(πx) − x‖² = Σᵢ(1−1/m)‖xᵢ − mean(xᵢ)‖²`), which discharges the ε-form reverse gate that
`scaffolding/PCSSCertificate.ReverseBound` leaves as dead code — the corpus's own named gap
`actual_reconstruction_section`, closed with a proof rather than a measurement.

---

## 10. What is NOT established

- No universal/quantum speedup. Every "quantum" artifact on this host is classical
  simulation, analytic linear algebra, or circuit-declaration counting; no QPU SDK is
  installed and no backend job ID exists anywhere on disk.
- No RSA break. Structured-plaintext small-root recovery, ≤ 304 unknown bits, 10/10 hash match.
- No Lean-verified timing theorem. `MeasuredRuntimeObligation := True` remains the only
  runtime obligation defined in the corpus.
- No variance-reduction result. Both arms are equally noisy; the noise is governor/thermal.
- `π_r_identity_error`, `closure_residual`, `state_max_error` are correct **for the class
  `Ū ⊗ I_m`**. They are not evidence about arbitrary operators, and must never be reported
  as such.