#include "agd_elev.h"
#include "agd_cert.h"
#include <string.h>

void agd_build_tensor_dense(double *A, const double *U,
                            size_t d, size_t m, size_t r) {
  memset(A, 0, d * d * sizeof(double));
  for (size_t b = 0; b < r; b++)
    for (size_t c = 0; c < r; c++) {
      double u = U[b * r + c];
      for (size_t j = 0; j < m; j++)
        A[(b * m + j) * d + (c * m + j)] = u;
    }
}

void agd_dense_apply(const double *A, const double *x, double *y, size_t d) {
  for (size_t i = 0; i < d; i++) {
    const double *row = A + i * d;
    double acc = 0.0;
    for (size_t k = 0; k < d; k++) acc += row[k] * x[k];
    y[i] = acc;
  }
}

void agd_heat_U(double *U, size_t r, double a) {
  memset(U, 0, r * r * sizeof(double));
  for (size_t b = 0; b < r; b++) {
    U[b * r + b] = 1.0 - 2.0 * a;
    U[b * r + ((b + r - 1) % r)] += a;
    U[b * r + ((b + 1) % r)] += a;
  }
}

void agd_heat_direct_step(const double *x, double *y,
                          size_t d, size_t m, size_t r, double a) {
  for (size_t b = 0; b < r; b++) {
    for (size_t j = 0; j < m; j++) {
      size_t i = b * m + j;
      double c = x[i];
      double l = x[((b + r - 1) % r) * m + j];
      double rr = x[((b + 1) % r) * m + j];
      y[i] = c + a * (l - 2.0 * c + rr);
    }
  }
}

int agd_refine_selftest(void) {
  /* A fixed block-constant vector and a fixed 3x3 U. If the full-state path and
     the quotient path do not agree BITWISE on this binary, the certificate must
     not authorise the optimised path. */
  enum { D = 12, M = 4, R = 3 };
  double U[R * R] = { 0.5, -0.25, 0.125,
                      0.125, 0.5, -0.25,
                      -0.25, 0.125, 0.5 };
  double x[D];
  for (size_t b = 0; b < R; b++)
    for (size_t j = 0; j < M; j++) x[b * M + j] = 0.25 + 0.5 * (double)b;
  double ref[D], out[D];
  agd_original_apply(x, ref, U, D, M, R);
  AGDCertificate cert = agd_certificate_self();
  AGDPlan *p = agd_plan_create(x, D, M, U, 0.0, &cert);
  if (!p) return 0;
  if (agd_plan_in_fallback(p)) { agd_plan_destroy(p); return 0; }
  agd_plan_run(p, 1);
  agd_plan_reconstruct(p, out);
  int ok = 1;
  for (size_t i = 0; i < D; i++) if (out[i] != ref[i]) ok = 0;
  agd_plan_destroy(p);
  return ok;
}

const char *agd_tolerance_claim(double tol) {
  return (tol == 0.0) ? "EXACT_BITWISE" : "APPROX_UNBOUNDED";
}

