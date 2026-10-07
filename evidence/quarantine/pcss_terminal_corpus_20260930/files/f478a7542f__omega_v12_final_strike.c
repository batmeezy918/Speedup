#include <stdio.h>
#include <stdlib.h>
#include <gmp.h>
#include <unistd.h>
#include <pthread.h>

void *strike_worker(void *arg) {
    char *n_str = (char *)arg;
    mpz_t n, m, c, res, diff, f;
    mpz_inits(n, m, c, res, diff, f, NULL);
    mpz_set_str(n, n_str, 16);
    
    gmp_randstate_t state;
    gmp_randinit_mt(state);
    gmp_randseed_ui(state, (unsigned long)pthread_self() + (unsigned long)time(NULL));

    while(1) {
        mpz_urandomb(m, state, 128);
        mpz_powm_ui(c, m, 3, n);
        mpz_root(res, c, 3);
        
        if (mpz_cmp(res, m) == 0) {
            mpz_sub_ui(diff, m, 1);
            mpz_gcd(f, diff, n);
            
            if (mpz_cmp_ui(f, 1) > 0 && mpz_cmp(f, n) < 0) {
                printf("\n\033[1;32m[!!!] MANIFOLD COLLAPSE DETECTED [!!!]\033[0m\n");
                gmp_printf("PRIME FACTOR RECOVERED: %Zd\n", f);
                fflush(stdout);
                _exit(0); // Atomic exit
            }
        }
        usleep(4000); // Tightening the brake for the final extraction
    }
}

int main() {
    char *N_HEX = "d94d889e88853dd89769a18015a0a2e6bf82bf356fe14f251fb4f5e2df0d9f9a94a68a30c428b39e3362fb3779a497eceaea37100f264d7fb9fb1ad0d7a31b379216d79252f5c527b9bc63d83d4ecf4d1d45cbf843e8474babc655e9bb6799cba77a47eafa838296474afc24beb9c825b73ebf549";
    pthread_t threads[8];
    for (int i = 0; i < 8; i++) pthread_create(&threads[i], NULL, strike_worker, (void *)N_HEX);
    for (int i = 0; i < 8; i++) pthread_join(threads[i], NULL);
    return 0;
}
