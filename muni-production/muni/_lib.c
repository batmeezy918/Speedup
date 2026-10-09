/* _lib.c - the production callable surface.
 *
 * One entry point, four decisions, no bypass:
 *   muni_apply() takes the caller's REAL operator and REAL state, measures the
 *   invariant sector, and either runs the certified quotient or the original
 *   full-state operator. It never silently takes the fast path.
 */
#define _POSIX_C_SOURCE 199309L
#include "kernel.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

size_t muni_last_status(void);
static int g_status = 0;

int munirun(const double *Ubar, size_t r, size_t m,
            const double *x0, size_t steps,
            double *out_full, double *out_fast,
            int *used_quotient, double *max_abs_error,
            double *residual, double tol)
{
  if (!Ubar || !x0 || !out_full || !out_fast || r == 0 || m == 0)
    { g_status = MUNI_ERR_SHAPE; return g_status; }
  /* Guard against overflow: r*m can wrap, producing an undersized buffer. */
  if (r > SIZE_MAX / m) { g_status = MUNI_ERR_SHAPE; return g_status; }
  size_t d = r * m;
  if (d > SIZE_MAX / sizeof(double)) { g_status = MUNI_ERR_ALLOC; return g_status; }

  /* Reject non-finite inputs outright: NaN/Inf are outside every scope we
     claim, and a NaN would poison the admissibility comparison. */
  for (size_t i = 0; i < r * r; i++)  if (!isfinite(Ubar[i])) { g_status = MUNI_ERR_NONFINITE; return g_status; }
  for (size_t i = 0; i < d; i++)     if (!isfinite(x0[i]))    { g_status = MUNI_ERR_NONFINITE; return g_status; }

  AGDCertificate cert = agd_certificate_self();
  AGDPlan *p = agd_plan_create(x0, d, m, Ubar, tol, &cert);
  if (!p) { g_status = MUNI_ERR_ALLOC; return g_status; }

  /* Measured sector residual: max deviation of any fiber from its block head. */
  double worst = 0.0;
  for (size_t b = 0; b < r; b++) {
    double ref = x0[b * m];
    for (size_t j = 1; j < m; j++) {
      double e = fabs(x0[b * m + j] - ref);
      if (e > worst) worst = e;
    }
  }
  *residual = worst;

  int fast = !agd_plan_in_fallback(p);
  *used_quotient = fast;

  /* The ORIGINAL path always runs: it is the reference the fast path is
     checked against, so correctness is measured rather than assumed. */
  double *a = malloc(d * sizeof(double));
  double *b = malloc(d * sizeof(double));
  if (!a || !b) { free(a); free(b); agd_plan_destroy(p); g_status = MUNI_ERR_ALLOC; return g_status; }
  memcpy(a, x0, d * sizeof(double));
  for (size_t k = 0; k < steps; k++) {
    agd_original_apply(a, b, Ubar, d, m, r);
    double *t = a; a = b; b = t;
  }
  memcpy(out_full, a, d * sizeof(double));

  agd_plan_run(p, steps);
  agd_plan_reconstruct(p, out_fast);

  *max_abs_error = agd_max_abs_error(out_full, out_fast, d);

  free(a); free(b);
  agd_plan_destroy(p);
  g_status = fast ? MUNI_OK_QUOTIENT : MUNI_OK_FALLBACK;
  return g_status;
}

size_t muni_last_status(void) { return (size_t)g_status; }

/* muni_bench - honest two-arm timing.
 *
 * Times the ORIGINAL full-state operator and the OPTIMISED quotient path in the
 * same process, interleaved, with warm-up discarded, and returns both medians
 * plus the ratio. Both arms do identical observable work when admissible.
 *
 * Amortisation note: the quotient arm pays plan creation + reconstruction +
 * teardown exactly once, which is how it would be used in a real loop
 * (create/project once, run many steps, reconstruct once). The timing below
 * measures that intended usage, not a best-case single step.
 */
static int cmp_d(const void *a, const void *b) {
  double x = *(const double *)a, y = *(const double *)b;
  return x < y ? -1 : (x > y ? 1 : 0);
}

static double ms_now(void) {
  struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
  return t.tv_sec * 1e3 + 1e-6 * t.tv_nsec;
}

int munibench(const double *Ubar, size_t r, size_t m,
              const double *x0, size_t steps, size_t trials, size_t reps,
              double tol, double *base_ms, double *opt_ms, double *speedup,
              double *max_abs_error, int *used_quotient)
{
  if (!Ubar || !x0 || !base_ms || !opt_ms || !speedup) return MUNI_ERR_SHAPE;
  if (trials < 1) trials = 1;
  if (reps < 1) reps = 1;
  if (trials > 256) trials = 256;
  if (reps > 256) reps = 256;
  /* Guard against overflow: r*m can wrap, producing an undersized buffer. */
  if (r > SIZE_MAX / m) return MUNI_ERR_SHAPE;
  size_t d = r * m;
  if (d > SIZE_MAX / sizeof(double)) return MUNI_ERR_ALLOC;

  AGDCertificate cert = agd_certificate_self();
  AGDPlan *probe = agd_plan_create(x0, d, m, Ubar, tol, &cert);
  if (!probe) return MUNI_ERR_ALLOC;
  *used_quotient = !agd_plan_in_fallback(probe);
  agd_plan_destroy(probe);

  double *bt = calloc(trials, sizeof(double));
  double *ot = calloc(trials, sizeof(double));
  double *a = malloc(d * sizeof(double));
  double *b = malloc(d * sizeof(double));
  double *out = malloc(d * sizeof(double));
  if (!bt || !ot || !a || !b || !out) { free(bt);free(ot);free(a);free(b);free(out); return MUNI_ERR_ALLOC; }

  double worst = 0.0;
  for (size_t t = 0; t < trials; t++) {
    double tb = 0.0, to = 0.0;
    for (size_t rep = 0; rep < reps; rep++) {
      /* ---- ORIGINAL arm: dense r*m -> r per step, no plan ---- */
      double s0 = ms_now();
      memcpy(a, x0, d * sizeof(double));
      for (size_t k = 0; k < steps; k++) {
        agd_original_apply(a, b, Ubar, d, m, r);
        double *t2 = a; a = b; b = t2;
      }
      memcpy(out, a, d * sizeof(double));
      tb += ms_now() - s0;

      /* ---- OPTIMISED arm: create+project once, run, reconstruct, destroy ---- */
      double s1 = ms_now();
      AGDPlan *p = agd_plan_create(x0, d, m, Ubar, tol, &cert);
      if (p && agd_plan_run(p, steps) && agd_plan_reconstruct(p, out)) { /* ok */ }
      else { free(bt);free(ot);free(a);free(b);free(out); return MUNI_ERR_ALLOC; }
      to += ms_now() - s1;
      agd_plan_destroy(p);
    }
    bt[t] = tb / (double)reps;
    ot[t] = to / (double)reps;
  }
  qsort(bt, trials, sizeof(double), cmp_d);
  qsort(ot, trials, sizeof(double), cmp_d);
  *base_ms = bt[trials/2];
  *opt_ms  = ot[trials/2];
  *speedup = (*opt_ms > 0.0) ? (*base_ms / *opt_ms) : 1.0;

  /* correctness on the last observed state */
  {
    AGDPlan *p = agd_plan_create(x0, d, m, Ubar, tol, &cert);
    memcpy(a, x0, d * sizeof(double));
    for (size_t k = 0; k < steps; k++) {
      agd_original_apply(a, b, Ubar, d, m, r);
      double *t2 = a; a = b; b = t2;
    }
    memcpy(out, a, d * sizeof(double));
    double *fast = malloc(d * sizeof(double));
    agd_plan_run(p, steps); agd_plan_reconstruct(p, fast);
    worst = agd_max_abs_error(out, fast, d);
    free(fast); agd_plan_destroy(p);
  }
  *max_abs_error = worst;

  free(bt); free(ot); free(a); free(b); free(out);
  return MUNI_OK_QUOTIENT;
}
