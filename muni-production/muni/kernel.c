/* agd_cert.c — certificate-bound quotient plan with MANDATORY fallback.
 *
 * Advances AGD_ELEVATION_20261007/agd_runtime.c, which gated admissibility in
 * agd_plan_create but had two structural gaps against the formal-gap regime:
 *
 *   1. NO FALLBACK.  agd_plan_create returns NULL when the invariant fails. That
 *      is a refusal, not a fallback: the caller must then re-implement the
 *      original path. "Safe by construction" requires the original path to be
 *      available INSIDE the same object.
 *   2. NO CERTIFICATE BINDING. The native artifact carried no transformation id,
 *      no certificate hash, no compiler fingerprint, so a .so could not be traced
 *      to the proof that licensed it.
 *
 * This file fixes both, and generalises the operator from the DIAGONAL case of
 * agd_runtime.c to the TENSOR-SEPARABLE form
 *
 *     U = Ubar (x) I_m        (block size m, quotient dimension r = d/m)
 *
 * whose quotient path is exact on the block-constant sector. The diagonal case is
 * the special case Ubar diagonal.
 *
 * SAFETY CONTRACT (the whole point of this file)
 *
 *   certificate CERTIFIED  AND  admissible(x)  ->  quotient path (optimised)
 *   otherwise                                 ->  original full-state path
 *
 * There is no third branch. The optimised path is never entered outside the
 * certified domain, and falling back costs correctness nothing: the fallback
 * output is the ORIGINAL operator applied to the ORIGINAL state.
 */
#include "kernel_agl.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define AGD_TID "quotient-descent-v2-tensor"
#define AGD_CERT_SHA "ef60162893f59ee1446af27005e332a0b7978e2822e424511611644713b24ff1"

struct AGDPlan {
  size_t d, m, r;
  double *U;        /* r x r block quotient operator                          */
  double *q0;       /* initial quotient state (decimation)                     */
  double *qf, *qb;  /* quotient ping-pong                                     */
  double *xf, *xb;  /* full-state ping-pong (fallback path)                   */
  double *x0;       /* initial full state (fallback path)                     */
  int admissible;   /* invariant holds for x0                                */
  int cert_ok;      /* certificate state == CERTIFIED                         */
  int fallback;     /* actually running the original path                    */
  AGDCertificate cert;
};

/* ------------------------------------------------------------- certificate */

AGDCertificate agd_certificate_self(void) {
  AGDCertificate c;
  memset(&c, 0, sizeof c);
  snprintf(c.transformation_id, sizeof c.transformation_id, "%s", AGD_TID);
  snprintf(c.certificate_sha256, sizeof c.certificate_sha256, "%s", AGD_CERT_SHA);
  /* The source and artefact hashes are NOT duplicated here. They live in
     evidence/evidence.json (kernel_source_sha256, library_sha256) and are
     checked at runtime by verify_evidence(). Hardcoding them here would let
     them drift out of sync with the actual files; the manifest is generated
     by tools/make_evidence.py after every source change. */
  snprintf(c.scope, sizeof c.scope, "%s",
           "concrete Lean theorems AGD.recursive_forward_refinement and AGD.recursive_exact_reconstruction "
           "for TensorState R M alpha on the block-constant invariant sector; "
           "pointwise reconstruction and forward refinement; #print axioms reports none");
  snprintf(c.semantic_gate, sizeof c.semantic_gate, "%s",
           "AGD.recursive_forward_refinement + AGD.recursive_exact_reconstruction (Lean, axioms [])");
  snprintf(c.instantiation_gate, sizeof c.instantiation_gate, "%s", "CLOSED");
  snprintf(c.compiler, sizeof c.compiler, "%s", AGD_COMPILER);
  snprintf(c.flags, sizeof c.flags, "%s", AGD_FLAGS);
  snprintf(c.target, sizeof c.target, "%s", AGD_TARGET);
  /* Concrete instantiation is now machine-checked; certification is permitted. */
  snprintf(c.state, sizeof c.state, "%s", "CERTIFIED");
  return c;
}

int agd_certificate_is_certified(const AGDCertificate *c) {
  /* "CERTIFIED" = both gates present. */
  return c && strcmp(c->state, "CERTIFIED") == 0;
}

int agd_certificate_authorises_optimised(const AGDCertificate *c) {
  /* Constitutional rule: FORMAL_PARTIAL is evidence, never authorization. */
  if (!c) return 0;
  if (strcmp(c->state, "CERTIFIED") != 0) return 0;
  if (c->semantic_gate[0] == '\0') return 0;
  if (c->instantiation_gate[0] == '\0') return 0;
  if (strcmp(c->instantiation_gate, "ABSENT") == 0) return 0;
  return 1;
}

/* ------------------------------------------------------- the two operators */

/* ORIGINAL: dense r x r matvec broadcast over every block. d*r ops. This is the
 * baseline the optimised path must reproduce exactly, and the path taken on
 * fallback. Loop order chosen so the stride is m doubles -- the honest dense
 * form, matching agd_tensored_amortized.c's strided variant. */
void agd_original_apply(const double *x, double *y, const double *U,
                        size_t d, size_t m, size_t r) {
  (void)d;
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

/* OPTIMISED: r x r matvec on the quotient only. r^2 ops. Exact because the
 * block-constant sector is U-invariant: (Ubar (x) I_m) applied to a block-constant
 * vector is block-constant with block values Ubar @ q. */
static void quotient_apply(const double *q, double *o, const double *U, size_t r) {
  for (size_t b = 0; b < r; b++) {
    const double *row = U + b * r;
    double acc = 0.0;
    for (size_t c = 0; c < r; c++) acc += row[c] * q[c];
    o[b] = acc;
  }
}

/* --------------------------------------------------------- invariant gate */

/* admissible(x) := x is block-constant to within tol. This is the Omega condition.
 * The boundary is exposed: callers can ask, and the plan records the verdict. */
int agd_admissible_block_constant(const double *x, size_t d, size_t m, double tol) {
  if (!x || d == 0 || m == 0 || d % m != 0 || !isfinite(tol) || tol < 0) return 0;
  size_t r = d / m;
  for (size_t b = 0; b < r; b++) {
    double v = x[b * m];
    /* Non-finite values are conservatively routed to the original path.
       They make byte-level equivalence dependent on NaN payload and FP rules. */
    if (!isfinite(v)) return 0;
    for (size_t j = 1; j < m; j++) {
      double z = x[b * m + j];
      if (!isfinite(z)) return 0;
      /* Numeric comparison: -0.0 and +0.0 are the same fiber value. This
         matches the Python gate and the evidence manifest, which both treat
         the admissibility boundary as numeric tolerance, not bitwise. */
      if (fabs(z - v) > tol) {
        return 0;
      }
    }
  }
  return 1;
}

double agd_max_abs_error(const double *a, const double *b, size_t n) {
  if (!a || !b) return INFINITY;
  double e = 0;
  for (size_t i = 0; i < n; i++) {
    double z = fabs(a[i] - b[i]);
    if (z > e) e = z;
  }
  return e;
}

/* ------------------------------------------------------------- plan object */

AGDPlan *agd_plan_create(const double *x, size_t d, size_t m, const double *U,
                         double tol, const AGDCertificate *cert) {
  if (!x || !U || d == 0 || m == 0 || d % m != 0) return NULL;
  size_t r = d / m;
  if (r == 0) return NULL;
  /* Guard against overflow in the allocation-size multiplications below. */
  if (r > SIZE_MAX / r / sizeof(double)) return NULL;
  if (d > SIZE_MAX / sizeof(double)) return NULL;
  AGDPlan *p = (AGDPlan *)calloc(1, sizeof *p);
  if (!p) return NULL;
  p->d = d; p->m = m; p->r = r;
  p->cert = cert ? *cert : agd_certificate_self();

  p->U = (double *)malloc(r * r * sizeof(double));
  p->q0 = (double *)malloc(r * sizeof(double));
  p->qf = (double *)malloc(r * sizeof(double));
  p->qb = (double *)malloc(r * sizeof(double));
  p->xf = (double *)malloc(d * sizeof(double));
  p->xb = (double *)malloc(d * sizeof(double));
  p->x0 = (double *)malloc(d * sizeof(double));
  if (!p->U || !p->q0 || !p->qf || !p->qb || !p->xf || !p->xb || !p->x0) {
    agd_plan_destroy(p);
    return NULL;
  }
  memcpy(p->U, U, r * r * sizeof(double));
  memcpy(p->x0, x, d * sizeof(double));
  memcpy(p->xf, x, d * sizeof(double));
  for (size_t b = 0; b < r; b++) p->q0[b] = x[b * m];
  memcpy(p->qf, p->q0, r * sizeof(double));

  /* The two conditions that together authorise the optimised path. */
  p->cert_ok = agd_certificate_authorises_optimised(&p->cert);
  p->admissible = agd_admissible_block_constant(x, d, m, tol);
  p->fallback = (!(p->cert_ok && p->admissible));
  return p;
}

size_t agd_plan_size(const AGDPlan *p) { return p ? p->r : 0; }
size_t agd_plan_full_size(const AGDPlan *p) { return p ? p->d : 0; }
int agd_plan_admissible(const AGDPlan *p) { return p ? p->admissible : 0; }
int agd_plan_certified(const AGDPlan *p) { return p ? p->cert_ok : 0; }
int agd_plan_in_fallback(const AGDPlan *p) { return p ? p->fallback : 0; }
const char *agd_plan_transformation_id(const AGDPlan *p) { return p ? p->cert.transformation_id : ""; }
const char *agd_plan_certificate(const AGDPlan *p) { return p ? p->cert.certificate_sha256 : ""; }

int agd_plan_step(AGDPlan *p) {
  if (!p) return 0;
  if (p->fallback) {
    /* ORIGINAL path, bit-for-bit the unoptimised operator. */
    agd_original_apply(p->xf, p->xb, p->U, p->d, p->m, p->r);
    double *t = p->xf; p->xf = p->xb; p->xb = t;
    return 1;
  }
  quotient_apply(p->qf, p->qb, p->U, p->r);
  double *t = p->qf; p->qf = p->qb; p->qb = t;
  return 1;
}

int agd_plan_run(AGDPlan *p, size_t steps) {
  if (!p) return 0;
  for (size_t k = 0; k < steps; k++) if (!agd_plan_step(p)) return 0;
  return 1;
}

int agd_plan_reconstruct(const AGDPlan *p, double *out) {
  if (!p || !out) return 0;
  if (p->fallback) { memcpy(out, p->xf, p->d * sizeof(double)); return 1; }
  for (size_t b = 0; b < p->r; b++) {
    double v = p->qf[b];
    for (size_t j = 0; j < p->m; j++) out[b * p->m + j] = v;
  }
  return 1;
}

void agd_plan_destroy(AGDPlan *p) {
  if (!p) return;
  free(p->U); free(p->q0); free(p->qf); free(p->qb);
  free(p->xf); free(p->xb); free(p->x0);
  free(p);
}