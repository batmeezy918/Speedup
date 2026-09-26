/*
 * Corrected hierarchical-occupancy kernel.
 *
 * This replaces /root/eof_hierarchical_acceleration_full_validation.py, whose
 * "quotient" counted only the two admissible states (Q0 -> 1, Q1 -> parity)
 * and therefore never computed the baseline observable.
 *
 * THE OBSERVABLE (single, shared by both sides):
 *
 *     phi(L) = sum over ALL s in {0,1}^L of occupancy(s)
 *            = sum over ALL s in {0,1}^L of popcount(s)
 *            = L * 2^(L-1)
 *
 * Site 0 is the most significant bit, matching the Lean model where
 * pi s = s.headD false over `bits L`.
 *
 * BASELINE  : enumerate all 2^L states, sum popcounts.  O(2^L * L).
 * CANDIDATE : per-site symmetry.  For each of the L sites exactly 2^(L-1)
 *             states have that site set, so sum L copies of 2^(L-1).  O(L).
 *
 * Both sides return the SAME integer, bit for bit.  The candidate is checked
 * against the baseline for every L in [LMIN_EQ, LMAX_EQ], not against a
 * closed form only.
 *
 * A negative control `half_space_phi` deliberately reproduces the original
 * invalid candidate (the two admissible states) and MUST be shown unequal to
 * the baseline.  If the control ever matches, the harness is broken and the
 * experiment must fail closed.
 *
 * Timings come from CLOCK_MONOTONIC.  The candidate is O(L) and lands below
 * the timer floor, so both a direct single-call median and an amortized
 * batch ratio are reported; the headline metric is declared, not implied.
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define LMIN_EQ 1
#define LMAX_EQ 20
#define LMAX_RECONSTRUCT 16
#define LMAX_TIMED 20

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static int popcount64(uint64_t x) {
    int n = 0;
    while (x) { n += (int)(x & 1u); x >>= 1; }
    return n;
}

static int width_bits(int L) { return L; }

/*
 * MEASUREMENT INTEGRITY.
 *
 * The first version of this kernel timed the kernels with a *local* volatile
 * sink.  GCC eliminates a local volatile whose address never escapes, which
 * made the pure call CSE-able against the equivalence/sector loops that ran
 * earlier in the same process: 31 "baseline samples" were all a cache hit
 * (~1.7us instead of ~80ms) and the reported speedup was fiction.
 *
 * Fix, both halves required:
 *   - every kernel is noinline, so no cross-call CSE or hoisting is possible;
 *   - results are sunk into a file-scope volatile, whose address escapes, so
 *     the store cannot be deleted; plus explicit compiler barriers around the
 *     timed region so the clock reads cannot migrate across the work.
 */
/*
 * noipa (not merely noinline) is REQUIRED here.  With -O2 gcc runs an
 * interprocedural pure-const pass and, because these kernels only read their
 * argument, it marks them const and CSEs the timed call against the earlier
 * equivalence/sector loops in the same process.  Measured symptom: a 2^20
 * state baseline reported 1.7us instead of ~80ms.  noipa disables IPA, so the
 * timed region provably re-executes the loop.
 */
#define NOINLINE __attribute__((noinline, noipa))
#define BARRIER() __asm__ __volatile__("" ::: "memory")

static volatile uint64_t g_sink = 0;

/* BASELINE: exhaustive enumeration of the full 2^L state space. */
static NOINLINE uint64_t baseline_phi(int L) {
    const int nbits = width_bits(L);
    const uint64_t nstates = 1ull << nbits;
    uint64_t total = 0;
    for (uint64_t s = 0; s < nstates; ++s) total += (uint64_t)popcount64(s);
    return total;
}

/* CANDIDATE: per-site symmetry, one O(1) quotient per site, O(L) total. */
static NOINLINE uint64_t candidate_phi(int L) {
    const uint64_t per_site = 1ull << (L - 1);   /* states with site i set */
    uint64_t total = 0;
    for (int i = 0; i < L; ++i) total += per_site;  /* L sites */
    return total;
}

/* Independent closed form, used only as a THIRD cross-check. */
static NOINLINE uint64_t closed_form_phi(int L) {
    return (uint64_t)L * (1ull << (L - 1));
}

/*
 * NEGATIVE CONTROL: the original experiment's "quotient".  It never visits the
 * 2^L state space; it reports the two admissible states only.
 *   Q0 = 1, Q1 = parity of L
 * Reproduced here so the refutation of the original claim is a measured fact
 * inside the same harness that certifies the new candidate.
 */
static NOINLINE uint64_t half_space_phi(int L) {
    uint64_t q0 = 1;
    uint64_t q1 = (uint64_t)(L & 1);
    return q0 + q1;
}

/* --- sector / reconstruction machinery for gates Q and Q^-1 --- */

static int site0(uint64_t s, int L) { return (int)((s >> (L - 1)) & 1u); }

static uint64_t residual_of(uint64_t s, int L) {
    return s & ((1ull << (L - 1)) - 1ull);
}

static uint64_t reconstruct(int tag, uint64_t residual, int L) {
    return ((uint64_t)tag << (L - 1)) | residual;
}

/*
 * Q^-1: for every state s in the full space, recover (tag, residual), lift it
 * back, and require exact identity.  Also requires the lift to be injective
 * (all reconstructed states distinct) and to reproduce the candidate total.
 * Reverse error is therefore identically zero, by construction and by check.
 */
static int reconstruction_check(int L, uint64_t *out_max_err, uint64_t *out_sum) {
    const uint64_t nstates = 1ull << L;
    unsigned char *seen = (unsigned char *)calloc(nstates, 1);
    if (!seen) return 0;
    uint64_t max_err = 0, sum = 0;
    int ok = 1;
    for (uint64_t s = 0; s < nstates; ++s) {
        int tag = site0(s, L);
        uint64_t t = residual_of(s, L);
        uint64_t r = reconstruct(tag, t, L);
        if (r != s) { ok = 0; }
        if (seen[r]) { ok = 0; }          /* injectivity */
        seen[r] = 1;
        sum += (uint64_t)popcount64(r);
        uint64_t e = (r > s) ? (r - s) : (s - r);
        if (e > max_err) max_err = e;
    }
    /* the reconstruction must also see every state exactly once */
    for (uint64_t s = 0; s < nstates; ++s) if (!seen[s]) { ok = 0; }
    free(seen);
    *out_max_err = max_err;
    *out_sum = sum;
    return ok;
}

static void json_u64(const char *key, uint64_t v, int last) {
    printf("  \"%s\": %llu%s\n", key, (unsigned long long)v, last ? "" : ",");
}

int main(int argc, char **argv) {
    int Ltimed = LMAX_TIMED;
    int repeats = 31, warmups = 7, batch = 20000;
    if (argc > 1) Ltimed = atoi(argv[1]);
    if (argc > 2) repeats = atoi(argv[2]);
    if (argc > 3) warmups = atoi(argv[3]);
    if (argc > 4) batch = atoi(argv[4]);
    if (Ltimed < 2 || Ltimed > 30) { fprintf(stderr, "bad L\n"); return 2; }

    printf("{\n");
    printf("  \"toolchain\": \"gcc -O2 (native aarch64)\",\n");
    json_u64("lmin_eq", LMIN_EQ, 0);
    json_u64("lmax_eq", LMAX_EQ, 0);
    json_u64("lmax_reconstruct", LMAX_RECONSTRUCT, 0);
    json_u64("l_timed", (uint64_t)Ltimed, 0);
    json_u64("repeats", (uint64_t)repeats, 0);
    json_u64("warmups", (uint64_t)warmups, 0);
    json_u64("candidate_batch", (uint64_t)batch, 0);

    /* ---- gate I/R support: exact equivalence over the full domain ---- */
    printf("  \"equivalence\": [\n");
    for (int L = LMIN_EQ; L <= LMAX_EQ; ++L) {
        uint64_t b = baseline_phi(L);
        uint64_t c = candidate_phi(L);
        uint64_t f = closed_form_phi(L);
        printf("    {\"L\": %d, \"baseline\": %llu, \"candidate\": %llu, \"closed_form\": %llu, "
               "\"candidate_eq_baseline\": %s, \"closed_form_eq_baseline\": %s}%s\n",
               L, (unsigned long long)b, (unsigned long long)c, (unsigned long long)f,
               (c == b) ? "true" : "false", (f == b) ? "true" : "false",
               (L == LMAX_EQ) ? "" : ",");
    }
    printf("  ],\n");

    /* ---- gate Q: site-0 sector partition ---- */
    printf("  \"sectors\": [\n");
    for (int L = LMIN_EQ; L <= LMAX_EQ; ++L) {
        const uint64_t nstates = 1ull << L;
        uint64_t n0 = 0, n1 = 0, s0 = 0, s1 = 0;
        for (uint64_t s = 0; s < nstates; ++s) {
            if (site0(s, L) == 0) { n0++; s0 += (uint64_t)popcount64(s); }
            else                 { n1++; s1 += (uint64_t)popcount64(s); }
        }
        printf("    {\"L\": %d, \"sector0_states\": %llu, \"sector1_states\": %llu, "
               "\"sector_sizes_equal\": %s, \"sector0_occupancy\": %llu, "
               "\"sector1_occupancy\": %llu, \"sector_sum_equals_baseline\": %s}%s\n",
               L, (unsigned long long)n0, (unsigned long long)n1,
               (n0 == n1) ? "true" : "false",
               (unsigned long long)s0, (unsigned long long)s1,
               ((s0 + s1) == baseline_phi(L)) ? "true" : "false",
               (L == LMAX_EQ) ? "" : ",");
    }
    printf("  ],\n");

    /* ---- gate Q^-1: exact reconstruction ---- */
    printf("  \"reconstruction\": [\n");
    for (int L = 2; L <= LMAX_RECONSTRUCT; ++L) {
        uint64_t max_err = 0, rsum = 0;
        int ok = reconstruction_check(L, &max_err, &rsum);
        printf("    {\"L\": %d, \"bijection\": %s, \"max_reverse_error\": %llu, "
               "\"reconstructed_occupancy\": %llu, \"candidate\": %llu, "
               "\"matches_candidate\": %s}%s\n",
               L, ok ? "true" : "false", (unsigned long long)max_err,
               (unsigned long long)rsum, (unsigned long long)candidate_phi(L),
               (rsum == candidate_phi(L)) ? "true" : "false",
               (L == LMAX_RECONSTRUCT) ? "" : ",");
    }
    printf("  ],\n");

    /* ---- negative controls ---- */
    printf("  \"negative_controls\": [\n");
    {
        uint64_t b = baseline_phi(Ltimed), h = half_space_phi(Ltimed);
        printf("    {\"control\": \"half_space_two_admissible_states\", \"L\": %d, "
               "\"value\": %llu, \"baseline\": %llu, \"rejected\": %s},\n",
               Ltimed, (unsigned long long)h, (unsigned long long)b,
               (h != b) ? "true" : "false");
        uint64_t off = candidate_phi(Ltimed) + 1;
        printf("    {\"control\": \"candidate_off_by_one\", \"L\": %d, "
               "\"value\": %llu, \"baseline\": %llu, \"rejected\": %s},\n",
               Ltimed, (unsigned long long)off, (unsigned long long)b,
               (off != b) ? "true" : "false");
        uint64_t half = candidate_phi(Ltimed) / 2;
        printf("    {\"control\": \"half_the_sites\", \"L\": %d, "
               "\"value\": %llu, \"baseline\": %llu, \"rejected\": %s}\n",
               Ltimed, (unsigned long long)half, (unsigned long long)b,
               (half != b) ? "true" : "false");
    }
    printf("  ],\n");

    /* ---- gate X: timing ---- */
    printf("  \"timing\": {\n");
    printf("    \"clock\": \"CLOCK_MONOTONIC\",\n");
    printf("    \"baseline_ns\": [");
    for (int i = 0; i < repeats; ++i) {
        for (int w = 0; w < warmups; ++w) { g_sink += baseline_phi(Ltimed); }
        BARRIER();
        uint64_t t0 = now_ns();
        uint64_t v = baseline_phi(Ltimed);
        uint64_t t1 = now_ns();
        BARRIER();
        g_sink += v;
        printf("%s%llu", i ? ", " : "", (unsigned long long)(t1 - t0));
    }
    printf("],\n");
    printf("    \"candidate_direct_ns\": [");
    for (int i = 0; i < repeats; ++i) {
        for (int w = 0; w < warmups; ++w) { g_sink += candidate_phi(Ltimed); }
        BARRIER();
        uint64_t t0 = now_ns();
        uint64_t v = candidate_phi(Ltimed);
        uint64_t t1 = now_ns();
        BARRIER();
        g_sink += v;
        printf("%s%llu", i ? ", " : "", (unsigned long long)(t1 - t0));
    }
    printf("],\n");
    printf("    \"candidate_amortized_ns_per_call\": [");
    for (int i = 0; i < repeats; ++i) {
        for (int w = 0; w < warmups; ++w)
            for (int k = 0; k < batch; ++k) g_sink += candidate_phi(Ltimed);
        BARRIER();
        uint64_t t0 = now_ns();
        uint64_t acc = 0;
        for (int k = 0; k < batch; ++k) acc += candidate_phi(Ltimed);
        uint64_t t1 = now_ns();
        BARRIER();
        g_sink += acc;
        printf("%s%.4f", i ? ", " : "",
               (double)(t1 - t0) / (double)batch);
    }
    printf("]\n  },\n");

    json_u64("baseline_value_at_L", baseline_phi(Ltimed), 0);
    json_u64("candidate_value_at_L", candidate_phi(Ltimed), 0);
    json_u64("closed_form_value_at_L", closed_form_phi(Ltimed), 1);
    printf("}\n");
    return 0;
}
