/*
 * sovereign_elevate.c — attempt to earn a REAL speedup on the same observable.
 *
 * The audit found the corpus's only correct kernel is 0.73x (a slowdown) and
 * that its two "fast" kernels are fast only because they compute 1/8 and 1/4
 * of the matrix. sovereign_gemm_max.c had the right structural idea (register
 * blocking + packed B) but the implementation was wrong: b1 was dead, and only
 * 4 of every 8 rows were written.
 *
 * This file implements that idea CORRECTLY at several tile shapes and measures
 * each against the same timed scalar baseline on the same observable (the full
 * C=A*B matrix, elementwise). A tile shape that fails the observable check is
 * rejected regardless of speed. Any speedup printed here is a real one: same
 * work, both sides timed, both sides verified.
 */
#include <math.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arm_neon.h>

#define WARMUPS 3
#define REPEATS 15
#define TOL 1e-3

static double now(void) { return omp_get_wtime(); }
static float *alloc64(size_t n) { void *p; posix_memalign(&p, 64, n * sizeof(float)); return (float *)p; }
static double sumf(const float *p, size_t m) { double s = 0; for (size_t i = 0; i < m; i++) s += p[i]; return s; }
static int cmp_desc(const void *x, const void *y) { double a = *(const double *)x, b = *(const double *)y; return (a > b) - (a < b); }

typedef void (*kern)(int, const float *, const float *, float *);

/* baseline: the corpus's own reference_gemm, now TIMED */
static void baseline_gemm(int n, const float *A, const float *B, float *C) {
    for (int i = 0; i < n; i++)
        for (int k = 0; k < n; k++) {
            float a = A[i * n + k];
            for (int j = 0; j < n; j++) C[i * n + j] += a * B[k * n + j];
        }
}

/* naive NEON, 1 row at a time (this is sovereign_gemm_fixed_verify.c) */
static void neon_naive(int n, const float *A, const float *B, float *C) {
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j += 4) {
            float32x4_t s = vdupq_n_f32(0);
            for (int k = 0; k < n; k++) s = vmlaq_n_f32(s, vld1q_f32(&B[k * n + j]), A[i * n + k]);
            vst1q_f32(&C[i * n + j], s);
        }
}

/* 4 rows x 4 cols: each B load feeds 4 accumulators */
static void neon_4x4(int n, const float *A, const float *B, float *C) {
    for (int i = 0; i < n; i += 4)
        for (int j = 0; j < n; j += 4) {
            float32x4_t c0 = vdupq_n_f32(0), c1 = vdupq_n_f32(0);
            float32x4_t c2 = vdupq_n_f32(0), c3 = vdupq_n_f32(0);
            const float *a0 = &A[(i + 0) * n], *a1 = &A[(i + 1) * n];
            const float *a2 = &A[(i + 2) * n], *a3 = &A[(i + 3) * n];
            for (int k = 0; k < n; k++) {
                float32x4_t b = vld1q_f32(&B[k * n + j]);
                c0 = vmlaq_n_f32(c0, b, a0[k]); c1 = vmlaq_n_f32(c1, b, a1[k]);
                c2 = vmlaq_n_f32(c2, b, a2[k]); c3 = vmlaq_n_f32(c3, b, a3[k]);
            }
            vst1q_f32(&C[(i + 0) * n + j], c0); vst1q_f32(&C[(i + 1) * n + j], c1);
            vst1q_f32(&C[(i + 2) * n + j], c2); vst1q_f32(&C[(i + 3) * n + j], c3);
        }
}

/* 4 rows x 8 cols: 8 accumulators, 2 B loads per k */
static void neon_4x8(int n, const float *A, const float *B, float *C) {
    for (int i = 0; i < n; i += 4)
        for (int j = 0; j < n; j += 8) {
            float32x4_t c0 = vdupq_n_f32(0), c1 = vdupq_n_f32(0);
            float32x4_t c2 = vdupq_n_f32(0), c3 = vdupq_n_f32(0);
            float32x4_t c4 = vdupq_n_f32(0), c5 = vdupq_n_f32(0);
            float32x4_t c6 = vdupq_n_f32(0), c7 = vdupq_n_f32(0);
            const float *a0 = &A[(i + 0) * n], *a1 = &A[(i + 1) * n];
            const float *a2 = &A[(i + 2) * n], *a3 = &A[(i + 3) * n];
            for (int k = 0; k < n; k++) {
                float32x4_t b0 = vld1q_f32(&B[k * n + j]);
                float32x4_t b1 = vld1q_f32(&B[k * n + j + 4]);
                c0 = vmlaq_n_f32(c0, b0, a0[k]); c1 = vmlaq_n_f32(c1, b0, a1[k]);
                c2 = vmlaq_n_f32(c2, b0, a2[k]); c3 = vmlaq_n_f32(c3, b0, a3[k]);
                c4 = vmlaq_n_f32(c4, b1, a0[k]); c5 = vmlaq_n_f32(c5, b1, a1[k]);
                c6 = vmlaq_n_f32(c6, b1, a2[k]); c7 = vmlaq_n_f32(c7, b1, a3[k]);
            }
            vst1q_f32(&C[(i + 0) * n + j + 0], c0); vst1q_f32(&C[(i + 0) * n + j + 4], c4);
            vst1q_f32(&C[(i + 1) * n + j + 0], c1); vst1q_f32(&C[(i + 1) * n + j + 4], c5);
            vst1q_f32(&C[(i + 2) * n + j + 0], c2); vst1q_f32(&C[(i + 2) * n + j + 4], c6);
            vst1q_f32(&C[(i + 3) * n + j + 0], c3); vst1q_f32(&C[(i + 3) * n + j + 4], c7);
        }
}

/* 8 rows x 8 cols: 16 accumulators, one per (row, col-block) pair.
 * This is what sovereign_gemm_max.c CLAIMED to do; gemm_max.c actually used
 * 4 accumulators for 8 rows and only ever stored 4 rows, so it lost 3/4 of
 * the matrix. Here every accumulator owns exactly one output row-segment. */
static void neon_8x8(int n, const float *A, const float *B, float *C) {
    for (int i = 0; i < n; i += 8) {
        const float *a0 = &A[(i + 0) * n], *a1 = &A[(i + 1) * n];
        const float *a2 = &A[(i + 2) * n], *a3 = &A[(i + 3) * n];
        const float *a4 = &A[(i + 4) * n], *a5 = &A[(i + 5) * n];
        const float *a6 = &A[(i + 6) * n], *a7 = &A[(i + 7) * n];
        for (int j = 0; j < n; j += 8) {
            float32x4_t c00 = vdupq_n_f32(0), c10 = vdupq_n_f32(0);
            float32x4_t c20 = vdupq_n_f32(0), c30 = vdupq_n_f32(0);
            float32x4_t c40 = vdupq_n_f32(0), c50 = vdupq_n_f32(0);
            float32x4_t c60 = vdupq_n_f32(0), c70 = vdupq_n_f32(0);
            float32x4_t c01 = vdupq_n_f32(0), c11 = vdupq_n_f32(0);
            float32x4_t c21 = vdupq_n_f32(0), c31 = vdupq_n_f32(0);
            float32x4_t c41 = vdupq_n_f32(0), c51 = vdupq_n_f32(0);
            float32x4_t c61 = vdupq_n_f32(0), c71 = vdupq_n_f32(0);
            for (int k = 0; k < n; k++) {
                float32x4_t b0 = vld1q_f32(&B[k * n + j]);
                float32x4_t b1 = vld1q_f32(&B[k * n + j + 4]);
                c00 = vmlaq_n_f32(c00, b0, a0[k]); c01 = vmlaq_n_f32(c01, b1, a0[k]);
                c10 = vmlaq_n_f32(c10, b0, a1[k]); c11 = vmlaq_n_f32(c11, b1, a1[k]);
                c20 = vmlaq_n_f32(c20, b0, a2[k]); c21 = vmlaq_n_f32(c21, b1, a2[k]);
                c30 = vmlaq_n_f32(c30, b0, a3[k]); c31 = vmlaq_n_f32(c31, b1, a3[k]);
                c40 = vmlaq_n_f32(c40, b0, a4[k]); c41 = vmlaq_n_f32(c41, b1, a4[k]);
                c50 = vmlaq_n_f32(c50, b0, a5[k]); c51 = vmlaq_n_f32(c51, b1, a5[k]);
                c60 = vmlaq_n_f32(c60, b0, a6[k]); c61 = vmlaq_n_f32(c61, b1, a6[k]);
                c70 = vmlaq_n_f32(c70, b0, a7[k]); c71 = vmlaq_n_f32(c71, b1, a7[k]);
            }
            vst1q_f32(&C[(i + 0) * n + j], c00); vst1q_f32(&C[(i + 0) * n + j + 4], c01);
            vst1q_f32(&C[(i + 1) * n + j], c10); vst1q_f32(&C[(i + 1) * n + j + 4], c11);
            vst1q_f32(&C[(i + 2) * n + j], c20); vst1q_f32(&C[(i + 2) * n + j + 4], c21);
            vst1q_f32(&C[(i + 3) * n + j], c30); vst1q_f32(&C[(i + 3) * n + j + 4], c31);
            vst1q_f32(&C[(i + 4) * n + j], c40); vst1q_f32(&C[(i + 4) * n + j + 4], c41);
            vst1q_f32(&C[(i + 5) * n + j], c50); vst1q_f32(&C[(i + 5) * n + j + 4], c51);
            vst1q_f32(&C[(i + 6) * n + j], c60); vst1q_f32(&C[(i + 6) * n + j + 4], c61);
            vst1q_f32(&C[(i + 7) * n + j], c70); vst1q_f32(&C[(i + 7) * n + j + 4], c71);
        }
    }
}

static void observable_check(kern f, int n, const float *A, const float *B,
                             const float *REF, double *max_err, double *coverage) {
    size_t m = (size_t)n * n;
    float *C = alloc64(m);
    memset(C, 0, m * sizeof(float));
    f(n, A, B, C);
    *max_err = 0; *coverage = 0;
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
    int n = (argc > 1) ? atoi(argv[1]) : 512;
    size_t sz = (size_t)n * n;
    float *A = alloc64(sz), *B = alloc64(sz), *CT = alloc64(sz);
    for (size_t i = 0; i < sz; i++) { A[i] = 1.1f; B[i] = 2.2f; }

    double flops = 2.0 * (double)n * n * n;
    double tb = timeit(baseline_gemm, n, A, B, CT);
    float *REF = alloc64(sz);
    memcpy(REF, CT, sz * sizeof(float));
    double base_sum = sumf(REF, sz);

    printf("{\n  \"n\": %d,\n  \"omp_num_threads\": %d,\n", n, omp_get_max_threads());
    printf("  \"baseline\": {\"median_s\": %.9f, \"gflops\": %.4f},\n", tb, flops / tb / 1e9);

    struct { const char *name; kern f; } cands[] = {
        {"neon_naive_1x4",   neon_naive},
        {"neon_4x4",         neon_4x4},
        {"neon_4x8",         neon_4x8},
        {"neon_8x8_fixed",   neon_8x8},
    };
    int nc = (int)(sizeof(cands) / sizeof(cands[0]));
    double best = 0; const char *bestname = NULL;
    printf("  \"candidates\": [\n");
    for (int i = 0; i < nc; i++) {
        double me, cov;
        observable_check(cands[i].f, n, A, B, REF, &me, &cov);
        int ok = (me <= TOL) && (cov >= 0.999);
        double tc = timeit(cands[i].f, n, A, B, CT);
        double frac = sumf(CT, sz) / base_sum;
        char spbuf[64];
        if (ok) { snprintf(spbuf, sizeof spbuf, "%.4f", tb / tc); if (tb / tc > best) { best = tb / tc; bestname = cands[i].name; } }
        else    { snprintf(spbuf, sizeof spbuf, "null"); }
        printf("    {\"name\": \"%s\", \"observable_ok\": %s, \"max_error\": %.6f, "
               "\"coverage_frac\": %.6f, \"result_frac_of_baseline\": %.6f, "
               "\"median_s\": %.9f, \"gflops\": %.4f, \"speedup\": %s}%s\n",
               cands[i].name, ok ? "true" : "false", me, cov, frac, tc,
               flops / tc / 1e9, spbuf, (i + 1 < nc) ? "," : "");
    }
    printf("  ],\n");
    printf("  \"best_accepted\": \"%s\",\n", bestname ? bestname : "none");
    printf("  \"best_speedup\": %.4f\n", best);
    printf("}\n");
    return 0;
}
