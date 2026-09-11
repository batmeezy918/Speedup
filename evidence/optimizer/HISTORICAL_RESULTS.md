# Historical Optimizer / Quotient Results

Source: authorized corpus inventory, 2026-09-11. This file records source-reported results without elevating claim strength.

## SNAP vs CMA-ES — 24-case runner

Runner: `Snap_9/24.py`; 5 trials; up to 20,000 evaluations; dimensions 10, 30, 50. Source reports median final objective, median evaluations, convergence rate, winner and ratio.

SNAP wins reported:

| Problem | Dimension | SNAP median | CMA-ES median | Reported ratio |
|---|---:|---:|---:|---:|
| Rastrigin | 10 | 2.718723 | 8.954626 | 3.29x |
| RotRastrigin | 10 | 3.201733 | 11.93950 | 3.73x |
| Rastrigin | 30 | 3.814913 | 33.82858 | 8.87x |
| RotRastrigin | 30 | 3.864928 | 48.75292 | 12.61x |
| Rastrigin | 50 | 4.399032 | 75.61679 | 17.19x |
| RotRastrigin | 50 | 4.433459 | 69.64705 | 15.71x |

Additional reported SNAP wins in the same 24-case table are the three NoisySphere cases (the ratio field is `inf` because the CMA-ES objective is negative), while CMA-ES wins the remaining cases. Overall: SNAP 9/24, CMA-ES 15/24.

Source evidence: Snap_9/24.py search record.

## OMEGA / GF2 SAT-style corpus

Source spreadsheet `omega_sandbox_speedup_rows.csv` contains verified-answer agreement rows. Example POS_INTERVAL_XOR, n=500:
- param=2: repeat=5, OMEGA 0.000161904 s, GF2 0.006781082 s, both SAT, agree=True, speedup GF2/OMEGA = 41.88335x.
- param=3: repeat=1, OMEGA 0.000161899 s, GF2 0.007018139 s, both SAT, agree=True, speedup 43.34887x.
- param=5: repeat=4, OMEGA 0.000160929 s, GF2 0.007008485 s, both SAT, agree=True, speedup 43.55017x.

These are source-reported verified-answer comparisons for the listed cases, not SAT Competition rankings.

## AGD real-speedup gauntlet

Seed 42, closed world. Primary exact speedup cases: 16; semantic failures: 0; maximum qualifying speed ratio: 6.256345971119905. The gate required observable error <=1e-10, inclusion of projection/quotient/reconstruction/observable costs, and equivalent declared work.

Example PASS_SPEEDUP records:
- N=2048, K=8: full 0.001631548 s; quotient 0.000525622 s; ratio 3.1040329365x; observable error 6.8212102633e-13; reduction ratio 0.00390625.
- N=2048, K=16: full 0.001631548 s; quotient 0.000489299 s; ratio 3.3344601151x; same observable error; reduction ratio 0.0078125.

## ChronoFold quantitative quotient tests

Source dossier reports end-to-end modeled/operational speedups including cache regimes:
- cache 0%: 19.894x
- cache 25%: 13.330x
- cache 50%: 10.023x
- cache 75%: 8.031x
- cache 100%: 6.699x
- expensive quotient operator: 4.448x
- extreme one-class collapse: 6.722x

The same dossier contains explicit counterexamples where reconstruction or parallelism overhead removes speedup; these remain part of the evidence record.

## Omega optimizer

The corpus describes OMEGA as a low-rank natural-gradient optimizer and reports that it outperforms Adam and CMA in high-dimensional noisy regimes. The q7 optimizer record characterizes the result as a specific-regime advantage and identifies low-rank signal suppression as the mechanism.

## Recorded broader speedup ledger

The consolidated AGD ledger reports:
- GS254 / Ω-V185 / Sovereign Overdrive: 254.30x
- SPME-QEC: 254.30x simulated acceleration
- SIM2XR-C: 1024x theoretical scaling
- S8 Optimizer / S8 Chronograph Holo: 80.9x
- Omega Tensor Mobile v2.0: 4.91x
- Ω-SNAP⁴ structured-search report: 209.23x

These ledger values retain their source labels/statuses and are not silently converted into universal or independently ranked claims.

## Formal quotient/equivalence evidence

The formal corpus reports closed results for equivalence, operator descent, composition, iteration, reconstruction existence, residual-zero observable agreement, observable factorization, finite cardinality reduction, and certified class transitions. Objective reformulation and argmin-value equivalence are conditional on stated hypotheses. The corpus explicitly distinguishes these mathematical results from runtime speedup, wall-clock superiority, and external benchmark transfer.
