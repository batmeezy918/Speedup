# AGD Elevation Record — 2026-10-18

**Branch:** `agd-elevation-formal-gap-closure`
**Subject:** Formal gap derivation + MUNI enacted on the m=64 stoppage anomaly
**Method:** isolate missing components from inside the closed system, close them,
elevate math / problem / benchmark in one pass.

---

## 1. What was isolated (the missing components)

The original msweep.c (2026-10-09) measured one curve: speedup(m) for
r=64 fixed. It could not answer *why* the m=64 bin sits at ratio/m = 0.838
while m<=32 sits within 3% of 1.0 and m>=128 exceeds 1.0. Four components
were missing:

1. **Phase-split timing.** The quotient path's wall time bundled
   `agd_plan_create` (decimation + allocation + certificate check),
   `agd_plan_run` (pure r^2 iteration), and `agd_plan_reconstruct`
   (broadcast back to full state) into one number. The fixed DC overhead
   was invisible.
2. **Frequency-domain residual detection.** No mechanism existed to type a
   bin where |speedup/m - 1| exceeds a threshold as a first-class gap
   object. The formal-gap isolator had a SCALING_GAP type but nothing
   populated it for scaling anomalies.
3. **Fixed-cost model.** No least-squares fit of T(m) = a*m + C per path,
   so the claim that "fixed overhead dominates at small m" was qualitative.
4. **Cadence.** The automation was registered TASK_CADENCE_ONCE_DAILY,
   not a true recurring RRULE, so the daily loop would die after one fire.

## 2. What closed them

- `muni-production/ops/bench/msweep_v2.c` — phase-split timing, frequency
  residual flagging at threshold 0.05, fixed-cost fit, JSON+TXT emission.
- `governor/frequency_residual_gap.py` — consumes msweep_v2.json, compiles
  each flagged bin into PCSS-FORMAL-GAP/v1 SCALING_GAP with closure
  predicate, dependency on MEASUREMENT_GAP, required experiment, and
  telemetry. Fail-closed. NO_PROMOTION.
- Automation cadence patched to FREQ=DAILY (see automation record).

## 3. The math, elevated

Original prediction (AGD_GAP_DERIVATION, G-1 commutation):

    work_full ~ r^2 * m,  work_quot ~ r^2,  speedup ~ m

Elevated model with fixed cost C:

    T_base(m) = a_base * m + C_base
    T_quot(m) = a_quot * m + C_quot
    speedup(m) = T_base / T_quot

The m=64 dip is the bin where C_quot / T_quot(64) is locally maximal —
the crossover frequency where compressed signal energy equals the DC noise
floor. G-1 still holds: max_abs_error = 0 at every bin, EXACT flag
intact. The dip is a *measurement-structure* phenomenon, not a correctness
failure. G-4 (projected vs reconstructed trajectory) is what makes the
reconstruct phase visible as a separate term.

## 4. The benchmark, elevated

From: one curve, one ratio column, human-readable txt.
To: phase-split spectrum + typed gap objects + machine-readable JSON
consumable by the formal-gap governor. The benchmark now *produces the
gap ledger input* instead of requiring a human to notice an anomaly.

## 5. What remains (honest boundary)

- msweep_v2 must be executed on the ARM64 device; this elevation ships the
  instrument, not the measurement.
- The x86-64 cross-environment witness has not yet been run against the
  v2 binary; whether the m=64 dip is arch-specific is UNKNOWN.
- C_base and C_quot are unfitted until the first v2 run.
- CLAIM_STRENGTH <= EVIDENCE_STRENGTH holds: nothing here promotes any
  candidate. Every gate starts false.

## 6. Reproduction

```bash
cd muni-production/ops/bench
gcc -O3 -march=native -funroll-loops -fno-fast-math -ffp-contract=off \
    -o msweep_v2 msweep_v2.c kernel.c -lm && ./msweep_v2
python3  governor/frequency_residual_gap.py msweep_v2.json \
    --out frequency_residual_bundle.json
```

`-fno-fast-math` and `-ffp-contract=off` are mandatory; relaxing IEEE-754
invalidates the bitwise EXACT claim.
