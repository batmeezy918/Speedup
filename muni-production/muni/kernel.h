/* kernel.h - the production callable surface of MUNI.
 *
 * One entry point, no bypass:
 *   munirun() takes the caller's REAL quotient operator and REAL full state,
 *   MEASURES the invariant sector, and either runs the certified quotient or
 *   the original full-state operator. It never silently takes the fast path.
 *
 * Provenance: the algebraic law proved in Lean 4 (AGD_TENSOR_INSTANTIATION.lean,
 * AGD.recursive_exact_reconstruction) applies to U = Ubar (x) I_m on the
 * block-constant sector. Everything here is bound to that scope and nothing
 * outside it.
 */
#ifndef MUNI_KERNEL_H
#define MUNI_KERNEL_H
#include <stddef.h>
#include <stdint.h>
#include "kernel_agl.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Status codes (mirrored in muni/__init__.py) */
enum {
  MUNI_OK_QUOTIENT   = 0,  /* certified quotient path executed, exact        */
  MUNI_OK_FALLBACK   = 1,  /* inadmissible -> original path, exact         */
  MUNI_ERR_SHAPE     = 2,  /* illegal shape: r==0, m==0, or null pointer   */
  MUNI_ERR_ALLOC     = 3,  /* allocation failure                           */
  MUNI_ERR_NONFINITE = 4   /* NaN or Inf present: outside every scope     */
};

/* Run `steps` iterations of U = Ubar (x) I_m on the block-constant sector.
 *
 *   Ubar            r*r quotient operator, row-major, caller-owned, finite
 *   r               quotient dimension
 *   m               fiber size; d = r*m
 *   x0              d initial full state, caller-owned, finite
 *   steps           number of iterations (0 is legal and means identity)
 *   out_full        d doubles, receives the ORIGINAL full-state result
 *                   (this is the reference the fast path is checked against)
 *   out_fast        d doubles, receives the optimised result
 *   used_quotient   1 if the quotient path ran, 0 if it fell back
 *   max_abs_error   max |out_full - out_fast| over all d coordinates
 *   residual        measured max deviation of any fiber from its block head
 *   tol             admissibility tolerance; fibers within tol count as
 *                   identical
 *
 * Returns one of the status codes above. Both outputs are always written on
 * success, so the caller can verify exactness itself rather than trusting a
 * flag. */
int munirun(const double *Ubar, size_t r, size_t m,
            const double *x0, size_t steps,
            double *out_full, double *out_fast,
            int *used_quotient, double *max_abs_error,
            double *residual, double tol);

/* Honest two-arm benchmark: ORIGINAL vs OPTIMISED, interleaved in one
 * process, median of `trials`, each trial the mean of `reps`, warm-up not
 * separately discarded (callers should pass reps>=3). The optimised arm is
 * timed the way it is meant to be used: create/project once, run all steps,
 * reconstruct once, destroy. Returns MUNI_OK_QUOTIENT and fills the outputs. */
int munibench(const double *Ubar, size_t r, size_t m,
              const double *x0, size_t steps, size_t trials, size_t reps,
              double tol, double *base_ms, double *opt_ms, double *speedup,
              double *max_abs_error, int *used_quotient);

#ifdef __cplusplus
}
#endif
#endif
