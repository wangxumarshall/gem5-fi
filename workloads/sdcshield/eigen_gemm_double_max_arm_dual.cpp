/*
 * eigen_gemm_double_max_arm_dual — per-tier Eigen SVE GEMM extraction for
 * gem5-SE. Same-source mirror of the sdcshield test's payload:
 * tests/cpu/eigen_gemm/gemm_double_max_arm_body.cpp (run_body's fill ->
 * prime product -> repeat multiply -> byte-exact memcmp loop) and, since
 * the T6 fix (2026-10-28), the child-side joint-solver probe
 * gemm_vl<tier>::solve_once — the same splitmix same-lineage fill
 * ([-1,1); lineage contract review #51, same hash chain) and the same
 * dynamic-square double GEMM through Eigen's SVE packet backend.
 *
 * Why a separate program rather than the sdcshield binary: that binary
 * cannot run under gem5-fi's ARM64 SE (pre-main page fault, prctl
 * unimplemented -> fatal, signal syscalls ignored; gem5-fi/findings.md
 * F-SS-6). The project's established substitute is a same-source
 * extraction kernel (cf. eigen_svd_cdouble_sve_dual.cpp and the *_dual.c
 * family).
 *
 * Channel A (runtime reference, mirrors run_body's golden-recompute +
 * memcmp_or_fail): the SAME product is computed twice through the same
 * Eigen SVE GEMM — the two results must be byte-identical (deterministic
 * same-order computation; the sdcshield run loop's exact oracle) and
 * every element finite (|sum| <= kDim because every fill value is in
 * [-1,1)). Channel B: FNV-1a checksum over the product bytes (the FI
 * oracle).
 *
 * Unlike the complex SVD pair, the 1024-bit tier IS built: the real
 * (non-complex) GEMM packets have no ptranspose defect, so all of
 * 256/512/1024 execute the real payload (the sdcshield test compiles and
 * dispatches this payload at every tier).
 *
 * Build (one binary per tier):
 *   g++ -O2 -march=armv8.2-a+sve -msve-vector-bits=512 \
 *       -DEIGEN_ARM64_SVE_VL=512 -DEigen=EigenSVE512 -DEIGEN_ARM64_USE_SVE \
 *       -I<sdcshield>/third-party/eigen5 \
 *       -o eigen_gemm_double_max_arm_vl512_dual \
 *       eigen_gemm_double_max_arm_dual.cpp
 * (dynamic, like eigen_svd_cdouble_sve_vl512_dual: this host has no static
 * libstdc++; gem5-SE runs the dynamic ELF fine)
 *   gem5 ... --cmd workloads/sdcshield/eigen_gemm_double_max_arm_vl512_dual \
 *       --sve_vl 4
 *
 * Output contract (same as the other dual kernels):
 *   SDCSHIELD_FAILS=<n>     0 = clean
 *   <16 hex digits>         FNV-1a checksum of the products
 */
#if !defined(__ARM_FEATURE_SVE_BITS)
#  error "build with -msve-vector-bits=<bits> (size-specific SVE code)"
#endif
/* Tier via __ARM_FEATURE_SVE_BITS, not -DEIGEN_ARM64_SVE_VL: Eigen's
 * ConfigureVectorization.h redefines the latter to the former after the
 * include anyway, and the compiler-provided macro is authoritative. */

#include <Eigen/Core>

#include <cstdint>
#include <cstdio>
#include <cstring>

using namespace Eigen;
typedef Matrix<double, Dynamic, Dynamic> Mat;

/* gem5-SE scale: 96 doubles = 768 B rows, packet-friendly at every tier
 * built (12 x 64 B at 512-bit, 6 lanes at 1024-bit); same size class as
 * the pre-existing eigen_gemm_vl_dual extraction. */
static constexpr int kDim = 96;
static constexpr int kRounds = 3;

static uint64_t fnv1a(const void *p, size_t n, uint64_t h = 1469598103934665603ULL)
{
    const uint8_t *b = static_cast<const uint8_t *>(p);
    for (size_t i = 0; i < n; ++i) {
        h ^= b[i];
        h *= 1099511628211ULL;
    }
    return h;
}

/* Splitmix same-lineage fill — byte-for-byte the same hash chain as
 * gemm_vl<tier>::solve_once (tests/cpu/eigen_gemm/gemm_double_max_arm_
 * body.cpp): two INDEPENDENT streams (a from h, b from the h2 round) of
 * uniform random [-1,1), the same distribution run_body's fill_rand
 * draws, so the sized run and this mirror take the same GEMM code paths
 * with independent operands.
 */
static void fill_pair(Mat &a, Mat &b)
{
    for (int r = 0; r < a.rows(); ++r)
        for (int c = 0; c < a.cols(); ++c) {
            std::uint64_t h = (std::uint64_t)r * 0x9E3779B97F4A7C15ull
                            ^ (std::uint64_t)c * 0xC2B2AE3D27D4EB4Full;
            h ^= h >> 32;
            h *= 0xD6E8FEB86659FD93ull;
            h ^= h >> 32;
            std::uint64_t h2 = h * 0xD6E8FEB86659FD93ull
                             + 0x9E3779B97F4A7C15ull;
            h2 ^= h2 >> 32;
            a(r, c) = (double)(h % 2000u) / 1000.0 - 1.0;
            b(r, c) = (double)(h2 % 2000u) / 1000.0 - 1.0;
        }
}

int main()
{
    printf("dim=%d rounds=%d vl=%d\n", kDim, kRounds, __ARM_FEATURE_SVE_BITS);
    int fails = 0;
    uint64_t sum = 0;
    const size_t bytes = (size_t)kDim * kDim * sizeof(double);
    for (int round = 0; round < kRounds; ++round) {
        Mat a(kDim, kDim), b(kDim, kDim);
        fill_pair(a, b);
        Mat golden = a * b;     /* prime, mirrors run_body's l_prod */
        Mat x = a * b;          /* same-source repeat: must be byte-identical */

        if (std::memcmp(x.data(), golden.data(), bytes) != 0) {
            ++fails;
            if (fails <= 4)
                printf("REPEAT-MISMATCH round=%d\n", round);
        }
        for (size_t i = 0; i < bytes / sizeof(double); ++i) {
            double v = x.data()[i];
            if (v != v || v > kDim || v < -kDim) {    /* |sum| <= kDim·1·1 */
                ++fails;
                if (fails <= 4)
                    printf("NON-FINITE round=%d i=%zu\n", round, i);
            }
        }
        sum = fnv1a(x.data(), bytes, sum);
    }
    printf("SDCSHIELD_FAILS=%d\n", fails);
    printf("%016llx\n", (unsigned long long)sum);
    return fails ? 1 : 0;
}
