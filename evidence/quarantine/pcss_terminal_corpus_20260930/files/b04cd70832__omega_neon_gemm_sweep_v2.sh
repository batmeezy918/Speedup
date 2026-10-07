#!/usr/bin/env bash
set -euo pipefail

RUN_ID="omega_neon_gemm_sweep_v2_$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="$HOME/$RUN_ID"
mkdir -p "$ROOT"
SRC="$ROOT/sweep.c"
BIN="$ROOT/sweep"
LOG="$ROOT/sweep.log"
CSV="$ROOT/results.csv"

cat > "$SRC" <<'C'
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <arm_neon.h>

static double now() {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

void gemm_4x4(int n, const float *a, const float *b, float *c) {
    for (int i = 0; i < n; i += 4) {
        for (int j = 0; j < n; j += 4) {
            float32x4_t c0 = vld1q_f32(&c[(i+0)*n + j]);
            float32x4_t c1 = vld1q_f32(&c[(i+1)*n + j]);
            float32x4_t c2 = vld1q_f32(&c[(i+2)*n + j]);
            float32x4_t c3 = vld1q_f32(&c[(i+3)*n + j]);
            for (int k = 0; k < n; k++) {
                float32x4_t bvec = vld1q_f32(&b[k*n + j]);
                c0 = vfmaq_n_f32(c0, bvec, a[(i+0)*n + k]);
                c1 = vfmaq_n_f32(c1, bvec, a[(i+1)*n + k]);
                c2 = vfmaq_n_f32(c2, bvec, a[(i+2)*n + k]);
                c3 = vfmaq_n_f32(c3, bvec, a[(i+3)*n + k]);
            }
            vst1q_f32(&c[(i+0)*n + j], c0);
            vst1q_f32(&c[(i+1)*n + j], c1);
            vst1q_f32(&c[(i+2)*n + j], c2);
            vst1q_f32(&c[(i+3)*n + j], c3);
        }
    }
}

int main() {
    printf("N,GFLOPS\n");
    for (int n = 128; n <= 1024; n += 128) {
        float *a = aligned_alloc(64, n*n*sizeof(float));
        float *b = aligned_alloc(64, n*n*sizeof(float));
        float *c = aligned_alloc(64, n*n*sizeof(float));
        double start = now();
        gemm_4x4(n, a, b, c);
        double end = now();
        double gflops = (2.0 * n * n * n) / (end - start) / 1e9;
        printf("%d,%.6f\n", n, gflops);
        free(a); free(b); free(c);
    }
    return 0;
}
C

cc -O3 -march=armv8-a+simd -ffast-math "$SRC" -o "$BIN"
"$BIN" | tee "$CSV"
