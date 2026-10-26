/* agu_2src_dual.c — dual-channel extraction of the FIXED
 * agu_stress_2src_sve (sdcshield feat/allvl2-hardening, PR #294 review
 * round 3: tail-batch buffer slack + run-side VL drift guard +
 * family-sized phase[]) for CHAOS/gem5 SE-O3.
 *
 * The unfixed form allocated exactly count*sizeof(uint64_t) per buffer
 * while the run path drives an asm full-width ldr z (svcntb() bytes) and
 * svwhilelt(0, svcntd()) full-width stores: with count not a multiple of
 * svcntd() the tail batch reads AND writes past the buffer end (default
 * count=600 at VL=1024: 600%16=8 -> 8 elements / 64B past count; gem5 has
 * no ASAN, so the overrun is proven gone by construction here, not by
 * detection — same honest boundary as sve_arith_bounds_dual).
 *
 * Mirrored fix (kreg-family slack pattern + policy #3 fail-closed):
 *   - srcA/srcB/expected/temp/dst sized (count + lanes) elements; the
 *     slack region never enters golden or the compared range;
 *   - init lanes recorded, re-read at run entry, mismatch -> fail closed;
 *   - phase[SVE_MAX_VECTOR_BYTES / 8] (family form, was [16] with a
 *     comment claiming a gate that only existed at init).
 *
 * The kernel deliberately picks count with a non-zero remainder mod
 * lanes so EVERY tier exercises the tail batch.
 *
 * Channel A: dst[0..count) vs the init-time golden, byte-exact per
 * element (cold path dumps golden/actual/xor + total, mirroring the
 * test's mismatch dump). Channel B: FNV-1a over dst[0..count).
 *
 * argv: [fixed|random|poison] [seed]
 * Build: make agu_2src_dual
 * Run:   gem5.opt configs/se/arm_chaos.py --cmd <bin> --sve_vl {1,2,4,8} \
 *          --workload_args "random 1"
 */
#include <arm_sve.h>
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#ifndef SVE_MAX_VECTOR_BYTES
#define SVE_MAX_VECTOR_BYTES 256
#endif

static uint64_t rng_state;
static uint64_t sm64(void)
{
    uint64_t z = (rng_state += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static uint64_t fnv = 1469598103934665603ULL;
static void fnv_u64(uint64_t v)
{
    fnv ^= v;
    fnv *= 1099511628211ULL;
}

static unsigned g_fails;

/* ---- verbatim from the fixed test (agu_stress_2src_sve.cpp) ---- */
static inline void store_vec_sve(void *addr, svuint64_t val) {
    svbool_t pg = svwhilelt_b64((uint64_t)0, (uint64_t)svcntd());
    svst1_u64(pg, (uint64_t *)addr, val);
}

static inline svuint64_t load_vec_sve(const void *addr) {
    svuint64_t res;
    __asm__ volatile ("ldr %0, [%1]" : "=w"(res) : "r"(addr) : "memory");
    return res;
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "fixed";
    const uint64_t seed = (argc > 2) ? strtoull(argv[2], 0, 0) : 1;
    const int poison = (strcmp(mode, "poison") == 0);
    rng_state = seed * 0x2545F4914F6CDD1DULL + 0x9E3779B97F4A7C15ULL;

    /* mirrors test_init's gate-derived record: u64 lanes = SVL bytes / 8 */
    const int init_lanes = (int)(svcntb() / 8);
    const int lanes = (int)svcntd();
    if (lanes < 2 || lanes > 16 || lanes != init_lanes) {
        fprintf(stderr, "unsupported VL (svcntd=%d)\n", lanes);
        return 3;
    }

    /* non-multiple count: every tier runs a tail batch with n < lanes */
    const size_t count = (size_t)(4 * lanes + (lanes + 1) / 2);
    const size_t total = count + (size_t)lanes;   /* tail slack (the fix) */

    uint64_t *srcA = malloc(total * sizeof(uint64_t));
    uint64_t *srcB = malloc(total * sizeof(uint64_t));
    uint64_t *expected = malloc(total * sizeof(uint64_t));
    uint64_t *temp = malloc(total * sizeof(uint64_t));
    uint64_t *dst = malloc(total * sizeof(uint64_t));
    if (!srcA || !srcB || !expected || !temp || !dst)
        return 4;

    for (size_t i = 0; i < count; ++i) {
        srcA[i] = sm64();
        srcB[i] = sm64();
    }
    /* golden: same rotating composition as test_init (absolute index % 4) */
    for (size_t i = 0; i < count; ++i) {
        switch (i % 4) {
        case 0: expected[i] = srcA[i] + srcB[i]; break;
        case 1: expected[i] = srcA[i] ^ srcB[i]; break;
        case 2: expected[i] = srcA[i] & srcB[i]; break;
        default: expected[i] = srcA[i] | srcB[i]; break;
        }
    }

    /* run-side drift guard (mirrored verbatim; fixed-VL sim never trips
     * it — its presence + non-interference is what the mirror proves) */
    if ((int)svcntd() != init_lanes) {
        fprintf(stderr, "agu_2src_dual: SVE VL drifted between init "
                "(lanes=%d) and run (svcntd()=%d)\n", init_lanes, (int)svcntd());
        return 2;
    }

    svbool_t pg = svwhilelt_b64((uint64_t)0, (uint64_t)lanes);
    for (int round = 0; round < 3; ++round) {
        for (size_t base = 0; base < count; base += (size_t)lanes) {
            svuint64_t a = load_vec_sve(srcA + base);
            svuint64_t b = load_vec_sve(srcB + base);
            svuint64_t res;
            {
                svuint64_t r_add = svadd_u64_x(pg, a, b);
                svuint64_t r_eor = sveor_u64_x(pg, a, b);
                svuint64_t r_and = svand_u64_x(pg, a, b);
                svuint64_t r_orr = svorr_u64_x(pg, a, b);
                uint64_t phase[SVE_MAX_VECTOR_BYTES / 8];
                int n = (count - base < (size_t)lanes)
                            ? (int)(count - base) : lanes;
                for (int k = 0; k < n; ++k)
                    phase[k] = (base + (size_t)k) % 4;
                svbool_t pgn = svwhilelt_b64((uint64_t)0, (uint64_t)n);
                svuint64_t vphase = svld1_u64(pgn, phase);
                res = svsel_u64(svcmpeq_n_u64(pgn, vphase, 0), r_add,
                     svsel_u64(svcmpeq_n_u64(pgn, vphase, 1), r_eor,
                     svsel_u64(svcmpeq_n_u64(pgn, vphase, 2), r_and, r_orr)));
            }
            store_vec_sve(temp + base, res);
            store_vec_sve(dst + base, load_vec_sve(temp + base));
        }

        if (poison && round == 0)
            expected[1] ^= 1ULL;               /* negative control */

        size_t bad = 0;
        int shown = 0;
        for (size_t i = 0; i < count; ++i) {
            if (dst[i] != expected[i]) {
                ++bad;
                if (shown < 8) {
                    fprintf(stderr, "agu_2src_dual: mismatch at index %zu: "
                            "golden=%016llx actual=%016llx xor=%016llx\n",
                            i, (unsigned long long)expected[i],
                            (unsigned long long)dst[i],
                            (unsigned long long)(expected[i] ^ dst[i]));
                    ++shown;
                }
            }
        }
        if (bad) {
            fprintf(stderr, "agu_2src_dual: total mismatched elements: "
                    "%zu / %zu\n", bad, count);
            ++g_fails;
        }
    }

    for (size_t i = 0; i < count; ++i)
        fnv_u64(dst[i]);

    free(srcA); free(srcB); free(expected); free(temp); free(dst);
    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
