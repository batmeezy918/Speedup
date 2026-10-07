/*
 * sovereign_blas_compare.c — the G_non_advantageous gate, run for real.
 *
 * The sovereign audit could not certify its 3.7x NEON speedup because the
 * baseline was the corpus's own unoptimized triple loop. A tuned blocked GEMM
 * is the honest reference, not a naive loop. OpenBLAS is present on this
 * machine (libopenblas.aarch64, confirmed by visible_hpc.c's use of cblas.h),
 * so that reference can be measured instead of hand-waved.
 *
 * Same observable for all three: the full C = A*B matrix, compared elementwise.
 *   ref_scalar : the corpus's own reference_gemm, timed
 *   neon_8x8   : the corrected register-blocked kernel from sovereign_elevate.c
 *   openblas   : cblas_sgemm, the tuned reference implementation
 *
 * Single-threaded on all three (OPENBLAS_NUM_THREADS=1) so the comparison is
 * core-for-core and not a thread-count artifact.
 */
#include <math.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arm_neon.h>
#include <cblas.h>

#define WARMUPS 5
#define REPEATS 21
/*
 * Tolerance must be RELATIVE. A fixed absolute threshold silently mislabels a
 * correct implementation as broken once n grows: OpenBLAS accumulates in
 * blocked/FMA order, so at n=1024 (true C value 2478.08) its float32 drift is
 * 5.1e-3 absolute but only 2.1e-6 relative. Measured with an absolute 1e-3
 * threshold, OpenBLAS was reported as failing the observable check at n>=768,
 * which is an artifact of the harness, not a defect. Relative tolerance below.
 */
#define RTOL 1e-4

static double now(void) { return omp_get_wtime(); }
static float *alloc64(size_t n) { void *p; posix_memalign(&p, 64, n * sizeof(float)); return (float *)p; }
static int cmp_desc(const void *x, const void *y) { double a = *(const double *)x, b = *(const double *)y; return (a > b) - (a < b); }

static void ref_scalar(int n, const float *A, const float *B, float *C) {
    for (int i = 0; i < n; i++)
        for (int k = 0; k < n; k++) {
            float a = A[i * n + k];
            for (int j = 0; j < n; j++) C[i * n + j] += a * B[k * n + j];
        }
}

/* corrected 8x8 register-blocked NEON kernel, 16 accumulators */
static void neon_8x8(int n, const float *A, const float *B, float *C) {
    for (int i = 0; i < n; i += 8) {
        const float *a0 = &A[(i+0)*n], *a1 = &A[(i+1)*n], *a2 = &A[(i+2)*n], *a3 = &A[(i+3)*n];
        const float *a4 = &A[(i+4)*n], *a5 = &A[(i+5)*n], *a6 = &A[(i+6)*n], *a7 = &A[(i+7)*n];
        for (int j = 0; j < n; j += 8) {
            float32x4_t c00=vdupq_n_f32(0),c10=vdupq_n_f32(0),c20=vdupq_n_f32(0),c30=vdupq_n_f32(0);
            float32x4_t c40=vdupq_n_f32(0),c50=vdupq_n_f32(0),c60=vdupq_n_f32(0),c70=vdupq_n_f32(0);
            float32x4_t c01=vdupq_n_f32(0),c11=vdupq_n_f32(0),c21=vdupq_n_f32(0),c31=vdupq_n_f32(0);
            float32x4_t c41=vdupq_n_f32(0),c51=vdupq_n_f32(0),c61=vdupq_n_f32(0),c71=vdupq_n_f32(0);
            for (int k = 0; k < n; k++) {
                float32x4_t b0 = vld1q_f32(&B[k*n+j]);
                float32x4_t b1 = vld1q_f32(&B[k*n+j+4]);
                c00=vmlaq_n_f32(c00,b0,a0[k]); c01=vmlaq_n_f32(c01,b1,a0[k]);
                c10=vmlaq_n_f32(c10,b0,a1[k]); c11=vmlaq_n_f32(c11,b1,a1[k]);
                c20=vmlaq_n_f32(c20,b0,a2[k]); c21=vmlaq_n_f32(c21,b1,a2[k]);
                c30=vmlaq_n_f32(c30,b0,a3[k]); c31=vmlaq_n_f32(c31,b1,a3[k]);
                c40=vmlaq_n_f32(c40,b0,a4[k]); c41=vmlaq_n_f32(c41,b1,a4[k]);
                c50=vmlaq_n_f32(c50,b0,a5[k]); c51=vmlaq_n_f32(c51,b1,a5[k]);
                c60=vmlaq_n_f32(c60,b0,a6[k]); c61=vmlaq_n_f32(c61,b1,a6[k]);
                c70=vmlaq_n_f32(c70,b0,a7[k]); c71=vmlaq_n_f32(c71,b1,a7[k]);
            }
            vst1q_f32(&C[(i+0)*n+j],c00); vst1q_f32(&C[(i+0)*n+j+4],c01);
            vst1q_f32(&C[(i+1)*n+j],c10); vst1q_f32(&C[(i+1)*n+j+4],c11);
            vst1q_f32(&C[(i+2)*n+j],c20); vst1q_f32(&C[(i+2)*n+j+4],c21);
            vst1q_f32(&C[(i+3)*n+j],c30); vst1q_f32(&C[(i+3)*n+j+4],c31);
            vst1q_f32(&C[(i+4)*n+j],c40); vst1q_f32(&C[(i+4)*n+j+4],c41);
            vst1q_f32(&C[(i+5)*n+j],c50); vst1q_f32(&C[(i+5)*n+j+4],c51);
            vst1q_f32(&C[(i+6)*n+j],c60); vst1q_f32(&C[(i+6)*n+j+4],c61);
            vst1q_f32(&C[(i+7)*n+j],c70); vst1q_f32(&C[(i+7)*n+j+4],c71);
        }
    }
}

static void blas_sgemm(int n, const float *A, const float *B, float *C) {
    cblas_sgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans, n, n, n,
                1.0f, A, n, B, n, 0.0f, C, n);
}

typedef void (*kern)(int, const float *, const float *, float *);

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

static void check(kern f, int n, const float *A, const float *B, const float *REF,
                  double *max_err, double *cov) {
    size_t m = (size_t)n * n;
    float *C = alloc64(m);
    memset(C, 0, m * sizeof(float));
    f(n, A, B, C);
    /* scale = magnitude of a representative output element */
    double scale = 0;
    for (size_t i = 0; i < m; i += (m / 64 + 1)) if (fabs((double)REF[i]) > scale) scale = fabs((double)REF[i]);
    if (scale < 1.0) scale = 1.0;
    *max_err = 0; *cov = 0;
    for (size_t i = 0; i < m; i++) {
        double e = fabs((double)C[i] - (double)REF[i]) / scale;
        if (e > *max_err) *max_err = e;
        if (e <= RTOL) *cov += 1.0;
    }
    *cov /= (double)m;
    free(C);
}

int main(int argc, char **argv) {
    int sizes[4] = {256, 512, 768, 1024};
    if (argc > 1) { sizes[0] = atoi(argv[1]); sizes[1] = sizes[0]; sizes[2] = sizes[0]; sizes[3] = sizes[0]; }
    setenv("OPENBLAS_NUM_THREADS", "1", 1);

    printf("{\n");
    printf("  \"gate\": \"G_non_advantageous\",\n");
    printf("  \"reference_impl\": \"OpenBLAS cblas_sgemm (tuned, blocked, packed)\",\n");
    printf("  \"openblas_num_threads\": 1,\n");
    printf("  \"tolerance\": \"relative %g, coverage >= 0.999\",\n", (double)RTOL);
    printf("  \"omp_num_threads\": %d,\n", omp_get_max_threads());
    printf("  \"results\": [\n");
    for (int s = 0; s < 4; s++) {
        int n = sizes[s];
        size_t sz = (size_t)n * n;
        float *A = alloc64(sz), *B = alloc64(sz), *CT = alloc64(sz);
        for (size_t i = 0; i < sz; i++) { A[i] = 1.1f; B[i] = 2.2f; }
        double flops = 2.0 * (double)n * n * n;

        double tref = timeit(ref_scalar, n, A, B, CT);
        float *REF = alloc64(sz);
        memcpy(REF, CT, sz * sizeof(float));

        double e_neon, c_neon, e_blas, c_blas;
        check(neon_8x8, n, A, B, REF, &e_neon, &c_neon);
        check(blas_sgemm, n, A, B, REF, &e_blas, &c_blas);

        double tneon = timeit(neon_8x8, n, A, B, CT);
        double tblas = timeit(blas_sgemm, n, A, B, CT);

        printf("    {\"n\": %d,\n", n);
        printf("     \"ref_scalar_s\": %.9f, \"ref_scalar_gflops\": %.4f,\n", tref, flops / tref / 1e9);
        printf("     \"neon_8x8\": {\"observable_ok\": %s, \"max_rel_error\": %.3e, \"coverage_frac\": %.6f, "
               "\"median_s\": %.9f, \"gflops\": %.4f, \"speedup_vs_ref_scalar\": %.4f, \"speedup_vs_openblas\": %.4f},\n",
               (e_neon <= RTOL && c_neon >= 0.999) ? "true" : "false", e_neon, c_neon, tneon,
               flops / tneon / 1e9, tref / tneon, tblas / tneon);
        printf("     \"openblas_sgemm\": {\"observable_ok\": %s, \"max_rel_error\": %.3e, \"coverage_frac\": %.6f, "
               "\"median_s\": %.9f, \"gflops\": %.4f, \"speedup_vs_ref_scalar\": %.4f}\n",
               (e_blas <= RTOL && c_blas >= 0.999) ? "true" : "false", e_blas, c_blas, tblas,
               flops / tblas / 1e9, tref / tblas);
        printf("    }%s\n", (s < 3) ? "," : "");
        free(A); free(B); free(CT); free(REF);
    }
    printf("  ]\n}\n");
    return 0;
}
