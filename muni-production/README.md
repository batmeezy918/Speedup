# MUNI — certified exact quotient reduction

Run your real arrays through a kernel whose algebra is proved in Lean 4, and get
an honest, measured, per-call answer about whether you got a speedup.

```python
import muni

Ubar = [[0.9, 0.1], [0.2, 0.8]]     # r x r quotient operator
x0    = [1.0, 1.0, 2.0, 2.0]        # d = r*m, constant across each fiber of m=2

res = muni.run(Ubar, x0, steps=64)

res.used_quotient   # True  -> certified quotient path ran
res.exact           # True  -> optimised result == original result, bit for bit
res.max_abs_error   # 0.0
res.reason          # 'ADMISSIBLE: state is constant across each fiber; ...'
res.receipt         # a full JSON record of the run, including input hashes
```

If your data is not block-constant the kernel refuses the fast path and says so:

```python
res = muni.run(Ubar, [1.0, 1.1, 2.0, 2.0], steps=64)
res.used_quotient   # False
res.exact           # True  -- still correct, just not faster
res.reason          # 'INADMISSIBLE: state leaves the block-constant sector; ...'
```

To decide whether it is worth enabling:

```python
bench = muni.benchmark(Ubar, x0, steps=64, trials=7, reps=5)
bench.speedup       # measured on YOUR arrays, both arms, one process
bench.baseline_ms, bench.optimised_ms
```

## What the claim actually is

> Exact quotient reduction for operators `U = Ū ⊗ I_m` applied to states that
> are constant across each identity fiber. The algebraic law is proved in Lean 4
> (`AGD.recursive_exact_reconstruction`); the native kernel implements exactly
> that law and is checked against the original full-state operator on **every
> call**.

That is the whole claim. Specifically **not** claimed:

- Not a general-purpose accelerator. The speedup exists only when the input is
  constant across each fiber. Otherwise it falls back.
- No claim for arbitrary operators, arbitrary neural-network weights, or shapes
  outside `U = Ū ⊗ I_m`.
- Speedups are measured per call on your data and are workload- and
  machine-specific. Do not multiply them or quote them without the receipt.
- No independent-hardware replication: the evidence package comes from one ARM64
  device under two runtimes.
- No automatic discovery of invariant sectors. Admissibility is *measured* from
  data you supply.
- No research-priority, patent-novelty, or prior-art claim.

`muni.claim()` returns all of this as data, along with the current evidence
hashes, so your users cannot be misled by a downstream summary.

## Why you can trust `exact`

`muni.run()` never takes your word for anything:

1. The kernel **always** computes the original full-state result as well.
2. `exact` is computed by comparing the two outputs, not asserted.
3. `res.reference` is returned so you can verify yourself.
4. Non-finite input is refused outright rather than silently propagated.

```python
res = muni.run(Ubar, x0, steps=64)
assert res.values == res.reference        # you can check this yourself
```

## Install

```bash
git clone https://github.com/batmeezy918/Speedup
cd Speedup/muni-production        # or wherever this package lives
make                # builds libmuni.so
make test           # 22 tests
make proof          # re-verifies all Lean proofs, axiom check
make evidence       # regenerates evidence/evidence.json and SHA256SUMS.txt
```

Requires a C compiler. `-fno-fast-math -ffp-contract=off` are mandatory — the
IEEE semantics must not be relaxed or the bytewise guarantee is void.

## Real-world carriers

The kernel applies when your state is literally replicated across fibers:

| Domain | Structure | Why the sector holds |
|---|---|---|
| Detector sub-channels | `m` identical sub-channels per event | one binned count stored per sub-channel |
| Multicore / fibre bundles | `m` identical waveguides | identical propagation coefficients |
| Phased arrays | `m` identical ADC channels per element | matched electronics |
| Thermal panel arrays | `m` identical quadrature nodes | identical discretisation |
| Phonon transport | `m` identical atoms per unit cell | translational symmetry |

Check before you commit, with no cost:

```python
resid, bad_blocks, total = muni.measure_sector(your_state, m)
if bad_blocks == 0:
    ...   # worth enabling
```

Real measured data that is **not** block-constant — global temperature by
month, seismic per-event observables — will correctly report as inadmissible.
That refusal is the product working, not failing.

## Known characteristics

- **Signed zero** does not survive an iteration in either arm (both accumulate
  into `acc = 0.0`). The two arms still agree bit-for-bit, which is the enforced
  contract. Pin this behaviour with `tests/test_muni.py`.
- **The admissibility gate is numeric, not bitwise.** `-0.0` and `+0.0` compare
  equal, so they are treated as the same fiber value.
- **`speedup` is never extrapolated.** It is `baseline_ms / optimised_ms` from
  this call.

## License

Apache-2.0. See `LICENSE`.