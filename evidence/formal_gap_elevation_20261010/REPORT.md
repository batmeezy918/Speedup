# AGD / MUNI Research-Grade Elevation — Formal Gap Derivation

Date: 2026-10-10
Scope: tasks **1, 3, 4, 5, 6, 7** (task 2, invariant auto-discovery, explicitly
excluded; the block-constant invariant is assumed by design).
Device: Moto G Power 5G (2024), Android 16, AArch64, Debian PRoot.
Toolchain: gcc 14.2.0, Lean 4.29.0, Python 3.13.5.

Everything below is produced by `run_all.sh` and stored under `receipts/`
with `receipts/deliverables.sha256`. No divergent source copies exist.

---

## Headline results

| Claim | Value | Evidence |
|---|---|---|
| Speedup vs general dense (median of 9 sessions) | **6774x** (min 6668, max 7682) | `receipts/session_stats.txt` |
| Speedup vs structured baseline (median) | **68.5x** (min 67.6, max 68.9) | `receipts/session_stats.txt` |
| General dense is honest (dense path really runs) | dense_ms=172, dense_abs_error=0 | `receipts/bench.txt` |
| A/A noise floor (null difference) | median 0.02%, worst session 14.8% | `receipts/session_stats.txt` |
| Adversarial suite | 23/23 PASS, exit 0 | `receipts/adversarial.txt` |
| Property fuzz (20 000 cases) | 0 violations | `receipts/fuzz.txt` |
| Lean core lane | ALL PASS, 46 sources | `receipts/lean_core_verification.log` |
| Recursive gap ledger | 8 closed, 1 open, 1 residual, 1 assumed | `receipts/gap_ledger.txt` |

The speedup medians (68.5x, 6774x) exceed the A/A noise floor (worst 14.8%, median
0.02%) by orders of magnitude, so the claims are robust. The 14.8% outlier session
is real environment variance on a single-core PRoot and is why we report session
medians, not single runs.

---

## Task 1 — honest general dense baseline

`agd_elev bench` builds the tensor-separable operator and compares three paths on
identical work:

```
structured_ms=1.59   dense_ms=172.18   quotient_ms=0.0252
speedup_vs_structured=63.2   speedup_vs_dense=6835   dense_vs_structured=108
max_abs_error_quotient=0     dense_abs_error=0
```

The `dense` path materialises and applies a full d×d operator (172 ms), so
`speedup_vs_dense` is measured against a genuine general baseline, not the
structured one. `dense_abs_error=0` proves the baseline computes the same result.

## Task 3 — close / prove the refinement gap

`lean4/AGDRefinement.lean` proves fold-level refinement over an abstract carrier:
`fullCoord_eq_quotCoord_of_blockConstant`, `fstep_eq_qstep_coord`, `iter_refines`,
`float_iter_refines`. Axiom footprint: `[Quot.sound]` (`float_iter_refines` adds
`Classical.choice`); **no `sorryAx`**. This closes the gap at the
model/operation-order level (ledger obligation O4a).

The residual is the C-binary ↔ Lean-model binding (O4c): proving the compiled
binary implements the Lean fold order needs a verified-float/compiler artifact
(CompCert/Frama-C) and is honestly left as a named residual.

## Task 4 — property-based gate fuzzing

`agd_fuzz` (seed 20261010, 20 000 cases) exercises five properties:
P1 fallback exactness, P2 optimized exact at tol=0, P3 gate soundness,
P4 fail-closed on tamper, P5 output confined to the block-constant sector.

```
FUZZ cases=20000 optimal=9535 fallback=10465 null=0 tampered=4952 violations=0
FUZZ_RESULT=PASS
```

It also surfaced the tolerance-accumulation gap below.

## Task 5 — named real workload

`agd_elev heat` runs the stencil as an explicit 1-D heat/diffusion kernel over a
block-constant field, comparing the quotient path against the full path and
against a hand-written direct three-point update:

```
speedup_vs_structured=68.4   max_abs_error_quotient=0
direct_stencil_abs_error=2.22e-16   (one ulp, 32 steps)
```

`max_abs_error_quotient=0` is bit-exact; the `2.22e-16` records the one-ulp
association-order residual against the hand-written stencil (obligation O4).

## Task 6 — multi-session statistics + noise floor

`run_sessions.sh` runs 9 independent bench sessions and 9 A/A (quotient vs
quotient) sessions; `aggregate_sessions.py` reports medians and spread. A/A on a
null difference is median 0.02% but reaches 14.8% in the worst session — the
honest single-core dispersion. See the headline table.

## Task 7 — recursive formal gap derivation (strengthening MUNI)

The gap derivation (`lean4/AGDGapDerivation.lean`) proves admissibility is
sufficient and its failure is necessary, so any gap is real. `agd_gap_ledger.py`
turns that into a recursive operational process: enumerate obligations, probe
each, let closed obligations reveal successors, and iterate to a fixed point.
Trace (`receipts/gap_ledger_trace.txt`):

```
[1] O1  operator is certified U(x)I_m ................ ASSUMED (chosen invariant)
[2] O2  admissibility gate sound (tol=0 exact) ....... CLOSED
[3] O2b nonzero tolerance bounds error over steps .... OPEN   <-- discovered gap
[4] O2b_guard MUNI refuses to label tol>0 as exact ... CLOSED <-- hardening applied
[5] O3  certificate fails closed on tamper ........... CLOSED
[6] O4a refinement (model order, Lean) ............... CLOSED
[7] O4b native binary path agreement (selftest) ...... CLOSED
[8] O4c C binary == Lean float model ................. RESIDUAL
[9] O5  exact reconstruction on the sector .......... CLOSED
[10] O6 baseline is genuinely general dense ......... CLOSED
[11] O7 timing claims exceed a measured noise floor . CLOSED
```

Recursion chain: O4a → O4b → O4c.

### Discovered gap O2b (real, and now guarded)

A nonzero tolerance admits states whose reconstruction error **accumulates across
steps and is not bounded by the tolerance**:

```
tol = 9.99e-10  ->  observed max output error = 3.15e-07   (315x the tolerance)
```

So only `tol = 0` is bit-exact; `tol > 0` is approximate with no proven budget.
Only a contraction argument or removal of `tol>0` closes this mathematically.

**MUNI hardening applied (O2b_guard):** `agd_tolerance_claim()` classifies the
guarantee so the tool can never overstate a tolerance-gated result:

```
CLAIM_TOL0   = EXACT_BITWISE
CLAIM_TOLPOS = APPROX_UNBOUNDED
```

`agd_refine_selftest()` additionally verifies at runtime that the two paths agree
bit-for-bit on the actual binary (catches `-ffast-math`/FMA contraction between
the two loop shapes) and refuses the optimized path on mismatch.

---

## Reproduce

```
bash run_all.sh          # build, all tests, sessions, ledger, hash manifest
bash run_sessions.sh 9   # session timing only
python3 agd_gap_ledger.py 5
bash /root/Speedup/scripts/verify_lean4_all.sh /root/Speedup/lean4 core \
     --hash-out receipts/lean_core_hashes.sha256
```

## Remaining uncertainty

- **O2b** (open, guarded): `tol>0` error is not provably bounded; a contraction
  condition or removal is required to close it.
- **O4c** (residual): the compiled binary ↔ Lean float-model binding is not
  kernel-proved; needs a verified-float/compiler refinement.
- **O1** (assumed): the operator is assumed to be the certified U⊗I_m; automatic
  invariant discovery is out of scope by instruction.
- Timing is single-core PRoot; medians are used and the A/A floor is reported.
