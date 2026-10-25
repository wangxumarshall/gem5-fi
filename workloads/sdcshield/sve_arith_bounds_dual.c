/* sve_arith_bounds_dual.c — dual-channel extraction of the four PR #294
 * review-round hardening fixes in sdcshield (branch
 * feat/allvl2-hardening, review round 1) for CHAOS/gem5 SE-O3:
 *
 *   A. sve_bigint_mul512 (tests/cpu/sve/arithmetic/bigint_mulx_sve.cpp +
 *      gmp_bignum_sve.cpp, byte-identical duplicates): reworked to chunk
 *      over svcntd() with svwhilelt_b64 predicates bounded by NUM_WORDS
 *      (the old svptrue full-width svld1_u64(pg, b) read 64B past the
 *      8-element heap buffer at VL=1024), and the SVE product low half
 *      now participates in the accumulation (the old (void)lo discarded
 *      it, so an SVE multiplier fault could never reach the compared
 *      output). Healthy hardware: lo_row[j] == (uint64_t)prod, results
 *      bit-identical to the scalar schoolbook golden.
 *   B. sve_mul_words (operand_space_sve.cpp): predicate clamped to the
 *      4-lane row (svptrue made svld1/svst1 read/write past the 4-element
 *      ai/bi/out stack arrays at any VL > 256); out[0] is consumed, so
 *      the SVE multiply was and stays load-bearing.
 *   C. neon_rot_2src phase dispatch (neon_rot_2src_sve.cpp): the phase[]
 *      staging array is sized SVE_MAX_VECTOR_BYTES/8 (was [8] — an OOB
 *      stack write/read of 8 elements at VL=1024 where n == svcntd() ==
 *      16); the svsel phase chain and the (base+k)%4 golden dispatch are
 *      mirrored verbatim.
 *   D. do_movmskps_sve/do_movmskpd_sve (movmskpspd_sve.cpp): the
 *      row-width-clamped (FPS_LANES=4/FPD_LANES=2) sign-bit masks with
 *      out[] capacity now exactly the clamped width — first four-tier
 *      execution of the clamped form (previously equivalence-argued
 *      only).
 *
 * Channel A: each section's SVE result vs its scalar golden, byte-exact.
 * Channel B: FNV-1a over all section outputs.
 *
 * Honest scope: gem5 has no ASAN, so the REMOVED OOB accesses are proven
 * gone by construction (predicates/arrays bounded in the mirrored
 * source), not by detection; this kernel proves the FIXED logic computes
 * correct results at every tier, including the tiers (512/1024-bit)
 * where the old code was out of bounds.
 *
 * argv: [fixed|random|poison] [seed]
 * Build: make sve_arith_bounds_dual
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

#define NUM_WORDS 8

/* movmsk row widths (tests/cpu/sve/fma2/movmskpspd_sve.cpp) */
#define FPS_LANES 4
#define FPD_LANES 2

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

static unsigned g_fails = 0;

/* ---- Section A: fixed sve_bigint_mul512 (verbatim, PR #294 form) ---- */
static void sve_bigint_mul512(const uint64_t *a, const uint64_t *b, uint64_t *out_lo) {
    uint64_t acc[NUM_WORDS * 2];
    memset(acc, 0, sizeof(acc));

    for (int i = 0; i < NUM_WORDS; ++i) {
        uint64_t lo_row[NUM_WORDS];
        for (uint64_t j0 = 0; j0 < (uint64_t)NUM_WORDS; j0 += (uint64_t)svcntd()) {
            svbool_t pgj = svwhilelt_b64(j0, (uint64_t)NUM_WORDS);
            svuint64_t va = svdup_n_u64(a[i]);
            svuint64_t vb = svld1_u64(pgj, b + j0);
            svst1_u64(pgj, lo_row + j0, svmul_u64_x(pgj, va, vb));
        }

        uint64_t carry = 0;
        for (int j = 0; j < NUM_WORDS; ++j) {
            unsigned __int128 prod = (unsigned __int128)a[i] * b[j];
            unsigned __int128 s = (unsigned __int128)acc[i + j] + lo_row[j] + carry;
            acc[i + j] = (uint64_t)s;
            carry = (uint64_t)(prod >> 64) + (uint64_t)(s >> 64);
        }
        acc[i + NUM_WORDS] += carry;
    }
    memcpy(out_lo, acc, NUM_WORDS * sizeof(uint64_t));
}

static void sw_bigint_mul512(const uint64_t *a, const uint64_t *b, uint64_t *out_lo) {
    uint64_t acc[NUM_WORDS * 2];
    memset(acc, 0, sizeof(acc));
    for (int i = 0; i < NUM_WORDS; ++i) {
        uint64_t carry = 0;
        for (int j = 0; j < NUM_WORDS; ++j) {
            unsigned __int128 prod = (unsigned __int128)a[i] * b[j];
            unsigned __int128 s = (unsigned __int128)acc[i + j] + (uint64_t)prod + carry;
            acc[i + j] = (uint64_t)s;
            carry = (uint64_t)(prod >> 64) + (uint64_t)(s >> 64);
        }
        acc[i + NUM_WORDS] += carry;
    }
    memcpy(out_lo, acc, NUM_WORDS * sizeof(uint64_t));
}

/* ---- Section B: fixed sve_mul_words (verbatim, PR #294 form) ---- */
static void sve_mul_words(uint64_t a, uint64_t b, uint64_t *lo, uint64_t *hi)
{
    svbool_t pg = svwhilelt_b64((uint64_t)0, (uint64_t)4);
    uint64_t ai[4] = {a, a, a, a}, bi[4] = {b, b, b, b}, out[4];
    svst1_u64(pg, out, svmul_u64_x(pg, svld1_u64(pg, ai), svld1_u64(pg, bi)));
    *lo = out[0];
    unsigned __int128 prod = (unsigned __int128)a * b;
    *hi = (uint64_t)(prod >> 64);
}

/* ---- Section D: fixed movmsk (verbatim, PR #294 form) ---- */
static inline uint32_t do_movmskps_sve(const float *p)
{
    uint32_t out[FPS_LANES];
    svbool_t pg = svwhilelt_b32((uint64_t)0, (uint64_t)FPS_LANES);
    svfloat32_t v = svld1_f32(pg, p);
    svbool_t neg = svcmpge_n_u32(pg, svreinterpret_u32_f32(v), 0x80000000u);
    svuint32_t bits = svsel_u32(neg, svdup_u32(1u), svdup_u32(0u));
    svst1_u32(pg, out, bits);
    uint32_t mask = 0;
    for (int i = 0; i < FPS_LANES; ++i) mask |= (out[i] & 1u) << i;
    return mask;
}

static inline uint32_t do_movmskpd_sve(const double *p)
{
    uint64_t out[FPD_LANES];
    svbool_t pg = svwhilelt_b64((uint64_t)0, (uint64_t)FPD_LANES);
    svfloat64_t v = svld1_f64(pg, p);
    svbool_t neg = svcmpge_n_u64(pg, svreinterpret_u64_f64(v), 0x8000000000000000ull);
    svuint64_t bits = svsel_u64(neg, svdup_u64(1ull), svdup_u64(0));
    svst1_u64(pg, out, bits);
    uint32_t mask = 0;
    for (int i = 0; i < FPD_LANES; ++i) mask |= (out[i] & 1u) << i;
    return mask;
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "fixed";
    const uint64_t seed = (argc > 2) ? strtoull(argv[2], 0, 0) : 1;
    const int poison = (strcmp(mode, "poison") == 0);
    rng_state = seed * 0x2545F4914F6CDD1DULL + 0x9E3779B97F4A7C15ULL;

    const size_t lanes = svcntd();
    if (lanes < 2 || lanes > 16) {
        fprintf(stderr, "unsupported VL (svcntd=%zu)\n", lanes);
        return 3;
    }

    /* ---------- Section A: 512-bit multiplies, SVE vs schoolbook ---------- */
    for (int rep = 0; rep < 4; ++rep) {
        uint64_t a[NUM_WORDS], b[NUM_WORDS];
        for (int i = 0; i < NUM_WORDS; ++i) {
            a[i] = sm64();
            b[i] = sm64();
        }
        uint64_t sve_lo[NUM_WORDS], sw_lo[NUM_WORDS];
        sve_bigint_mul512(a, b, sve_lo);
        sw_bigint_mul512(a, b, sw_lo);
        if (poison && rep == 0)
            sw_lo[0] ^= 1ULL;                  /* negative control */
        for (int i = 0; i < NUM_WORDS; ++i) {
            fnv_u64(sve_lo[i]);
            if (sve_lo[i] != sw_lo[i]) {
                fprintf(stderr, "A mul512 rep %d word %d sve=%016llx sw=%016llx\n",
                        rep, i, (unsigned long long)sve_lo[i],
                        (unsigned long long)sw_lo[i]);
                ++g_fails;
            }
        }
    }

    /* ---------- Section B: 64x64->128 multiply, clamped predicate ---------- */
    for (int rep = 0; rep < 64; ++rep) {
        uint64_t a = sm64(), b = sm64();
        uint64_t lo, hi;
        sve_mul_words(a, b, &lo, &hi);
        unsigned __int128 prod = (unsigned __int128)a * b;
        uint64_t glo = (uint64_t)prod, ghi = (uint64_t)(prod >> 64);
        if (poison && rep == 0)
            glo ^= 1ULL;                       /* negative control */
        fnv_u64(lo);
        fnv_u64(hi);
        if (lo != glo || hi != ghi) {
            fprintf(stderr, "B mul_words rep %d lo=%016llx/%016llx hi=%016llx/%016llx\n",
                    rep, (unsigned long long)lo, (unsigned long long)glo,
                    (unsigned long long)hi, (unsigned long long)ghi);
            ++g_fails;
        }
    }

    /* ---------- Section C: rotating phase dispatch, wide phase[] ---------- */
    {
        /* 4 batches of full vectors; the test rounds count down to a
         * multiple of svcntd(), so every batch has n == lanes. */
        const size_t count = 4 * lanes;
        uint64_t *srcA = malloc(count * 8), *srcB = malloc(count * 8);
        uint64_t *out = calloc(count, 8), *golden = malloc(count * 8);
        for (size_t i = 0; i < count; ++i) {
            srcA[i] = sm64();
            srcB[i] = sm64();
        }
        svbool_t pg = svwhilelt_b64((uint64_t)0, (uint64_t)lanes);
        for (size_t base = 0; base < count; base += lanes) {
            svuint64_t a = svld1_u64(pg, srcA + base);
            svuint64_t b = svld1_u64(pg, srcB + base);
            svuint64_t res;
            {
                svuint64_t r_add = svadd_u64_x(pg, a, b);
                svuint64_t r_eor = sveor_u64_x(pg, a, b);
                svuint64_t r_and = svand_u64_x(pg, a, b);
                svuint64_t r_orr = svorr_u64_x(pg, a, b);
                uint64_t phase[SVE_MAX_VECTOR_BYTES / 8];
                int n = (int)lanes;
                for (int k = 0; k < n; ++k) phase[k] = (base + (size_t)k) % 4;
                svbool_t pgn = svwhilelt_b64((uint64_t)0, (uint64_t)n);
                svuint64_t vphase = svld1_u64(pgn, phase);
                res = svsel_u64(svcmpeq_n_u64(pgn, vphase, 0), r_add,
                     svsel_u64(svcmpeq_n_u64(pgn, vphase, 1), r_eor,
                     svsel_u64(svcmpeq_n_u64(pgn, vphase, 2), r_and, r_orr)));
            }
            svst1_u64(pg, out + base, res);
        }
        for (size_t i = 0; i < count; ++i) {
            switch (i % 4) {
            case 0: golden[i] = srcA[i] + srcB[i]; break;
            case 1: golden[i] = srcA[i] ^ srcB[i]; break;
            case 2: golden[i] = srcA[i] & srcB[i]; break;
            default: golden[i] = srcA[i] | srcB[i]; break;
            }
        }
        if (poison)
            golden[1] ^= 1ULL;                 /* negative control */
        for (size_t i = 0; i < count; ++i) {
            fnv_u64(out[i]);
            if (out[i] != golden[i]) {
                fprintf(stderr, "C phase idx %zu golden=%016llx actual=%016llx\n",
                        i, (unsigned long long)golden[i],
                        (unsigned long long)out[i]);
                ++g_fails;
            }
        }
        free(srcA); free(srcB); free(out); free(golden);
    }

    /* ---------- Section D: clamped MOVMSKPS/PD sign masks ---------- */
    for (int rep = 0; rep < 64; ++rep) {
        uint32_t fbits[FPS_LANES];
        uint64_t dbits[FPD_LANES];
        for (int i = 0; i < FPS_LANES; ++i) fbits[i] = (uint32_t)sm64();
        for (int i = 0; i < FPD_LANES; ++i) dbits[i] = sm64();
        float frow[FPS_LANES];
        double drow[FPD_LANES];
        memcpy(frow, fbits, sizeof(frow));
        memcpy(drow, dbits, sizeof(drow));

        uint32_t fgot = do_movmskps_sve(frow);
        uint32_t dgot = do_movmskpd_sve(drow);
        uint32_t fg = 0, dg = 0;
        for (int i = 0; i < FPS_LANES; ++i) fg |= ((fbits[i] >> 31) & 1u) << i;
        for (int i = 0; i < FPD_LANES; ++i) dg |= ((uint32_t)(dbits[i] >> 63) & 1u) << i;
        if (poison && rep == 0) {
            fg ^= 1u;                          /* negative control */
            dg ^= 1u;
        }
        fnv_u64(fgot);
        fnv_u64(dgot);
        if (fgot != fg) {
            fprintf(stderr, "D movmskps rep %d got=%x golden=%x\n", rep, fgot, fg);
            ++g_fails;
        }
        if (dgot != dg) {
            fprintf(stderr, "D movmskpd rep %d got=%x golden=%x\n", rep, dgot, dg);
            ++g_fails;
        }
    }

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
