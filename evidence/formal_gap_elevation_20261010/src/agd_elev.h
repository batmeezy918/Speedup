#ifndef AGD_ELEV_H
#define AGD_ELEV_H
#include <stddef.h>

/* Materialize A = U (x) I_m as a d x d row-major matrix (d = r*m).
   A[(b*m+j)*d + (c*m+k)] = U[b*r + c] when j == k, else 0.
   This is the structure-BLIND representation: a general dense operator that a
   caller who did not know the tensor form would be handed. */
void agd_build_tensor_dense(double *A, const double *U,
                            size_t d, size_t m, size_t r);

/* Structure-blind dense matvec y = A x, O(d^2). Honest "naive dense" baseline. */
void agd_dense_apply(const double *A, const double *x, double *y, size_t d);

/* Named physical workload: explicit 1D diffusion (heat) stencil, periodic BC.
   U[b][b] = 1 - 2a ; U[b][b-1] = U[b][b+1] = a (cyclic). Size r x r. */
void agd_heat_U(double *U, size_t r, double a);

/* The SAME stencil written as a direct three-point update, NOT through U.
   In exact arithmetic identical to agd_original_apply with the heat U; in
   binary64 it differs only by association order. Used to expose the residual
   refinement obligation (o4) rather than hide it. */
void agd_heat_direct_step(const double *x, double *y,
                          size_t d, size_t m, size_t r, double a);

/* Runtime refinement self-test: on this exact binary, does one block-constant
   step produce BIT-IDENTICAL results on the full-state path and the quotient
   path? Returns 1 if yes. This is a runtime WITNESS of path agreement (catches
   -ffast-math / FMA contraction differences between the two loop shapes); it is
   NOT a kernel proof of C-vs-model refinement. Wired into a guarded plan so a
   mismatch falls back. */
int agd_refine_selftest(void);

/* MUNI hardening (from gap O2b): a NONZERO tolerance admits states whose
   reconstruction error accumulates across steps and is NOT bounded by tol.
   This classifier makes the guarantee explicit so the tool can never overstate:
   tol == 0  -> "EXACT_BITWISE"      (the only bit-exact regime)
   tol  > 0  -> "APPROX_UNBOUNDED"   (empirically finite, no proven budget) */
const char *agd_tolerance_claim(double tol);

#endif

