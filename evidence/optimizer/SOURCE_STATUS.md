# Source / Evidence Status

Updated 2026-09-11.

## Direct executable benchmark

`Snap_9/24.py` is the primary direct SNAP/CMA-ES artifact. It contains the executable benchmark configuration and terminal output. The 24-case result table records SNAP wins on Rastrigin, rotated Rastrigin, and NoisySphere, with 9/24 overall wins.

## Quotient speedup

`AGD_REAL_SPEEDUP_GAUNTLET` is a stronger end-to-end evidence artifact because its acceptance gate explicitly includes projection, quotient execution, reconstruction/observable evaluation, and observable error. Maximum qualifying ratio recorded: 6.256345971119905x.

## SAT-style OMEGA/GF2

`omega_sandbox_speedup_rows.csv` contains repeated rows with both answers verified and `agree=True`; selected POS_INTERVAL_XOR n=500 rows report ~41.5–43.6x GF2-over-OMEGA speed ratios. These are local corpus measurements, not official competition placements.

## Formal mathematics

ChronoFold/AGD proof dossier reports P-status for operator descent, interchangeability, iteration soundness, reconstruction, residual-zero observables, finite reduction, invariant safety, and related structures. This is mathematical evidence, distinct from timing evidence.

## Publication discipline

Do not merge empirical timing into formal theorem status. Do not convert a local benchmark into a market/SOTA ranking. Preserve exact scenario identity, environment, command, seeds, repetitions, raw outputs and artifact hashes when available. Apply the repository constitution before promotion.
