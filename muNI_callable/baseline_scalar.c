#include <stddef.h>
#include <string.h>
#include <omp.h>
#define B 64
void gemm_scalar(int n,const float *a,const float *b,float *c){
 memset(c,0,(size_t)n*n*sizeof(float));
 #pragma omp parallel for schedule(static)
 for(int ii=0;ii<n;ii+=B){
  int im=ii+B<n?ii+B:n;
  for(int kk=0;kk<n;kk+=B){
   int km=kk+B<n?kk+B:n;
   for(int jj=0;jj<n;jj+=B){
    int jm=jj+B<n?jj+B:n;
    for(int i=ii;i<im;i++) for(int k=kk;k<km;k++){
     float aik=a[(size_t)i*n+k];
     for(int j=jj;j<jm;j++) c[(size_t)i*n+j]+=aik*b[(size_t)k*n+j];
    }
   }
  }
 }
}
