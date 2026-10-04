#include <arm_neon.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define MAXC 32
#define MAXD 16384
typedef struct {const char*n;int B,C,D,P,S,seed,adv;} Rg;
static volatile float sink;
static uint64_t ns(){struct timespec t;clock_gettime(CLOCK_MONOTONIC_RAW,&t);return(uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec;}
static uint32_t rng(uint32_t*z){*z=1664525u*(*z)+1013904223u;return*z;}
static float sd(const float*x,const float*w,int D){float z=0;for(int i=0;i<D;i++)z+=x[i]*w[i];return z;}
static float nd(const float*x,const float*w,int D){float32x4_t a=vdupq_n_f32(0);int i=0;for(;i+4<=D;i+=4)a=vmlaq_f32(a,vld1q_f32(x+i),vld1q_f32(w+i));float t[4];vst1q_f32(t,a);float z=t[0]+t[1]+t[2]+t[3];for(;i<D;i++)z+=x[i]*w[i];return z;}
static void fill(float*x,float*w,int D,uint32_t s,int adv){for(int i=0;i<D;i++){float u=((rng(&s)>>8)&65535)/65535.0f-.5f;if(adv)u=(i&1)?1e-3f:-1e-3f;x[i]=u;}for(int i=0;i<D;i++){float u=((rng(&s)>>8)&65535)/65535.0f-.5f;if(adv)u=(i&3)?-1e3f:1e3f;w[i]=u;}}
static int cl(int b,int B,int C){return(b*C)/B;}
static float bb(const float*x,const float*w,int B,int C,int D,int P,int S,int b){int c=cl(b,B,C);float scale=1+.0001f*c,p=0,t=0;for(int k=0;k<P;k++)p+=sd(x,w,D)*scale*.00001f;for(int s=0;s<S;s++)t+=sd(x,w,D)*scale+p+c*.0001f;return t;}
static float cc(const float*x,const float*w,int B,int C,int D,int P,int S,float*r){float d[MAXC],p[MAXC],tot=0;for(int c=0;c<C;c++){float scale=1+.0001f*c,q=0;for(int k=0;k<P;k++)q+=sd(x,w,D)*scale*.00001f;p[c]=q;d[c]=nd(x,w,D)*scale;}for(int b=0;b<B;b++){int c=cl(b,B,C);float v=0;for(int s=0;s<S;s++)v+=d[c]+p[c]+c*.0001f;r[b]=v;tot+=v;}return tot;}
static int cmp(const void*a,const void*b){double x=*(double*)a,y=*(double*)b;return(x>y)-(x<y);}
static double med(double*a,int n){qsort(a,n,sizeof(double),cmp);return a[n/2];}
int main(){Rg rs[]={{"balanced",64,8,4096,100,20,101,0},{"quotient_pressure",128,8,8192,120,30,211,0},{"class_fragmentation",256,32,4096,80,20,307,0},{"numerical_cancellation",128,16,4096,100,20,401,1}};float*x=aligned_alloc(64,MAXD*4),*w=aligned_alloc(64,MAXD*4),*rv=aligned_alloc(64,256*4),*bv=aligned_alloc(64,256*4);int global=1;puts("ELEVATED_PCSS_SUITE_V1");puts("REGIME,B,C,D,P,S,SEED,SPEEDUP,RECON_ERR,INV_ERR,BASE_NS,COMP_NS,GATE");for(int ri=0;ri<4;ri++){Rg q=rs[ri];fill(x,w,q.D,q.seed,q.adv);double bt=0;for(int b=0;b<q.B;b++){bv[b]=bb(x,w,q.B,q.C,q.D,q.P,q.S,b);bt+=bv[b];}float ct=cc(x,w,q.B,q.C,q.D,q.P,q.S,rv);double re=0;for(int b=0;b<q.B;b++){double e=fabs((double)rv[b]-bv[b]);if(e>re)re=e;}double ie=fabs(ct-bt)/(fabs(bt)+1e-12);double tb[5],tc[5];for(int r=0;r<5;r++){uint64_t a=ns();double z=0;for(int b=0;b<q.B;b++)z+=bb(x,w,q.B,q.C,q.D,q.P,q.S,b);uint64_t e=ns();tb[r]=e-a;sink=z;a=ns();float zc=cc(x,w,q.B,q.C,q.D,q.P,q.S,rv);e=ns();tc[r]=e-a;sink=zc;}double mb=med(tb,5),mc=med(tc,5),sp=mb/mc;int pass=sp>1&&re/(fabs(bt)+1e-12)<1e-4&&ie<1e-4&&isfinite(sp);if(!pass)global=0;printf("%s,%d,%d,%d,%d,%d,%d,%.6f,%.9g,%.9g,%.0f,%.0f,%s\n",q.n,q.B,q.C,q.D,q.P,q.S,q.seed,sp,re,ie,mb,mc,pass?"PASS":"FAIL");fflush(stdout);}puts(global?"GLOBAL_GATE=PASS_WITH_ALL_REGIMES":"GLOBAL_GATE=FAIL");free(x);free(w);free(rv);free(bv);return global?0:1;}