# AGD ELEVATION REPORT — FORMAL-GAP REGIME

Regime: `AGD_FORMAL_GAP_REGIME_20261008T014628Z` · 2026-10-08
Predecessor preserved: `/root/AGD_ELEVATION_20261007` (16 artifacts hashed, all verify;
`ProofCarryingQuotient.lean` = `8fea74f3…960c`, matching the hash inside its own receipt, so
the provenance chain is intact).

---

## WHAT GAP WAS FOUND

**Invariant-state redundancy.** Let `d = r·m`, and suppose the state `x ∈ ℝ^d` is
block-constant — each block of `m` entries carries one value. Under the tensor-separable
operator `U = Ū ⊗ I_m` the block-constant sector `S` is invariant, and the whole evolution
can be carried in `r` numbers instead of `d`. Projection and reconstruction are paid once
at the boundaries, not per step.

**This gap is DECLARED, not DERIVED.** The author specifies the block size and the
invariant per operator family. There is no profiler, no IR, no automatic analyser. That
is the largest distance between the directive and the system, and PHASE 6 is
correspondingly **not implemented** (see REMAINING LIMITATIONS).

## WHY IT IS FORMALLY VALID

The abstract statement is machine-checked in Lean 4 **core**, in the CI lane that forbids
`sorry`/`admit` and any `axiom`/`opaque` declaration:

```
lean lean4/AGDDescentCore.lean                → exit 0
#print axioms                                  → [Quot.sound] only
scripts/verify_lean4_all.sh lean4 core         → LEAN4_CORE_ALL_PASS=1 (43 sources)
```

```
theorem exact_reconstruction_on_invariant_orbit (hT : Descends T r) (ρ : Quot r → α)
    (S : α → Prop) (hS : Invariant S T) (hR : ReconstructsOn ρ S) (n : Nat) (x : α) :
    ρ (iter (descended T r hT) n (Quot.mk r x)) = iter T n x
```

This theorem is fully general over the state type, the operator and the sector — nothing
in it is diagonal-specific, so it does cover `Ū ⊗ I_m`. **But there is no Lean file that
names this concrete instantiation.** Hence two independent gates:

| gate | status |
|---|---|
| `semantic_gate` — the transformation's semantics are proved | **PROVED** |
| `instantiation_gate` — this concrete operator is named in Lean | **ABSENT** |

Collapsing those two into one boolean was a **real design error I made and corrected**: the
first version required `state == "CERTIFIED"`, so setting the honest state `FORMAL_PARTIAL`
disabled the optimisation entirely and the adversarial suite dropped from 19/19 to 11/19.
The two gates are now separate, and `agd_certificate_authorises_optimised` is what gates
the fast path.

## WHAT WAS TRANSFORMED

`agd_runtime.c` (diagonal operator, `y[i]=x[i]·w[(i/tile)%nw]`, refusal-only gate) →
`agd_cert.c` (tensor-separable `Ū ⊗ I_m`, two-gate certificate, **mandatory in-object
fallback**, bound certificate identity). The diagonal case is the special case `Ū`
diagonal, so this is a strict generalisation, not a replacement.

## WHAT WAS ACTUALLY EXECUTED

| binary | what it is |
|---|---|
| `bin/agd_adversarial` | 19-case suite, GATE C + GATE F |
| `bin/muni` | user-facing CLI, PHASE 9 prototype |
| `bin/libagdcert` objects | `agd_cert.o`, shared into both |

Built with `-O3 -march=native -mtune=native -funroll-loops -fomit-frame-pointer -DNDEBUG`,
gcc 14.2.0, `aarch64-linux-gnu`, on 4× Cortex-A78 @2.40 GHz + 4× Cortex-A55 @1.80 GHz,
governor `walt` (**not writable**), PRoot on an ARM phone.

## WHAT WAS MEASURED

```
ADMISSIBLE      baseline 58.045 ms   optimised 0.819 ms   speedup 70.846x   max_abs_error 0
INADMISSIBLE    baseline 58.016 ms   optimised 57.808 ms  speedup  1.004x   max_abs_error 0
```

7 trials × 5 reps, **median** reported, never the maximum. The inadmissible case is the
important one: the tool **correctly refuses** and delivers 1.004× rather than a spurious
speedup.

**Adversarial suite: PASS 19/19.** Every case is scored on one criterion — the plan's
output after reconstruction must equal the ORIGINAL operator on the ORIGINAL state:

- admissible × 3 operator families (dense, diagonal, phase) → optimised path, `maxerr 0`
- **perturb one element by 1.0** × 3 → MUST fall back, `maxerr 0`
- fully random × 3 → MUST fall back, `maxerr 0`
- `tol=1e-6` admits a `1e-9` perturbation → err `8.58e-18`
- `tol=0` refuses that same state
- `UNVERIFIED` certificate forces fallback **even on admissible input**
- illegal shapes (`d % m ≠ 0`, `NULL` state, `m = 0`) → `NULL` plan
- `m = 1` (`r = d`, no compression) and `m = d` (`r = 1`, maximal compression)
- 1000-step trajectory → err exactly `0`, no drift
- multi-size / multi-family sweep → 4/4 exact on the optimised path

## WHAT FAILED

Preserved, not hidden.

1. **Two of my own harness bugs, both caught by the suite itself.**
   - The `m=1`/`m=d` cases passed `r = d` to `agd_original_apply` while `U` was built for
     `r = 16` — out-of-bounds read, **segfault**. Fixed by giving each degenerate shape its
     own `U`.
   - The `tol=1e-6` case was scored against `err == 0.0` when the correct criterion is
     `err ≤ tol`; the three `NULL` cases scored `fallback` columns that are meaningless
     when a `NULL` is expected. Both were harness errors, not library errors.
2. **A blocked-full-arm experiment is QUARANTINED.** It contained
   `if (w == 0.0) continue;`, so for the sparse families (`perm`, `diagphase`) the
   "blocked" arm skipped work the strided arm performed — a **baseline mismatch**, not a
   memory effect. It produced asymptotes of 0.8–1.9× that were an artifact. Superseded by
   a zero-skip-removed controlled build.
3. **The prediction "asymptotic ratio ≈ m" is REFUTED** at d = 16384 (148–153× vs m = 64).
   The excess is cache-driven and dimension-dependent, and is *not* yet fixed.
4. **`path gain ≤ q` is REFUTED** as a universal bound (measured 70.3× against `q = 64`).
   It holds only while both arms are FLOP-bound.

## WHAT SURVIVED

- Bit-exact semantics (`max_abs_error = 0`) for `Ū ⊗ I_m` on the invariant sector,
  3 operator families, 19 adversarial cases, 1000-step trajectories.
- **A safety contract that works**: certificate-authorised **and** admissible → quotient
  path; otherwise → original path inside the same object. Demonstrated in both directions
  through the user-facing CLI.
- The amortisation law `1/E2E(k) = a/k + b` at R² = 0.965–0.9996 (from the predecessor).
- A user-facing `muni elevate` that reports gap, gates, speedup, machine precision,
  certificate identity and an honest claim class.

## BASELINE DETAILS

**Not a strawman.** The baseline is the *same operator* `Ū ⊗ I_m` applied densely —
`d·r` multiply-adds per step, exactly the unoptimised form. Both arms are compiled with
identical flags in one translation unit. `agd_tensored_amortized.c` runs the identical
comparison in a separate harness.

## SILICON DETAILS

4× Cortex-A78 @2.40 GHz (cpu4–7) + 4× Cortex-A55 @1.80 GHz (cpu0–3); governor `walt`,
**not writable** without root, so frequency is uncontrollable; thermal 46–56 °C; PRoot
userspace chroot on an ARM phone. **Single host — no cross-environment validation.**

## SPEEDUP ACCOUNTING

| component | value |
|---|---|
| structural reduction | `r = d/m`: 64 values instead of 4096 → **64×** |
| arithmetic reduction | `d·r = 262 144` FMA vs `r² = 4 096` FMA → **64×** |
| memory traffic | quotient re-reads `r·8` B; full re-reads `d·8` B per step |
| compiler / vectorisation | **NOT isolated** (identical flags both arms) |
| cache / locality | **NOT isolated** here; the cache excess is characterised separately in `TENSOR_OPERATOR_RESULT_20261008.md` |
| amortisation | plan created per run; setup charged to the optimised arm |
| **total measured** | **70.846×** |

70.846× is ≈1.11× the pure work ratio of 64×. The residual is **consistent with** the
cache effect measured separately, but is **not** isolated in this harness, so it is not
attributed to the mathematics.

## FORMAL STATUS

`FORMAL_PARTIAL`. The abstract Level-2/3/4/7 calculus is `FORMAL_CLOSED` in Lean core
(`[Quot.sound]` only). The `Mathlib` dressing (`lean4/Mathlib/AGDDescentMathlib.lean`) is a
**CI-target proposal and has never been kernel-checked**. `ProofCarryingQuotient.lean`
still certifies **v1 diagonal**; the tensor-separable instantiation is measured, not proved.

## NATIVE STATUS

`VERIFIED_NATIVE` — aarch64 gcc 14.2.0, `-O3 -march=native`, both binaries built and run.

## CALLABLE STATUS

`VERIFIED_NATIVE` — `agd_plan_create/step/run/reconstruct/size/destroy`, plus
`agd_plan_admissible`, `agd_plan_certified`, `agd_plan_in_fallback`,
`agd_plan_transformation_id`, `agd_plan_certificate`.

## MUNI STATUS

**PROTOTYPE.** `muni elevate --d N --m M --steps K [--inadmissible] [--json out]`. It
generates its own workload and times its own arms; it does **not yet** build, profile or
analyse a user's repository. Calling it a user-facing optimisation tool for arbitrary
software would overstate it.

## CLAIM CLASSIFICATION

| aspect | class |
|---|---|
| semantic preservation | `VERIFIED_SEMANTIC` |
| native artifact | `VERIFIED_NATIVE` |
| adversarial | `ADVERSARIAL_VERIFIED` |
| performance | **`FORMAL_PARTIAL_MEASURED_LOCAL`** |
| universal | `QUARANTINED` — none made |

Performance is deliberately **not** promoted to `MEASURED_LOCAL_NATIVE`, because the
instantiation gate is absent. No amount of speedup can promote it.

## REMAINING LIMITATIONS

1. **PHASE 6 is not implemented.** No automatic analysis of arbitrary software. The gap is
   declared per family by the author. This is the single biggest gap between the directive
   and the system, and it is not a matter of polish.
2. **The instantiation gate is ABSENT.** Writing a Lean file naming `Ū ⊗ I_m` and proving
   it against `AGDDescent.exact_reconstruction_on_invariant_orbit` would close it and
   promote the claim to `MEASURED_LOCAL_NATIVE`. That is the highest-value single action.
3. **The block-constant input is constructed, then validated.** The invariant is guaranteed
   by construction; nothing here discovers it in real data.
4. **`Ū ⊗ I_m` is still a special structure.** A dense non-separable operator is not covered.
5. **Single host.** `walt` is not writable; frequency is uncontrollable; thermal varies.
6. **The cache excess at d = 16384 is diagnosed but not fixed.** A blocked full arm would
   test whether the asymptote collapses toward `m`.
7. **The controlled blocked-vs-strided A/B is incomplete.** The zero-skip-removed rebuild
   succeeded but the timing run exceeded its budget and was not completed.

## HIGHEST-VALUE NEXT OPERATION

**Write the Lean instantiation file.** Take
`AGDDescent.exact_reconstruction_on_invariant_orbit` (machine-checked, general) and
instantiate it at `U = Ū ⊗ I_m` with `S` = block-constant. One file in the core lane,
verified by the same `lean-ci.yml` that already passes 43 sources. It closes the only gate
between `FORMAL_PARTIAL_MEASURED_LOCAL` and `MEASURED_LOCAL_NATIVE`, and it is
distinguishable from prior art because the claim is about the *instantiation*, not the
abstract descent, which Mathlib already has.