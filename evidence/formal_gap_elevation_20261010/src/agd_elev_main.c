/* agd_elev_main.c — elevation harness for the AGD quotient-descent claim.
 *
 *   agd_elev bench  d m steps trials reps [json]   structured vs DENSE vs quotient
 *   agd_elev heat   d m steps trials reps [json]   named diffusion workload + direct-stencil gap
 *   agd_elev noise  d m steps trials reps [json]   A/A floor (quotient vs quotient)
 *
 * Purpose (Tasks 1, 5, 6): replace the tautological baseline with a GENUINELY
 * GENERAL dense baseline (A = U (x) I_m materialised as a d x d matrix), add a
 * NAMED physical workload (explicit heat/diffusion) whose block-constant sector
 * is natural, and provide an A/A noise-floor mode for session statistics.
 *
 * Exactness is always checked against the ORIGINAL operator (agd_original_apply
 * with the same U); the dense path must also agree, proving the reduction is not
 * an artefact of the two implementations sharing a loop shape.
 */
#include "agd_cert.h"
#include "agd_elev.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static uint64_t rs = 0x9E3779B97F4A7C15ULL;
static double urand(void) {
  rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17;
  return (double)(rs >> 11) * (1.0 / 9007199254740992.0);
}
static uint64_t now_ns(void) {
  struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
  return (uint64_t)t.tv_sec * 1000000000ULL + (uint64_t)t.tv_nsec;
}
static double median(double *a, size_t n) {
  for (size_t i = 1; i < n; i++) { double v = a[i]; size_t j = i;
    while (j && a[j - 1] > v) { a[j] = a[j - 1]; j--; } a[j] = v; }
  return a[n / 2];
}
static void fill_random_U(double *U, size_t r) {
  for (size_t b = 0; b < r; b++)
    for (size_t c = 0; c < r; c++) U[b * r + c] = (urand() * 2 - 1) / sqrt((double)r);
}
static void fill_block_constant(double *x, size_t d, size_t m) {
  for (size_t i = 0; i < d; i += m) {
    double v = .25 + 1.75 * urand();
    for (size_t j = 0; j < m; j++) x[i + j] = v;
  }
}

typedef struct {
  const char *mode; size_t d, m, r, steps, trials, reps;
  double struct_ms, dense_ms, quot_ms, struct_x, dense_x, dense_vs_struct;
  double max_abs_error, dense_abs_error, direct_abs_error;
  double noise_ratio;
} Result;

static void emit(const Result *R, const char *json) {
  printf("MODE=%s d=%zu m=%zu r=%zu steps=%zu trials=%zu reps=%zu\n",
         R->mode, R->d, R->m, R->r, R->steps, R->trials, R->reps);
  printf("structured_ms=%.6f dense_ms=%.6f quotient_ms=%.6f\n",
         R->struct_ms, R->dense_ms, R->quot_ms);
  printf("speedup_vs_structured=%.6f speedup_vs_dense=%.6f dense_vs_structured=%.6f\n",
         R->struct_x, R->dense_x, R->dense_vs_struct);
  printf("max_abs_error_quotient=%.3g dense_abs_error=%.3g direct_stencil_abs_error=%.3g\n",
         R->max_abs_error, R->dense_abs_error, R->direct_abs_error);
  if (R->noise_ratio > 0) printf("noise_ratio=%.6f\n", R->noise_ratio);
  if (json) {
    FILE *f = fopen(json, "w");
    if (f) {
      fprintf(f, "{\n  \"mode\": \"%s\",\n", R->mode);
      fprintf(f, "  \"d\": %zu, \"m\": %zu, \"r\": %zu, \"steps\": %zu, \"trials\": %zu, \"reps\": %zu,\n",
              R->d, R->m, R->r, R->steps, R->trials, R->reps);
      fprintf(f, "  \"structured_ms\": %.6f, \"dense_ms\": %.6f, \"quotient_ms\": %.6f,\n",
              R->struct_ms, R->dense_ms, R->quot_ms);
      fprintf(f, "  \"speedup_vs_structured\": %.6f, \"speedup_vs_dense\": %.6f, \"dense_vs_structured\": %.6f,\n",
              R->struct_x, R->dense_x, R->dense_vs_struct);
      fprintf(f, "  \"max_abs_error\": %.17g, \"dense_abs_error\": %.17g, \"direct_stencil_abs_error\": %.17g,\n",
              R->max_abs_error, R->dense_abs_error, R->direct_abs_error);
      fprintf(f, "  \"noise_ratio\": %.6f\n}\n", R->noise_ratio);
      fclose(f);
    }
  }
}

/* median per-call ns of the STRUCTURED operator. */
static double time_structured(const double *x, const double *U,
                              size_t d, size_t m, size_t r, size_t steps,
                              size_t trials, size_t reps) {
  double *a = malloc(d * sizeof(double)), *b = malloc(d * sizeof(double));
  double out[64];
  volatile double sink = 0;
  for (size_t t = 0; t < trials; t++) {
    uint64_t tot = 0;
    for (size_t rep = 0; rep < reps; rep++) {
      memcpy(a, x, d * sizeof(double));
      uint64_t t0 = now_ns();
      for (size_t k = 0; k < steps; k++) { agd_original_apply(a, b, U, d, m, r); double *z = a; a = b; b = z; }
      uint64_t t1 = now_ns(); tot += t1 - t0;
      sink += a[0];
    }
    out[t] = (double)tot / (double)reps;
  }
  (void)sink;
  double v = median(out, trials);
  free(a); free(b);
  return v;
}

/* median per-call ns of the GENERAL DENSE operator. */
static double time_dense(const double *x, const double *A, size_t d,
                         size_t steps, size_t trials, size_t reps) {
  double *a = malloc(d * sizeof(double)), *b = malloc(d * sizeof(double));
  double out[64];
  volatile double sink = 0;
  for (size_t t = 0; t < trials; t++) {
    uint64_t tot = 0;
    for (size_t rep = 0; rep < reps; rep++) {
      memcpy(a, x, d * sizeof(double));
      uint64_t t0 = now_ns();
      for (size_t k = 0; k < steps; k++) { agd_dense_apply(A, a, b, d); double *z = a; a = b; b = z; }
      uint64_t t1 = now_ns(); tot += t1 - t0;
      sink += a[0];
    }
    out[t] = (double)tot / (double)reps;
  }
  (void)sink;
  double v = median(out, trials);
  free(a); free(b);
  return v;
}

/* median per-call ns of the QUOTIENT plan, resetting the plan outside timing. */
static double time_quotient(const double *x, size_t d, size_t m, const double *U,
                            const AGDCertificate *cert, size_t steps,
                            size_t trials, size_t reps) {
  double out[64];
  AGDPlan *p = agd_plan_create(x, d, m, U, 0.0, cert);
  if (!p) return -1;
  for (size_t t = 0; t < trials; t++) {
    uint64_t tot = 0;
    for (size_t rep = 0; rep < reps; rep++) {
      uint64_t t0 = now_ns();
      agd_plan_run(p, steps);
      uint64_t t1 = now_ns(); tot += t1 - t0;
      agd_plan_destroy(p);
      p = agd_plan_create(x, d, m, U, 0.0, cert);
      if (!p) return -1;
    }
    out[t] = (double)tot / (double)reps;
  }
  agd_plan_destroy(p);
  return median(out, trials);
}

int main(int argc, char **argv) {
  if (argc < 2) { fprintf(stderr, "usage: agd_elev {bench|heat|noise|selftest} d m steps trials reps [json]\n"); return 2; }
  const char *mode = argv[1];
  if (!strcmp(mode, "selftest")) {
    int ok = agd_refine_selftest();
    printf("REFINE_SELFTEST=%s\n", ok ? "PASS" : "FAIL");
    printf("CLAIM_TOL0=%s\n", agd_tolerance_claim(0.0));
    printf("CLAIM_TOLPOS=%s\n", agd_tolerance_claim(1e-9));
    return ok ? 0 : 1;
  }
  size_t d = (argc > 2) ? strtoull(argv[2], 0, 10) : 2048;
  size_t m = (argc > 3) ? strtoull(argv[3], 0, 10) : 64;
  size_t steps = (argc > 4) ? strtoull(argv[4], 0, 10) : 32;
  size_t trials = (argc > 5) ? strtoull(argv[5], 0, 10) : 5;
  size_t reps = (argc > 6) ? strtoull(argv[6], 0, 10) : 3;
  const char *json = (argc > 7) ? argv[7] : NULL;
  if (d == 0 || m == 0 || d % m) { fprintf(stderr, "bad shape\n"); return 2; }
  size_t r = d / m;

  double *U = malloc(r * r * sizeof(double));
  double *x = malloc(d * sizeof(double));
  double *ref = malloc(d * sizeof(double));
  double *tmp = malloc(d * sizeof(double));
  double *out = malloc(d * sizeof(double));
  if (!U || !x || !ref || !tmp || !out) { fprintf(stderr, "alloc\n"); return 3; }
  fill_block_constant(x, d, m);
  if (!strcmp(mode, "heat")) agd_heat_U(U, r, 0.3);
  else fill_random_U(U, r);

  AGDCertificate cert = agd_certificate_self();
  Result R; memset(&R, 0, sizeof R);
  R.mode = mode; R.d = d; R.m = m; R.r = r; R.steps = steps; R.trials = trials; R.reps = reps;

  /* exact reference = ORIGINAL operator applied `steps` times. */
  memcpy(ref, x, d * sizeof(double));
  for (size_t k = 0; k < steps; k++) { agd_original_apply(ref, tmp, U, d, m, r); double *z = ref; ref = tmp; tmp = z; }

  /* quotient exactness (fresh plan). */
  AGDPlan *p = agd_plan_create(x, d, m, U, 0.0, &cert);
  if (!p) { fprintf(stderr, "plan refused\n"); return 3; }
  agd_plan_run(p, steps);
  agd_plan_reconstruct(p, out);
  R.max_abs_error = agd_max_abs_error(ref, out, d);
  int fell_back = agd_plan_in_fallback(p);
  agd_plan_destroy(p);

  if (!strcmp(mode, "bench")) {
    double *A = malloc(d * d * sizeof(double));
    if (!A) { fprintf(stderr, "dense alloc failed\n"); return 3; }
    agd_build_tensor_dense(A, U, d, m, r);
    /* dense reference must also equal the structured reference */
    memcpy(out, x, d * sizeof(double));
    for (size_t k = 0; k < steps; k++) { agd_dense_apply(A, out, tmp, d); double *z = out; out = tmp; tmp = z; }
    R.dense_abs_error = agd_max_abs_error(ref, out, d);
    R.struct_ms = time_structured(x, U, d, m, r, steps, trials, reps) / 1e6;
    R.dense_ms  = time_dense(x, A, d, steps, trials, reps) / 1e6;
    R.quot_ms   = time_quotient(x, d, m, U, &cert, steps, trials, reps) / 1e6;
    free(A);
  } else if (!strcmp(mode, "heat")) {
    /* Direct three-point stencil: SAME continuum operator, DIFFERENT association.
       Its deviation from the defined operator is the residual refinement gap. */
    memcpy(out, x, d * sizeof(double));
    for (size_t k = 0; k < steps; k++) { agd_heat_direct_step(out, tmp, d, m, r, 0.3); double *z = out; out = tmp; tmp = z; }
    R.direct_abs_error = agd_max_abs_error(ref, out, d);
    R.struct_ms = time_structured(x, U, d, m, r, steps, trials, reps) / 1e6;
    R.quot_ms   = time_quotient(x, d, m, U, &cert, steps, trials, reps) / 1e6;
  } else if (!strcmp(mode, "noise")) {
    R.struct_ms = time_quotient(x, d, m, U, &cert, steps, trials, reps) / 1e6;
    R.quot_ms   = time_quotient(x, d, m, U, &cert, steps, trials, reps) / 1e6;
    R.noise_ratio = R.struct_ms / R.quot_ms;
    R.struct_ms = 0;
  } else {
    fprintf(stderr, "unknown mode '%s'\n", mode);
    return 2;
  }

  R.struct_x = (R.quot_ms > 0 && R.struct_ms > 0) ? R.struct_ms / R.quot_ms : 0;
  R.dense_x  = (R.quot_ms > 0 && R.dense_ms > 0) ? R.dense_ms / R.quot_ms : 0;
  R.dense_vs_struct = (R.struct_ms > 0 && R.dense_ms > 0) ? R.dense_ms / R.struct_ms : 0;
  emit(&R, json);

  /* Fail loudly if exactness is broken, or if the gate silently fell back. */
  if (!isfinite(R.max_abs_error) || R.max_abs_error != 0.0) { fprintf(stderr, "EXACTNESS FAIL\n"); return 4; }
  if (!strcmp(mode, "bench") && R.dense_abs_error != 0.0) { fprintf(stderr, "DENSE EXACTNESS FAIL\n"); return 4; }
  if (fell_back) { fprintf(stderr, "NOTE: plan fell back (unexpected on block-constant input)\n"); return 5; }
  free(U); free(x); free(ref); free(tmp); free(out);
  return 0;
}
