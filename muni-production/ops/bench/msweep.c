/* msweep.c -- the operational consequence of the theorem, isolated.
 *
 * The Lean theorem says: for U = Ubar (x) I_m on the block-constant sector,
 * the full path applies an r x r operator to EACH of m fibers, while the
 * quotient applies it ONCE per block. That predicts
 *
 *      work_full  ~ r * (r*m)  = r^2 * m
 *      work_quot  ~ 1 * (r*r)  = r^2
 *      speedup    ~ m
 *
 * This sweep holds r fixed and varies m to test that prediction directly.
 */
#define _POSIX_C_SOURCE 199309L
#include "kernel_agl.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
static double now_ms(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
  return t.tv_sec*1e3+1e-6*t.tv_nsec;}
static int cmp_d(const void*a,const void*b){double x=*(const double*)a,y=*(const double*)b;
  return x<y?-1:(x>y?1:0);}
int main(void){
  const size_t r=64, steps=256, trials=9, reps=3;
  printf("# fiber-replication sweep: r fixed = %zu, steps = %zu\n", r, steps);
  printf("# predicted speedup ~ m (the replication factor)\n");
  printf("%5s %8s %11s %11s %9s %9s %8s %7s\n",
         "m","d=r*m","base_ms","quot_ms","speedup","m_pred","ratio/m","exact");
  size_t ms[]={1,2,4,8,16,32,64,128,256};
  for(size_t c=0;c<sizeof ms/sizeof ms[0];c++){
    size_t m=ms[c], d=r*m;
    double *U=aligned_alloc(64,r*r*sizeof(double));
    double *x=aligned_alloc(64,d*sizeof(double));
    double *a=malloc(d*sizeof(double)), *b=malloc(d*sizeof(double));
    for(size_t i=0;i<r*r;i++) U[i]=0.02*(double)((i*2654435761u)%97+1)/97.0;
    for(size_t i=0;i<r;i++) U[i*r+i]+=0.5;
    for(size_t k=0;k<r;k++) for(size_t j=0;j<m;j++) x[k*m+j]=0.25+0.01*(double)k;
    AGDCertificate cert=agd_certificate_self();
    double *bt=calloc(trials,sizeof(double)),*qt=calloc(trials,sizeof(double));
    for(int w=0;w<3;w++){
      memcpy(a,x,d*sizeof(double));
      for(size_t k=0;k<steps;k++){agd_original_apply(a,b,U,d,m,r);double*t=a;a=b;b=t;}
      AGDPlan*p=agd_plan_create(x,d,m,U,0.0,&cert); agd_plan_run(p,steps);
      double*o=malloc(d*sizeof(double)); agd_plan_reconstruct(p,o);
      agd_plan_destroy(p); free(o);
    }
    for(size_t t=0;t<trials;t++){
      double tb=0,tq=0;
      for(size_t rep=0;rep<reps;rep++){
        double s0=now_ms();
        memcpy(a,x,d*sizeof(double));
        for(size_t k=0;k<steps;k++){agd_original_apply(a,b,U,d,m,r);double*tt=a;a=b;b=tt;}
        tb+=now_ms()-s0;
        double s1=now_ms();
        AGDPlan*p=agd_plan_create(x,d,m,U,0.0,&cert); agd_plan_run(p,steps);
        double*o=malloc(d*sizeof(double)); agd_plan_reconstruct(p,o);
        tq+=now_ms()-s1;
        agd_plan_destroy(p); free(o);
      }
      bt[t]=tb/reps; qt[t]=tq/reps;
    }
    qsort(bt,trials,sizeof(double),cmp_d); qsort(qt,trials,sizeof(double),cmp_d);
    double bm=bt[trials/2], qm=qt[trials/2], sp=bm/qm;
    double err=0;
    { AGDPlan*p=agd_plan_create(x,d,m,U,0.0,&cert);
      memcpy(a,x,d*sizeof(double));
      for(size_t k=0;k<steps;k++){agd_original_apply(a,b,U,d,m,r);double*tt=a;a=b;b=tt;}
      memcpy(b,a,d*sizeof(double));
      double*f=malloc(d*sizeof(double)); agd_plan_run(p,steps);
      agd_plan_reconstruct(p,f); err=agd_max_abs_error(b,f,d);
      free(f); agd_plan_destroy(p); }
    printf("%5zu %8zu %11.5f %11.5f %8.2fx %8zu %7.3f %9s\n",
      m,d,bm,qm,sp,m,sp/(double)m, err==0.0?"EXACT":"ERR");
    fflush(stdout);
    free(bt);free(qt);free(U);free(x);free(a);free(b);
  }
  return 0;
}
