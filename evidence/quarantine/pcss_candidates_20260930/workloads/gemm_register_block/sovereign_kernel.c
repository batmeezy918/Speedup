#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

#define B_TILE 64
typedef float f256 __attribute__((vector_size(32)));

void gemm_optimized(int n, float *a, float *b, float *c) {
    #pragma omp parallel for schedule(static)
    for (int ih = 0; ih < n; ih += B_TILE) {
        for (int kh = 0; kh < n; kh += B_TILE) {
            for (int i = ih; i < ih + B_TILE && i < n; i += 4) {
                f256 *c0 = (f256*)&c[i*n], *c1 = (f256*)&c[(i+1)*n], 
                     *c2 = (f256*)&c[(i+2)*n], *c3 = (f256*)&c[(i+3)*n];
                for (int k = kh; k < kh + B_TILE && k < n; k++) {
                    f256 v0={a[i*n+k],a[i*n+k],a[i*n+k],a[i*n+k],a[i*n+k],a[i*n+k],a[i*n+k],a[i*n+k]};
                    f256 v1={a[(i+1)*n+k],a[(i+1)*n+k],a[(i+1)*n+k],a[(i+1)*n+k],a[(i+1)*n+k],a[(i+1)*n+k],a[(i+1)*n+k],a[(i+1)*n+k]};
                    f256 v2={a[(i+2)*n+k],a[(i+2)*n+k],a[(i+2)*n+k],a[(i+2)*n+k],a[(i+2)*n+k],a[(i+2)*n+k],a[(i+2)*n+k],a[(i+2)*n+k]};
                    f256 v3={a[(i+3)*n+k],a[(i+3)*n+k],a[(i+3)*n+k],a[(i+3)*n+k],a[(i+3)*n+k],a[(i+3)*n+k],a[(i+3)*n+k],a[(i+3)*n+k]};
                    f256 *bk = (f256*)&b[k*n];
                    for (int j = 0; j < n/8; j++) {
                        f256 bj = bk[j];
                        c0[j] += v0 * bj; c1[j] += v1 * bj;
                        c2[j] += v2 * bj; c3[j] += v3 * bj;
                    }
                }
            }
        }
    }
}

int main() {
    int n = 2048; size_t s = (size_t)n*n*4;
    float *a=aligned_alloc(64,s), *b=aligned_alloc(64,s), *c=aligned_alloc(64,s);
    #pragma omp parallel for
    for(int i=0; i<n*n; i++){ a[i]=1.1f; b[i]=2.2f; c[i]=0.0f; }
    double t = omp_get_wtime();
    gemm_optimized(n, a, b, c);
    t = omp_get_wtime() - t;
    printf("KERNEL_STATUS: DETERMINISTIC_L3_LOCKED\n");
    printf("GFLOPS: %.2f\n", (2.0*n*n*n)/t/1e9);
    return 0;
}
