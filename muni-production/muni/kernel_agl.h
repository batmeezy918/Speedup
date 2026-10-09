#ifndef AGD_CERT_H
#define AGD_CERT_H
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Compiled-in provenance, supplied by -D at build time. */
#ifndef AGD_COMPILER
#define AGD_COMPILER "unknown"
#endif
#ifndef AGD_FLAGS
#define AGD_FLAGS "unknown"
#endif
#ifndef AGD_TARGET
#define AGD_TARGET "unknown"
#endif

typedef struct {
  char transformation_id[48];
  char certificate_sha256[72];
  char source_sha256[72];
  char compiler[40];
  char flags[112];
  char target[32];
  char state[24];
  char scope[512];
  char certified_artefact_sha256[72];
  char semantic_gate[160];
  char instantiation_gate[32];
} AGDCertificate;

AGDCertificate agd_certificate_self(void);
int agd_certificate_is_certified(const AGDCertificate *c);
int agd_certificate_authorises_optimised(const AGDCertificate *c);

/* The ORIGINAL (unoptimised) operator: dense Ubar (x) I_m. */
void agd_original_apply(const double *x, double *y, const double *U,
                        size_t d, size_t m, size_t r);
void agd_quotient_apply(const double *q, double *o, const double *U, size_t r);

int agd_admissible_block_constant(const double *x, size_t d, size_t m, double tol);
double agd_max_abs_error(const double *a, const double *b, size_t n);

typedef struct AGDPlan AGDPlan;

/* Always returns a plan when the shape is legal. Whether it runs the optimised
   or the original path is decided by the certificate and the admissibility gate,
   and is observable via agd_plan_in_fallback(). Returns NULL only for an illegal
   shape (d==0, m==0, m does not divide d) or allocation failure. */
AGDPlan *agd_plan_create(const double *x, size_t d, size_t m, const double *U,
                         double tol, const AGDCertificate *cert);

size_t agd_plan_size(const AGDPlan *p);
size_t agd_plan_full_size(const AGDPlan *p);
int agd_plan_admissible(const AGDPlan *p);
int agd_plan_certified(const AGDPlan *p);
int agd_plan_in_fallback(const AGDPlan *p);
const char *agd_plan_transformation_id(const AGDPlan *p);
const char *agd_plan_certificate(const AGDPlan *p);

int agd_plan_step(AGDPlan *p);
int agd_plan_run(AGDPlan *p, size_t steps);
int agd_plan_reconstruct(const AGDPlan *p, double *out);
void agd_plan_destroy(AGDPlan *p);

#ifdef __cplusplus
}
#endif
#endif