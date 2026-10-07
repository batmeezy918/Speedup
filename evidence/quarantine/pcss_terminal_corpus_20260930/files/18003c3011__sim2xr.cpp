#include <openssl/sha.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include <string>

static constexpr double M=2.0;
static constexpr double K=5.0;
static constexpr double C=0.2;
static constexpr double DT=0.02;
static constexpr double X0=0.5;
static constexpr double V0=0.2;
static constexpr int STEPS=500;

static double acceleration(double x,double v)
{
    volatile double p1=K*x;
    volatile double p2=C*v;
    volatile double s1=p1+p2;
    volatile double q1=s1/M;
    volatile double a1=-q1;
    return a1;
}

static double energy(double x,double v)
{
    volatile double h=0.5;

    volatile double p1=h*K;
    volatile double p2=p1*x;
    volatile double p3=p2*x;

    volatile double q1=h*M;
    volatile double q2=q1*v;
    volatile double q3=q2*v;

    volatile double e=p3+q3;
    return e;
}

static uint64_t bits(double x)
{
    uint64_t u;
    std::memcpy(&u,&x,8);
    return u;
}

static void append_u64_be(
    std::vector<unsigned char>& b,
    uint64_t u)
{
    b.push_back((u>>56)&255);
    b.push_back((u>>48)&255);
    b.push_back((u>>40)&255);
    b.push_back((u>>32)&255);
    b.push_back((u>>24)&255);
    b.push_back((u>>16)&255);
    b.push_back((u>>8)&255);
    b.push_back(u&255);
}

static void append_f64_be(
    std::vector<unsigned char>& b,
    double x)
{
    append_u64_be(b,bits(x));
}

static std::string hash_bytes(
    const std::vector<unsigned char>& b)
{
    unsigned char d[SHA256_DIGEST_LENGTH];

    SHA256_CTX ctx;
    SHA256_Init(&ctx);
    SHA256_Update(&ctx,b.data(),b.size());
    SHA256_Final(d,&ctx);

    char out[65];

    for(int i=0;i<32;i++)
        std::sprintf(out+2*i,"%02x",d[i]);

    out[64]=0;

    return std::string(out);
}

static std::vector<unsigned char> run(
    int perturb_step=-1,
    double perturb_value=0.0)
{
    std::vector<unsigned char> b;
    b.reserve(24048);

    double x=X0;
    double v=V0;

    for(int i=0;i<=STEPS;i++)
    {
        if(i==perturb_step)
        {
            volatile double tmp=x+perturb_value;
            x=tmp;
        }

        volatile double ii=(double)i;
        volatile double t=ii*DT;

        double a=acceleration(x,v);
        double e=energy(x,v);

        append_u64_be(b,(uint64_t)i);
        append_f64_be(b,t);
        append_f64_be(b,x);
        append_f64_be(b,v);
        append_f64_be(b,a);
        append_f64_be(b,e);

        if(i<STEPS)
        {
            volatile double av=a*DT;
            volatile double v_new=v+av;

            volatile double xv=v*DT;
            volatile double x_new=x+xv;

            v=v_new;
            x=x_new;
        }
    }

    if(b.size()!=24048)
    {
        std::fprintf(
            stderr,
            "CANONICAL SIZE FAILURE: %zu\n",
            b.size());
        std::exit(2);
    }

    return b;
}

int main()
{
    auto base=run();
    auto base2=run();

    auto pert=run(250,1e-15);
    auto pert2=run(250,1e-15);

    auto bh=hash_bytes(base);
    auto bh2=hash_bytes(base2);

    auto ph=hash_bytes(pert);
    auto ph2=hash_bytes(pert2);

    FILE* f=fopen("cpp_baseline.bin","wb");
    fwrite(base.data(),1,base.size(),f);
    fclose(f);

    f=fopen("cpp_perturbed.bin","wb");
    fwrite(pert.data(),1,pert.size(),f);
    fclose(f);

    std::printf("C++\n");
    std::printf("SIZE=%zu\n",base.size());
    std::printf("HASH=%s\n",bh.c_str());
    std::printf("REPLAY_BYTES=%s\n",
        base==base2?"true":"false");
    std::printf("REPLAY_HASH=%s\n",
        bh==bh2?"true":"false");
    std::printf("PERTURBED_HASH=%s\n",ph.c_str());
    std::printf("PERTURBED_REPLAY=%s\n",
        pert==pert2 && ph==ph2?"true":"false");
    std::printf("PERTURBATION_CHANGED=%s\n",
        bh!=ph?"true":"false");

    return 0;
}
