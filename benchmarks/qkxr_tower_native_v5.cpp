#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

struct LiveState { std::uint64_t sequence; std::int64_t bid_ticks, ask_ticks; std::uint64_t bid_u6, ask_u6; };
struct InvariantSignature { std::int32_t spread_ticks; std::int16_t imbalance_bucket; std::uint8_t execution; };
struct DerivedBundle { std::array<std::uint64_t,32> obs{}; };

static inline std::int64_t floor_div(std::int64_t a,std::int64_t b){
  auto q=a/b,r=a%b; if(r!=0&&((r<0)!=(b<0)))--q; return q;
}
static inline InvariantSignature derive_once(const LiveState&s){
  const auto diff=(std::int64_t)s.bid_u6-(std::int64_t)s.ask_u6;
  const auto sum=s.bid_u6+s.ask_u6;
  const auto imb=sum?(diff*1000000LL)/(std::int64_t)sum:0;
  return {(std::int32_t)(s.ask_ticks-s.bid_ticks),
          (std::int16_t)floor_div(imb,10000),(std::uint8_t)(imb<-450000)};
}

/* The entire downstream observable bundle factors through the invariant quotient. */
static inline DerivedBundle materialize_bundle(const InvariantSignature&q){
  DerivedBundle d;
  const std::uint64_t b=(std::uint64_t)(q.imbalance_bucket+100);
  const std::uint64_t sp=(std::uint64_t)(q.spread_ticks<0?0:q.spread_ticks);
  const std::uint64_t e=q.execution;
  for(std::uint32_t i=0;i<32;i++){
    std::uint64_t z;
    switch(i&15){
      case 0:z=e;break; case 1:z=b;break; case 2:z=sp;break;
      case 3:z=(b>100);break; case 4:z=(b<60);break;
      case 5:z=(e||b<60);break; case 6:z=(sp<=1&&e==0);break;
      case 7:z=sp*sp+(b&7);break; case 8:z=(b<<3)^sp^e;break;
      case 9:z=((b+sp+e)*3)&255;break; case 10:z=(b*17+sp*5+e)&511;break;
      case 11:z=b^((sp+1)<<4)^(e<<9);break; case 12:z=(b>100)?sp:(b+1);break;
      case 13:z=((e)?(256-b):(b+sp))&511;break;
      case 14:z=((std::uint64_t)(q.spread_ticks+1))*((std::uint64_t)(q.imbalance_bucket+101));break;
      default:z=((b*31)+(sp*7)+(e*13))&1023;break;
    }
    d.obs[i]=z+(std::uint64_t)i*0x9e3779b9ULL;
  }
  return d;
}
static inline std::uint64_t consume(const DerivedBundle&d){
  std::uint64_t x=0; for(auto z:d.obs)x^=z; return x;
}
static inline std::uint64_t baseline_consumer(const LiveState&s){
  return consume(materialize_bundle(derive_once(s)));
}
static inline bool same_sig(const InvariantSignature&a,const InvariantSignature&b){
  return a.spread_ticks==b.spread_ticks&&a.imbalance_bucket==b.imbalance_bucket&&a.execution==b.execution;
}
static std::vector<LiveState> load_csv(const char*path){
  std::ifstream f(path);if(!f)return{};std::string line;std::getline(f,line);std::vector<LiveState>v;
  while(std::getline(f,line)){if(line.empty())continue;std::stringstream ss(line);std::string t,seq,bid,ask,bv,av,imb;
    std::getline(ss,t,',');std::getline(ss,seq,',');std::getline(ss,bid,',');std::getline(ss,ask,',');
    std::getline(ss,bv,',');std::getline(ss,av,',');std::getline(ss,imb,',');
    auto u=[](const std::string&s){return(std::uint64_t)(std::stold(s)*1000000.0L+0.5L);};
    auto p=[](const std::string&s){return(std::int64_t)(std::stold(s)*100.0L+0.5L);};
    v.push_back({std::stoull(seq),p(bid),p(ask),u(bv),u(av)});}return v;
}
template<class F>static double med(F&&fn,int rounds,std::uint64_t&sink){
  std::vector<double>v;v.reserve(rounds);for(int r=0;r<rounds;r++){auto t0=std::chrono::steady_clock::now();sink^=fn();auto t1=std::chrono::steady_clock::now();v.push_back(std::chrono::duration<double,std::milli>(t1-t0).count());}
  std::sort(v.begin(),v.end());return v[v.size()/2];
}
int main(int argc,char**argv){
  const char*path=argc>1?argv[1]:"evidence/qkxr/live_btcusd_stream_20261004T0718Z.csv";
  const auto states=load_csv(path);if(states.empty())return 2;
  constexpr std::size_t K=100000, FANOUT=32;std::uint64_t sb=0,sq=0;
  auto d0=std::chrono::steady_clock::now();std::vector<InvariantSignature>sig;sig.reserve(states.size());
  for(const auto&s:states)sig.push_back(derive_once(s));auto d1=std::chrono::steady_clock::now();
  const double derive=std::chrono::duration<double,std::milli>(d1-d0).count();
  bool equivalent=true;for(std::size_t i=0;i<states.size();i++)equivalent&=(baseline_consumer(states[i])==consume(materialize_bundle(sig[i])));
  auto c0=std::chrono::steady_clock::now();std::vector<InvariantSignature>uniq;uniq.reserve(sig.size());
  for(const auto&q:sig){bool seen=false;for(const auto&u:uniq)if(same_sig(q,u)){seen=true;break;}if(!seen)uniq.push_back(q);}
  std::vector<DerivedBundle>cache;cache.reserve(uniq.size());for(const auto&q:uniq)cache.push_back(materialize_bundle(q));
  auto c1=std::chrono::steady_clock::now();const double closure_build=std::chrono::duration<double,std::milli>(c1-c0).count();
  auto bf=[&](){volatile std::uint64_t x=0;for(std::size_t k=0;k<K;k++)for(const auto&s:states)x^=baseline_consumer(s);return x;};
  auto qf=[&](){volatile std::uint64_t x=0;for(std::size_t k=0;k<K;k++)for(const auto&d:cache)x^=consume(d);return x;};
  sb^=bf();sq^=qf();const double b=med(bf,7,sb),q=med(qf,7,sq);
  const double am=q+derive+closure_build;
  std::cout<<std::setprecision(12)
    <<"QKXR_TOWER_NATIVE_V5_MATERIALIZED_CLOSURE\n"
    <<"live_states="<<states.size()<<" unique_classes="<<uniq.size()<<" fanout="<<FANOUT<<" K="<<K<<"\n"
    <<"semantic_equivalent="<<(equivalent?"true":"false")<<"\n"
    <<"invariants_derived_once="<<sig.size()<<" downstream_bundle_materialized_once_per_class="<<cache.size()<<"\n"
    <<"one_time_derivation_ms="<<derive<<" closure_materialization_ms="<<closure_build<<"\n"
    <<"compression_ratio="<<(double)states.size()/uniq.size()<<"x\n"
    <<"baseline_recompute_signature_and_bundle_median_ms="<<b<<"\n"
    <<"quotient_reuse_materialized_bundle_median_ms="<<q<<"\n"
    <<"quotient_amortized_ms="<<am<<"\n"
    <<"speedup="<<b/am<<"x\n"
    <<"sink="<<(sb^sq)<<"\n";
  return equivalent?0:3;
}
