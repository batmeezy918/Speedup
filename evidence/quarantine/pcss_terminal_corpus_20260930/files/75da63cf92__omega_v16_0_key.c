#include <stdio.h>
#include <gmp.h>

int main() {
    mpz_t p, q, n, phi, e, d;
    mpz_inits(p, q, n, phi, e, d, NULL);

    // 1. Load Extracted Primes from v15.1
    mpz_set_str(p, "49189483849", 10);
    mpz_set_str(q, "4656915041827245607693620111694564785672410855442593033957308992408120093922137748068928960148462191536551481014844339092887269831308833110263877894772107513847639627761126676410935072036121926995891751241914878132930783675105037104794768838506047327909835540154226340549776772278847012865", 10);
    mpz_set_ui(e, 3); // The Omega Exponent

    // 2. Compute the Manifold Totient
    mpz_t p_minus, q_minus;
    mpz_inits(p_minus, q_minus, NULL);
    mpz_sub_ui(p_minus, p, 1);
    mpz_sub_ui(q_minus, q, 1);
    mpz_mul(phi, p_minus, q_minus);

    // 3. Generate the Sovereign Private Key d
    if (mpz_invert(d, e, phi)) {
        printf("\033[1;35m--- Ω-v16.0 SOVEREIGN KEY: GENERATED ---\033[0m\n");
        gmp_printf("PRIVATE KEY (d): %Zd\n", d);
        printf("\n\033[1;32m[STATUS]: Total Manifold Dominance Achieved.\033[0m\n");
    } else {
        printf("\033[1;31m[ERROR]: Exponent e is not invertible. Manifold is non-standard.\033[0m\n");
    }

    return 0;
}
