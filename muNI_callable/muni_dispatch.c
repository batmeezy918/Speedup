#include "muni_runtime.h"
#include <string.h>
void gemm_scalar(int n, const float *a, const float *b, float *c);
void gemm_blocked(int n, const float *a, const float *b, float *c);
const char *muni_backend(void){ return "aarch64-neon-fma-register-block"; }
const char *muni_version(void){ return "MuNi-callable-0.1"; }
void muni_baseline(int n,const float*a,const float*b,float*c){ gemm_scalar(n,a,b,c); }
void muni_neon(int n,const float*a,const float*b,float*c){ gemm_blocked(n,a,b,c); }
