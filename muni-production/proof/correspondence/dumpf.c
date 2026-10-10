/* dumpf.c -- emit IEEE-754 BIT PATTERNS of the C kernel on NON-INTEGER inputs,
 * so Lean's Float model can be compared bit-for-bit rather than approximately. */
#include "kernel_agl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static uint64_t bits(double d){uint64_t u;memcpy(&u,&d,8);return u;}
int main(void){
  const size_t r=3, m=4, d=r*m, steps=3;
  /* deliberately non-integer, non-representable values: rounding is unavoidable
     and any difference between the two systems must therefore show up. */
  double U[9]={ 0.1, 0.3, -0.7,   1.0/3.0, 2.5, 0.2,   -0.9, 0.6, 1.0/7.0 };
  double x0[12]; for(size_t b=0;b<r;b++){ double v=0.1*(double)(b+1)/(double)(b+2);
    for(size_t j=0;j<m;j++) x0[b*m+j]=v; }
  double *a=malloc(d*sizeof(double)),*b=malloc(d*sizeof(double));
  double *fa=malloc(d*sizeof(double));
  memcpy(a,x0,d*sizeof(double));
  printf("U_BITS");
  for(size_t i=0;i<r*r;i++) printf(" %llu",(unsigned long long)bits(U[i]));
  printf("\nX_BITS");
  for(size_t i=0;i<d;i++) printf(" %llu",(unsigned long long)bits(x0[i]));
  printf("\n");
  for(size_t s=0;s<steps;s++){
    agd_original_apply(a,b,U,d,m,r); double*t=a;a=b;b=t;
    printf("FULL%d",(int)(s+1));
    for(size_t i=0;i<d;i++) printf(" %llu",(unsigned long long)bits(a[i]));
    printf("\n");
  }
  AGDCertificate c=agd_certificate_self();
  AGDPlan*p=agd_plan_create(x0,d,m,U,0.0,&c);
  printf("ADMISSIBLE=%d FALLBACK=%d\n",agd_plan_admissible(p),agd_plan_in_fallback(p));
  agd_plan_run(p,steps); agd_plan_reconstruct(p,fa);
  printf("QUOT");
  for(size_t i=0;i<d;i++) printf(" %llu",(unsigned long long)bits(fa[i]));
  printf("\nMAXERR=%llu\n",(unsigned long long)bits(agd_max_abs_error(a,fa,d)));
  return 0;
}
