# CT-004 — Conditional Scaling Extrapolation Bound

**Status:** CANDIDATE / DERIVED TARGET  
**Scope:** finite observed benchmark domain with an explicitly modeled scaling law  
**Evidence class:** CANDIDATE  

## Requirement

Determine what can legitimately be inferred about unmeasured problem sizes from measured speedups without treating extrapolation as native evidence.

## Definitions

Let `d` denote problem size and let `S(d) > 0` be the speedup ratio defined by the locked baseline and candidate measurements at size `d`.

Assume that on a declared interval `D`, the speedup obeys the model

`S(d) = a d^p`

with `a > 0`, together with a measured uncertainty model whose residuals are explicitly bounded by `epsilon(d)` in the chosen transformed domain.

For two distinct measured sizes `d1,d2` in `D`, define

`p = log(S(d2)/S(d1)) / log(d2/d1)`

and

`a = S(d1) / d1^p`.

## Candidate theorem

Under the exact scaling assumption above, the model uniquely determines `S(d)` for every `d` in the declared model domain:

`S(d) = S(d1) (d/d1)^p`.

If the fitted residual is bounded by the declared uncertainty model, the extrapolated value is a **model-derived estimate**, not a measured speedup. A publication-grade speedup claim at an unmeasured `d*` therefore cannot be classified as native empirical evidence solely from the extrapolation.

## Derivation

Taking logarithms gives

`log S(d) = log a + p log d`.

Two distinct measured points determine the affine function in `log d`, yielding the stated `p` and `a`. Substitution produces

`S(d) = S(d1)(d/d1)^p`.

The second conclusion follows from the distinction between the model's mathematical consequence and an actual execution at `d*`: no runtime observation exists at `d*` unless the benchmark is executed there.

## Proof boundary

The theorem is conditional on the scaling model. Finite observations do not prove that the model remains valid outside the measured domain, and a good in-domain fit does not establish asymptotic behavior. Hardware effects, cache transitions, algorithmic regime changes, numerical effects, and scheduler behavior may invalidate the model.

## Required evidence closure

- measured speedups at multiple locked sizes;
- exact scenario/source/input/environment identity for each measurement;
- explicit fit interval and scaling model;
- residuals and uncertainty bounds;
- a held-out measured size where feasible;
- direct native measurement at any size for which an empirical claim is made;
- separate labeling of measured, model-derived, and verified values;
- no conversion of extrapolated values into `S_verified` without the full PCSS gate.

## Speedup boundary

`S(d*)` inferred from the model is not `S_measured(d*)`. It must remain labeled extrapolated/model-derived until a native run supplies direct evidence. No `S_verified`, `S_composed`, or `S_cumulative` value is asserted by this theorem.
