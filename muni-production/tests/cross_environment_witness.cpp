#include "kernel.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <vector>

static std::uint64_t fnv1a(const double* p, std::size_t n) {
  const auto* b = reinterpret_cast<const unsigned char*>(p);
  std::uint64_t h = 14695981039346656037ULL;
  for (std::size_t i = 0; i < n * sizeof(double); ++i) {
    h ^= b[i];
    h *= 1099511628211ULL;
  }
  return h;
}

int main() {
  constexpr std::size_t d = 4096, m = 64, r = d / m, steps = 256;
  std::vector<double> U(r*r), x(d), full(d), fast(d);
  for (std::size_t i = 0; i < r*r; ++i) {
    const int v = static_cast<int>((i * 17 + 13) % 101) - 50;
    U[i] = static_cast<double>(v) / 1024.0;
  }
  for (std::size_t b = 0; b < r; ++b) {
    const double v = static_cast<double>((b % 17) + 1) / 32.0;
    for (std::size_t j = 0; j < m; ++j) x[b*m+j] = v;
  }

  int used = 0;
  double err = INFINITY, residual = INFINITY;
  const int status = munirun(U.data(), r, m, x.data(), steps,
                             full.data(), fast.data(), &used, &err,
                             &residual, 0.0);
  const bool exact = std::memcmp(full.data(), fast.data(), d*sizeof(double)) == 0;
  std::cout << std::setprecision(12)
            << "WITNESS=AGD_MUNI_CROSS_ENVIRONMENT\n"
            << "arch=" << (sizeof(void*) == 8 ? "64-bit" : "other") << "\n"
            << "d=" << d << " m=" << m << " r=" << r << " steps=" << steps << "\n"
            << "status=" << status << " used_quotient=" << used << "\n"
            << "max_abs_error=" << err << " residual=" << residual << "\n"
            << "full_output_fnv1a64=" << fnv1a(full.data(), d) << "\n"
            << "fast_output_fnv1a64=" << fnv1a(fast.data(), d) << "\n"
            << "bitwise_equal=" << (exact ? "PASS" : "FAIL") << "\n";
  if (status != MUNI_OK_QUOTIENT || used != 1 || err != 0.0 ||
      residual != 0.0 || !exact) {
    std::cerr << "CROSS_ENVIRONMENT_EXACTNESS_GATE=FAIL\n";
    return 10;
  }

  double base_ms=0, opt_ms=0, speedup=0, bench_err=INFINITY;
  int bench_used=0;
  const int bench_status = munibench(U.data(), r, m, x.data(), steps, 5, 3, 0.0,
                                     &base_ms, &opt_ms, &speedup,
                                     &bench_err, &bench_used);
  std::cout << "benchmark_status=" << bench_status
            << " baseline_ms=" << base_ms
            << " quotient_e2e_ms=" << opt_ms
            << " speedup=" << speedup
            << " benchmark_error=" << bench_err
            << " benchmark_used_quotient=" << bench_used << "\n";
  if (bench_status != MUNI_OK_QUOTIENT || bench_used != 1 || bench_err != 0.0 ||
      !(base_ms > 0.0) || !(opt_ms > 0.0) || !std::isfinite(speedup)) {
    std::cerr << "CROSS_ENVIRONMENT_BENCHMARK_GATE=FAIL\n";
    return 11;
  }

  // Adversarial negative control: violate the invariant and require exact fallback.
  x[m/2] += 1.0;
  int fallback_used=1;
  double fallback_err=INFINITY, fallback_residual=0.0;
  const int fallback_status = munirun(U.data(), r, m, x.data(), steps,
                                      full.data(), fast.data(), &fallback_used,
                                      &fallback_err, &fallback_residual, 0.0);
  const bool fallback_exact =
      std::memcmp(full.data(), fast.data(), d*sizeof(double)) == 0;
  std::cout << "inadmissible_status=" << fallback_status
            << " fallback_used_quotient=" << fallback_used
            << " fallback_error=" << fallback_err
            << " fallback_bitwise_equal=" << (fallback_exact ? "PASS" : "FAIL")
            << "\n";
  if (fallback_status != MUNI_OK_FALLBACK || fallback_used != 0 ||
      fallback_err != 0.0 || !fallback_exact) {
    std::cerr << "CROSS_ENVIRONMENT_FALLBACK_GATE=FAIL\n";
    return 12;
  }

  std::cout << "CROSS_ENVIRONMENT_EXACTNESS_GATE=PASS\n"
            << "CROSS_ENVIRONMENT_BENCHMARK_GATE=PASS (timing informational only)\n"
            << "CROSS_ENVIRONMENT_FALLBACK_GATE=PASS\n"
            << "CROSS_ENVIRONMENT=PASS\n";
  return 0;
}
