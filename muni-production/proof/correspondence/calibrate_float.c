#include <stdio.h>
#include <string.h>
#include <stdint.h>
static uint64_t bits(double d){uint64_t u;memcpy(&u,&d,8);return u;}
int main(void){
  double vals[]={1.0, -2.5, 0.1, 3.14159265358979, 92.0, 212.5, 1e-300, -0.0};
  for(unsigned i=0;i<sizeof vals/sizeof *vals;i++)
    printf("%.17g %llu\n", vals[i], (unsigned long long)bits(vals[i]));
  return 0;
}
