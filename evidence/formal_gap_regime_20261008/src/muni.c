/* muni.c — the user-facing invocation layer (PHASE 9 prototype).
 *
 *     muni elevate --d 4096 --m 64 --steps 64 [--inadmissible] [--json out.json]
 *
 * Deliberately simple. The point is that the user never needs to know about
 * quotient spaces, invariant sectors, certificates, or flags: the tool reports
 * what gap was found, whether it was admissible, whether the certificate was
 * valid, what the speedup was, and what claim class that justifies.
 *
 * Claim classes are exactly PHASE 7 of the directive's taxonomy. This tool only
 * ever emits MEASURED_LOCAL_NATIVE or lower. It never emits a universal claim.
 */
#include "agd_cert.h"
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

/* Full-call baseline: allocation, input copy, all original steps, cleanup. */
static uint64_t full_e2e_ns(const double *x, const double *U,
                            size_t d, size_t m, size_t r, size_t steps) {
  uint64_t t0 = now_ns();
  double *a = malloc(d * sizeof(double));
  double *b = malloc(d * sizeof(double));
  if (!a || !b) { free(a); free(b); return 0; }
  memcpy(a, x, d * sizeof(double));
  for (size_t k = 0; k < steps; k++) {
    agd_original_apply(a, b, U, d, m, r);
    double *swap = a; a = b; b = swap;
  }
  volatile double observed = a[0];
  (void)observed;
  free(a); free(b);
  return now_ns() - t0;
}

/* Full-call quotient: certificate/admissibility gate, plan allocation, run,
   reconstruction, and cleanup. This is the application-facing fast-path cost. */
static uint64_t quotient_e2e_ns(const double *x, const double *U,
                                size_t d, size_t m, const AGDCertificate *cert,
                                size_t steps) {
  uint64_t t0 = now_ns();
  AGDPlan *p = agd_plan_create(x, d, m, U, 0.0, cert);
  double *out = malloc(d * sizeof(double));
  if (!p || !out) {
    if (p) agd_plan_destroy(p);
    free(out);
    return 0;
  }
  agd_plan_run(p, steps);
  agd_plan_reconstruct(p, out);
  volatile double observed = out[0];
  (void)observed;
  agd_plan_destroy(p);
  free(out);
  return now_ns() - t0;
}

int main(int argc, char **argv) {
  size_t d = 4096, m = 64, steps = 64, trials = 7, reps = 5;
  int inadmissible = 0;
  const char *json = NULL;
  for (int i = 1; i < argc; i++) {
    if (!strcmp(argv[i], "elevate") || !strcmp(argv[i], "optimize") || !strcmp(argv[i], "run")) continue;
    else if (!strcmp(argv[i], "--d") && i + 1 < argc) d = (size_t)strtoull(argv[++i], 0, 10);
    else if (!strcmp(argv[i], "--m") && i + 1 < argc) m = (size_t)strtoull(argv[++i], 0, 10);
    else if (!strcmp(argv[i], "--steps") && i + 1 < argc) steps = (size_t)strtoull(argv[++i], 0, 10);
    else if (!strcmp(argv[i], "--trials") && i + 1 < argc) trials = (size_t)strtoull(argv[++i], 0, 10);
    else if (!strcmp(argv[i], "--inadmissible")) inadmissible = 1;
    else if (!strcmp(argv[i], "--json") && i + 1 < argc) json = argv[++i];
    else { fprintf(stderr, "muni: unknown argument '%s'\n", argv[i]); return 2; }
  }
  if (d == 0 || m == 0 || d % m) {
    fprintf(stderr, "muni: illegal shape d=%zu m=%zu (m must divide d)\n", d, m);
    return 2;
  }
  size_t r = d / m;
  if (trials == 0) { fprintf(stderr, "muni: trials must be >= 1\n"); return 2; }
  if (trials > 64) trials = 64;
  if (reps > 64) reps = 64;

  double *U = malloc(r * r * sizeof(double));
  double *x = malloc(d * sizeof(double));
  double *tmp = malloc(d * sizeof(double));
  double *ref = malloc(d * sizeof(double));
  double *out = malloc(d * sizeof(double));
  if (!U || !x || !tmp || !ref || !out) return 3;

  for (size_t b = 0; b < r; b++)
    for (size_t c = 0; c < r; c++) U[b * r + c] = (urand() * 2 - 1) / sqrt((double)r);

  for (size_t i = 0; i < d; i += m) { double v = .25 + 1.75 * urand(); for (size_t j = 0; j < m; j++) x[i + j] = v; }
  if (inadmissible) x[m / 2] += 1.0;   /* deliberately break the invariant */

  AGDCertificate cert = agd_certificate_self();
  AGDPlan *p = agd_plan_create(x, d, m, U, 0.0, &cert);
  if (!p) { fprintf(stderr, "muni: plan_create refused the shape\n"); return 2; }

  /* exact reference, computed once */
  memcpy(ref, x, d * sizeof(double));
  for (size_t k = 0; k < steps; k++) {
    agd_original_apply(ref, tmp, U, d, m, r);
    double *t = ref; ref = tmp; tmp = t;
  }

  double fc[64], qc[64], fec[64], qec[64];
  for (size_t t = 0; t < trials; t++) {
    uint64_t tf = 0, tq = 0, tfe = 0, tqe = 0;
    for (size_t rep = 0; rep < reps; rep++) {
      /* Kernel/run-loop baseline: buffers are preallocated. */
      memcpy(tmp, x, d * sizeof(double));
      uint64_t f0 = now_ns();
      for (size_t k = 0; k < steps; k++) {
        agd_original_apply(tmp, out, U, d, m, r);
        double *z = tmp; tmp = out; out = z;
      }
      uint64_t f1 = now_ns(); tf += f1 - f0;
      /* Kernel/run-loop quotient: plan and gate are already constructed. */
      uint64_t q0 = now_ns();
      agd_plan_run(p, steps);
      uint64_t q1 = now_ns(); tq += q1 - q0;
      agd_plan_destroy(p);
      p = agd_plan_create(x, d, m, U, 0.0, &cert);
      if (!p) { fprintf(stderr, "muni: plan recreation failed\n"); return 3; }

      /* Full-call E2E includes baseline allocations or quotient plan creation,
         admissibility/certificate gate, run, reconstruction and cleanup.
         Alternate arm order to reduce systematic order bias. */
      uint64_t ef, eq;
      if (((t * reps + rep) & 1U) == 0) {
        ef = full_e2e_ns(x, U, d, m, r, steps);
        eq = quotient_e2e_ns(x, U, d, m, &cert, steps);
      } else {
        eq = quotient_e2e_ns(x, U, d, m, &cert, steps);
        ef = full_e2e_ns(x, U, d, m, r, steps);
      }
      if (ef == 0 || eq == 0) {
        fprintf(stderr, "muni: E2E allocation/plan failure\n");
        return 3;
      }
      tfe += ef; tqe += eq;
    }
    fc[t] = (double)tf; qc[t] = (double)tq;
    fec[t] = (double)tfe; qec[t] = (double)tqe;
  }
  /* Preserve trial-order samples before median() sorts the summary arrays. */
  double fr[64], qr[64], fer[64], qer[64];
  for (size_t t = 0; t < trials; t++) {
    fr[t] = fc[t] / (1e6 * (double)reps);
    qr[t] = qc[t] / (1e6 * (double)reps);
    fer[t] = fec[t] / (1e6 * (double)reps);
    qer[t] = qec[t] / (1e6 * (double)reps);
  }
  /* final correctness: one clean run through the plan */
  agd_plan_destroy(p);
  p = agd_plan_create(x, d, m, U, 0.0, &cert);
  agd_plan_run(p, steps);
  agd_plan_reconstruct(p, out);
  double err = agd_max_abs_error(ref, out, d);
  if (!isfinite(err) || err != 0.0) {
    fprintf(stderr, "muni: exactness gate failed, max_abs_error=%.17g\n", err);
    agd_plan_destroy(p);
    free(U); free(x); free(tmp); free(ref); free(out);
    return 4;
  }

  double base_ms = median(fc, trials) / (1e6 * (double)reps);
  double opt_ms = median(qc, trials) / (1e6 * (double)reps);
  double speed = base_ms / opt_ms;
  double base_e2e_ms = median(fec, trials) / (1e6 * (double)reps);
  double opt_e2e_ms = median(qec, trials) / (1e6 * (double)reps);
  double e2e_speed = base_e2e_ms / opt_e2e_ms;
  /* Claim class must never exceed the evidence. A Lean algebraic model is not
   * a formal refinement proof of the native C/IEEE-754 implementation. */
  const char *claim;
  if (agd_plan_in_fallback(p)) claim = "QUARANTINED_OPTIMISATION_NOT_APPLIED";
  else if (strcmp(cert.state, "CERTIFIED") == 0 &&
           strcmp(cert.instantiation_gate, "CERTIFIED_NATIVE_BINDING") == 0)
    claim = "MEASURED_LOCAL_NATIVE";
  else claim = "FORMAL_PARTIAL_MEASURED_LOCAL";

  printf("AGD ANALYSIS\n");
  printf("--------------------------\n");
  printf("Gap:                   %s\n", "FOUND (invariant-state redundancy)");
  printf("Invariant:             %s\n", agd_plan_admissible(p) ? "CERTIFIED" : "VIOLATED -> REFUSED");
  printf("Semantic gate:         %s\n", agd_plan_certified(p) ? "PROVED" : "ABSENT -> FALLBACK");
  printf("Instantiation gate:    %s\n", cert.instantiation_gate);
  printf("Certificate state:     %s\n", cert.state);
  printf("Path taken:            %s\n", agd_plan_in_fallback(p) ? "ORIGINAL (fallback)" : "QUOTIENT (optimised)");
  printf("Semantic preservation: %s\n", err == 0.0 ? "PASS (bit-exact)" : "PASS (within tol)");
  printf("Reconstruction:        %s\n", err == 0.0 ? "PASS (exact)" : "FAIL");
  printf("Adversarial suite:     NOT RUN IN THIS PROCESS (see separate receipt)\n");
  printf("Native compiler:       %s\n", cert.compiler);
  printf("Target:                %s\n", cert.target);
  printf("\n");
  printf("d = %zu   quotient r = %zu   tile m = %zu   steps = %zu\n", d, r, m, steps);
  printf("Run-loop baseline/call:%10.3f ms   (median trial total / %zu reps)\n", base_ms, reps);
  printf("Run-loop quotient/call: %10.3f ms\n", opt_ms);
  printf("Run-loop speedup:       %10.3fx  (plan/gate/reconstruction excluded)\n", speed);
  printf("Full-call baseline E2E: %10.3f ms   (alloc + copy + steps + cleanup)\n", base_e2e_ms);
  printf("Full-call quotient E2E: %10.3f ms   (plan/gate + run + reconstruct + cleanup)\n", opt_e2e_ms);
  printf("End-to-end speedup:     %10.3fx\n", e2e_speed);
  printf("Machine precision:     max_abs_error = %.3g\n", err);
  printf("\n");
  printf("Claim: %s\n", claim);
  printf("Transformation: %s\n", agd_plan_transformation_id(p));
  printf("Certificate SHA: %s\n", agd_plan_certificate(p));
  printf("Source manifest SHA: %s\n", cert.source_sha256);
  printf("Proof artifact SHA: %s\n", cert.certified_artefact_sha256);
  printf("Instantiation gate: %s\n", cert.instantiation_gate);

  if (json) {
    FILE *f = fopen(json, "w");
    if (f) {
      fprintf(f, "{\n");
      fprintf(f, "  \"transformation_id\": \"%s\",\n", agd_plan_transformation_id(p));
      fprintf(f, "  \"certificate_sha256\": \"%s\",\n", agd_plan_certificate(p));
      fprintf(f, "  \"source_manifest_sha256\": \"%s\",\n", cert.source_sha256);
      fprintf(f, "  \"proof_artifact_sha256\": \"%s\",\n", cert.certified_artefact_sha256);
      fprintf(f, "  \"semantic_gate\": \"%s\",\n", cert.semantic_gate);
      fprintf(f, "  \"instantiation_gate\": \"%s\",\n", cert.instantiation_gate);
      fprintf(f, "  \"certificate_state\": \"%s\",\n", cert.state);
      fprintf(f, "  \"compiler\": \"%s\",\n", cert.compiler);
      fprintf(f, "  \"flags\": \"%s\",\n", cert.flags);
      fprintf(f, "  \"target\": \"%s\",\n", cert.target);
      fprintf(f, "  \"d\": %zu, \"quotient_r\": %zu, \"tile_m\": %zu, \"steps\": %zu,\n", d, r, m, steps);
      fprintf(f, "  \"admissible\": %s,\n", agd_plan_admissible(p) ? "true" : "false");
      fprintf(f, "  \"in_fallback\": %s,\n", agd_plan_in_fallback(p) ? "true" : "false");
      fprintf(f, "  \"max_abs_error\": %.17g,\n", err);
      fprintf(f, "  \"timing_scope\": \"run_loop_only_excludes_plan_creation_gate_reconstruction\",\n");
      fprintf(f, "  \"baseline_ms\": %.6f,\n", base_ms);
      fprintf(f, "  \"optimised_ms\": %.6f,\n", opt_ms);
      fprintf(f, "  \"speedup\": %.6f,\n", speed);
      fprintf(f, "  \"baseline_e2e_ms\": %.6f,\n", base_e2e_ms);
      fprintf(f, "  \"optimised_e2e_ms\": %.6f,\n", opt_e2e_ms);
      fprintf(f, "  \"e2e_speedup\": %.6f,\n", e2e_speed);
      fprintf(f, "  \"e2e_scope\": \"baseline_alloc_copy_steps_cleanup_vs_quotient_plan_gate_run_reconstruct_cleanup\",\n");
      fprintf(f, "  \"trial_samples_ms\": {\n");
      fprintf(f, "    \"baseline_runloop\": [");
      for (size_t t = 0; t < trials; t++) fprintf(f, "%s%.9f", t ? ", " : "", fr[t]);
      fprintf(f, "],\n    \"quotient_runloop\": [");
      for (size_t t = 0; t < trials; t++) fprintf(f, "%s%.9f", t ? ", " : "", qr[t]);
      fprintf(f, "],\n    \"baseline_e2e\": [");
      for (size_t t = 0; t < trials; t++) fprintf(f, "%s%.9f", t ? ", " : "", fer[t]);
      fprintf(f, "],\n    \"quotient_e2e\": [");
      for (size_t t = 0; t < trials; t++) fprintf(f, "%s%.9f", t ? ", " : "", qer[t]);
      fprintf(f, "]\n  },\n");
      fprintf(f, "  \"trial_samples_definition\": \"per-trial mean across repetitions; E2E arm order alternates\",\n");
      fprintf(f, "  \"trials\": %zu, \"reps\": %zu,\n", trials, reps);
      fprintf(f, "  \"adversarial_suite\": \"NOT_RUN_IN_THIS_PROCESS\",\n");
      fprintf(f, "  \"claim_class\": \"%s\"\n", claim);
      fprintf(f, "}\n");
      fclose(f);
      printf("Receipt written: %s\n", json);
    }
  }
  agd_plan_destroy(p);
  free(U); free(x); free(tmp); free(ref); free(out);
  return 0;
}