/* sve512_chain_dual.c — cluster-A dual kernel for the all-VL Phase 2 P3
 * rework of the sve512 chain/special family (sve512_{f64,f32}_chain_{arm,
 * svd}, sve512_f64_special_{arm,svd}, libomp_ctx ACTIVE window). One run
 * covers four modes; per-mode FAILS lines, one combined checksum.
 *
 * Same-source: the tests' chains are pure sizeless SVE intrinsics
 * (svptrue + svld1 + svmla_x + svst1, serial dependency per step) — this
 * kernel mirrors that exact form, so the compiler emits the same fmla
 * chain shape. The scalar golden uses fma/fmaf (single-rounding, like
 * svmla) in the same order, so hardware and golden agree bit-for-bit by
 * construction.
 *
 *   chain_f64     — 512-step serial svmla_f64_x chain over two double
 *                   streams, window [s*L, s*L+L)  (f64_chain_arm).
 *   chain_f64_slab— the same chain over stream segments selected by the
 *                   _svd block-slab formula
 *                   ((row/16)*19 + col/16) * (2*STEPS*L), 4 representative
 *                   blocks of the 19x19 grid (f64_chain_svd addressing).
 *   chain_f32     — the f32 form, lanes_w = svcntw() (f32_chain_*).
 *   special_f64   — 64-step chain with per-lane IEEE special values,
 *                   category-compare golden (f64_special_*).
 *
 * This kernel also settles the issue #182 question: the 512-bit gate
 * existed because a hosted CI runner (VL=128) once saw golden mismatches;
 * four-tier channel-A green here is the evidence that clears it.
 *
 * Channels: A = per-lane byte/category compare vs the scalar golden;
 *           B = FNV-1a over the result bits (all modes).
 * argv: [fixed|random] [seed]; exit 0 / 1 (fails) / 3 (unsupported VL).
 * Build: gcc -static -O2 -march=armv9-a+sve -Wall -Wextra
 * Run:   gem5.opt configs/se/arm_chaos.py --cpu O3 --cmd \
 *          workloads/sdcshield/sve512_chain_dual --sve_vl 4 \
 *          --workload_args "fixed 1"
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <arm_sve.h>

#define STEPS         512    /* the tests' CHAIN_STEPS (VL-independent) */
#define SPECIAL_STEPS 64     /* the tests' SPECIAL_CHAIN_STEPS */
#define LMAX          16     /* 1024-bit cap: 16 f64 lanes */
#define LWMAX         32     /* 1024-bit cap: 32 f32 lanes */
#define SLAB_BLOCKS   4      /* representative blocks for the slab mode */

static uint32_t xs_state;
static uint32_t xs32(void)
{
    xs_state ^= xs_state << 13;
    xs_state ^= xs_state >> 17;
    xs_state ^= xs_state << 5;
    return xs_state;
}
static double rnd_band(void)   /* uniform in (-2, 2) */
{
    return (double)(xs32() >> 8) / (double)(1u << 24) * 4.0 - 2.0;
}
static float rnd_band_f32(void)
{
    return (float)((xs32() >> 8) / (float)(1u << 24) * 4.0f - 2.0f);
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

/* Category compare (the f64_special idiom): NaN-class equal, ±Inf equal
   by sign, finite byte-exact. */
static int f64_cat_ok(double a, double g)
{
    if (isnan(a) && isnan(g))
        return 1;
    if (isinf(a) && isinf(g))
        return signbit(a) == signbit(g);
    uint64_t ba, bg;
    memcpy(&ba, &a, 8);
    memcpy(&bg, &g, 8);
    return ba == bg;
}

/* The tests' kernel form: a serial svmla chain over two streams. */
static void chain_f64_kernel(const double *m, const double *a, int steps,
                             int lanes, double *out)
{
    const svbool_t pg = svptrue_b64();
    svfloat64_t acc = svdup_f64(0.0);
    for (int s = 0; s < steps; ++s) {
        const svfloat64_t vm = svld1_f64(pg, m + (size_t)s * lanes);
        const svfloat64_t va = svld1_f64(pg, a + (size_t)s * lanes);
        acc = svmla_f64_x(pg, acc, vm, va);
    }
    svst1_f64(pg, out, acc);
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "fixed";
    const uint32_t seed = (argc > 2) ? (uint32_t)strtoul(argv[2], 0, 0) : 1;
    const int randomize = (strcmp(mode, "random") == 0);
    xs_state = seed ? seed : 1;

    const int lanes = (int)svcntd();    /* f64 lanes of the runtime VL */
    const int lanes_w = (int)svcntw();  /* f32 lanes */
    if (lanes < 2 || lanes > LMAX || lanes_w < 4 || lanes_w > LWMAX) {
        fprintf(stderr, "unsupported VL (f64 lanes %d, f32 lanes %d)\n",
                lanes, lanes_w);
        return 3;
    }

    /* ---------------- mode: chain_f64 ---------------- */
    {
        static double ma[STEPS * LMAX], aa[STEPS * LMAX];
        static double golden[LMAX], hw[LMAX];
        for (size_t i = 0; i < (size_t)STEPS * lanes; ++i) {
            if (randomize) {
                ma[i] = rnd_band();
                aa[i] = rnd_band();
            } else {
                ma[i] = (double)((int)(i % 97) - 48) / 24.0;
                aa[i] = (double)((int)(i % 89) - 44) / 22.0;
            }
        }
        for (int r = 0; r < lanes; ++r)
            golden[r] = 0.0;
        for (int s = 0; s < STEPS; ++s)
            for (int r = 0; r < lanes; ++r)
                golden[r] = fma(ma[(size_t)s * lanes + r],
                                aa[(size_t)s * lanes + r], golden[r]);
        chain_f64_kernel(ma, aa, STEPS, lanes, hw);
        unsigned fails = 0;
        for (int r = 0; r < lanes; ++r) {
            fnv_bits(&hw[r], 8);
            if (hw[r] != golden[r])
                ++fails;
        }
        for (int r = 0; fails && r < lanes && r < 2; ++r)
            fprintf(stderr, "chain_f64 @%d hw=%.17g sw=%.17g\n",
                    r, hw[r], golden[r]);
        g_fails += fails;
        printf("mode=chain_f64 lanes=%d FAILS=%u\n", lanes, fails);
    }

    /* ---------------- mode: chain_f64_slab ---------------- */
    {
        /* 19x19 slab grid; each slab holds TWO streams of STEPS*lanes
           doubles back to back (the _svd layout). Run the standard chain
           over 4 representative blocks selected by the slab formula. */
        static double slab[19 * 19 * 2 * STEPS * LMAX];
        static double golden[LMAX], hw[LMAX];
        const int blocks[SLAB_BLOCKS][2] =
            { {0, 0}, {0, 18}, {18, 0}, {9, 9} };
        for (size_t i = 0; i < sizeof(slab) / sizeof(slab[0]); ++i)
            slab[i] = randomize ? rnd_band()
                                : (double)((int)(i % 83) - 41) / 20.0;
        unsigned fails = 0;
        for (int b = 0; b < SLAB_BLOCKS; ++b) {
            const size_t base = ((size_t)blocks[b][0] * 19 + blocks[b][1])
                                * (2 * STEPS * lanes);
            const double *m = slab + base;
            const double *a = slab + base + (size_t)STEPS * lanes;
            for (int r = 0; r < lanes; ++r)
                golden[r] = 0.0;
            for (int s = 0; s < STEPS; ++s)
                for (int r = 0; r < lanes; ++r)
                    golden[r] = fma(m[(size_t)s * lanes + r],
                                    a[(size_t)s * lanes + r], golden[r]);
            chain_f64_kernel(m, a, STEPS, lanes, hw);
            for (int r = 0; r < lanes; ++r) {
                fnv_bits(&hw[r], 8);
                if (hw[r] != golden[r])
                    ++fails;
            }
        }
        if (fails)
            fprintf(stderr, "chain_f64_slab: mismatch (see above runs)\n");
        g_fails += fails;
        printf("mode=chain_f64_slab lanes=%d FAILS=%u\n", lanes, fails);
    }

    /* ---------------- mode: chain_f32 ---------------- */
    {
        static float ma[STEPS * LWMAX], aa[STEPS * LWMAX];
        static float golden[LWMAX], hw[LWMAX];
        for (size_t i = 0; i < (size_t)STEPS * lanes_w; ++i) {
            if (randomize) {
                ma[i] = rnd_band_f32();
                aa[i] = rnd_band_f32();
            } else {
                ma[i] = (float)((int)(i % 97) - 48) / 24.0f;
                aa[i] = (float)((int)(i % 89) - 44) / 22.0f;
            }
        }
        for (int r = 0; r < lanes_w; ++r)
            golden[r] = 0.0f;
        for (int s = 0; s < STEPS; ++s)
            for (int r = 0; r < lanes_w; ++r)
                golden[r] = fmaf(ma[(size_t)s * lanes_w + r],
                                 aa[(size_t)s * lanes_w + r], golden[r]);
        const svbool_t pgw = svptrue_b32();
        svfloat32_t acc = svdup_f32(0.0f);
        for (int s = 0; s < STEPS; ++s) {
            const svfloat32_t vm = svld1_f32(pgw, ma + (size_t)s * lanes_w);
            const svfloat32_t va = svld1_f32(pgw, aa + (size_t)s * lanes_w);
            acc = svmla_f32_x(pgw, acc, vm, va);
        }
        svst1_f32(pgw, hw, acc);
        unsigned fails = 0;
        for (int r = 0; r < lanes_w; ++r) {
            fnv_bits(&hw[r], 4);
            if (hw[r] != golden[r])
                ++fails;
        }
        for (int r = 0; fails && r < lanes_w && r < 2; ++r)
            fprintf(stderr, "chain_f32 @%d hw=%.9g sw=%.9g\n",
                    r, hw[r], golden[r]);
        g_fails += fails;
        printf("mode=chain_f32 lanes=%d FAILS=%u\n", lanes_w, fails);
    }

    /* ---------------- mode: special_f64 ---------------- */
    {
        static const double tab[] = {
            0.0, -0.0, 1.0, -1.0, 0.5, -0.5,
            INFINITY, -INFINITY, NAN, 1.5, -2.0, 0.25,
        };
        const int NT = (int)(sizeof(tab) / sizeof(tab[0]));
        static double sa[SPECIAL_STEPS * LMAX], sb[SPECIAL_STEPS * LMAX];
        static double golden[LMAX], hw[LMAX];
        for (size_t i = 0; i < (size_t)SPECIAL_STEPS * lanes; ++i) {
            sa[i] = tab[xs32() % (unsigned)NT];
            sb[i] = tab[xs32() % 3];   /* b in {0, -0, 1}: most products
                                          stay well-defined; NaN still
                                          propagates through the chain */
        }
        for (int r = 0; r < lanes; ++r)
            golden[r] = 0.0;   /* symmetric with the hw accumulator's
                                  svdup_f64(0.0) start — the first matrix
                                  left this at 1.0, an asymmetry masked by
                                  NaN (adversarial review Important-1) */
        for (int s = 0; s < SPECIAL_STEPS; ++s)
            for (int r = 0; r < lanes; ++r)
                golden[r] = fma(sa[(size_t)s * lanes + r],
                                sb[(size_t)s * lanes + r], golden[r]);
        chain_f64_kernel(sa, sb, SPECIAL_STEPS, lanes, hw);
        unsigned fails = 0;
        for (int r = 0; r < lanes; ++r) {
            fnv_bits(&hw[r], 8);
            if (!f64_cat_ok(hw[r], golden[r]))
                ++fails;
        }
        for (int r = 0; fails && r < lanes && r < 3; ++r)
            fprintf(stderr, "special_f64 @%d hw=%.17g sw=%.17g\n",
                    r, hw[r], golden[r]);
        g_fails += fails;
        printf("mode=special_f64 lanes=%d FAILS=%u\n", lanes, fails);
    }

    printf("SDCSHIELD_FAILS=%u\n%016llx\n",
           g_fails, (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
