/* SOTA differential benchmark for the AGD/MuNi quotient-descent operator.
 *
 * Compares, on the SAME machine/session/flags and interleaved with a rotating
 * order, four implementations of the SAME operation (apply the dense operator
 * Ubar (x) I_m for `steps` iterations):
 *
 *   cand   : AGD quotient descent (optimized path; asserted via fallback flag)
 *   blas   : OpenBLAS dgemv on the materialised dense matrix  (SOTA baseline)
 *   naive  : hand-written dense mat-vec loop                  (honest dense baseline)
 *   struct : exact Ubar (x) I_m direct operator               (structured baseline)
 *
 * Output is a plain line protocol parsed by sota_aggregate.py.
 */
#include "agd_elev.h"
#include "agd_cert.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* Fortran BLAS interface (avoids header dependency). */
extern void dgemv_(const char *trans, const int *m, const int *n,
                   const double *alpha, const double *A, const int *lda,
                   const double *x, const int *incx, const double *beta,
                   double *y, const int *incy);

static double now_ms(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ts.tv_sec * 1000.0 + ts.tv_nsec / 1.0e6;
}

static void build_A_colmajor(double *A, const double *U,
                             size_t d, size_t m, size_t r) {
  memset(A, 0, d * d * sizeof(double));
  for (size_t b = 0; b < r; b++)
    for (size_t c = 0; c < r; c++) {
      double u = U[b * r + c];
      for (size_t j = 0; j < m; j++)
        A[(b * m + j) + (c * m + j) * d] = u;
    }
}

static void run_blas(const double *A, double *x, double *y, size_t d, size_t steps) {
  int n = (int)d, one = 1;
  double a = 1.0, b = 0.0;
  for (size_t s = 0; s < steps; s++) {
    dgemv_("N", &n, &n, &a, A, &n, x, &one, &b, y, &one);
    double *t = x; x = y; y = t;
  }
}

static void run_naive(const double *A, double *x, double *y, size_t d, size_t steps) {
  for (size_t s = 0; s < steps; s++) {
    for (size_t i = 0; i < d; i++) {
      double acc = 0.0;
      for (size_t k = 0; k < d; k++) acc += A[i + k * d] * x[k];
      y[i] = acc;
    }
    double *t = x; x = y; y = t;
  }
}

static void run_struct(const double *U, double *x, double *y,
                       size_t d, size_t m, size_t r, size_t steps) {
  for (size_t s = 0; s < steps; s++) {
    agd_original_apply(x, y, U, d, m, r);
    double *t = x; x = y; y = t;
  }
}

/* Rotating interleave order: path p at trial t runs at slot (p+t)%4. */
enum { P_CAND = 0, P_BLAS = 1, P_NAIVE = 2, P_STRUCT = 3, NP = 4 };
static const char *PNAME[NP] = {"cand", "blas", "naive", "struct"};

int main(int argc, char **argv) {
  if (argc < 7) {
    fprintf(stderr, "usage: sota_bench d m r steps trials reps [noblas]\n");
    return 2;
  }
  size_t d = strtoul(argv[1], 0, 10);
  size_t m = strtoul(argv[2], 0, 10);
  size_t r = strtoul(argv[3], 0, 10);
  size_t steps = strtoul(argv[4], 0, 10);
  int trials = atoi(argv[5]);
  int reps = atoi(argv[6]);
  int use_blas = 1, use_naive = 1;
  for (int i = 7; i < argc; i++) {
    if (!strcmp(argv[i], "noblas")) use_blas = 0;
    if (!strcmp(argv[i], "nonaive")) use_naive = 0;
  }
  if (d == 0 || m == 0 || d % m != 0) { fprintf(stderr, "bad shape\n"); return 2; }

  /* memory guard for dense matrix */
  double dense_bytes = (double)d * (double)d * 8.0;
  if (use_blas && dense_bytes > 700e6) { use_blas = 0; }

  double *U = malloc(r * r * sizeof(double));
  double *x0 = malloc(d * sizeof(double));
  for (size_t b = 0; b < r; b++)
    for (size_t j = 0; j < m; j++) x0[b * m + j] = 0.25 + 0.5 * (double)b;
  agd_heat_U(U, r, 0.25);

  /* reference (exact) and correctness checks, untimed */
  double *ref = malloc(d * sizeof(double));
  double *chk = malloc(d * sizeof(double));
  agd_original_apply(x0, ref, U, d, m, r);
  AGDCertificate cert = agd_certificate_self();
  AGDPlan *plan = agd_plan_create(x0, d, m, U, 0.0, &cert);
  if (!plan) { fprintf(stderr, "plan null\n"); return 3; }
  int fallback = agd_plan_in_fallback(plan);
  agd_plan_run(plan, 1);
  agd_plan_reconstruct(plan, chk);
  double cand_err = agd_max_abs_error(ref, chk, d);

  double blas_err = -1, naive_err = -1;
  double *A = NULL, *bx = NULL, *by = NULL;
  int dense_ok = (dense_bytes <= 700e6);
  if (dense_ok) {
    A = malloc(d * d * sizeof(double));
    bx = malloc(d * sizeof(double));
    by = malloc(d * sizeof(double));
    dense_ok = (A && bx && by);
  }
  int have_blas = dense_ok && use_blas;
  int have_naive = dense_ok && use_naive;
  if (dense_ok) {
    build_A_colmajor(A, U, d, m, r);
    if (have_naive) {
      memcpy(bx, x0, d * sizeof(double));
      memcpy(by, x0, d * sizeof(double));
      run_naive(A, bx, by, d, 1);
      memcpy(chk, by, d * sizeof(double));
      naive_err = agd_max_abs_error(ref, chk, d);
    }
    if (have_blas) {
      memcpy(bx, x0, d * sizeof(double));
      memcpy(by, x0, d * sizeof(double));
      run_blas(A, bx, by, d, 1);
      memcpy(chk, by, d * sizeof(double));
      blas_err = agd_max_abs_error(ref, chk, d);
    }
  }

  /* timing buffers */
  double *cx = malloc(d * sizeof(double)), *cy = malloc(d * sizeof(double));
  double *times[NP];
  for (int p = 0; p < NP; p++) times[p] = malloc(sizeof(double) * trials);
  double *aa2[2]; for (int p = 0; p < 2; p++) aa2[p] = malloc(sizeof(double) * trials);

  int cand_fb_total = 0, cand_runs_total = 0;

  /* warmup: 2 full rounds of all paths */
  for (int w = 0; w < 2; w++) {
    for (int p = 0; p < NP; p++) {
      if ((p == P_BLAS && !have_blas) || (p == P_NAIVE && !have_naive)) continue;
      if (p == P_CAND) {
        AGDPlan *fp = agd_plan_create(x0, d, m, U, 0.0, &cert);
        cand_fb_total += agd_plan_in_fallback(fp); cand_runs_total++;
        agd_plan_run(fp, steps); agd_plan_reconstruct(fp, cx); agd_plan_destroy(fp);
      }
      else if (p == P_BLAS) { memcpy(cx,x0,d*8);memcpy(cy,x0,d*8); run_blas(A,cx,cy,d,steps); }
      else if (p == P_NAIVE) { memcpy(cx,x0,d*8);memcpy(cy,x0,d*8); run_naive(A,cx,cy,d,steps); }
      else { memcpy(cx,x0,d*8);memcpy(cy,x0,d*8); run_struct(U,cx,cy,d,m,r,steps); }
    }
  }

  for (int t = 0; t < trials; t++) {
    for (int slot = 0; slot < NP; slot++) {
      int p = (slot + t) % NP;
      if ((p == P_BLAS && !have_blas) || (p == P_NAIVE && !have_naive)) continue;
      double best = 1e300;
      for (int k = 0; k < reps; k++) {
        double t0, t1;
        if (p == P_CAND) {
          AGDPlan *fp = agd_plan_create(x0, d, m, U, 0.0, &cert);
          cand_fb_total += agd_plan_in_fallback(fp); cand_runs_total++;
          t0 = now_ms(); agd_plan_run(fp, steps); agd_plan_reconstruct(fp, cx); t1 = now_ms();
          agd_plan_destroy(fp);
        } else if (p == P_BLAS) {
          memcpy(cx, x0, d * 8); memcpy(cy, x0, d * 8);
          t0 = now_ms(); run_blas(A, cx, cy, d, steps); t1 = now_ms();
        } else if (p == P_NAIVE) {
          memcpy(cx, x0, d * 8); memcpy(cy, x0, d * 8);
          t0 = now_ms(); run_naive(A, cx, cy, d, steps); t1 = now_ms();
        } else {
          memcpy(cx, x0, d * 8); memcpy(cy, x0, d * 8);
          t0 = now_ms(); run_struct(U, cx, cy, d, m, r, steps); t1 = now_ms();
        }
        double dt = t1 - t0;
        if (dt < best) best = dt;
      }
      times[p][t] = best;
    }
  }

  /* A/A sweeps: a second independent pass over cand and blas */
  for (int t = 0; t < trials; t++) {
    for (int q = 0; q < 2; q++) {
      int p = q; /* 0=cand, 1=blas */
      if ((p == P_BLAS && !have_blas) || (p == P_NAIVE && !have_naive)) { aa2[q][t] = -1; continue; }
      double best = 1e300;
      for (int k = 0; k < reps; k++) {
        double t0, t1;
        if (p == P_CAND) {
          AGDPlan *fp = agd_plan_create(x0, d, m, U, 0.0, &cert);
          cand_fb_total += agd_plan_in_fallback(fp); cand_runs_total++;
          t0=now_ms(); agd_plan_run(fp, steps); agd_plan_reconstruct(fp, cx); t1=now_ms();
          agd_plan_destroy(fp);
        }
        else { memcpy(cx,x0,d*8);memcpy(cy,x0,d*8); t0=now_ms(); run_blas(A,cx,cy,d,steps); t1=now_ms(); }
        double dt = t1 - t0; if (dt < best) best = dt;
      }
      aa2[q][t] = best;
    }
  }

  printf("CONFIG d=%zu m=%zu r=%zu steps=%zu trials=%d reps=%d dense_bytes=%.0f blas=%d naive=%d\n",
         d, m, r, steps, trials, reps, dense_bytes, have_blas, dense_ok);
  for (int p = 0; p < NP; p++) {
    printf("RAW %s", PNAME[p]);
    for (int t = 0; t < trials; t++) printf(" %.6f", times[p][t]);
    printf("\n");
  }
  printf("AA cand"); for (int t = 0; t < trials; t++) printf(" %.6f", aa2[0][t]); printf("\n");
  printf("AA blas"); for (int t = 0; t < trials; t++) printf(" %.6f", aa2[1][t]); printf("\n");
  printf("ERR cand=%.3g blas=%.3g naive=%.3g struct=0\n", cand_err, blas_err, naive_err);
  printf("PATH fallback=%d admissible=%d certified=%d cand_runs=%d cand_fallback=%d\n",
         fallback, agd_plan_admissible(plan), agd_plan_certified(plan),
         cand_runs_total, cand_fb_total);
  return 0;
}
