#define _GNU_SOURCE

#include <arm_neon.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include <unistd.h>

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

static uint32_t rng_state = 0x9E3779B9u;

static uint32_t rng_u32(void) {
    uint32_t x = rng_state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    rng_state = x;
    return x;
}

static float rng_float(void) {
    return ((float)(rng_u32() & 0xFFFFu) / 65535.0f) - 0.5f;
}

static void fill_matrix(float *x, size_t count) {
    for (size_t i = 0; i < count; ++i)
        x[i] = rng_float();
}

static void zero_matrix(float *x, size_t count) {
    memset(x, 0, count * sizeof(float));
}

/* Scalar reference GEMM:
 *
 * C = A * B
 *
 * Row-major:
 * A[i,k] * B[k,j]
 */
static void gemm_scalar(int n,
                        const float *a,
                        const float *b,
                        float *c)
{
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            float sum = 0.0f;

            for (int k = 0; k < n; ++k)
                sum += a[(size_t)i*n + k] *
                       b[(size_t)k*n + j];

            c[(size_t)i*n + j] = sum;
        }
    }
}

/*
 * 4x4 AArch64 NEON FMA microkernel.
 *
 * Four output rows are accumulated simultaneously.
 * Each iteration loads four contiguous B values:
 *
 *   B[k][j:j+3]
 *
 * and broadcasts four scalar A values.
 */
static void gemm_neon_4x4(int n,
                          const float *a,
                          const float *b,
                          float *c)
{
    for (int i = 0; i < n; i += 4) {

        for (int j = 0; j < n; j += 4) {

            float32x4_t c0 = vdupq_n_f32(0.0f);
            float32x4_t c1 = vdupq_n_f32(0.0f);
            float32x4_t c2 = vdupq_n_f32(0.0f);
            float32x4_t c3 = vdupq_n_f32(0.0f);

            for (int k = 0; k < n; ++k) {

                float32x4_t bv =
                    vld1q_f32(&b[(size_t)k*n + j]);

                c0 = vfmaq_n_f32(
                    c0, bv,
                    a[(size_t)(i+0)*n + k]);

                c1 = vfmaq_n_f32(
                    c1, bv,
                    a[(size_t)(i+1)*n + k]);

                c2 = vfmaq_n_f32(
                    c2, bv,
                    a[(size_t)(i+2)*n + k]);

                c3 = vfmaq_n_f32(
                    c3, bv,
                    a[(size_t)(i+3)*n + k]);
            }

            vst1q_f32(&c[(size_t)(i+0)*n + j], c0);
            vst1q_f32(&c[(size_t)(i+1)*n + j], c1);
            vst1q_f32(&c[(size_t)(i+2)*n + j], c2);
            vst1q_f32(&c[(size_t)(i+3)*n + j], c3);
        }
    }
}

static double checksum(const float *x, size_t count) {
    double s = 0.0;

    for (size_t i = 0; i < count; ++i)
        s += (double)x[i] * (double)(i + 1);

    return s;
}

static void compare_results(const float *ref,
                            const float *test,
                            size_t count,
                            double *max_abs,
                            double *rmse)
{
    double maxerr = 0.0;
    double sumsq = 0.0;

    for (size_t i = 0; i < count; ++i) {

        double d = (double)test[i] - (double)ref[i];

        double ad = fabs(d);

        if (ad > maxerr)
            maxerr = ad;

        sumsq += d*d;
    }

    *max_abs = maxerr;
    *rmse = sqrt(sumsq / (double)count);
}

static int cmp_double(const void *pa, const void *pb) {
    double a = *(const double *)pa;
    double b = *(const double *)pb;

    return (a > b) - (a < b);
}

static double median(double *x, int n) {
    qsort(x, (size_t)n, sizeof(double), cmp_double);

    if (n & 1)
        return x[n/2];

    return 0.5 * (x[n/2 - 1] + x[n/2]);
}

static void print_cpu_info(void) {

    FILE *f = fopen("/proc/cpuinfo", "r");

    if (!f) {
        printf("CPU_INFO=unavailable\n");
        return;
    }

    char line[512];

    while (fgets(line, sizeof(line), f)) {

        if (strncmp(line, "Hardware", 8) == 0 ||
            strncmp(line, "model name", 10) == 0 ||
            strncmp(line, "Features", 8) == 0) {

            line[strcspn(line, "\n")] = 0;
            printf("CPU_%s", line);
            putchar('\n');
        }
    }

    fclose(f);
}

int main(void) {

#if !defined(__aarch64__)
    fprintf(stderr,
            "ERROR: this benchmark requires AArch64.\n");
    return 2;
#endif

    printf("============================================================\n");
    printf("SIMD SWEEP v3 — AArch64 NEON FMA\n");
    printf("============================================================\n");

    printf("ARCH=%s\n", "aarch64");

#ifdef __GNUC__
    printf("GCC=%d.%d.%d\n",
           __GNUC__,
           __GNUC_MINOR__,
           __GNUC_PATCHLEVEL__);
#endif

#ifdef __ARM_FEATURE_FMA
    printf("ARM_FMA=1\n");
#else
    printf("ARM_FMA=0\n");
#endif

#ifdef __ARM_NEON
    printf("ARM_NEON=1\n");
#else
    printf("ARM_NEON=0\n");
#endif

    print_cpu_info();

    const int warmups = 2;
    const int repeats = 7;

    printf("\n");
    printf("warmups=%d repeats=%d\n", warmups, repeats);
    printf("\n");

    printf("N,scalar_median_s,neon_median_s,"
           "scalar_GFLOPS,neon_GFLOPS,speedup,"
           "max_abs_error,rmse,checksum\n");

    for (int n = 128; n <= 1024; n += 128) {

        size_t elems = (size_t)n * (size_t)n;
        size_t bytes = elems * sizeof(float);

        float *a   = NULL;
        float *b   = NULL;
        float *ref = NULL;
        float *out = NULL;

        if (posix_memalign((void **)&a, 64, bytes) != 0 ||
            posix_memalign((void **)&b, 64, bytes) != 0 ||
            posix_memalign((void **)&ref, 64, bytes) != 0 ||
            posix_memalign((void **)&out, 64, bytes) != 0) {

            fprintf(stderr,
                    "ERROR: allocation failed at N=%d\n",
                    n);

            free(a);
            free(b);
            free(ref);
            free(out);

            return 3;
        }

        fill_matrix(a, elems);
        fill_matrix(b, elems);

        zero_matrix(ref, elems);
        zero_matrix(out, elems);

        /*
         * Reference result.
         *
         * We calculate this once because correctness verification
         * is separate from timed execution.
         */
        printf("VERIFYING N=%d ... ", n);
        fflush(stdout);

        gemm_scalar(n, a, b, ref);
        gemm_neon_4x4(n, a, b, out);

        double max_abs;
        double rmse;

        compare_results(
            ref,
            out,
            elems,
            &max_abs,
            &rmse);

        /*
         * FP32 accumulation order differs slightly between
         * implementations, so use a numerical tolerance rather
         * than requiring bit-for-bit equality.
         */
        int pass =
            (max_abs <= 1e-3) &&
            (rmse <= 1e-4);

        printf("%s max_abs=%.9g rmse=%.9g\n",
               pass ? "PASS" : "FAIL",
               max_abs,
               rmse);

        if (!pass) {

            fprintf(stderr,
                    "ERROR: NEON correctness gate failed at N=%d\n",
                    n);

            free(a);
            free(b);
            free(ref);
            free(out);

            return 4;
        }

        /*
         * Warmup.
         */
        for (int r = 0; r < warmups; ++r) {

            gemm_scalar(n, a, b, out);
            gemm_neon_4x4(n, a, b, out);
        }

        double scalar_times[repeats];
        double neon_times[repeats];

        /*
         * Scalar benchmark.
         */
        for (int r = 0; r < repeats; ++r) {

            double t0 = now_sec();

            gemm_scalar(n, a, b, out);

            double t1 = now_sec();

            scalar_times[r] = t1 - t0;
        }

        /*
         * NEON benchmark.
         */
        for (int r = 0; r < repeats; ++r) {

            double t0 = now_sec();

            gemm_neon_4x4(n, a, b, out);

            double t1 = now_sec();

            neon_times[r] = t1 - t0;
        }

        double scalar_med = median(scalar_times, repeats);
        double neon_med   = median(neon_times, repeats);

        double operations =
            2.0 *
            (double)n *
            (double)n *
            (double)n;

        double scalar_gflops =
            operations /
            scalar_med /
            1e9;

        double neon_gflops =
            operations /
            neon_med /
            1e9;

        double speedup =
            scalar_med /
            neon_med;

        double cs = checksum(out, elems);

        printf("%d,%.9f,%.9f,"
               "%.6f,%.6f,%.6fx,"
               "%.9g,%.9g,%.9e\n",
               n,
               scalar_med,
               neon_med,
               scalar_gflops,
               neon_gflops,
               speedup,
               max_abs,
               rmse,
               cs);

        fflush(stdout);

        free(a);
        free(b);
        free(ref);
        free(out);
    }

    printf("\n============================================================\n");
    printf("SIMD SWEEP COMPLETE\n");
    printf("Correctness gate: PASS\n");
    printf("Kernel: 4x4 NEON FMA\n");
    printf("Precision: FP32\n");
    printf("Layout: row-major\n");
    printf("============================================================\n");

    return 0;
}
