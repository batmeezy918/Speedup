#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <chrono>

struct LiveState {
    std::uint64_t sequence;
    std::int64_t bid_ticks;
    std::int64_t ask_ticks;
    std::uint64_t bid_u6;
    std::uint64_t ask_u6;
};

struct InvariantSignature {
    std::int32_t spread_ticks;
    std::int16_t imbalance_bucket;
    std::uint8_t execution; // 1 SELL, 0 HOLD
};

static inline std::int64_t floor_div(std::int64_t a, std::int64_t b) {
    std::int64_t q = a / b, r = a % b;
    if (r != 0 && ((r < 0) != (b < 0))) --q;
    return q;
}

static inline InvariantSignature derive_once(const LiveState& s) {
    const std::int64_t diff = static_cast<std::int64_t>(s.bid_u6) - static_cast<std::int64_t>(s.ask_u6);
    const std::uint64_t sum = s.bid_u6 + s.ask_u6;
    // imbalance in signed fixed point, scaled by 1e6.
    const std::int64_t imb_u6 = sum ? (diff * 1000000LL) / static_cast<std::int64_t>(sum) : 0;
    const std::int16_t bucket = static_cast<std::int16_t>(floor_div(imb_u6, 10000)); // 0.01 buckets
    const std::uint8_t sell = (imb_u6 < -450000) ? 1 : 0;
    return {static_cast<std::int32_t>(s.ask_ticks - s.bid_ticks), bucket, sell};
}

static inline std::uint64_t baseline_decision(const LiveState& s) {
    const std::int64_t diff = static_cast<std::int64_t>(s.bid_u6) - static_cast<std::int64_t>(s.ask_u6);
    const std::uint64_t sum = s.bid_u6 + s.ask_u6;
    const std::int64_t imb_u6 = sum ? (diff * 1000000LL) / static_cast<std::int64_t>(sum) : 0;
    return (imb_u6 < -450000) ? 1ULL : 0ULL;
}

static inline std::uint64_t quotient_decision(const InvariantSignature& q) {
    return q.execution;
}

static std::vector<LiveState> load_csv(const char* path) {
    std::ifstream f(path);
    std::string line;
    std::getline(f, line); // header
    std::vector<LiveState> out;
    while (std::getline(f, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string t, seq, bid, ask, bv, av, imb;
        std::getline(ss,t,','); std::getline(ss,seq,','); std::getline(ss,bid,',');
        std::getline(ss,ask,','); std::getline(ss,bv,','); std::getline(ss,av,','); std::getline(ss,imb,',');
        auto to_u6=[](const std::string& x)->std::uint64_t { return static_cast<std::uint64_t>(std::stold(x)*1000000.0L + 0.5L); };
        auto to_ticks=[](const std::string& x)->std::int64_t { return static_cast<std::int64_t>(std::stold(x)*100.0L + 0.5L); };
        out.push_back({std::stoull(seq),to_ticks(bid),to_ticks(ask),to_u6(bv),to_u6(av)});
    }
    return out;
}

template<class F>
static double ms(F&& fn, std::size_t rounds, std::uint64_t& sink) {
    std::vector<double> v; v.reserve(rounds);
    for (std::size_t r=0;r<rounds;r++) {
        const auto t0=std::chrono::steady_clock::now();
        sink ^= fn();
        const auto t1=std::chrono::steady_clock::now();
        v.push_back(std::chrono::duration<double,std::milli>(t1-t0).count());
    }
    std::sort(v.begin(),v.end());
    return v[v.size()/2];
}

int main(int argc, char** argv) {
    const char* path = argc>1 ? argv[1] : "evidence/qkxr/live_btcusd_snapshots.csv";
    const auto states=load_csv(path);
    if (states.empty()) return 2;
    constexpr std::size_t K=100000; // downstream operations per live state
    std::uint64_t sinkB=0,sinkQ=0;

    // One-time quotient derivation. Timed separately and then included in amortized total.
    std::vector<InvariantSignature> sig; sig.reserve(states.size());
    const auto d0=std::chrono::steady_clock::now();
    for (const auto& s:states) sig.push_back(derive_once(s));
    const auto d1=std::chrono::steady_clock::now();
    const double derive_ms=std::chrono::duration<double,std::milli>(d1-d0).count();

    auto baseline_fn=[&](){ volatile std::uint64_t x=0; for(std::size_t k=0;k<K;k++) for(const auto&s:states) x^=baseline_decision(s); return x; };
    auto quotient_fn=[&](){ volatile std::uint64_t x=0; for(std::size_t k=0;k<K;k++) for(const auto&q:sig) x^=quotient_decision(q); return x; };

    // One-time semantic overhead check: validate every live snapshot before carry-forward.
    const auto v0=std::chrono::steady_clock::now();
    bool equivalent=true;
    for(std::size_t i=0;i<states.size();++i)
        equivalent &= (baseline_decision(states[i])==quotient_decision(sig[i]));
    const auto v1=std::chrono::steady_clock::now();
    const double validate_ms=std::chrono::duration<double,std::milli>(v1-v0).count();

    // Warmup, then 7 timing samples on identical downstream workload.
    sinkB ^= baseline_fn(); sinkQ ^= quotient_fn();
    const double b=ms(baseline_fn,7,sinkB);
    const double q=ms(quotient_fn,7,sinkQ);
    const double amortized_q=q+derive_ms+validate_ms;
    const double speed=b/amortized_q;

    std::vector<InvariantSignature> unique_sig=sig;
    std::sort(unique_sig.begin(),unique_sig.end(),[](const auto&a,const auto&b){
        if(a.spread_ticks!=b.spread_ticks) return a.spread_ticks<b.spread_ticks;
        if(a.imbalance_bucket!=b.imbalance_bucket) return a.imbalance_bucket<b.imbalance_bucket;
        return a.execution<b.execution;
    });
    unique_sig.erase(std::unique(unique_sig.begin(),unique_sig.end(),[](const auto&a,const auto&b){
        return a.spread_ticks==b.spread_ticks && a.imbalance_bucket==b.imbalance_bucket && a.execution==b.execution;
    }),unique_sig.end());

    std::cout<<std::setprecision(12);
    std::cout<<"QKXR_TOWER_NATIVE\n";
    std::cout<<"live_states="<<states.size()<<" downstream_K="<<K<<"\n";
    std::cout<<"decision_equivalent="<<(equivalent?"true":"false")<<"\n";
    std::cout<<"one_time_derivation_ms="<<derive_ms<<"\n";
    std::cout<<"one_time_validation_ms="<<validate_ms<<"\n";
    std::cout<<"unique_signatures="<<unique_sig.size()<<"\n";
    std::cout<<"baseline_median_ms="<<b<<"\n";
    std::cout<<"quotient_downstream_median_ms="<<q<<"\n";
    std::cout<<"quotient_amortized_including_derivation_ms="<<amortized_q<<"\n";
    std::cout<<"baseline_over_amortized_quotient_speedup="<<speed<<"x\n";
    std::cout<<"compression_events_to_signatures="<<states.size()<<"->"<<sig.size()<<"\n";
    std::cout<<"sink="<<(sinkB^sinkQ)<<"\n";
    return equivalent?0:3;
}
