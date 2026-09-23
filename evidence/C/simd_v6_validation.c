#define _GNU_SOURCE

#include <arm_neon.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <errno.h>

#ifndef MC
#define MC 128
#endif

#ifndef NC
#define NC 128
#endif

#ifndef KC
#define KC 128
#endif

#define REPEATS 5
#define WARMUPS 2
#define ALIGNMENT 64

static double now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

static void *aligned_malloc(size_t alignment, size_t size)
{
    void *p = NULL;

    if (posix_memalign(&p, alignment, size) != 0)
        return NULL;

    return p;
}

static void fill_matrix(float *x, int n, uint32_t seed)
{
    uint32_t s = seed;
    size_t nn = (size_t)n * n;

    for (size_t i = 0; i < nn; ++i) {
        s = 1664525u * s + 1013904223u;
        x[i] = ((float)(s & 0xffffu) / 32768.0f) - 1.0f;
    }
}

/*
 * Independent scalar FP32 reference.
 */
static void scalar_gemm(
    const float *A,
    const float *B,
    float *C,
    int n)
{
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {

            float sum = 0.0f;

            for (int k = 0; k < n; ++k)
                sum += A[(size_t)i*n + k] *
                       B[(size_t)k*n + j];

            C[(size_t)i*n + j] = sum;
        }
    }
}

/*
 * 8x8 packed NEON/FMA kernel.
 *
 * PA[k*8+i]
 * PB[k*8+j]
 *
 * Eight rows x eight columns.
 */
static inline void kernel_8x8(
    const float *PA,
    const float *PB,
    float *C,
    int ldc,
    int K)
{
    float32x4_t c00=vdupq_n_f32(0), c01=vdupq_n_f32(0);
    float32x4_t c10=vdupq_n_f32(0), c11=vdupq_n_f32(0);
    float32x4_t c20=vdupq_n_f32(0), c21=vdupq_n_f32(0);
    float32x4_t c30=vdupq_n_f32(0), c31=vdupq_n_f32(0);
    float32x4_t c40=vdupq_n_f32(0), c41=vdupq_n_f32(0);
    float32x4_t c50=vdupq_n_f32(0), c51=vdupq_n_f32(0);
    float32x4_t c60=vdupq_n_f32(0), c61=vdupq_n_f32(0);
    float32x4_t c70=vdupq_n_f32(0), c71=vdupq_n_f32(0);

    for (int k=0; k<K; ++k) {

        float32x4_t b0=vld1q_f32(PB+k*8);
        float32x4_t b1=vld1q_f32(PB+k*8+4);

        float32x4_t a0=vdupq_n_f32(PA[k*8+0]);
        float32x4_t a1=vdupq_n_f32(PA[k*8+1]);
        float32x4_t a2=vdupq_n_f32(PA[k*8+2]);
        float32x4_t a3=vdupq_n_f32(PA[k*8+3]);
        float32x4_t a4=vdupq_n_f32(PA[k*8+4]);
        float32x4_t a5=vdupq_n_f32(PA[k*8+5]);
        float32x4_t a6=vdupq_n_f32(PA[k*8+6]);
        float32x4_t a7=vdupq_n_f32(PA[k*8+7]);

        c00=vfmaq_f32(c00,a0,b0);
        c01=vfmaq_f32(c01,a0,b1);

        c10=vfmaq_f32(c10,a1,b0);
        c11=vfmaq_f32(c11,a1,b1);

        c20=vfmaq_f32(c20,a2,b0);
        c21=vfmaq_f32(c21,a2,b1);

        c30=vfmaq_f32(c30,a3,b0);
        c31=vfmaq_f32(c31,a3,b1);

        c40=vfmaq_f32(c40,a4,b0);
        c41=vfmaq_f32(c41,a4,b1);

        c50=vfmaq_f32(c50,a5,b0);
        c51=vfmaq_f32(c51,a5,b1);

        c60=vfmaq_f32(c60,a6,b0);
        c61=vfmaq_f32(c61,a6,b1);

        c70=vfmaq_f32(c70,a7,b0);
        c71=vfmaq_f32(c71,a7,b1);
    }

    vst1q_f32(C+0*ldc+0,c00);
    vst1q_f32(C+0*ldc+4,c01);

    vst1q_f32(C+1*ldc+0,c10);
    vst1q_f32(C+1*ldc+4,c11);

    vst1q_f32(C+2*ldc+0,c20);
    vst1q_f32(C+2*ldc+4,c21);

    vst1q_f32(C+3*ldc+0,c30);
    vst1q_f32(C+3*ldc+4,c31);

    vst1q_f32(C+4*ldc+0,c40);
    vst1q_f32(C+4*ldc+4,c41);

    vst1q_f32(C+5*ldc+0,c50);
    vst1q_f32(C+5*ldc+4,c51);

    vst1q_f32(C+6*ldc+0,c60);
    vst1q_f32(C+6*ldc+4,c61);

    vst1q_f32(C+7*ldc+0,c70);
    vst1q_f32(C+7*ldc+4,c71);
}

static void pack_A(
    const float *A,
    float *PA,
    int n,
    int row0,
    int k0,
    int mr,
    int K)
{
    for (int k=0;k<K;k++) {
        for (int i=0;i<8;i++) {
            PA[k*8+i] =
                (i<mr)
                ? A[(size_t)(row0+i)*n+(k0+k)]
                : 0.0f;
        }
    }
}

static void pack_B(
    const float *B,
    float *PB,
    int n,
    int k0,
    int col0,
    int nr,
    int K)
{
    for (int k=0;k<K;k++) {
        for (int j=0;j<8;j++) {
            PB[k*8+j] =
                (j<nr)
                ? B[(size_t)(k0+k)*n+(col0+j)]
                : 0.0f;
        }
    }
}

/*
 * Correct blocked packed GEMM.
 *
 * IMPORTANT:
 * C is accumulated across K blocks.
 * The previous v5 implementation effectively exposed
 * a packing/accumulation correctness defect at larger N.
 */
static void packed_gemm(
    const float *A,
    const float *B,
    float *C,
    int n,
    double *packA_time,
    double *packB_time,
    double *kernel_time)
{
    size_t nn=(size_t)n*n;
    memset(C,0,nn*sizeof(float));

    float *PA=aligned_malloc(
        ALIGNMENT,
        (size_t)KC*8*sizeof(float));

    float *PB=aligned_malloc(
        ALIGNMENT,
        (size_t)KC*8*sizeof(float));

    if (!PA || !PB) {
        fprintf(stderr,"allocation failure\n");
        free(PA);
        free(PB);
        exit(2);
    }

    double ta=0.0;
    double tb=0.0;
    double tk=0.0;

    for (int i0=0;i0<n;i0+=MC) {

        int imax=(i0+MC<n)?i0+MC:n;

        for (int j0=0;j0<n;j0+=NC) {

            int jmax=(j0+NC<n)?j0+NC:n;

            for (int k0=0;k0<n;k0+=KC) {

                int kmax=(k0+KC<n)?k0+KC:n;

                for (int i=i0;i<imax;i+=8) {

                    int mr=(i+8<=imax)?8:(imax-i);

                    double p0=now_sec();

                    pack_A(
                        A,PA,n,i,k0,mr,kmax-k0);

                    ta+=now_sec()-p0;

                    for (int j=j0;j<jmax;j+=8) {

                        int nr=(j+8<=jmax)?8:(jmax-j);

                        double p1=now_sec();

                        pack_B(
                            B,PB,n,k0,j,nr,kmax-k0);

                        tb+=now_sec()-p1;

                        /*
                         * Full 8x8 kernel only on complete tiles.
                         * Boundary tiles use scalar fallback below.
                         */
                        if (mr==8 && nr==8) {

                            double q=now_sec();

                            /*
                             * Accumulate into a temporary tile so
                             * K-block accumulation is mathematically
                             * explicit and independent of C layout.
                             */
                            float T[64];

                            for (int z=0;z<64;z++)
                                T[z]=0.0f;

                            kernel_8x8(
                                PA,PB,T,8,kmax-k0);

                            for (int r=0;r<8;r++)
                                for (int c=0;c<8;c++)
                                    C[(size_t)(i+r)*n+(j+c)]
                                        += T[r*8+c];

                            tk+=now_sec()-q;

                        } else {

                            double q=now_sec();

                            for (int r=0;r<mr;r++) {
                                for (int c=0;c<nr;c++) {

                                    float sum=0.0f;

                                    for (int k=k0;k<kmax;k++)
                                        sum +=
                                            A[(size_t)(i+r)*n+k] *
                                            B[(size_t)k*n+(j+c)];

                                    C[(size_t)(i+r)*n+(j+c)]
                                        +=sum;
                                }
                            }

                            tk+=now_sec()-q;
                        }
                    }
                }
            }
        }
    }

    free(PA);
    free(PB);

    *packA_time=ta;
    *packB_time=tb;
    *kernel_time=tk;
}

/*
 * Validation statistics.
 */
static void validate(
    const float *ref,
    const float *got,
    int n,
    double *max_abs,
    double *rmse,
    double *max_rel,
    uint64_t *checksum)
{
    size_t nn=(size_t)n*n;

    double sumsq=0.0;
    double ma=0.0;
    double mr=0.0;

    uint64_t h=1469598103934665603ULL;

    for (size_t i=0;i<nn;i++) {

        double a=(double)ref[i];
        double b=(double)got[i];

        double d=fabs(a-b);
        double rel=d/(fabs(a)+1e-12);

        if (d>ma) ma=d;
        if (rel>mr) mr=rel;

        sumsq+=d*d;

        uint32_t bits;
        memcpy(&bits,&got[i],sizeof(bits));

        h^=bits;
        h*=1099511628211ULL;
    }

    *max_abs=ma;
    *rmse=sqrt(sumsq/(double)nn);
    *max_rel=mr;
    *checksum=h;
}

static void compiler_info(void)
{
#ifdef __clang__
    printf("COMPILER=Clang %s\n",__clang_version__);
#elif defined(__GNUC__)
    printf("COMPILER=GCC %s\n",__VERSION__);
#else
    printf("COMPILER=unknown\n");
#endif

#if defined(__aarch64__)
    printf("ARCH=aarch64\n");
#else
    printf("ARCH=unknown\n");
#endif

#if defined(__ARM_NEON) || defined(__ARM_NEON__)
    printf("NEON=1\n");
#else
    printf("NEON=0\n");
#endif

#if defined(__ARM_FEATURE_FMA)
    printf("FMA=1\n");
#else
    printf("FMA=0\n");
#endif
}

int main(void)
{
    printf("============================================================\n");
    printf("SIMD v6 PACKED/BLOCKED CORRECTNESS-FIRST VALIDATION\n");
    printf("============================================================\n");

    compiler_info();

    printf("MC=%d NC=%d KC=%d MICROKERNEL=8x8\n",
           MC,NC,KC);

    printf("WARMUPS=%d REPEATS=%d\n",
           WARMUPS,REPEATS);

    printf("RESULT_HEADER,kernel,N,ref_s,packA_s,packB_s,"
           "kernel_s,end2end_s,GFLOPS,kernel_speedup,"
           "end2end_speedup,max_abs,rmse,max_rel,checksum,status\n");

    int sizes[]={
        128,256,384,512,
        640,768,896,1024
    };

    int count=(int)(sizeof(sizes)/sizeof(sizes[0]));

    for (int si=0;si<count;si++) {

        int n=sizes[si];

        size_t nn=(size_t)n*n;
        size_t bytes=nn*sizeof(float);

        float *A=aligned_malloc(ALIGNMENT,bytes);
        float *B=aligned_malloc(ALIGNMENT,bytes);
        float *R=aligned_malloc(ALIGNMENT,bytes);
        float *C=aligned_malloc(ALIGNMENT,bytes);

        if (!A || !B || !R || !C) {
            fprintf(stderr,"allocation failure N=%d\n",n);
            return 2;
        }

        fill_matrix(A,n,0x12345678u);
        fill_matrix(B,n,0x9abcdef0u);

        double t0=now_sec();

        scalar_gemm(A,B,R,n);

        double ref_s=now_sec()-t0;

        /*
         * Warmups.
         */
        for (int w=0;w<WARMUPS;w++) {

            double pa,pb,pk;

            packed_gemm(
                A,B,C,n,
                &pa,&pb,&pk);
        }

        double best_end=1e100;
        double best_pa=0.0;
        double best_pb=0.0;
        double best_pk=0.0;

        for (int r=0;r<REPEATS;r++) {

            double pa,pb,pk;

            double q=now_sec();

            packed_gemm(
                A,B,C,n,
                &pa,&pb,&pk);

            double end=now_sec()-q;

            if (end<best_end) {
                best_end=end;
                best_pa=pa;
                best_pb=pb;
                best_pk=pk;
            }
        }

        double ma,rmse,mr;
        uint64_t checksum;

        validate(
            R,C,n,
            &ma,&rmse,&mr,
            &checksum);

        /*
         * Numerical gate.
         *
         * FP32 FMA is not bit-identical to the scalar
         * accumulation order, therefore use a conservative
         * tolerance rather than exact equality.
         */
        int numerical_pass =
            isfinite(ma) &&
            isfinite(rmse) &&
            ma <= 1e-3 &&
            rmse <= 1e-4 &&
            mr <= 1e-3;

        double flops=2.0*(double)n*n*n;

        double gflops=
            flops/(best_end*1e9);

        double kernel_speedup=
            ref_s/best_pk;

        double end_speedup=
            ref_s/best_end;

        printf(
            "RESULT,PACKED_NEON_8x8,%d,"
            "%.9f,%.9f,%.9f,%.9f,%.9f,"
            "%.6f,%.6fx,%.6fx,"
            "%.9g,%.9g,%.9g,%llu,%s\n",

            n,
            ref_s,
            best_pa,
            best_pb,
            best_pk,
            best_end,
            gflops,
            kernel_speedup,
            end_speedup,
            ma,
            rmse,
            mr,
            (unsigned long long)checksum,
            numerical_pass ? "PASS":"FAIL");

        free(A);
        free(B);
        free(R);
        free(C);
    }

    printf("============================================================\n");
    printf("V6 VALIDATION CONTRACT\n");
    printf("============================================================\n");
    printf("1. Independent scalar FP32 reference\n");
    printf("2. Deterministic inputs\n");
    printf("3. Packed A/B representation\n");
    printf("4. Explicit K-block accumulation\n");
    printf("5. AArch64 NEON/FMA 8x8 kernel\n");
    printf("6. Boundary-safe fallback\n");
    printf("7. Absolute/relative/RMSE error gate\n");
    printf("8. Kernel and end-to-end timing\n");
    printf("9. Deterministic checksum\n");
    printf("10. Compiler/architecture provenance\n");
    printf("============================================================\n");

    return 0;
}
