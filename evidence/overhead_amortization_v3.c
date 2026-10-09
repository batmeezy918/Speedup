#define _POSIX_C_SOURCE 200809L
#include "../src/agd_cert.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define MAXT 9
static uint64_t rng=0x243f6a8885a308d3ULL;
static double urand(void){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return (double)(rng>>11)*(1.0/9007199254740992.0);}
static uint64_t ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec;}
static double med(double *a,size_t n){for(size_t i=1;i<n;i++){double v=a[i];size_t j=i;while(j&&a[j-1]>v){a[j]=a[j-1];j--;}a[j]=v;}return a[n/2];}
static void full(const double*x,double*out,double*U,size_t d,size_t m,size_t r,size_t n,double*a,double*b){
 memcpy(a,x,d*sizeof(double));double*cur=a,*next=b;
 for(size_t k=0;k<n;k++){agd_original_apply(cur,next,U,d,m,r);double*z=cur;cur=next;next=z;}
 memcpy(out,cur,d*sizeof(double));
}
int main(void){
 const size_t d=4096,m=64,r=d/m,trials=7,reps=5,warmups=2;
 const size_t depths[]={0,1,2,4,8,16,32,64,128,256,512,1024};
 double *U=malloc(r*r*sizeof(double)),*x=malloc(d*sizeof(double)),*a=malloc(d*sizeof(double)),*b=malloc(d*sizeof(double)),*ref=malloc(d*sizeof(double)),*out=malloc(d*sizeof(double));
 if(!U||!x||!a||!b||!ref||!out)return 2;
 for(size_t i=0;i<r*r;i++)U[i]=(urand()*2-1)/sqrt((double)r);
 for(size_t k=0;k<r;k++){double v=.25+1.75*urand();for(size_t j=0;j<m;j++)x[k*m+j]=v;}
 AGDCertificate cert=agd_certificate_self();
 printf("AMORTIZATION_SWEEP v3; d=%zu m=%zu r=%zu trials=%zu reps=%zu warmups=%zu; create/project, quotient steps, reconstruction, and plan destruction all included in quotient end-to-end\n",d,m,r,trials,reps,warmups);
 puts("steps,baseline_ms,create_project_ms,quotient_steps_ms,reconstruct_ms,destroy_ms,quotient_e2e_ms,speedup,baseline_per_step_us,quotient_step_us,max_abs_error,memcmp_equal,admissible,fallback");
 for(size_t di=0;di<sizeof(depths)/sizeof(depths[0]);di++){
  size_t steps=depths[di];double bt[MAXT],ct[MAXT],qt[MAXT],rt[MAXT],dt[MAXT];double err=INFINITY;int equal=0,adm=0,fb=1;
  for(size_t w=0;w<warmups;w++){
   full(x,ref,U,d,m,r,steps,a,b);
   AGDPlan*p=agd_plan_create(x,d,m,U,0.0,&cert);if(!p)return 3;
   if(!agd_plan_run(p,steps)||!agd_plan_reconstruct(p,out))return 4;
   if(agd_max_abs_error(ref,out,d)!=0.0||memcmp(ref,out,d*sizeof(double))!=0)return 5;
   agd_plan_destroy(p);
  }
  for(size_t ti=0;ti<trials;ti++){
   uint64_t bs=0,cs=0,qs=0,rsum=0,ds=0;
   for(size_t rep=0;rep<reps;rep++){
    uint64_t t0=ns();full(x,ref,U,d,m,r,steps,a,b);uint64_t t1=ns();bs+=t1-t0;
    uint64_t c0=ns();AGDPlan*p=agd_plan_create(x,d,m,U,0.0,&cert);uint64_t c1=ns();
    if(!p)return 6;adm=agd_plan_admissible(p);fb=agd_plan_in_fallback(p);
    uint64_t q0=ns();if(!agd_plan_run(p,steps))return 7;uint64_t q1=ns();
    uint64_t r0=ns();if(!agd_plan_reconstruct(p,out))return 8;uint64_t r1=ns();
    err=agd_max_abs_error(ref,out,d);equal=(memcmp(ref,out,d*sizeof(double))==0);
    uint64_t d0=ns();agd_plan_destroy(p);uint64_t d1=ns();
    cs+=c1-c0;qs+=q1-q0;rsum+=r1-r0;ds+=d1-d0;
   }
   bt[ti]=(double)bs/reps/1e6;ct[ti]=(double)cs/reps/1e6;qt[ti]=(double)qs/reps/1e6;rt[ti]=(double)rsum/reps/1e6;dt[ti]=(double)ds/reps/1e6;
  }
  double bm=med(bt,trials),cm=med(ct,trials),qm=med(qt,trials),rm=med(rt,trials),dm=med(dt,trials),e2e=cm+qm+rm+dm;
  printf("%zu,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.3f,%.3f,%.3f,%.17g,%d,%d,%d\n",steps,bm,cm,qm,rm,dm,e2e,bm/e2e,steps?(bm*1000.0/steps):0.0,steps?(qm*1000.0/steps):0.0,err,equal,adm,fb);
  if(err!=0.0||!equal||!adm||fb)return 9;
 }
 puts("AMORTIZATION_SWEEP_GATE=PASS");
 free(U);free(x);free(a);free(b);free(ref);free(out);return 0;
}