#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <openssl/sha.h>

#pragma STDC FP_CONTRACT OFF // Disable FMA to match Python

int main() {
    double m = 2.0, k = 5.0, c = 0.2, dt = 0.02;
    double x = 0.5, v = 0.2;
    int steps = 500;
    
    SHA256_CTX ctx;
    SHA256_Init(&ctx);
    
    union { double d; uint64_t u; } conv;
    
    printf("C_EXEC_START\n");
    for (int i = 0; i <= steps; i++) {
        double t = i * dt;
        double a = -(k * x + c * v) / m;
        double E = 0.5 * k * x * x + 0.5 * m * v * v;
        
        if (i == 0 || i == 1 || i == 2 || i == 10 || i == 100 || i == 250 || i == 500) {
            conv.d = t; uint64_t t_h = __builtin_bswap64(conv.u);
            conv.d = x; uint64_t x_h = __builtin_bswap64(conv.u);
            conv.d = v; uint64_t v_h = __builtin_bswap64(conv.u);
            conv.d = a; uint64_t a_h = __builtin_bswap64(conv.u);
            conv.d = E; uint64_t E_h = __builtin_bswap64(conv.u);
            
            printf("CHK_%d|t=%016llx|x=%016llx|v=%016llx|a=%016llx|E=%016llx\n", 
                   i, t_h, x_h, v_h, a_h, E_h);
            
            // Hash exactly the same byte sequence as Python
            SHA256_Update(&ctx, &t_h, 8);
            SHA256_Update(&ctx, &x_h, 8);
            SHA256_Update(&ctx, &v_h, 8);
            SHA256_Update(&ctx, &a_h, 8);
            SHA256_Update(&ctx, &E_h, 8);
        } else {
            conv.d = t; uint64_t t_h = __builtin_bswap64(conv.u);
            conv.d = x; uint64_t x_h = __builtin_bswap64(conv.u);
            conv.d = v; uint64_t v_h = __builtin_bswap64(conv.u);
            conv.d = a; uint64_t a_h = __builtin_bswap64(conv.u);
            conv.d = E; uint64_t E_h = __builtin_bswap64(conv.u);
            SHA256_Update(&ctx, &t_h, 8);
            SHA256_Update(&ctx, &x_h, 8);
            SHA256_Update(&ctx, &v_h, 8);
            SHA256_Update(&ctx, &a_h, 8);
            SHA256_Update(&ctx, &E_h, 8);
        }
        
        double v_new = v + a * dt;
        double x_new = x + v * dt;
        v = v_new;
        x = x_new;
    }
    
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_Final(hash, &ctx);
    printf("FULL_HASH|");
    for(int i=0; i<SHA256_DIGEST_LENGTH; i++) printf("%02x", hash[i]);
    printf("\nC_EXEC_END\n");
    
    return 0;
}
