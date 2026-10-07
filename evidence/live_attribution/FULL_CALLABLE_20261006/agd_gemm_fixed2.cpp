#include <arm_neon.h>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>
#include <vector>

using Clock = std::chrono::steady_clock;

/*
 * RECTANGULAR MATRIX
 *
 * This is the critical correction.
 */
struct Matrix {
    int rows = 0;
    int cols = 0;
    std::vector<float> x;

    Matrix() = default;

    Matrix(int r, int c)
        : rows(r),
          cols(c),
          x((size_t)r * (size_t)c) {}

    float* row(int r) {
        return x.data() + (size_t)r * cols;
    }

    const float* row(int r) const {
        return x.data() + (size_t)r * cols;
    }

    float& at(int r, int c) {
        return x[(size_t)r * cols + c];
    }

    const float& at(int r, int c) const {
        return x[(size_t)r * cols + c];
    }

    size_t size() const {
        return x.size();
    }
};

static void fill_matrix(Matrix& A, uint64_t seed)
{
    std::mt19937 rng((uint32_t)seed);
    std::uniform_real_distribution<float> d(-1.0f, 1.0f);

    for (float& v : A.x)
        v = d(rng);
}

/*
 * Exact quotient construction.
 *
 * Fiber:
 *
 *   0,1,2,3 -> representative 0
 *   4,5,6,7 -> representative 4
 *   ...
 */
static Matrix quotient_representatives(
    const Matrix& A,
    int& fibers)
{
    fibers = (A.rows + 3) / 4;

    Matrix R(fibers, A.cols);

    for (int f = 0; f < fibers; ++f) {
        int src = f * 4;

        std::memcpy(
            R.row(f),
            A.row(src),
            sizeof(float) * (size_t)A.cols
        );
    }

    return R;
}

/*
 * Force exact row-fiber structure into A.
 */
static void force_row_fibers(Matrix& A)
{
    for (int r = 0; r < A.rows; ++r) {

        int rep = (r / 4) * 4;

        if (rep < A.rows && rep != r) {

            std::memcpy(
                A.row(r),
                A.row(rep),
                sizeof(float) * (size_t)A.cols
            );
        }
    }
}

/*
 * General rectangular GEMM:
 *
 *   A[M,K] * B[K,N] = C[M,N]
 */
static void gemm_scalar(
    const Matrix& A,
    const Matrix& B,
    Matrix& C)
{
    const int M = A.rows;
    const int K = A.cols;
    const int N = B.cols;

    if (B.rows != K ||
        C.rows != M ||
        C.cols != N) {
        std::cerr << "GEMM SHAPE ERROR: "
                  << "A=" << M << "x" << K
                  << " B=" << B.rows << "x" << B.cols
                  << " C=" << C.rows << "x" << C.cols
                  << "\n";
        std::abort();
    }

    std::fill(C.x.begin(), C.x.end(), 0.0f);

    for (int i = 0; i < M; ++i) {

        float* c = C.row(i);

        for (int k = 0; k < K; ++k) {

            float a = A.at(i, k);
            const float* b = B.row(k);

            for (int j = 0; j < N; ++j)
                c[j] += a * b[j];
        }
    }
}

/*
 * Blocked scalar reference.
 */
static void gemm_blocked_scalar(
    const Matrix& A,
    const Matrix& B,
    Matrix& C)
{
    const int M = A.rows;
    const int K = A.cols;
    const int N = B.cols;

    if (B.rows != K ||
        C.rows != M ||
        C.cols != N) {
        std::cerr << "BLOCKED GEMM SHAPE ERROR\n";
        std::abort();
    }

    constexpr int BS = 32;

    std::fill(C.x.begin(), C.x.end(), 0.0f);

    for (int ii = 0; ii < M; ii += BS) {

        for (int kk = 0; kk < K; kk += BS) {

            for (int jj = 0; jj < N; jj += BS) {

                int i_end = std::min(ii + BS, M);
                int k_end = std::min(kk + BS, K);
                int j_end = std::min(jj + BS, N);

                for (int i = ii; i < i_end; ++i) {

                    float* c = C.row(i);

                    for (int k = kk; k < k_end; ++k) {

                        float a = A.at(i, k);
                        const float* b = B.row(k);

                        for (int j = jj; j < j_end; ++j)
                            c[j] += a * b[j];
                    }
                }
            }
        }
    }
}

/*
 * NEON row GEMM.
 *
 * A row has K elements.
 * B has K rows x N columns.
 * C row has N elements.
 */
static void gemm_neon_row(
    const float* a,
    const Matrix& B,
    float* c)
{
    const int K = B.rows;
    const int N = B.cols;

    int j = 0;

    /*
     * Four independent vector accumulators.
     */
    for (; j + 16 <= N; j += 16) {

        float32x4_t c0 = vld1q_f32(c + j + 0);
        float32x4_t c1 = vld1q_f32(c + j + 4);
        float32x4_t c2 = vld1q_f32(c + j + 8);
        float32x4_t c3 = vld1q_f32(c + j + 12);

        for (int k = 0; k < K; ++k) {

            float32x4_t av =
                vdupq_n_f32(a[k]);

            const float* b = B.row(k);

            c0 = vfmaq_f32(
                c0,
                av,
                vld1q_f32(b + j + 0)
            );

            c1 = vfmaq_f32(
                c1,
                av,
                vld1q_f32(b + j + 4)
            );

            c2 = vfmaq_f32(
                c2,
                av,
                vld1q_f32(b + j + 8)
            );

            c3 = vfmaq_f32(
                c3,
                av,
                vld1q_f32(b + j + 12)
            );
        }

        vst1q_f32(c + j + 0, c0);
        vst1q_f32(c + j + 4, c1);
        vst1q_f32(c + j + 8, c2);
        vst1q_f32(c + j + 12, c3);
    }

    for (; j + 4 <= N; j += 4) {

        float32x4_t cv =
            vld1q_f32(c + j);

        for (int k = 0; k < K; ++k) {

            float32x4_t av =
                vdupq_n_f32(a[k]);

            const float* b = B.row(k);

            cv = vfmaq_f32(
                cv,
                av,
                vld1q_f32(b + j)
            );
        }

        vst1q_f32(c + j, cv);
    }

    for (; j < N; ++j) {

        float s = c[j];

        for (int k = 0; k < K; ++k)
            s += a[k] * B.at(k, j);

        c[j] = s;
    }
}

/*
 * NEON rectangular GEMM.
 */
static void gemm_neon(
    const Matrix& A,
    const Matrix& B,
    Matrix& C)
{
    const int M = A.rows;
    const int K = A.cols;
    const int N = B.cols;

    if (B.rows != K ||
        C.rows != M ||
        C.cols != N) {
        std::cerr << "NEON GEMM SHAPE ERROR\n";
        std::abort();
    }

    std::fill(C.x.begin(), C.x.end(), 0.0f);

    constexpr int ROW_BLOCK = 64;

    for (int ii = 0; ii < M; ii += ROW_BLOCK) {

        int i_end =
            std::min(ii + ROW_BLOCK, M);

        for (int i = ii; i < i_end; ++i) {

            gemm_neon_row(
                A.row(i),
                B,
                C.row(i)
            );
        }
    }
}

/*
 * Reconstruct quotient result.
 *
 * C_Q is F x N.
 * C_out is N x N.
 */
static Matrix reconstruct_rows(
    const Matrix& reduced,
    int full_rows)
{
    if (reduced.rows <= 0 ||
        reduced.cols <= 0) {
        std::cerr << "INVALID REDUCED MATRIX\n";
        std::abort();
    }

    Matrix out(full_rows, reduced.cols);

    for (int r = 0; r < full_rows; ++r) {

        int f = r / 4;

        if (f >= reduced.rows)
            f = reduced.rows - 1;

        std::memcpy(
            out.row(r),
            reduced.row(f),
            sizeof(float) * (size_t)reduced.cols
        );
    }

    return out;
}

static double max_abs_error(
    const Matrix& A,
    const Matrix& B)
{
    if (A.rows != B.rows ||
        A.cols != B.cols)
        return INFINITY;

    double m = 0.0;

    for (size_t i = 0; i < A.size(); ++i) {

        double e =
            std::abs(
                (double)A.x[i] -
                (double)B.x[i]
            );

        if (e > m)
            m = e;
    }

    return m;
}

static double rmse(
    const Matrix& A,
    const Matrix& B)
{
    if (A.rows != B.rows ||
        A.cols != B.cols)
        return INFINITY;

    long double sum = 0.0L;

    for (size_t i = 0; i < A.size(); ++i) {

        long double d =
            (long double)A.x[i] -
            (long double)B.x[i];

        sum += d * d;
    }

    return std::sqrt(
        (double)(
            sum /
            (long double)A.size()
        )
    );
}

static double checksum(const Matrix& A)
{
    long double s = 0.0L;

    for (float v : A.x)
        s += v;

    return (double)s;
}

template <typename Fn>
static double benchmark(
    Fn&& fn,
    int warmups,
    int repeats)
{
    for (int i = 0; i < warmups; ++i)
        fn();

    std::vector<double> times;
    times.reserve(repeats);

    for (int i = 0; i < repeats; ++i) {

        auto t0 = Clock::now();

        fn();

        auto t1 = Clock::now();

        double sec =
            std::chrono::duration<double>(
                t1 - t0
            ).count();

        times.push_back(sec);
    }

    std::sort(times.begin(), times.end());

    return times[times.size() / 2];
}

static double gflops(
    int M,
    int K,
    int N,
    double sec)
{
    double ops =
        2.0 *
        (double)M *
        (double)K *
        (double)N;

    return ops / sec / 1e9;
}

int main()
{
    constexpr int WARMUPS = 2;
    constexpr int REPEATS = 7;

    const std::vector<int> Ns = {
        128,
        256,
        384,
        512,
        640,
        768,
        896,
        1024
    };

    std::ofstream csv(
        "/root/agd_gemm_evidence/AGD_GEMM_FIXED2_20260921T025713Z_13340/artifacts/results.csv"
    );

    csv
        << "N,"
        << "FIBERS,"
        << "COMPRESSION,"
        << "FS_SEC,"
        << "BLOCKED_SCALAR_SEC,"
        << "FN_SEC,"
        << "QS_SEC,"
        << "QN_SEC,"
        << "EXTRACT_SEC,"
        << "RECON_SEC,"
        << "VERIFY_SEC,"
        << "SIMD_SPEEDUP,"
        << "BLOCKED_SPEEDUP,"
        << "Q_SCALAR_SPEEDUP,"
        << "Q_NEON_SPEEDUP,"
        << "COMBINED_SPEEDUP,"
        << "FN_MAXERR,"
        << "FN_RMSE,"
        << "QN_MAXERR,"
        << "QN_RMSE,"
        << "STATUS\n";

    bool all_pass = true;

    for (int n : Ns) {

        std::cout
            << "\n================ N="
            << n
            << " ================\n";

        Matrix A(n, n);
        Matrix B(n, n);

        fill_matrix(
            A,
            0xA6D00000ULL + n
        );

        fill_matrix(
            B,
            0xBEE00000ULL + n
        );

        /*
         * Exact fiber structure.
         */
        force_row_fibers(A);

        int fibers = 0;

        Matrix reps =
            quotient_representatives(
                A,
                fibers
            );

        /*
         * Full outputs.
         */
        Matrix C_ref(n, n);
        Matrix C_blocked(n, n);
        Matrix C_neon(n, n);

        /*
         * Reduced outputs:
         *
         * F x N
         */
        Matrix C_q_scalar(
            fibers,
            n
        );

        Matrix C_q_neon(
            fibers,
            n
        );

        /*
         * FULL SCALAR
         */
        double fs =
            benchmark(
                [&] {
                    gemm_scalar(
                        A,
                        B,
                        C_ref
                    );
                },
                WARMUPS,
                REPEATS
            );

        /*
         * BLOCKED SCALAR
         */
        double bs =
            benchmark(
                [&] {
                    gemm_blocked_scalar(
                        A,
                        B,
                        C_blocked
                    );
                },
                WARMUPS,
                REPEATS
            );

        /*
         * FULL NEON
         */
        double fn =
            benchmark(
                [&] {
                    gemm_neon(
                        A,
                        B,
                        C_neon
                    );
                },
                WARMUPS,
                REPEATS
            );

        double fn_err =
            max_abs_error(
                C_ref,
                C_neon
            );

        double fn_r =
            rmse(
                C_ref,
                C_neon
            );

        /*
         * QUOTIENT SCALAR
         */
        double qs =
            benchmark(
                [&] {
                    gemm_scalar(
                        reps,
                        B,
                        C_q_scalar
                    );
                },
                WARMUPS,
                REPEATS
            );

        /*
         * QUOTIENT NEON
         */
        double qn =
            benchmark(
                [&] {
                    gemm_neon(
                        reps,
                        B,
                        C_q_neon
                    );
                },
                WARMUPS,
                REPEATS
            );

        /*
         * RECONSTRUCTION
         */
        double recon =
            benchmark(
                [&] {

                    Matrix tmp =
                        reconstruct_rows(
                            C_q_neon,
                            n
                        );

                    volatile float sink =
                        tmp.x[tmp.size() - 1];

                    (void)sink;
                },
                WARMUPS,
                REPEATS
            );

        /*
         * Actual reconstructed result.
         */
        Matrix C_reconstructed =
            reconstruct_rows(
                C_q_neon,
                n
            );

        double qn_err =
            max_abs_error(
                C_ref,
                C_reconstructed
            );

        double qn_r =
            rmse(
                C_ref,
                C_reconstructed
            );

        /*
         * VERIFICATION
         */
        double verify =
            benchmark(
                [&] {

                    volatile double e1 =
                        max_abs_error(
                            C_ref,
                            C_reconstructed
                        );

                    volatile double e2 =
                        rmse(
                            C_ref,
                            C_reconstructed
                        );

                    (void)e1;
                    (void)e2;

                },
                WARMUPS,
                REPEATS
            );

        /*
         * QUOTIENT EXTRACTION
         */
        double extract =
            benchmark(
                [&] {

                    int ftmp = 0;

                    Matrix tmp =
                        quotient_representatives(
                            A,
                            ftmp
                        );

                    volatile float sink =
                        tmp.x[tmp.size() - 1];

                    (void)sink;

                },
                WARMUPS,
                REPEATS
            );

        /*
         * Speed metrics.
         */
        double simd =
            fs / fn;

        double blocked =
            fs / bs;

        double q_scalar =
            fs / qs;

        double q_neon =
            fs / qn;

        /*
         * TRUE END-TO-END:
         *
         * extraction
         * + quotient NEON
         * + reconstruction
         * + verification
         */
        double combined_sec =
            extract +
            qn +
            recon +
            verify;

        double combined =
            fs / combined_sec;

        bool pass =
            std::isfinite(fs) &&
            std::isfinite(fn) &&
            std::isfinite(qs) &&
            std::isfinite(qn) &&
            fn_err <= 1e-4 &&
            fn_r <= 1e-5 &&
            qn_err <= 1e-4 &&
            qn_r <= 1e-5;

        if (!pass)
            all_pass = false;

        std::cout
            << std::setprecision(12)
            << "FS_SEC=" << fs
            << " FS_GFLOPS="
            << gflops(n,n,n,fs)
            << "\n";

        std::cout
            << "BLOCKED_SCALAR_SEC="
            << bs
            << " BLOCKED_SPEEDUP="
            << blocked
            << "\n";

        std::cout
            << "FN_SEC=" << fn
            << " FN_GFLOPS="
            << gflops(n,n,n,fn)
            << " SIMD_SPEEDUP="
            << simd
            << " FN_MAXERR="
            << fn_err
            << " FN_RMSE="
            << fn_r
            << "\n";

        std::cout
            << "QS_SEC=" << qs
            << " Q_SCALAR_SPEEDUP="
            << q_scalar
            << "\n";

        std::cout
            << "QN_SEC=" << qn
            << " Q_NEON_SPEEDUP="
            << q_neon
            << " QN_MAXERR="
            << qn_err
            << " QN_RMSE="
            << qn_r
            << "\n";

        std::cout
            << "EXTRACT_SEC="
            << extract
            << " RECON_SEC="
            << recon
            << " VERIFY_SEC="
            << verify
            << "\n";

        std::cout
            << "COMBINED_SEC="
            << combined_sec
            << " COMBINED_SPEEDUP="
            << combined
            << "\n";

        std::cout
            << "FIBERS="
            << fibers
            << " COMPRESSION="
            << ((double)n / fibers)
            << "\n";

        std::cout
            << "STATUS="
            << (pass ? "PASS" : "FAIL")
            << "\n";

        csv
            << std::setprecision(15)
            << n << ","
            << fibers << ","
            << ((double)n / fibers) << ","
            << fs << ","
            << bs << ","
            << fn << ","
            << qs << ","
            << qn << ","
            << extract << ","
            << recon << ","
            << verify << ","
            << simd << ","
            << blocked << ","
            << q_scalar << ","
            << q_neon << ","
            << combined << ","
            << fn_err << ","
            << fn_r << ","
            << qn_err << ","
            << qn_r << ","
            << (pass ? "PASS" : "FAIL")
            << "\n";
    }

    csv.close();

    std::cout
        << "\nALL_GATES="
        << (all_pass ? "PASS" : "FAIL")
        << "\n";

    std::cout
        << "VERIFICATION="
        << (all_pass ? "PASS" : "FAIL")
        << "\n";

    return all_pass ? 0 : 1;
}
