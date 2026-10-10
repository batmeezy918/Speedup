#include "kernel_agl.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <vector>

using Clock = std::chrono::steady_clock;
static std::uint64_t fnv1a(const double* p, std::size_t n) {
  const auto* b = reinterpret_cast<const unsigned char*>(p);
  std::uint64_t h = 14695981039346656037ULL;
  for (std::size_t i = 0; i < n * sizeof(double); ++i) {
    h ^= b[i]; h *= 1099511628211ULL;
  }
  return h;
}
static void full_run(const std::vector<double>& x, const std::vector<double>& U,
                     std::size_t d, std::size_t m, std::size_t r,
                     std::size_t steps, std::vector<double>& out) {
  std::vector<double> a=x, b(d);
  for (std::size_t k=0;k<steps;k++) {
    agd_original_apply(a.data(),b.data(),U.data(),d,m,r);
    a.swap(b);
  }
  out.swap(a);
}
static double median(std::vector<double> v) {
  std::sort(v.begin(),v.end()); return v[v.size()/2];
}
int main() {
  constexpr std::size_t d=4096,m=64,r=d/m,steps=256,trials=5,reps=3;
  std::vector<double> U(r*r),x(d),reference(d),fast(d);
  for(std::size_t i=0;i<r*r;i++) {
    const int v=static_cast<int>((i*17+13)%101)-50;
    U[i]=static_cast<double>(v)/1024.0;
  }
  for(std::size_t b=0;b<r;b++) {
    const double v=static_cast<double>((b%17)+1)/32.0;
    for(std::size_t j=0;j<m;j++) x[b*m+j]=v;
  }
  AGDCertificate cert=agd_certificate_self();
  full_run(x,U,d,m,r,steps,reference);
  AGDPlan* p=agd_plan_create(x.data(),d,m,U.data(),0.0,&cert);
  if(!p || !agd_plan_certified(p) || !agd_plan_admissible(p) ||
     agd_plan_in_fallback(p) || !agd_plan_run(p,steps) ||
     !agd_plan_reconstruct(p,fast.data())) {
    std::cerr<<"CROSS_ENVIRONMENT_EXACTNESS_GATE=FAIL plan/admissibility\n"; return 10;
  }
  const double err=agd_max_abs_error(reference.data(),fast.data(),d);
  const bool exact=std::memcmp(reference.data(),fast.data(),d*sizeof(double))==0;
  std::cout<<std::setprecision(12)
    <<"WITNESS=AGD_MUNI_CROSS_ENVIRONMENT\n"
    <<"d="<<d<<" m="<<m<<" r="<<r<<" steps="<<steps<<"\n"
    <<"certificate_state="<<cert.state<<" target="<<cert.target<<" compiler="<<cert.compiler<<"\n"
    <<"max_abs_error="<<err<<" bitwise_equal="<<(exact?"PASS":"FAIL")<<"\n"
    <<"full_output_fnv1a64="<<fnv1a(reference.data(),d)<<"\n"
    <<"fast_output_fnv1a64="<<fnv1a(fast.data(),d)<<"\n";
  agd_plan_destroy(p);
  if(err!=0.0 || !exact) { std::cerr<<"CROSS_ENVIRONMENT_EXACTNESS_GATE=FAIL\n"; return 11; }

  std::vector<double> base_times,quot_times;
  for(std::size_t t=0;t<trials;t++) {
    double base_total=0,quot_total=0;
    for(std::size_t rep=0;rep<reps;rep++) {
      auto b0=Clock::now();
      full_run(x,U,d,m,r,steps,reference);
      auto b1=Clock::now();
      base_total+=std::chrono::duration<double,std::milli>(b1-b0).count();
      auto q0=Clock::now();
      AGDPlan* q=agd_plan_create(x.data(),d,m,U.data(),0.0,&cert);
      if(!q || !agd_plan_run(q,steps) || !agd_plan_reconstruct(q,fast.data())) return 12;
      auto q1=Clock::now();
      quot_total+=std::chrono::duration<double,std::milli>(q1-q0).count();
      if(agd_max_abs_error(reference.data(),fast.data(),d)!=0.0 ||
         std::memcmp(reference.data(),fast.data(),d*sizeof(double))!=0) return 13;
      agd_plan_destroy(q);
    }
    base_times.push_back(base_total/reps);
    quot_times.push_back(quot_total/reps);
  }
  const double bm=median(base_times),qm=median(quot_times);
  std::cout<<"baseline_ms="<<bm<<" quotient_e2e_ms="<<qm
           <<" speedup="<<bm/qm<<"x (timing informational only)\n";
  if(!(bm>0.0) || !(qm>0.0) || !std::isfinite(bm/qm)) {
    std::cerr<<"CROSS_ENVIRONMENT_BENCHMARK_GATE=FAIL\n"; return 14;
  }

  x[m/2]+=1.0;
  full_run(x,U,d,m,r,steps,reference);
  p=agd_plan_create(x.data(),d,m,U.data(),0.0,&cert);
  if(!p || !agd_plan_in_fallback(p) || agd_plan_admissible(p) ||
     !agd_plan_run(p,steps) || !agd_plan_reconstruct(fast.data())) {
    std::cerr<<"CROSS_ENVIRONMENT_FALLBACK_GATE=FAIL path\n"; return 15;
  }
  const double ferr=agd_max_abs_error(reference.data(),fast.data(),d);
  const bool fexact=std::memcmp(reference.data(),fast.data(),d*sizeof(double))==0;
  agd_plan_destroy(p);
  std::cout<<"inadmissible_fallback_error="<<ferr
           <<" fallback_bitwise_equal="<<(fexact?"PASS":"FAIL")<<"\n";
  if(ferr!=0.0 || !fexact) { std::cerr<<"CROSS_ENVIRONMENT_FALLBACK_GATE=FAIL\n"; return 16; }
  std::cout<<"CROSS_ENVIRONMENT_EXACTNESS_GATE=PASS\n"
           <<"CROSS_ENVIRONMENT_BENCHMARK_GATE=PASS (timing informational only)\n"
           <<"CROSS_ENVIRONMENT_FALLBACK_GATE=PASS\n"
           <<"CROSS_ENVIRONMENT=PASS\n";
  return 0;
}
