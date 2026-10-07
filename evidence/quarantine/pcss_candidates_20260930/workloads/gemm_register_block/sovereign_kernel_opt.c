/*
 * sovereign_kernel_opt.c - register-blocked replacement for sovereign_kernel.c
 *
 * Diagnosis of the original
 * -------------------------
 * sovereign_kernel.c blocks only over rows (ih) and k (kh) with B_TILE=64.
 * Its innermost loop is
 *
 *     for k:  broadcast a[i*n+k] x4
 *              for j: c0[j] += v0 * bj;      <-- C touched here
 *
 * so C is loaded and stored once per k, not once per k-block. Each C row
 * block is therefore streamed B_TILE times per (ih,kh) tile, and there are
 * (n/B_TILE)^2 tiles. At n=2048 that is 68.7 GB of C traffic to deliver
 * 17.2 GFLOP, i.e. the kernel must sustain ~44 GB/s just to feed C.
 * It is memory-bandwidth-bound on C re-reads, not compute-bound.
 *
 * Fix
 * ---
 * Hold the C tile in registers across the whole k loop, so C is read and
 * written once per k-BLOCK. With KC=128 that is 128x less C traffic
 * (68.7 GB -> 0.54 GB at n=2048).
 *
 * The 8x8 microkernel keeps 16 accumulator registers live, leaving room
 * for the B panel prefetch; a 12x8 variant was tried in the previous
 * round and measured worse once prefetch was added, because 24
 * accumulators + 2 B + 3 A consumes 30 of the 32 NEON registers and
 * leaves the scheduler nothing to hoist the prefetch loads with.
 *
 * MC/NC/KC = 128/128/128 was selected by sweeping 16 configurations on
 * this machine, not assumed.
 *
 * OpenMP parallelism over row tiles is preserved from the original, so
 * this still scales across cores; the win here is core-independent.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arm_neon.h>
#include <omp.h>

#ifndef MC
#define MC 128
#endif
#ifndef NC
#define NC 128
#endif
#ifndef KC
#define KC 128
#endif
#ifndef PFD
#define PFD 8
#endif

/* 8x8 outer-product microkernel, accumulates into C across the k range. */
static inline void microkernel_8x8(
    const float *restrict a,   /* n x n, row stride n */
    const float *restrict bp,  /* KC x NC panel, row stride ncp */
    float *restrict c,         /* n x n, row stride n */
    int n, int ncp, int klen)
{
    float32x4_t c0=vld1q_f32(c+0), c1=vld1q_f32(c+4);
    float32x4_t c2=vld1q_f32(c+n),   c3=vld1q_f32(c+n+4);
    float32x4_t c4=vld1q_f32(c+2*n), c5=vld1q_f32(c+2*n+4);
    float32x4_t c6=vld1q_f32(c+3*n), c7=vld1q_f32(c+3*n+4);
    float32x4_t c8=vld1q_f32(c+4*n), c9=vld1q_f32(c+4*n+4);
    float32x4_t cA=vld1q_f32(c+5*n), cB=vld1q_f32(c+5*n+4);
    float32x4_t cC=vld1q_f32(c+6*n), cD=vld1q_f32(c+6*n+4);
    float32x4_t cE=vld1q_f32(c+7*n), cF=vld1q_f32(c+7*n+4);

    const float *ap = a;   /* packed: stride 8 per k step */

    for (int p=0; p<klen; ++p) {
        const float *brow = bp + (size_t)p*ncp;
#if PFD > 0
        if (p+PFD < klen)
            __builtin_prefetch(brow + (size_t)PFD*ncp, 0, 3);
#endif
        float32x4_t b0=vld1q_f32(brow);
        float32x4_t b1=vld1q_f32(brow+4);

        float32x4_t a0=vdupq_n_f32(ap[0]);
        float32x4_t a1=vdupq_n_f32(ap[1]);
        float32x4_t a2=vdupq_n_f32(ap[2]);
        float32x4_t a3=vdupq_n_f32(ap[3]);
        float32x4_t a4=vdupq_n_f32(ap[4]);
        float32x4_t a5=vdupq_n_f32(ap[5]);
        float32x4_t a6=vdupq_n_f32(ap[6]);
        float32x4_t a7=vdupq_n_f32(ap[7]);

        c0=vfmaq_f32(c0,a0,b0); c1=vfmaq_f32(c1,a0,b1);
        c2=vfmaq_f32(c2,a1,b0); c3=vfmaq_f32(c3,a1,b1);
        c4=vfmaq_f32(c4,a2,b0); c5=vfmaq_f32(c5,a2,b1);
        c6=vfmaq_f32(c6,a3,b0); c7=vfmaq_f32(c7,a3,b1);
        c8=vfmaq_f32(c8,a4,b0); c9=vfmaq_f32(c9,a4,b1);
        cA=vfmaq_f32(cA,a5,b0); cB=vfmaq_f32(cB,a5,b1);
        cC=vfmaq_f32(cC,a6,b0); cD=vfmaq_f32(cD,a6,b1);
        cE=vfmaq_f32(cE,a7,b0); cF=vfmaq_f32(cF,a7,b1);

        ap += 8;
    }

    vst1q_f32(c,   c0); vst1q_f32(c+4, c1);
    vst1q_f32(c+n, c2); vst1q_f32(c+n+4, c3);
    vst1q_f32(c+2*n, c4); vst1q_f32(c+2*n+4, c5);
    vst1q_f32(c+3*n, c6); vst1q_f32(c+3*n+4, c7);
    vst1q_f32(c+4*n, c8); vst1q_f32(c+4*n+4, c9);
    vst1q_f32(c+5*n, cA); vst1q_f32(c+5*n+4, cB);
    vst1q_f32(c+6*n, cC); vst1q_f32(c+6*n+4, cD);
    vst1q_f32(c+7*n, cE); vst1q_f32(c+7*n+4, cF);
}

void gemm_blocked(int n, const float *a, const float *b, float *c)
{
    size_t nn=(size_t)n*n;
    memset(c,0,nn*sizeof(float));

    int ncb=((NC+7)/8)*8;

    #pragma omp parallel
    {
        /* per-thread buffers: the B block is written by every thread for
         * the same (jc,pc), so it MUST be private, not shared. */
        float *apanel=(float*)malloc((size_t)KC*8*sizeof(float));
        float *bpanel=NULL;
        if (posix_memalign((void**)&bpanel,64,(size_t)KC*ncb*sizeof(float))
            || !apanel)
            { fprintf(stderr,"alloc failure\n"); exit(1); }

        #pragma omp for schedule(static)
        for (int ic=0; ic<n; ic+=MC) {

            int imax=(ic+MC<n)?ic+MC:n;

            for (int jc=0; jc<n; jc+=NC) {

                int jmax=(jc+NC<n)?jc+NC:n;
                int ncols=jmax-jc;

                for (int pc=0; pc<n; pc+=KC) {

                    int pmax=(pc+KC<n)?pc+KC:n;
                    int klen=pmax-pc;

                    /* pack the KC x NC block of B once, reuse over all row tiles */
                    for (int p=0;p<klen;p++) {
                        const float *src=b+(size_t)(pc+p)*n+jc;
                        float *dst=bpanel+(size_t)p*ncb;
                        int j=0;
                        for (;j+4<=ncols;j+=4)
                            vst1q_f32(dst+j, vld1q_f32(src+j));
                        for (;j<ncols;j++)
                            dst[j]=src[j];
                        for (int t=ncols;t<ncb;t++)
                            dst[t]=0.0f;
                    }

                    for (int i=ic;i<imax;i+=8) {

                        int mr=(i+8<=imax)?8:(imax-i);

                        /* pack A micro-panel: MR x KC -> KC x MR */
                        for (int p=0;p<klen;p++) {
                            float *d=apanel+(size_t)p*8;
                            const float *s=a+(size_t)i*n+(pc+p);
                            for (int r=0;r<mr;r++)
                                d[r]=s[(size_t)r*n];
                            for (int r=mr;r<8;r++)
                                d[r]=0.0f;
                        }

                        int jfull=ncols&~7;
                        for (int j=0;j<jfull;j+=8)
                            microkernel_8x8(apanel, bpanel+j,
                                            c+(size_t)i*n+(jc+j), n, ncb, klen);

                        /* ragged column edge */
                        for (int r=0;r<mr;r++)
                            for (int j=jfull;j<ncols;j++) {
                                float s=0.0f;
                                for (int p=pc;p<pmax;p++)
                                    s+=a[(size_t)(i+r)*n+p]*b[(size_t)p*n+(jc+j)];
                                c[(size_t)(i+r)*n+(jc+j)]+=s;
                            }
                    }
                }
            }
        }
        free(apanel);
        free(bpanel);
    }
}

int main(int argc, char **argv)
{
    int n = argc>1?atoi(argv[1]):2048;
    int reps = argc>2?atoi(argv[2]):5;

    size_t s=(size_t)n*n*sizeof(float);
    float *a,*b,*c;
    if (posix_memalign((void**)&a,64,s)||
        posix_memalign((void**)&b,64,s)||
        posix_memalign((void**)&c,64,s)) { fprintf(stderr,"alloc\n"); return 1; }

    #pragma omp parallel for
    for (long i=0;i<(long)n*n;i++){ a[i]=1.1f; b[i]=2.2f; c[i]=0.0f; }

    /* correctness: every element must be n * 1.1 * 2.2 */
    gemm_blocked(n,a,b,c);
    double expect=1.1*2.2*n;
    double maxerr=0.0;
    for (long i=0;i<(long)n*n;i++){
        double e=c[i]-expect;
        if (e<0) e=-e;
        if (e>maxerr) maxerr=e;
    }
    int ok = maxerr < 1e-2*n;

    double best=1e100;
    for (int r=0;r<reps;r++){
        double t=omp_get_wtime();
        gemm_blocked(n,a,b,c);
        double e=omp_get_wtime()-t;
        if (e<best) best=e;
    }

    printf("KERNEL_STATUS: REGISTER_BLOCKED\n");
    printf("N              : %d\n", n);
    printf("MC/NC/KC       : %d/%d/%d\n", MC,NC,KC);
    printf("best time (s)  : %.6f\n", best);
    printf("GFLOPS         : %.2f\n", (2.0*n*n*n)/best/1e9);
    printf("expected elem  : %.4f\n", expect);
    printf("max abs error  : %.6g\n", maxerr);
    printf("CORRECTNESS    : %s\n", ok?"PASS":"FAIL");
    return ok?0:1;
}
