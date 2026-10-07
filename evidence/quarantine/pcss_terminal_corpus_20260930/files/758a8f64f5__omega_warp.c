#include <stdio.h>
#include <gmp.h>
#include <pthread.h>
#include <unistd.h>

/* [Ω-WARP KERNEL]
   Logic: Multicore Saturation
   Status: Machine Precise */

void *warp_drive(void *arg) {
    int id = *(int*)arg;
    mpz_t p;
    mpz_init_set_ui(p, 100000000 + (id * 10000000));
    
    while(1) {
        mpz_nextprime(p, p);
        // Direct Frame-Buffer Output (The Waterfall)
        gmp_printf("\033[1;3%dm[CORE %d] | Δ-PRIME: %Zd\n", (id % 7) + 1, id, p);
    }
    return NULL;
}

int main() {
    printf("\033[1;31m--- INITIATING TOTAL HARDWARE COLLAPSE ---\033[0m\n");
    printf("State: 8-Core Sovereign Priority Lock Engaged\n");
    sleep(2);

    pthread_t cluster[8];
    int ids[8];

    for (int i = 0; i < 8; i++) {
        ids[i] = i;
        pthread_create(&cluster[i], NULL, warp_drive, &ids[i]);
    }

    for (int i = 0; i < 8; i++) pthread_join(cluster[i], NULL);
    return 0;
}
