/* agd_fuzz.c — property-based fuzzer for the AGD gate (Task 4).
 *
 * The adversarial suite checks 23 hand-picked cases. This checks the SAME
 * properties over many randomised shapes / tolerances / certificate mutations,
 * scored against the ORIGINAL operator. Properties (all are CLASS invariants,
 * so a single counterexample is a real bug):
 *
 *   P1 FALLBACK_EXACT   : if the plan fell back, output == original, exactly.
 *   P2 OPT_EXACT_TOL0   : if the optimised path ran with tol == 0, output ==
 *                         original, exactly.
 *   P3 GATE_SOUND       : the optimised path only runs when admissible(tol).
 *   P4 CERT_FAIL_CLOSED : a certificate whose state is neither FORMAL_PARTIAL
 *                         nor (CERTIFIED with native binding), or whose semantic
 *                         identity is unrecognised, MUST force fallback even on
 *                         an admissible state.
 *   P5 OUTPUTISH        : on the optimised path with tol == 0 the output lies in
 *                         the block-constant sector (reconstruction is sound).
 *
 * Exit status is nonzero on any violation; the counterexample is printed.
 */
#include "agd_cert.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint64_t rs = 20261010ULL;
static uint64_t xr(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }
static double urand(void) { return (double)(xr() >> 11) * (1.0 / 9007199254740992.0); }
static size_t pick(const size_t *v, size_t n) { return v[xr() % n]; }

static int violations = 0;
static long c_opt = 0, c_fb = 0, c_null = 0, c_tamper = 0;
static double max_err_tol_pos = 0.0, max_tol_saw = 0.0;

static void violate(const char *prop, size_t d, size_t m, size_t steps, double tol,
                    int fallback, int adm, double err, unsigned long iter) {
  violations++;
  printf("VIOLATION %s iter=%lu d=%zu m=%zu steps=%zu tol=%.3g fallback=%d adm=%d err=%.6g\n",
         prop, iter, d, m, steps, tol, fallback, adm, err);
}

int main(int argc, char **argv) {
  long N = (argc > 1) ? atol(argv[1]) : 20000;
  static const size_t ds[] = {2, 4, 8, 16, 32, 64, 96, 128, 192, 256};
  size_t maxd = 512;
  double *U = malloc(maxd * maxd * sizeof(double));
  double *x = malloc(maxd * sizeof(double));
  double *ref = malloc(maxd * sizeof(double));
  double *tmp = malloc(maxd * sizeof(double));
  double *out = malloc(maxd * sizeof(double));
  if (!U || !x || !ref || !tmp || !out) return 3;

  for (long it = 0; it < N; it++) {
    size_t d = pick(ds, sizeof ds / sizeof ds[0]);
    size_t divs[8]; size_t nd = 0;
    for (size_t m = 1; m <= d && nd < 8; m++) if (d % m == 0) divs[nd++] = m;
    size_t m = divs[xr() % nd];
    size_t r = d / m;
    if (r == 0 || r > maxd) continue;
    size_t steps = 1 + xr() % 33;
    double tol = (xr() % 4 == 0) ? (1e-12 * (double)(xr() % 1000)) : 0.0;

    for (size_t b = 0; b < r; b++)
      for (size_t c = 0; c < r; c++)
        U[b * r + c] = (xr() % 3 == 0) ? ((b == c) ? 1.0 : 0.0)
                                       : (urand() * 2 - 1) / sqrt((double)r);

    int blocky = (xr() % 3) != 0;
    for (size_t i = 0; i < d; i += m) {
      double v = urand() * 2 - 1;
      for (size_t j = 0; j < m; j++) x[i + j] = v;
    }
    if (!blocky) for (size_t i = 0; i < d; i++) if (xr() % 2) x[i] += urand() * 1e-3;
    if (xr() % 5 == 0) x[xr() % d] += 0.5;   /* coarse perturbation */
    if (tol > 0.0 && m > 1 && (xr() % 2 == 0)) {  /* SUB-tolerance: one non-rep element, admitted but inexact */
      size_t i0 = (xr() % (d / m)) * m;
      x[i0 + 1 + (xr() % (m - 1))] += tol * 0.4;
    }

    /* reference = ORIGINAL operator. */
    memcpy(ref, x, d * sizeof(double));
    for (size_t k = 0; k < steps; k++) { agd_original_apply(ref, tmp, U, d, m, r); double *z = ref; ref = tmp; tmp = z; }

    AGDCertificate cert = agd_certificate_self();
    int tampered = 0;
    if (xr() % 4 == 0) {                     /* certificate mutation */
      tampered = 1; c_tamper++;
      switch (xr() % 4) {
        case 0: snprintf(cert.state, sizeof cert.state, "%s", "CANDIDATE"); break;
        case 1: snprintf(cert.semantic_gate, sizeof cert.semantic_gate, "%s", "unreviewed"); break;
        case 2: snprintf(cert.state, sizeof cert.state, "%s", "CERTIFIED");
                snprintf(cert.instantiation_gate, sizeof cert.instantiation_gate, "%s", "LEAN_ALGEBRAIC_MODEL_ONLY"); break;
        default: snprintf(cert.state, sizeof cert.state, "%s", "CERTIFIED");
                 snprintf(cert.instantiation_gate, sizeof cert.instantiation_gate, "%s", "CERTIFIED_NATIVE_BINDING");
                 snprintf(cert.semantic_gate, sizeof cert.semantic_gate, "%s", "unreviewed"); break;
      }
    }

    AGDPlan *p = agd_plan_create(x, d, m, U, tol, &cert);
    if (!p) { c_null++; continue; }
    agd_plan_run(p, steps);
    agd_plan_reconstruct(p, out);
    double err = agd_max_abs_error(ref, out, d);
    int fb = agd_plan_in_fallback(p);
    int adm = agd_plan_admissible(p);

    if (fb) { c_fb++; if (err != 0.0) violate("P1_FALLBACK_EXACT", d, m, steps, tol, fb, adm, err, (unsigned long)it); }
    else {
      c_opt++;
      if (!adm) violate("P3_GATE_SOUND", d, m, steps, tol, fb, adm, err, (unsigned long)it);
      if (tol == 0.0 && err != 0.0) violate("P2_OPT_EXACT_TOL0", d, m, steps, tol, fb, adm, err, (unsigned long)it);
      if (tol > 0.0) {
        if (err > max_err_tol_pos) max_err_tol_pos = err;
        if (tol > max_tol_saw) max_tol_saw = tol;
      }
      if (tol == 0.0) {
        for (size_t i = 0; i < d && i < maxd; i += m)
          for (size_t j = 1; j < m; j++)
            if (out[i + j] != out[i]) { violate("P5_OUTPUT_SECTOR", d, m, steps, tol, fb, adm, err, (unsigned long)it); break; }
      }
    }
    if (tampered && !fb) violate("P4_CERT_FAIL_CLOSED", d, m, steps, tol, fb, adm, err, (unsigned long)it);
    agd_plan_destroy(p);
  }

  printf("FUZZ cases=%ld optimal=%ld fallback=%ld null=%ld tampered=%ld violations=%d\n",
         N, c_opt, c_fb, c_null, c_tamper, violations);
  printf("FUZZ_TOL_POS max_tol=%.6g max_err=%.6g ratio=%.6g\n",
         max_tol_saw, max_err_tol_pos,
         max_tol_saw > 0 ? max_err_tol_pos / max_tol_saw : 0.0);
  printf("FUZZ_RESULT=%s\n", violations ? "FAIL" : "PASS");
  free(U); free(x); free(ref); free(tmp); free(out);
  return violations ? 1 : 0;
}
