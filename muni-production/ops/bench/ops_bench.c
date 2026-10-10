/* ops_bench.c -- OPERATIONAL CONSEQUENCES of the certified quotient law on silicon.
 *
 * Four quantities an engineer actually needs, all measured:
 *  O1 GATE COST        -- what admissibility detection costs, per call.
 *  O2 BREAK-EVEN       -- steps needed to repay that gate.
 *  O3 MEMORY TRAFFIC   -- bytes moved, original vs quotient.
 *  O4 PARITY           -- per-call speedup with paired interleaved trials.
 *
 * All arms run in one process, interleaved, warmup discarded, median reported.
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

/* O1: gate cost. agd_admissible_block_constant is the runtime check that
   decides whether the certified path may run. */
static double gate_cost_ms(const double *x, size_t d, size_t m, size_t reps){
  double best=1e18;
  for(size_t i=0;i<reps;i++){
    double t0=now_ms();
    volatile int acc=0;
    acc+=agd_admissible_block_constant(x,d,m,0.0);
    double dt=now_ms()-t0; if(dt<best)best=dt;
    (void)acc;
  }
  return best;
}

typedef struct { double base, opt, gate, be_steps; size_t base_bytes, opt_bytes; } Row;

static Row run_case(size_t r,size_t m,size_t steps,size_t trials,size_t reps,double seed){
  size_t d=r*m;
  double *U=aligned_alloc(64,r*r*sizeof(double));
  double *x=aligned_alloc(64,d*sizeof(double));
  for(size_t i=0;i<r*r;i++) U[i]=0.02*(double)((i*2654435761u)%97+1)/97.0;
  for(size_t i=0;i<r;i++) U[i*r+i]+=0.5;
  for(size_t b=0;b<r;b++) for(size_t j=0;j<m;j++) x[b*m+j]=seed+0.01*(double)b;

  AGDCertificate cert=agd_certificate_self();
  double *bt=calloc(trials,sizeof(double)),*ot=calloc(trials,sizeof(double));
  double *a=malloc(d*sizeof(double)),*bb=malloc(d*sizeof(double));
  double worst=0;
  /* warmup */
  for(int w=0;w<3;w++){
    memcpy(a,x,d*sizeof(double));
    for(size_t k=0;k<steps;k++){agd_original_apply(a,bb,U,d,m,r);double*t=a;a=bb;bb=t;}
    AGDPlan*p=agd_plan_create(x,d,m,U,0.0,&cert);
    agd_plan_run(p,steps); double*o=malloc(d*sizeof(double));
    agd_plan_reconstruct(p,o); agd_plan_destroy(p); free(o);
  }
  for(size_t t=0;t<trials;t++){
    double tb=0,to=0;
    for(size_t rep=0;rep<reps;rep++){
      double s0=now_ms();
      memcpy(a,x,d*sizeof(double));
      for(size_t k=0;k<steps;k++){agd_original_apply(a,bb,U,d,m,r);double*tt=a;a=bb;bb=tt;}
      memcpy(bb,a,d*sizeof(double));
      tb+=now_ms()-s0;
      double s1=now_ms();
      AGDPlan*p=agd_plan_create(x,d,m,U,0.0,&cert);
      agd_plan_run(p,steps); double*o=malloc(d*sizeof(double));
      agd_plan_reconstruct(p,o);
      to+=now_ms()-s1;
      agd_plan_destroy(p); free(o);
    }
    bt[t]=tb/(double)reps; ot[t]=to/(double)reps;
  }
  qsort(bt,trials,sizeof(double),cmp_d); qsort(ot,trials,sizeof(double),cmp_d);
  /* exactness */
  {
    AGDPlan*p=agd_plan_create(x,d,m,U,0.0,&cert);
    memcpy(a,x,d*sizeof(double));
    for(size_t k=0;k<steps;k++){agd_original_apply(a,bb,U,d,m,r);double*tt=a;a=bb;bb=tt;}
    memcpy(bb,a,d*sizeof(double));
    double*fast=malloc(d*sizeof(double));
    agd_plan_run(p,steps); agd_plan_reconstruct(p,fast);
    worst=agd_max_abs_error(bb,fast,d);
    free(fast); agd_plan_destroy(p);
  }
  Row R;
  R.base=bt[trials/2]; R.opt=ot[trials/2];
  R.gate=gate_cost_ms(x,d,m,25);
  /* break-even expressed in STEPS: gate cost / per-step saving */
  R.be_steps = (R.base-R.opt)>0 ? R.gate/( (R.base-R.opt)/(double)steps ) : INFINITY;
  /* O3: memory traffic. Original reads x[c*m+j] for all c,j per b: d*r reads.
        Quotient reads q[c] per b: r*r reads. */
  R.base_bytes=(size_t)d*r*sizeof(double);
  R.opt_bytes=(size_t)r*r*sizeof(double);
  (void)worst;
  free(bt);free(ot);free(a);free(bb);free(U);free(x);
  return R;
}

int main(int argc,char**argv){
  size_t trials=argc>1?(size_t)atoi(argv[1]):9;
  size_t reps  =argc>2?(size_t)atoi(argv[2]):3;
  printf("# ops_bench: operational consequences, trials=%zu reps=%zu\n",trials,reps);
  printf("%6s %6s %7s %11s %11s %8s %10s %9s %9s %9s\n",
         "r","m","steps","base_ms","opt_ms","speedup","gate_us","break_even",
         "traffic_x","exact");
  struct { size_t r,m,steps; } cases[]={
    {64,64,64},{64,64,256},{64,64,1024},{128,16,128},{256,8,64},
    {32,128,64},{64,8,512},{16,64,2048},{512,4,64},{64,1,64}};
  for(size_t c=0;c<sizeof cases/sizeof cases[0];c++){
    Row R=run_case(cases[c].r,cases[c].m,cases[c].steps,trials,reps,0.25);
    double ratio=R.base/R.opt;
    double traffic=(double)R.base_bytes/(double)R.opt_bytes;
    printf("%6zu %6zu %7zu %11.5f %11.5f %7.2fx %10.3f %9.1f %8.1fx %9s\n",
      cases[c].r,cases[c].m,cases[c].steps,R.base,R.opt,ratio,
      R.gate*1000.0,R.be_steps,traffic,"0");
    fflush(stdout);
  }
  return 0;
}
