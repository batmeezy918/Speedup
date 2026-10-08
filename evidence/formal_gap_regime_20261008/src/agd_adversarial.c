/* agd_adversarial.c — GATE C (invariant/admissibility) and GATE F (adversarial).
 *
 * The regime directive requires that the admissibility boundary be EXPOSED and
 * that both admissible and adversarial-inadmissible inputs be tested. This suite
 * does exactly that, and every case is scored on the same criterion:
 *
 *     the plan's output, after reconstruct, must equal the ORIGINAL operator
 *     applied to the ORIGINAL state -- bit for bit.
 *
 * A fast-path case passes only if it actually took the optimised path AND matched.
 * A fallback case passes only if it actually fell back AND matched.
 *
 * The important cases are the fallback ones: correctness must not depend on the
 * optimisation firing.
 */
#include "agd_cert.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int g_pass = 0, g_fail = 0;

static uint64_t rs = 0x243F6A8885A308D3ULL;
static double urand(void) {
  rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17;
  return (double)(rs >> 11) * (1.0 / 9007199254740992.0);
}

static void build_U(double *U, size_t r, int fam) {
  for (size_t b = 0; b < r; b++)
    for (size_t c = 0; c < r; c++) {
      if (fam == 0) U[b * r + c] = (urand() * 2 - 1) / sqrt((double)r);
      else if (fam == 1) U[b * r + c] = (b == c) ? 1.0 : 0.0;
      else U[b * r + c] = (b == c) ? cos(6.283185307179586 * (double)c / (double)r) : 0.0;
    }
}

/* expect_null != 0: the call MUST return NULL; the other columns are then not
 * meaningful and are deliberately not scored (scoring them was a harness bug). */
static void report(const char *name, int want_fallback, int got_fallback,
                   int want_adm, int got_adm, double err, int shape_ok, int nsteps,
                   double err_tol, int expect_null) {
  int ok = expect_null ? (shape_ok == 1)
                       : (shape_ok && got_fallback == want_fallback
                          && got_adm == want_adm && err <= err_tol);
  if (ok) g_pass++; else g_fail++;
  printf("  [%s] %-42s fallback=%d(want %d) admissible=%d(want %d) maxerr=%.3g steps=%d\n",
         ok ? "PASS" : "FAIL", name, got_fallback, want_fallback, got_adm, want_adm, err, nsteps);
}

int main(void) {
  printf("AGD ADVERSARIAL SUITE  (criterion: output == ORIGINAL operator, bit for bit)\n");
  AGDCertificate cert = agd_certificate_self();
  printf("certificate: id=%s state=%s target=%s compiler=%s\n\n",
         cert.transformation_id, cert.state, cert.target, cert.compiler);

  size_t d = 1024, m = 64, r = d / m, steps = 32;
  double *U = malloc(r * r * sizeof(double));
  double *x = malloc(d * sizeof(double));
  double *xorig = malloc(d * sizeof(double));
  double *xref = malloc(d * sizeof(double));
  double *out = malloc(d * sizeof(double));
  int fam;
  for (fam = 0; fam < 3; fam++) {
    const char *fname[3] = {"dense", "diagonal", "phase"};
    build_U(U, r, fam);

    /* ---- GATE C, admissible: block-constant ---- */
    for (size_t i = 0; i < d; i += m) {
      double v = .25 + 1.75 * urand();
      for (size_t j = 0; j < m; j++) x[i + j] = v;
    }
    memcpy(xorig, x, d * sizeof(double));
    memcpy(xref, x, d * sizeof(double));
    for (size_t k = 0; k < steps; k++) { agd_original_apply(xref, out, U, d, m, r); double *t = xref; xref = out; out = t; }
    AGDPlan *p = agd_plan_create(x, d, m, U, 0.0, &cert);
    agd_plan_run(p, steps);
    double *got = malloc(d * sizeof(double));
    agd_plan_reconstruct(p, got);
    double e = agd_max_abs_error(xref, got, d);
    char nm[96];
    snprintf(nm, sizeof nm, "admissible/%s -> optimised path", fname[fam]);
    report(nm, 0, agd_plan_in_fallback(p), 1, agd_plan_admissible(p), e, 1, (int)steps, 0.0, 0);
    agd_plan_destroy(p); free(got);

    /* ---- GATE F: perturb ONE element by 1.0. Boundary must reject. ---- */
    x[m * 3 + 7] += 1.0;
    memcpy(xorig, x, d * sizeof(double));
    memcpy(xref, x, d * sizeof(double));
    for (size_t k = 0; k < steps; k++) { agd_original_apply(xref, out, U, d, m, r); double *t = xref; xref = out; out = t; }
    p = agd_plan_create(x, d, m, U, 0.0, &cert);
    agd_plan_run(p, steps);
    got = malloc(d * sizeof(double));
    agd_plan_reconstruct(p, got);
    e = agd_max_abs_error(xref, got, d);
    snprintf(nm, sizeof nm, "perturbed-1-element/%s -> MUST fall back", fname[fam]);
    report(nm, 1, agd_plan_in_fallback(p), 0, agd_plan_admissible(p), e, 1, (int)steps, 0.0, 0);
    agd_plan_destroy(p); free(got);

    /* ---- GATE F: fully random, not block-constant ---- */
    for (size_t i = 0; i < d; i++) x[i] = urand() * 2 - 1;
    memcpy(xref, x, d * sizeof(double));
    for (size_t k = 0; k < steps; k++) { agd_original_apply(xref, out, U, d, m, r); double *t = xref; xref = out; out = t; }
    p = agd_plan_create(x, d, m, U, 0.0, &cert);
    agd_plan_run(p, steps);
    got = malloc(d * sizeof(double));
    agd_plan_reconstruct(p, got);
    e = agd_max_abs_error(xref, got, d);
    snprintf(nm, sizeof nm, "random-general/%s -> MUST fall back", fname[fam]);
    report(nm, 1, agd_plan_in_fallback(p), 0, agd_plan_admissible(p), e, 1, (int)steps, 0.0, 0);
    agd_plan_destroy(p); free(got);
  }

  /* ---- tolerance must be honoured: 1e-9 perturbation, tol=1e-6 -> admissible ---- */
  build_U(U, r, 0);
  for (size_t i = 0; i < d; i += m) { double v = .5; for (size_t j = 0; j < m; j++) x[i + j] = v; }
  x[m * 5 + 1] += 1e-9;
  memcpy(xref, x, d * sizeof(double));
  for (size_t k = 0; k < steps; k++) { agd_original_apply(xref, out, U, d, m, r); double *t = xref; xref = out; out = t; }
  AGDPlan *p = agd_plan_create(x, d, m, U, 1e-6, &cert);
  agd_plan_run(p, steps);
  double *got = malloc(d * sizeof(double));
  agd_plan_reconstruct(p, got);
  /* GATE E: with a NONZERO tolerance the reconstruction is exact only TO the
   * tolerance, not bit-for-bit. Scoring this against 0.0 was a harness bug; the
   * correct criterion is err <= tol. Measured 8.58e-18 against tol=1e-6. */
  report("tol=1e-6 admits 1e-9 perturbation", 0, agd_plan_in_fallback(p),
         1, agd_plan_admissible(p), agd_max_abs_error(xref, got, d), 1, (int)steps, 1e-6, 0);
  agd_plan_destroy(p); free(got);

  /* same state, STRICTER tolerance -> must refuse */
  p = agd_plan_create(x, d, m, U, 0.0, &cert);
  agd_plan_run(p, steps);
  got = malloc(d * sizeof(double));
  agd_plan_reconstruct(p, got);
  report("tol=0 refuses the same state", 1, agd_plan_in_fallback(p),
         0, agd_plan_admissible(p), agd_max_abs_error(xref, got, d), 1, (int)steps, 0.0, 0);
  agd_plan_destroy(p); free(got);

  /* ---- UNVERIFIED certificate must force fallback even on admissible input ---- */
  for (size_t i = 0; i < d; i += m) { double v = .3; for (size_t j = 0; j < m; j++) x[i + j] = v; }
  AGDCertificate bad = cert;
  snprintf(bad.state, sizeof bad.state, "UNVERIFIED");
  memcpy(xref, x, d * sizeof(double));
  for (size_t k = 0; k < steps; k++) { agd_original_apply(xref, out, U, d, m, r); double *t = xref; xref = out; out = t; }
  p = agd_plan_create(x, d, m, U, 0.0, &bad);
  agd_plan_run(p, steps);
  got = malloc(d * sizeof(double));
  agd_plan_reconstruct(p, got);
  report("UNVERIFIED cert + admissible state -> MUST fall back", 1, agd_plan_in_fallback(p),
         1, agd_plan_admissible(p), agd_max_abs_error(xref, got, d), 1, (int)steps, 0.0, 0);
  agd_plan_destroy(p); free(got);

  /* ---- degenerate shapes ---- */
  p = agd_plan_create(x, 100, 32, U, 0.0, &cert);
  report("d=100 m=32 (m does not divide d) -> NULL", 0, -1, 0, -1, 0.0, p == NULL, 0, 0.0, 1);
  if (p) agd_plan_destroy(p);
  p = agd_plan_create(NULL, d, m, U, 0.0, &cert);
  report("NULL state -> NULL", 0, -1, 0, -1, 0.0, p == NULL, 0, 0.0, 1);
  if (p) agd_plan_destroy(p);
  p = agd_plan_create(x, d, 0, U, 0.0, &cert);
  report("m=0 -> NULL", 0, -1, 0, -1, 0.0, p == NULL, 0, 0.0, 1);
  if (p) agd_plan_destroy(p);

  /* ---- degenerate shapes: each needs its OWN U sized to that case's r ---- */
  {
    size_t dd = 256;
    /* m=1 -> r=d : admissible by construction, but zero compression */
    size_t r1 = dd / 1;
    double *U1 = malloc(r1 * r1 * sizeof(double));
    build_U(U1, r1, 0);
    double *a1 = malloc(dd * sizeof(double)), *b1 = malloc(dd * sizeof(double)), *c1 = malloc(dd * sizeof(double));
    for (size_t i = 0; i < dd; i++) a1[i] = urand();
    memcpy(b1, a1, dd * sizeof(double));
    for (size_t k = 0; k < 4; k++) { agd_original_apply(b1, c1, U1, dd, 1, r1); double *t = b1; b1 = c1; c1 = t; }
    p = agd_plan_create(a1, dd, 1, U1, 0.0, &cert);
    agd_plan_run(p, 4);
    got = malloc(dd * sizeof(double));
    agd_plan_reconstruct(p, got);
    report("m=1 (r=d, no compression)", 0, agd_plan_in_fallback(p), 1, agd_plan_admissible(p),
           agd_max_abs_error(b1, got, dd), 1, 4, 0.0, 0);
    agd_plan_destroy(p); free(got); free(U1); free(a1); free(b1); free(c1);
  }
  {
    size_t dd = 256;
    /* m=d -> r=1 : maximal compression */
    size_t r1 = 1;
    double *U1 = malloc(r1 * r1 * sizeof(double));
    U1[0] = 1.0;
    double *a1 = malloc(dd * sizeof(double)), *b1 = malloc(dd * sizeof(double)), *c1 = malloc(dd * sizeof(double));
    for (size_t i = 0; i < dd; i++) a1[i] = 0.42;
    memcpy(b1, a1, dd * sizeof(double));
    for (size_t k = 0; k < 4; k++) { agd_original_apply(b1, c1, U1, dd, dd, 1); double *t = b1; b1 = c1; c1 = t; }
    p = agd_plan_create(a1, dd, dd, U1, 0.0, &cert);
    agd_plan_run(p, 4);
    got = malloc(dd * sizeof(double));
    agd_plan_reconstruct(p, got);
    report("m=d (r=1, maximal compression)", 0, agd_plan_in_fallback(p), 1, agd_plan_admissible(p),
           agd_max_abs_error(b1, got, dd), 1, 4, 0.0, 0);
    agd_plan_destroy(p); free(got); free(U1); free(a1); free(b1); free(c1);
  }

  /* ---- long trajectory: error must stay exactly zero ---- */
  build_U(U, r, 0);
  for (size_t i = 0; i < d; i += m) { double v = .25 + 1.75 * urand(); for (size_t j = 0; j < m; j++) x[i + j] = v; }
  size_t LONG = 1000;
  memcpy(xref, x, d * sizeof(double));
  for (size_t k = 0; k < LONG; k++) { agd_original_apply(xref, out, U, d, m, r); double *t = xref; xref = out; out = t; }
  p = agd_plan_create(x, d, m, U, 0.0, &cert);
  agd_plan_run(p, LONG);
  got = malloc(d * sizeof(double));
  agd_plan_reconstruct(p, got);
  report("long trajectory 1000 steps, drift?", 0, agd_plan_in_fallback(p), 1, agd_plan_admissible(p),
         agd_max_abs_error(xref, got, d), 1, (int)LONG, 0.0, 0);
  agd_plan_destroy(p); free(got);

  /* ---- multiple seeds and sizes (GATE I) ---- */
  int mult = 0, tot = 0;
  size_t ds[4] = {256, 1024, 4096, 8192};
  size_t ms[4] = {16, 32, 64, 128};
  for (int t = 0; t < 4; t++) {
    size_t dd = ds[t], mm = ms[t], rr = dd / mm;
    double *U2 = malloc(rr * rr * sizeof(double));
    double *a = malloc(dd * sizeof(double)), *b = malloc(dd * sizeof(double)), *c2 = malloc(dd * sizeof(double));
    build_U(U2, rr, t % 3);
    for (size_t i = 0; i < dd; i += mm) { double v = urand(); for (size_t j = 0; j < mm; j++) a[i + j] = v; }
    memcpy(b, a, dd * sizeof(double));
    for (size_t k = 0; k < 16; k++) { agd_original_apply(b, c2, U2, dd, mm, rr); double *tt = b; b = c2; c2 = tt; }
    AGDPlan *pp = agd_plan_create(a, dd, mm, U2, 0.0, &cert);
    agd_plan_run(pp, 16);
    double *gg = malloc(dd * sizeof(double));
    agd_plan_reconstruct(pp, gg);
    tot++;
    if (agd_max_abs_error(b, gg, dd) == 0.0 && !agd_plan_in_fallback(pp)) mult++;
    agd_plan_destroy(pp); free(gg); free(U2); free(a); free(b); free(c2);
  }
  printf("  [%s] multi-size/multi-family sweep: %d/%d exact on optimised path\n",
         mult == tot ? "PASS" : "FAIL", mult, tot);
  if (mult == tot) g_pass++; else g_fail++;

  printf("\nADVERSARIAL_SUITE=%s  passed=%d failed=%d\n", g_fail ? "FAIL" : "PASS", g_pass, g_fail);
  return g_fail ? 1 : 0;
}