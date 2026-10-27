/*
 * eigen_svd_cdouble_sve_dual — per-tier Eigen SVE complex BDCSVD extraction
 * for gem5-SE. Same-source mirror of the sdcshield test's payload:
 * tests/cpu/eigen_svd/svd_cdouble_sve_body.cpp + sandstone_eigen_common.h
 * (EigenSVDTest::calculate_once / run) and, since the P0-1 fix (2026-10-27),
 * the child-side joint-solver probe svd_vl<tier>::solve_once — the same
 * splitmix same-lineage fill ([-1,1), independent re/im; lineage contract
 * review #51) and the same BDCSVD<complex<double>> ComputeFullU|ComputeFullV
 * solve.
 *
 * Why a separate program rather than the sdcshield binary: that binary
 * cannot run under gem5-fi's ARM64 SE (pre-main page fault, prctl
 * unimplemented -> fatal; gem5-fi/findings.md F-SS-6). The project's
 * established substitute is a same-source extraction kernel (cf.
 * eigen_gemm_vl_dual.cpp and the *_dual.c family).
 *
 * Channel A (runtime reference, mirrors EigenSVDTest::run's same-source
 * repeat): solve the SAME matrix twice through the same Eigen SVD — the
 * two results must be byte-identical and every element finite. Channel B:
 * FNV-1a checksum over the U/V bytes (the FI oracle).
 *
 * The 1024-bit tier deliberately does not compile the payload: Eigen's SVE
 * complex ptranspose indexes buf[N][NC] with i < NC, only in bounds when
 * NC <= N (=4 here); at 1024-bit NC = 8 — a genuine OOB read upstream (GCC
 * -Warray-bounds, see tests/cpu/meson.build). The 1024 main() below
 * mirrors the sdcshield dispatcher's honest skip for that tier ("no
 * variant built"), so a --sve_vl 8 run reports the skip reason instead of
 * executing unsound code — same behaviour as the in-repo test.
 *
 * Build (one binary per tier):
 *   g++ -O2 -march=armv8.2-a+sve -msve-vector-bits=512 \
 *       -DEIGEN_ARM64_SVE_VL=512 -DEigen=EigenSVE512 -DEIGEN_ARM64_USE_SVE \
 *       -I<sdcshield>/third-party/eigen5 -o eigen_svd_cdouble_sve_vl512_dual \
 *       eigen_svd_cdouble_sve_dual.cpp
 *   gem5 ... --cmd workloads/sdcshield/eigen_svd_cdouble_sve_vl512_dual \
 *       --sve_vl 4
 *
 * Output contract (same as the other dual kernels):
 *   SDCSHIELD_FAILS=<n>     0 = clean
 *   <16 hex digits>         FNV-1a checksum of the decomposition (payload
 *                           tiers only; the 1024 skip prints no checksum)
 */
#if !defined(__ARM_FEATURE_SVE_BITS)
#  error "build with -msve-vector-bits=<bits> (size-specific SVE code)"
#endif
/* Tier via __ARM_FEATURE_SVE_BITS, not -DEIGEN_ARM64_SVE_VL: Eigen's
 * ConfigureVectorization.h redefines the latter to the former after the
 * include anyway, and the compiler-provided macro is authoritative. */

/* Same deprecation mute as sandstone_eigen_common.h (vendored Eigen5 marks
 * the (matrix, unsigned options) BDCSVD constructor deprecated; the repo
 * calls it that way and so does this mirror). */
#define EIGEN_NO_DEPRECATED_WARNING
#include <Eigen/Eigenvalues>
#include <Eigen/SVD>

#include <complex>
#include <cstdint>
#include <cstdio>
#include <cstring>

using namespace Eigen;
typedef Matrix<std::complex<double>, Dynamic, Dynamic> Mat;
typedef BDCSVD<Mat> SVD;

/* gem5-SE scale: complex BDCSVD is one to two orders heavier than the GEMM
 * extraction at the same n; 48 is the size the e2e precedent validated at
 * VL=512 in SE mode (scripts/eigen-sve-double/test_e2e_xd.cpp --mini). */
static constexpr int kDim = 48;
static constexpr int kRounds = 2;

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
 * svd_vl<tier>::solve_once (and the calibrated probe in
 * sandstone_eigen_common.h): full-rank random [-1,1) with independent
 * re/im, so BDCSVD takes the same code paths the sized run takes. */
static void fill(Mat &m)
{
    for (int r = 0; r < m.rows(); ++r)
        for (int c = 0; c < m.cols(); ++c) {
            std::uint64_t h = (std::uint64_t)r * 0x9E3779B97F4A7C15ull
                            ^ (std::uint64_t)c * 0xC2B2AE3D27D4EB4Full;
            h ^= h >> 32;
            h *= 0xD6E8FEB86659FD93ull;
            h ^= h >> 32;
            std::uint64_t h2 = h * 0xD6E8FEB86659FD93ull
                             + 0x9E3779B97F4A7C15ull;
            h2 ^= h2 >> 32;
            m(r, c) = std::complex<double>(
                (double)(h % 2000u) / 1000.0 - 1.0,
                (double)(h2 % 2000u) / 1000.0 - 1.0);
        }
}

/* calculate_once, verbatim semantics. */
static void solve(const Mat &m, Mat &u, Mat &v)
{
    SVD fullSvd(m, ComputeFullU | ComputeFullV);
    u = fullSvd.matrixU();
    v = fullSvd.matrixV();
}

#if __ARM_FEATURE_SVE_BITS == 1024
int main()
{
    /* Mirror of the sdcshield dispatcher's honest 1024-bit skip
     * (tests/cpu/eigen_svd/svd_cdouble_sve.cpp): the complex payload is
     * not built for this tier, so nothing unsound executes. */
    printf("vl=%d\n", __ARM_FEATURE_SVE_BITS);
    printf("SKIP: 1024-bit Eigen complex packets are unsound upstream "
           "(SVE ptranspose reads past buf[N][NC] when NC > N); "
           "no variant built for this tier\n");
    printf("SDCSHIELD_FAILS=0\n");
    return 0;
}
#else
int main()
{
    printf("dim=%d rounds=%d vl=%d\n", kDim, kRounds, __ARM_FEATURE_SVE_BITS);
    int fails = 0;
    uint64_t sum = 0;
    for (int round = 0; round < kRounds; ++round) {
        Mat m(kDim, kDim);
        fill(m);
        Mat u1, v1, u2, v2;
        solve(m, u1, v1);
        solve(m, u2, v2);       /* same-source repeat: must be byte-identical */

        const size_t bytes = (size_t)kDim * kDim * sizeof(std::complex<double>);
        if (std::memcmp(u1.data(), u2.data(), bytes) != 0
                || std::memcmp(v1.data(), v2.data(), bytes) != 0) {
            ++fails;
            if (fails <= 4)
                printf("REPEAT-MISMATCH round=%d\n", round);
        }
        for (size_t i = 0; i < bytes / sizeof(double); ++i) {
            double x = reinterpret_cast<const double *>(u1.data())[i];
            double y = reinterpret_cast<const double *>(v1.data())[i];
            if (x != x || x > 1.0e300 || x < -1.0e300
                    || y != y || y > 1.0e300 || y < -1.0e300) {
                ++fails;
                if (fails <= 4)
                    printf("NON-FINITE round=%d i=%zu\n", round, i);
            }
        }
        sum = fnv1a(u1.data(), bytes, sum);
        sum = fnv1a(v1.data(), bytes, sum);
    }
    printf("SDCSHIELD_FAILS=%d\n", fails);
    printf("%016llx\n", (unsigned long long)sum);
    return fails ? 1 : 0;
}
#endif
