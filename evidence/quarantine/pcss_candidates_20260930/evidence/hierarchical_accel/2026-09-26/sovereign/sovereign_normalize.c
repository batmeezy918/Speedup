/*
 * sovereign_normalize.c — same-observable normalization harness for the
 * sovereign_* GEMM corpus.
 *
 * FINDING THAT MOTIVATES THIS FILE: not one of the sovereign_* programs times
 * a baseline. They time the NEON candidate and print its GFLOPS, then run the
 * scalar reference AFTER the clock stops, purely to compute an error. So the
 * corpus contains zero measured speedup ratios; every "x times faster" number
 * attributed to it came from outside these files.
 *
 * This harness puts both sides on one observable:
 *   observable  = the full C = A*B matrix, compared elementwise
 *   baseline    = scalar triple loop (i,k,j), as in sovereign_gemm_verify.c
 *   candidate   = NEON vmlaq_f32 kernel, as in sovereign_gemm_fixed_verify.c
 * A candidate that does not reproduce the baseline observable is REJECTED and
 * its timing is discarded, no matter how fast it is.
 *
 * Negative controls carried from the corpus verbatim:
 *   gemm_verify kernel - c1 reuses c0's column range, so every 2nd row is
 *                        half-computed and only 2 of 8 rows are written
 *   gemm_max kernel    - b1 is loaded and never used, and only 4 of 8 rows
 *                        are written
 */
#include <math.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arm_neon.h>

#ifndef N
#define N 512
#endif
#define WARMUPS 3
#define REPEATS 15
#define TOL 1e-3
#define TILE8 8

static double now(void) { return omp_get_wtime(); }

static float *alloc64(size_t n) {
    void *p = NULL;
    posix_memalign(&p, 64, n * sizeof(float));
    return (float *)p;
}

static double sumf(const float *p, size_t m) {
    double s = 0;
    for (size_t i = 0; i < m; i++) s += p[i];
    return s;
}

/* ---------------- baseline: the corpus's own reference_gemm -------------- */
static void baseline_gemm(int n, const float *A, const float *B, float *C) {
    for (int i = 0; i < n; i++)
        for (int k = 0; k < n; k++) {
            float a = A[i * n + k];
            for (int j = 0; j < n; j++) C[i * n + j] += a * B[k * n + j];
        }
}

/* ---------------- candidate A: the correct NEON kernel -------------------- */
static void neon_correct(int n, const float *A, const float *B, float *C) {
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j += 4) {
            float32x4_t s = vdupq_n_f32(0);
            for (int k = 0; k < n; k++)
                s = vmlaq_n_f32(s, vld1q_f32(&B[k * n + j]), A[i * n + k]);
            vst1q_f32(&C[i * n + j], s);
        }
}

/* ------- candidate B: sovereign_gemm_verify.c kernel, verbatim ---------- */
static void neon_broken_verify(int n, const float *A, const float *B, float *C) {
    for (int i = 0; i < n; i += TILE8)
        for (int j = 0; j < n; j += TILE8) {
            float32x4_t c0 = vdupq_n_f32(0), c1 = vdupq_n_f32(0);
            for (int k = 0; k < n; k++) {
                float32x4_t b0 = vld1q_f32(&B[k * n + j]);
                c0 = vmlaq_n_f32(c0, b0, A[(i + 0) * n + k]);
                c1 = vmlaq_n_f32(c1, b0, A[(i + 1) * n + k]);
            }
            vst1q_f32(&C[(i + 0) * n + j], c0);
            vst1q_f32(&C[(i + 1) * n + j], c1);
        }
}

/* --------- candidate C: sovereign_gemm_max.c kernel, verbatim ----------- */
static void neon_broken_max(int n, const float *A, const float *B, float *C) {
    for (int i = 0; i < n; i += 8)
        for (int j = 0; j < n; j += 8) {
            float32x4_t c0 = vdupq_n_f32(0), c1 = vdupq_n_f32(0);
            float32x4_t c2 = vdupq_n_f32(0), c3 = vdupq_n_f32(0);
            for (int k = 0; k < n; k++) {
                __builtin_prefetch(&B[(k + 8) * n + j], 0, 3);
                float32x4_t b0 = vld1q_f32(&B[k * n + j]);
                float32x4_t b1 = vld1q_f32(&B[k * n + j + 4]);
                (void)b1;
                c0 = vmlaq_n_f32(c0, b0, A[(i + 0) * n + k]);
                c1 = vmlaq_n_f32(c1, b0, A[(i + 1) * n + k]);
                c2 = vmlaq_n_f32(c2, b0, A[(i + 2) * n + k]);
                c3 = vmlaq_n_f32(c3, b0, A[(i + 3) * n + k]);
            }
            vst1q_f32(&C[(i + 0) * n + j], c0);
            vst1q_f32(&C[(i + 1) * n + j], c1);
            vst1q_f32(&C[(i + 2) * n + j], c2);
            vst1q_f32(&C[(i + 3) * n + j], c3);
        }
}

static int cmp_desc(const void *x, const void *y) {
    double a = *(const double *)x, b = *(const double *)y;
    return (a > b) - (a < b);
}

typedef void (*kern)(int, const float *, const float *, float *);

static void observable_check(kern f, int n, const float *A, const float *B,
                             const float *REF, double *max_err, double *coverage) {
    size_t m = (size_t)n * n;
    float *C = alloc64(m);
    memset(C, 0, m * sizeof(float));
    f(n, A, B, C);
    *max_err = 0;
    *coverage = 0;
    for (size_t i = 0; i < m; i++) {
        double e = fabs((double)C[i] - (double)REF[i]);
        if (e > *max_err) *max_err = e;
        if (e <= TOL) *coverage += 1.0;
    }
    *coverage /= (double)m;
    free(C);
}

static double timeit(kern f, int n, const float *A, const float *B, float *C) {
    size_t m = (size_t)n * n;
    double s[REPEATS];
    for (int r = 0; r < REPEATS; r++) {
        for (int w = 0; w < WARMUPS; w++) { memset(C, 0, m * sizeof(float)); f(n, A, B, C); }
        memset(C, 0, m * sizeof(float));
        double t0 = now();
        f(n, A, B, C);
        s[r] = now() - t0;
    }
    qsort(s, REPEATS, sizeof(double), cmp_desc);
    return s[REPEATS / 2];
}

int main(int argc, char **argv) {
    int n = (argc > 1) ? atoi(argv[1]) : N;
    size_t sz = (size_t)n * n;
    float *A = alloc64(sz), *B = alloc64(sz);
    float *CB = alloc64(sz), *CT = alloc64(sz), *REF = alloc64(sz);

    for (size_t i = 0; i < sz; i++) { A[i] = 1.1f; B[i] = 2.2f; CB[i] = CT[i] = 0; }

    double flops = 2.0 * (double)n * n * n;
    double tb = timeit(baseline_gemm, n, A, B, CB);
    memcpy(REF, CB, sz * sizeof(float));
    double base_sum = sumf(CB, sz);

    printf("{\n");
    printf("  \"n\": %d,\n", n);
    printf("  \"omp_num_threads\": %d,\n", omp_get_max_threads());
    printf("  \"observable\": \"full C=A*B matrix, elementwise vs scalar baseline\",\n");
    printf("  \"baseline\": {\"name\": \"scalar_triple_loop_i_k_j\", \"median_s\": %.9f, "
           "\"gflops\": %.4f, \"checksum\": %.1f},\n", tb, flops / tb / 1e9, base_sum);

    struct { const char *name; kern f; const char *src; } cands[] = {
        {"neon_correct",     neon_correct,       "sovereign_gemm_fixed_verify.c"},
        {"neon_broken_verify", neon_broken_verify, "sovereign_gemm_verify.c"},
        {"neon_broken_max",  neon_broken_max,    "sovereign_gemm_max.c"},
    };
    int nc = (int)(sizeof(cands) / sizeof(cands[0]));

    printf("  \"candidates\": [\n");
    for (int i = 0; i < nc; i++) {
        double me, cov;
        observable_check(cands[i].f, n, A, B, REF, &me, &cov);
        int ok = (me <= TOL) && (cov >= 0.999);
        double tc = timeit(cands[i].f, n, A, B, CT);
        double frac = sumf(CT, sz) / base_sum;
        printf("    {\n");
        printf("      \"name\": \"%s\",\n", cands[i].name);
        printf("      \"source\": \"%s\",\n", cands[i].src);
        printf("      \"observable_ok\": %s,\n", ok ? "true" : "false");
        printf("      \"max_error\": %.6f,\n", me);
        printf("      \"coverage_frac\": %.6f,\n", cov);
        printf("      \"result_frac_of_baseline\": %.6f,\n", frac);
        printf("      \"median_s\": %.9f,\n", tc);
        printf("      \"gflops\": %.4f,\n", flops / tc / 1e9);
        if (ok) printf("      \"speedup_vs_baseline\": %.4f\n", tb / tc);
        else    printf("      \"speedup_vs_baseline\": null,\n"
                       "      \"reject_reason\": \"does not reproduce the baseline observable; timing discarded\"\n");
        printf("    }%s\n", (i + 1 < nc) ? "," : "");
    }
    printf("  ]\n}\n");
    return 0;
}
