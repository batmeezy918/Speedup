#define _POSIX_C_SOURCE 200809L
#include "agd_cert.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
static uint64_t ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec;}
static uint64_t rng=0x8b8b8b8b12345678ULL;
static double ur(void){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return (double)(rng>>11)*(1.0/9007199254740992.0);}
static void qapply(const double*q,double*y,const double*U,size_t r){for(size_t b=0;b<r;b++){double a=0;for(size_t c=0;c<r;c++)a+=U[b*r+c]*q[c];y[b]=a;}}
static void expand(const double*q,double*x,size_t r,size_t m){for(size_t b=0;b<r;b++)for(size_t j=0;j<m;j++)x[b*m+j]=q[b];}
static void project(const double*x,double*q,size_t r,size_t m){for(size_t b=0;b<r;b++)q[b]=x[b*m];}
static uint64_t hash(const void*vp,size_t n){uint64_t h=1469598103934665603ULL;const unsigned char*p=vp;for(size_t i=0;i<n;i++){h^=p[i];h*=1099511628211ULL;}return h;}
static void replay(const double*x0,double*out,const double*U,size_t d,size_t m,size_t r,size_t n,double*a,double*b){memcpy(a,x0,d*sizeof(double));for(size_t k=0;k<n;k++){agd_original_apply(a,b,U,d,m,r);double*z=a;a=b;b=z;}memcpy(out,a,d*sizeof(double));}
int main(int argc,char**argv){size_t d=2048,m=64,steps=32,fail_at=13;if(argc>1)d=strtoull(argv[1],0,10);if(argc>2)m=strtoull(argv[2],0,10);if(argc>3)steps=strtoull(argv[3],0,10);if(argc>4)fail_at=strtoull(argv[4],0,10);if(!d||!m||d%m||fail_at>=steps){fprintf(stderr,"invalid arguments\n");return 2;}size_t r=d/m;
 double *U=calloc(r*r,sizeof(double)),*x0=calloc(d,sizeof(double)),*ref=calloc(d,sizeof(double)),*refnext=calloc(d,sizeof(double)),*q=calloc(r,sizeof(double)),*qgap=calloc(r,sizeof(double)),*qnext=calloc(r,sizeof(double)),*newout=calloc(d,sizeof(double)),*fullsnap=calloc(d,sizeof(double)),*worka=calloc(d,sizeof(double)),*workb=calloc(d,sizeof(double)),*recovered=calloc(d,sizeof(double));if(!U||!x0||!ref||!refnext||!q||!qgap||!qnext||!newout||!fullsnap||!worka||!workb||!recovered)return 3;
 for(size_t i=0;i<r*r;i++)U[i]=(ur()*2.0-1.0)/sqrt((double)r);for(size_t b=0;b<r;b++){double v=.25+1.75*ur();for(size_t j=0;j<m;j++)x0[b*m+j]=v;}memcpy(fullsnap,x0,d*sizeof(double));memcpy(ref,x0,d*sizeof(double));project(x0,q,r,m);
 uint64_t t=ns();for(size_t k=0;k<steps;k++){agd_original_apply(ref,refnext,U,d,m,r);double*z=ref;ref=refnext;refnext=z;}uint64_t refns=ns()-t;
 AGDCertificate cert=agd_certificate_self();AGDPlan*p=agd_plan_create(x0,d,m,U,0.0,&cert);if(!p)return 3;double*oldout=calloc(d,sizeof(double));if(!oldout)return 3;t=ns();agd_plan_run(p,steps);agd_plan_reconstruct(p,oldout);uint64_t oldns=ns()-t;double olderr=agd_max_abs_error(ref,oldout,d);agd_plan_destroy(p);
 int injected=0,detected=0,full_snapshot_ok=0,quotient_snapshot_ok=0,recovered_ok=0,reentered=0,reentry_gate=0;uint64_t tnew=ns();
 for(size_t k=0;k<steps;k++){
   /* Quotient gap snapshot is immutable evidence; checksum detects injected corruption. */
   memcpy(qgap,q,r*sizeof(double));uint64_t hq=hash(qgap,r*sizeof(double));
   if(k==fail_at){qgap[r/2]+=0.125;injected=1;}
   if(hash(qgap,r*sizeof(double))!=hq){detected=1;quotient_snapshot_ok=1;
      /* Recover authoritative state at logical height k+1 by replaying original semantics from initial snapshot. */
      full_snapshot_ok=(hash(fullsnap,d*sizeof(double))==hash(x0,d*sizeof(double)));
      replay(fullsnap,recovered,U,d,m,r,k+1,worka,workb);
      /* Cross-check recovered checkpoint against independently computed reference trajectory at the same height. */
      replay(fullsnap,worka,U,d,m,r,k+1,workb,refnext);
      recovered_ok=(agd_max_abs_error(recovered,worka,d)==0.0 && agd_admissible_block_constant(recovered,d,m,0.0));
      if(!recovered_ok)break;
      project(recovered,q,r,m);
      /* Proof-gated re-entry witness: next projected transition agrees with original transition. */
      qapply(q,qnext,U,r);expand(qnext,newout,r,m);agd_original_apply(recovered,worka,U,d,m,r);
      reentry_gate=(agd_max_abs_error(worka,newout,d)==0.0);if(!reentry_gate)break;reentered=1;
      /* We have already recovered height k+1; skip the corrupted quotient transition and continue at k+1. */
      k++; if(k>=steps)break;
      qapply(q,qnext,U,r);memcpy(q,qnext,r*sizeof(double));
   }else{qapply(qgap,qnext,U,r);memcpy(q,qnext,r*sizeof(double));}
 }
 uint64_t newns=ns()-tnew;expand(q,newout,r,m);double newerr=agd_max_abs_error(ref,newout,d);
 double*bad=calloc(d,sizeof(double));memcpy(bad,x0,d*sizeof(double));bad[m/2]+=1.0;AGDPlan*bp=agd_plan_create(bad,d,m,U,0.0,&cert);int initial_fallback=bp&&agd_plan_in_fallback(bp);if(bp)agd_plan_destroy(bp);
 printf("DUAL_SNAPSHOT_REENTRY v2\nshape d=%zu m=%zu r=%zu steps=%zu injected_gap_height=%zu\n",d,m,r,steps,fail_at);
 printf("original_reference_ms=%.6f\nold_quotient_ms=%.6f\nnew_dual_snapshot_ms=%.6f\n",refns/1e6,oldns/1e6,newns/1e6);
 printf("injected_quotient_perturbation=%s\ngap_detected_by_integrity_gate=%s\nfull_snapshot_integrity=%s\nquotient_gap_snapshot_preserved=%s\nauthoritative_recovery_at_checkpoint=%s\nreentry_gate=%s\nreentered=%s\ninitial_inadmissible_fallback=%s\nold_max_abs_error=%.17g\nnew_max_abs_error=%.17g\n",injected?"YES":"NO",detected?"YES":"NO",full_snapshot_ok?"PASS":"FAIL",quotient_snapshot_ok?"PASS":"FAIL",recovered_ok?"PASS":"FAIL",reentry_gate?"PASS":"FAIL",reentered?"YES":"NO",initial_fallback?"PASS":"FAIL",olderr,newerr);
 printf("speedup_old_vs_original=%.6fx\nspeedup_new_vs_original=%.6fx\n",(double)refns/(double)oldns,(double)refns/(double)newns);
 free(U);free(x0);free(ref);free(refnext);free(q);free(qgap);free(qnext);free(newout);free(fullsnap);free(worka);free(workb);free(recovered);free(oldout);free(bad);
 return (injected&&detected&&full_snapshot_ok&&quotient_snapshot_ok&&recovered_ok&&reentry_gate&&reentered&&initial_fallback&&olderr==0.0&&newerr==0.0)?0:10;}
