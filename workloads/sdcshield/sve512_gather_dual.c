/* sve512_gather_dual.c — cluster-B dual kernel for the all-VL Phase 2 P3
 * rework of the sve512 gather/scatter family (sve512_gather_scatter_{arm,
 * svd}, sve512_xlswave_ctx Phase B). Two modes per run.
 *
 * Same-source mirrors (the tests use sizeless SVE intrinsics; so does
 * this kernel):
 *   1d_tag   — gather_scatter_arm's u64index variant shape: a
 *              Fisher-Yates permutation of gn = 64*lanes indices, an
 *              index-tagged source table (low 20 mantissa bits carry the
 *              source index), svld1_gather_u64index_f64, an exact
 *              doubling svmla, svst1_scatter_u64index, and the
 *              read-offset tag assertion (gathered value's tag must
 *              equal its lane's index).
 *   2d_block — gather_scatter_svd's shape: a FIXED 300*300 = 90000
 *              workspace (VL-independent by design), flat
 *              gather/FMA/scatter walk with svwhilelt_b64 tail handling
 *              (90000 is not divisible by every runtime lane count) and
 *              an init-time scalar golden. The 2-D block permutation
 *              topology is the test's C++ addressing layer; this kernel
 *              validates the SVE surface and the tail predicate.
 *
 * All arithmetic is exact (doubling / integer-valued 1.5x), so hardware
 * and scalar golden agree bit-for-bit by construction.
 *
 * Channels: A = byte-exact buffer compare + tag assertion;
 *           B = FNV-1a over the destination buffer bits.
 * argv: [fixed|random] [seed]; exit 0 / 1 (fails) / 3 (unsupported VL).
 * Build: gcc -static -O2 -march=armv9-a+sve -Wall -Wextra
 * Run:   gem5.opt configs/se/arm_chaos.py --cpu O3 --cmd \
 *          workloads/sdcshield/sve512_gather_dual --sve_vl 4 \
 *          --workload_args "fixed 1"
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <arm_sve.h>

#define LMAX     16     /* 1024-bit cap: 16 f64 lanes */
#define N2D      (300 * 300)   /* the _svd workspace (VL-independent) */
#define ROUNDS_1D 2

static uint32_t xs_state;
static uint32_t xs32(void)
{
    xs_state ^= xs_state << 13;
    xs_state ^= xs_state >> 17;
    xs_state ^= xs_state << 5;
    return xs_state;
}

static unsigned g_fails = 0;
static uint64_t fnv = 1469598103934665603ULL;
static void fnv_bits(const void *p, size_t n)
{
    const unsigned char *b = p;
    for (size_t i = 0; i < n; ++i) {
        fnv ^= b[i];
        fnv *= 1099511628211ULL;
    }
}

static uint64_t f64_bits(double v)
{
    uint64_t b;
    memcpy(&b, &v, 8);
    return b;
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "fixed";
    const uint32_t seed = (argc > 2) ? (uint32_t)strtoul(argv[2], 0, 0) : 1;
    const int randomize = (strcmp(mode, "random") == 0);
    xs_state = seed ? seed : 1;

    const int lanes = (int)svcntd();
    if (lanes < 2 || lanes > LMAX) {
        fprintf(stderr, "unsupported VL (f64 lanes %d)\n", lanes);
        return 3;
    }

    /* ---------------- mode: 1d_tag ---------------- */
    {
        const int gn = 64 * lanes;
        static double src[64 * LMAX], dst[64 * LMAX], golden[64 * LMAX];
        static uint64_t perm[64 * LMAX];
        const svbool_t pg = svptrue_b64();
        unsigned fails = 0;

        for (int i = 0; i < gn; ++i) {
            /* value ~= 1.0, low 20 mantissa bits = i (the tag) */
            uint64_t b = 0x3FF0000000000000ULL | (uint64_t)i;
            memcpy(&src[i], &b, 8);
            perm[i] = (uint64_t)i;
        }
        for (int round = 0; round < ROUNDS_1D; ++round) {
            if (randomize) {          /* Fisher-Yates */
                for (int i = gn - 1; i > 0; --i) {
                    int j = (int)(xs32() % (uint32_t)(i + 1));
                    uint64_t t = perm[i];
                    perm[i] = perm[j];
                    perm[j] = t;
                }
            } else {                  /* deterministic rotate-by-prime */
                for (int i = 0; i < gn; ++i)
                    perm[i] = (uint64_t)((i * 131 + round * 7) % gn);
            }
            for (int i = 0; i < gn; ++i) {
                uint64_t b = 0x4000000000000000ULL | perm[i]; /* 2*src */
                memcpy(&golden[perm[i]], &b, 8);
                dst[i] = -1.0;
            }

            for (int off = 0; off < gn; off += lanes) {
                const svuint64_t idx = svld1_u64(pg, perm + off);
                const svfloat64_t g =
                    svld1_gather_u64index_f64(pg, src, idx);
                /* read-offset assertion (SEVI 76% wrong-offset-read
                   semantics): each lane's tag must equal its index. */
                double gathered[LMAX];
                svst1_f64(pg, gathered, g);
                for (int r = 0; r < lanes; ++r)
                    if ((f64_bits(gathered[r]) & 0xFFFFFULL) != perm[off + r]) {
                        if (fails < 4)
                            fprintf(stderr, "1d_tag tag @off+%d lane tag=%llu "
                                    "idx=%llu\n", r,
                                    (unsigned long long)(f64_bits(gathered[r])
                                                         & 0xFFFFFULL),
                                    (unsigned long long)perm[off + r]);
                        ++fails;
                    }
                const svfloat64_t out =
                    svmla_f64_x(pg, g, g, svdup_f64(1.0));   /* 2g */
                svst1_scatter_u64index_f64(pg, dst, idx, out);
            }

            /* tag assertion + golden compare, scalar side */
            for (int i = 0; i < gn; ++i) {
                const uint64_t want = 0x4000000000000000ULL | perm[i];
                if (f64_bits(dst[perm[i]]) != want) {
                    if (fails < 4)
                        fprintf(stderr, "1d_tag @perm[%d]=%llu hw=%016llx "
                                "want=%016llx\n", i,
                                (unsigned long long)perm[i],
                                (unsigned long long)f64_bits(dst[perm[i]]),
                                (unsigned long long)want);
                    ++fails;
                }
            }
            for (int i = 0; i < gn; ++i)
                fnv_bits(&dst[i], 8);
        }
        g_fails += fails;
        printf("mode=1d_tag lanes=%d gn=%d FAILS=%u\n", lanes, gn, fails);
    }

    /* ---------------- mode: 2d_block ---------------- */
    {
        static double src[N2D], dst[N2D], golden[N2D];
        static uint64_t perm[N2D];
        unsigned fails = 0;

        for (int i = 0; i < N2D; ++i) {
            src[i] = (double)((i % 1009) + 1);   /* exact integers */
            perm[i] = (uint64_t)i;
            dst[i] = -1.0;
        }
        if (randomize) {
            for (int i = N2D - 1; i > 0; --i) {
                int j = (int)(xs32() % (uint32_t)(i + 1));
                uint64_t t = perm[i];
                perm[i] = perm[j];
                perm[j] = t;
            }
        } else {
            for (int i = 0; i < N2D; ++i)
                perm[i] = (uint64_t)((i * 131) % N2D);
        }
        for (int i = 0; i < N2D; ++i)
            golden[perm[i]] = 1.5 * src[perm[i]];  /* exact: <= 1513.5 */

        for (int64_t off = 0; off < N2D; off += lanes) {
            const svbool_t pg = svwhilelt_b64((uint64_t)off, (uint64_t)N2D);
            const svuint64_t idx = svld1_u64(pg, perm + off);
            const svfloat64_t g = svld1_gather_u64index_f64(pg, src, idx);
            const svfloat64_t out =
                svmla_f64_x(pg, g, svdup_f64(0.5), g);   /* g + 0.5g */
            svst1_scatter_u64index_f64(pg, dst, idx, out);
        }

        for (int i = 0; i < N2D; ++i) {
            if (dst[i] != golden[i]) {
                if (fails < 4)
                    fprintf(stderr, "2d_block @%d hw=%.17g sw=%.17g\n",
                            i, dst[i], golden[i]);
                ++fails;
            }
            fnv_bits(&dst[i], 8);
        }
        g_fails += fails;
        printf("mode=2d_block lanes=%d n=%d FAILS=%u\n", lanes, N2D, fails);
    }

    printf("SDCSHIELD_FAILS=%u\n%016llx\n",
           g_fails, (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
