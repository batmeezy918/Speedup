/* agd_tensored_amortized.c
 *
 * TENSOR-SEPARABLE OPERATOR EXTENSION of the descending-quotient runtime.
 * ---------------------------------------------------------------------------
 *
 * The existing runtime (agd_amortized_total.c) uses a DIAGONAL / block-diagonal
 * operator:
 *
 *     full     : y[i]      = x[i] * w[(i/tile) % nw]          d   ops
 *     quotient : y[b]      = q[b] * w[b % nw]                 r   ops   (r = d/tile)
 *
 * and measured an asymptotic per-step ratio of 124.3x at tile = 64, i.e. 1.94x the
 * compression ratio. That excess is an IMPLEMENTATION artifact: the full arm pays
 * an `i/tile` integer division per element, and sweeps d*8 bytes against r*8.
 *
 * THIS PROGRAM replaces the operator with the tensor-separable form
 *
 *     U = Ubar (x) I_m          (block size m = tile, quotient dimension r = d/m)
 *
 * so the full arm is a dense r-by-r matvec broadcast across each block:
 *
 *     full     : y[b*m+j] = sum_{b'} Ubar[b][b'] * x[b'*m+j]    d*r ops, pure FMA
 *     quotient : q'[b]    = sum_{b'} Ubar[b][b'] * q[b']        r^2 ops
 *
 * and the full arm contains NO integer division.
 *
 * FALSIFIABLE PREDICTION (stated before the run)
 *
 *   Per-step asymptote  =  1/b  where  1/E2E(k) = a/k + b.
 *
 *   PREDICTED:  asymptote ~ m (= tile), NOT ~ 1.94*m.
 *   REASON:     the operator's compression ratio is exactly m, and with the
 *               division removed both arms are FLOP-bound, so the ratio is the
 *               pure work ratio m.
 *
 *   If the measured asymptote again lands near 124x at tile = 64, the excess is
 *   NOT an artifact of the diagonal operator and the earlier explanation is
 *   wrong. That is the discriminating observation either way.
 *
 *   Secondary: asymptote <= m exactly. Anything above m would mean the quotient
 *   path is doing less than r^2 work and the model is wrong.
 *
 * CORRECTNESS GATE (primary, must hold for every configuration)
 *
 *   maxerr = 0 between the full d-dimensional trajectory and the quotient
 *   trajectory after exact reconstruction. This is the Level-4 statement: the
 *   block-constant sector is T-invariant and reconstruction is exact on it.
 *   The input is CONSTRUCTED block-constant and then VALIDATED, exactly as the
 *   diagonal runtime does -- the invariant is guaranteed, not discovered.
 *
 * Honest scope, repeated deliberately: the operator is now non-diagonal, but the
 * invariant hypothesis is still constructed. This does not exercise a workload
 * where Omega might fail, and makes no claim about unrestricted d-dim state.
 */
#define _POSIX_C_SOURCE 200809L
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static volatile double sink;

static uint64_t now_ns(void) {
  struct timespec t;
  clock_gettime(CLOCK_MONOTONIC, &t);
  return (uint64_t)t.tv_sec * 1000000000ULL + (uint64_t)t.tv_nsec;
}

static uint64_t rng(uint64_t *s) {
  *s ^= *s << 13; *s ^= *s >> 7; *s ^= *s << 17;
  return *s;
}
static double urand(uint64_t *s) {
  return (double)(rng(s) >> 11) * (1.0 / 9007199254740992.0);
}

static double med(double *a, size_t n) {
  for (size_t i = 1; i < n; i++) {
    double v = a[i]; size_t j = i;
    while (j && a[j - 1] > v) { a[j] = a[j - 1]; j--; }
    a[j] = v;
  }
  return a[n / 2];
}

/* operator families: all are r x r and all are block-separable by construction */
static const char *FAM[] = {"dense", "perm", "diagphase"};
#define NFAM 3

static void build_ubar(int fam, double *U, size_t r) {
  uint64_t s = 0x9e3779b97f4a7c15ULL ^ (uint64_t)r;
  for (size_t b = 0; b < r; b++)
    for (size_t c = 0; c < r; c++) {
      double v;
      if (fam == 0) {
        v = (urand(&s) * 2.0 - 1.0) / sqrt((double)r);
      } else if (fam == 1) {
        v = (b == (c * 7 + 3) % r) ? 1.0 : 0.0;
      } else {
        v = (b == c) ? cos(2.0 * 3.14159265358979 * (double)c / (double)r) : 0.0;
      }
      U[b * r + c] = v;
    }
}

/* FULL arm: dense r x r matvec broadcast across every block. d*r ops, no division. */
static void full_apply(const double *x, double *y, const double *U, size_t d, size_t m, size_t r) {
  for (size_t b = 0; b < r; b++) {
    const double *row = U + b * r;
    for (size_t j = 0; j < m; j++) {
      const double *src = x + j;
      double acc = 0.0;
      for (size_t c = 0; c < r; c++) acc += row[c] * src[c * m];
      y[b * m + j] = acc;
    }
  }
}

/* QUOTIENT arm: r x r matvec only. r^2 ops. */
static void quotient_apply(const double *q, double *o, const double *U, size_t r) {
  for (size_t b = 0; b < r; b++) {
    const double *row = U + b * r;
    double acc = 0.0;
    for (size_t c = 0; c < r; c++) acc += row[c] * q[c];
    o[b] = acc;
  }
}

static double max_abs_err(const double *a, const double *b, size_t n) {
  double e = 0.0;
  for (size_t i = 0; i < n; i++) {
    double z = fabs(a[i] - b[i]);
    if (z > e) e = z;
  }
  return e;
}

static int validate_block_constant(const double *x, size_t d, size_t m, double tol) {
  size_t r = d / m;
  for (size_t b = 0; b < r; b++) {
    double v = x[b * m];
    for (size_t j = 1; j < m; j++)
      if (fabs(x[b * m + j] - v) > tol) return 0;
  }
  return 1;
}

static int run(int fam, size_t d, size_t m, size_t steps, size_t trials, size_t reps) {
  size_t r = d / m;
  double *U = malloc(r * r * sizeof(double));
  double *x = malloc(d * sizeof(double));
  double *a = malloc(d * sizeof(double));
  double *b = malloc(d * sizeof(double));
  double *q = malloc(r * sizeof(double));
  double *qa = malloc(r * sizeof(double));
  double *xr = malloc(d * sizeof(double));
  if (!U || !x || !a || !b || !q || !qa || !xr) { free(U);free(x);free(a);free(b);free(q);free(qa);free(xr); return 0; }

  build_ubar(fam, U, r);

  /* construct a block-constant state, then VALIDATE the invariant hypothesis */
  uint64_t s = 0x123456789abcdefULL;
  for (size_t i = 0; i < d; i += m) {
    double v = .25 + 1.75 * urand(&s);
    for (size_t j = 0; j < m; j++) x[i + j] = v;
  }
  int ok = validate_block_constant(x, d, m, 0.0);

  /* exact reference trajectory at full dimension */
  memcpy(a, x, d * sizeof(double));
  for (size_t k = 0; k < steps; k++) {
    full_apply(a, b, U, d, m, r);
    double *t = a; a = b; b = t;
  }

  /* one-time projection, charged to the quotient path */
  for (size_t i = 0; i < r; i++) q[i] = x[i * m];

  double full_cost[64], q_cost[64];
  for (size_t t = 0; t < trials; t++) {
    uint64_t tf = 0, tq = 0;
    for (size_t rep = 0; rep < reps; rep++) {
      memcpy(a, x, d * sizeof(double));
      uint64_t f0 = now_ns();
      for (size_t k = 0; k < steps; k++) {
        full_apply(a, b, U, d, m, r);
        double *z = a; a = b; b = z;
      }
      uint64_t f1 = now_ns(); tf += f1 - f0;

      memcpy(qa, q, r * sizeof(double));
      uint64_t q0 = now_ns();
      /* setup deliberately inside the quotient total */
      for (size_t i = 0; i < r; i++) qa[i] = x[i * m];
      for (size_t k = 0; k < steps; k++) {
        quotient_apply(qa, q, U, r);
        double *z = qa; qa = q; q = z;
      }
      for (size_t i = 0; i < r; i++) xr[i * m] = q[i];
      for (size_t i = 0; i < r; i++)
        for (size_t j = 1; j < m; j++) xr[i * m + j] = q[i];
      uint64_t q1 = now_ns(); tq += q1 - q0;

      sink += a[rep % d] + xr[(rep * 31) % d] + q[rep % r];
    }
    full_cost[t] = (double)tf; q_cost[t] = (double)tq;
  }

  /* independent verification of the quotient trajectory */
  for (size_t i = 0; i < r; i++) q[i] = x[i * m];
  for (size_t k = 0; k < steps; k++) { quotient_apply(q, qa, U, r); double *z = q; q = qa; qa = z; }
  for (size_t i = 0; i < r; i++) xr[i * m] = q[i];
  for (size_t i = 0; i < r; i++) for (size_t j = 1; j < m; j++) xr[i * m + j] = q[i];
  double er = max_abs_err(a, xr, d);

  double speed = med(full_cost, trials) / med(q_cost, trials);
  printf("TENSOR d=%zu tile=%zu r=%zu fam=%s steps=%zu total_speedup=%.6fx "
         "setup_included=YES maxerr=%.3g trials=%zu reps=%zu\n",
         d, m, r, FAM[fam], steps, speed, er, trials, reps);
  if (er != 0.0) ok = 0;
  if (!validate_block_constant(x, d, m, 0.0)) ok = 0;
  free(U);free(x);free(a);free(b);free(q);free(qa);free(xr);
  return ok;
}

int main(int argc, char **argv) {
  size_t trials = 5, reps = 5;
  if (argc > 1) trials = (size_t)atoi(argv[1]);
  if (argc > 2) reps = (size_t)atoi(argv[2]);
  int pass = 1;
  size_t ds[] = {4096, 16384};
  size_t ms[] = {32, 64};
  size_t ss[] = {1, 4, 16, 64};
  printf("# prediction: asymptotic per-step ratio ~ m (=tile), NOT ~1.94*m\n");
  printf("# d tile -> expect asymptote near 32 or 64, not near 62 or 124\n");
  for (int f = 0; f < NFAM; f++)
    for (size_t i = 0; i < 2; i++)
      for (size_t j = 0; j < 2; j++)
        for (size_t k = 0; k < 4; k++)
          if (!run(f, ds[i], ms[j], ss[k], trials, reps)) pass = 0;
  printf("TENSORSEPARABLE_GATE=%s\n", pass ? "PASS" : "FAIL");
  printf("SINK=%.17g\n", sink);
  return pass ? 0 : 1;
}