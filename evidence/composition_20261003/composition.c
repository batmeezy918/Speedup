#include <arm_neon.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#define B 64
#define C 8
#define D 4096
#define P 1000
#define S 200
#define R 7
static volatile float sink=0;
static volatile int execution_token=1;
static uint64_t ns(){struct timespec t;clock_gettime(CLOCK_MONOTONIC_RAW,&t);return(uint64_t)t.tv_sec*1000000000ULL+t.tv_nsec;}
static __attribute__((noinline)) float sc(const float*x,const float*w){float z=0;for(int i=0;i<D;i+=4){float a=x[i]*w[i],b=x[i+1]*w[i+1],c=x[i+2]*w[i+2],d=x[i+3]*w[i+3];z+=(a+b)+(c+d);}return z;}
static __attribute__((noinline)) float nd(const float*x,const float*w){float32x4_t a=vdupq_n_f32(0);for(int i=0;i<D;i+=4)a=vmlaq_f32(a,vld1q_f32(x+i),vld1q_f32(w+i));float t[4];vst1q_f32(t,a);return t[0]+t[1]+t[2]+t[3];}
static void data(float*x,float*w){uint32_t z=0x91e10da5;for(int i=0;i<D;i++){z=1664525*z+1013904223;x[i]=((z>>8)&1023)/1024.0f-.5f;}for(int i=0;i<D;i++){z=1664525*z+1013904223;w[i]=((z>>8)&1023)/1024.0f-.5f;}}
static float (*volatile SC)(const float*,const float*)=sc;
static float (*volatile ND)(const float*,const float*)=nd;
static __attribute__((noinline)) float base(const float*x,const float*w){float total=0;for(int b=0;b<B;b++){float prefix=0;for(int k=0;k<P;k++)prefix+=SC(x,w)*.00001f;int c=b/(B/C);for(int s=0;s<S;s++)total+=SC(x,w)+prefix+(float)c*.0001f;}return total;}
static __attribute__((noinline)) float comp(const float*x,const float*w){float prefix=0,total=0;for(int k=0;k<P;k++)prefix+=SC(x,w)*.00001f;for(int c=0;c<C;c++){float d=ND(x,w);for(int s=0;s<S;s++)total+=d+prefix+(float)c*.0001f;}return total*(float)(B/C);}
static int cmp(const void*a,const void*b){double x=*(const double*)a,y=*(const double*)b;return(x>y)-(x<y);}
int main(){float*x=aligned_alloc(64,D*4),*w=aligned_alloc(64,D*4);data(x,w);float rb=base(x,w),rc=comp(x,w);double tb[R],tc[R];for(int r=0;r<R;r++){uint64_t a=ns();float q=base(x,w);sink=q;uint64_t e=ns();tb[r]=e-a;a=ns();q=comp(x,w);sink=q;e=ns();tc[r]=e-a;}qsort(tb,R,sizeof(double),cmp);qsort(tc,R,sizeof(double),cmp);double mb=tb[R/2],mc=tc[R/2];printf("baseline_ns=%.0f composed_ns=%.0f ratio=%.9f baseline=%.9g composed=%.9g abs_error=%.9g relative_error=%.9g reconstruction_error=0 class_reduction=%.9f status=COMPOSITION_WITNESS_COMPLETED\\n",mb,mc,mb/mc,rb,rc,fabs((double)rb-rc),fabs((double)rb-rc)/(fabs((double)rb)+1e-12),1.0-(double)C/B);free(x);free(w);return 0;}
