/* sve512_fma_dual.c — dual-channel extraction of sdcshield test
 * `sve512_fma_arm` (PR #294 post-hardening form) for CHAOS/gem5 SE-O3
 * fault injection.
 *
 * Why this kernel exists (PR #294 review round 1): the test was wired
 * into the build by 3b293d9b as an "orphan" whose own init/golden/
 * comparison logic had never executed anywhere (family-level scoping
 * was the only prior evidence), and the review found its scatter
 * scratch lived in the worker-shared test->data (a -n>1 race). The
 * sdcshield fix (this PR) moves scatter_dst/scatter_golden into
 * test_run as worker-private buffers with output-pointer kernels.
 * This kernel mirrors the FIXED test source — seeds, operand streams,
 * goldens, compares, and the output-pointer gather/scatter — so the
 * test's own logic gets four-tier (128..1024-bit) execution evidence,
 * same-source.
 *
 * Channel A: the test's four workloads, byte-exact/category compared
 *   1. f64 FMLA serial dependency chain (svmla_f64_x over 512 steps)
 *      vs the scalar std::fma golden (identical op order);
 *   2. f64 special-value chain (NaN/sNaN/±Inf/±0/±1) with category
 *      compare (fsu_byteexact_arm precedent);
 *   3. f32 FMLA chain (svmla_f32_x) vs scalar fmaf golden;
 *   4. gather/scatter round-trip (svld1_gather_u64index_f64 ->
 *      svmla(v,v,1.5) -> svst1_scatter_u64index_f64) against the
 *      indirection-indexed scalar golden, with PER-CALL dst/golden
 *      buffers and a fill-reset between iterations (the fix mirror).
 * Channel B: FNV-1a over the four hardware result buffers.
 *
 * Determinism: the test is fully deterministic (splitmix64 constants,
 * pattern tables) — checksums are tier-dependent by design (lane count
 * differs per tier); cross-tier identity is NOT claimed.
 *
 * argv: [run|poison]   (poison flips one golden bit per workload class
 *                       — negative control, J1' discipline)
 * Build: make sve512_fma_dual
 * Run:   gem5.opt configs/se/arm_chaos.py --cmd <bin> --sve_vl {1,2,4,8} \
 *          --workload_args "run"
 */
#include <arm_sve.h>
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdbool.h>

#define CHAIN_STEPS 512
#define SPECIAL_CHAIN_STEPS 64

/* ---- verbatim from tests/cpu/arm64/sve512_fma_arm.cpp ---- */
static const uint64_t F64_FINITE[] = {
    0x3FF5555555555555ULL, 0xBFFAAAAAAAAAAAAAULL, 0x3FD5555555555555ULL,
    0xBFEAAAAAAAAAAAAAULL, 0x0015555555555555ULL, 0x801AAAAAAAAAAAAAULL,
    0x3FF0000000000000ULL, 0xBFF0000000000000ULL, 0x0005555555555555ULL,
    0x800AAAAAAAAAAAAAULL, 0x3FF999999999999AULL, 0xBFF6666666666667ULL,
    0x3FE5555555555555ULL, 0xBFE6666666666667ULL, 0x3FF3333333333333ULL,
    0xBFFCCCCCCCCCCCCDULL,
};
#define F64_FINITE_SIZE (sizeof(F64_FINITE) / sizeof(F64_FINITE[0]))

static const uint64_t F64_SPECIAL[] = {
    0x0000000000000000ULL, 0x8000000000000000ULL, 0x7FF8000000000000ULL,
    0x7FF0000000000001ULL, 0x7FF0000000000000ULL, 0xFFF0000000000000ULL,
    0x3FF0000000000000ULL, 0xBFF0000000000000ULL,
};
#define F64_SPECIAL_SIZE (sizeof(F64_SPECIAL) / sizeof(F64_SPECIAL[0]))

static const uint32_t F32_FINITE[] = {
    0x3FAAAAABU, 0xBFAAAAABU, 0x3EAAAAABU, 0xBF2AAAABU,
    0x3F800000U, 0xBF800000U, 0x00555555U, 0x80AAAAAAU,
    0x3FCCCCCDU, 0xBFCCCCCDU, 0x3F333333U, 0xBF333333U,
    0x3E555555U, 0xBE555555U, 0x3F666666U, 0xBF666666U,
};
#define F32_FINITE_SIZE (sizeof(F32_FINITE) / sizeof(F32_FINITE[0]))

static inline uint64_t splitmix64(uint64_t x)
{
    uint64_t z = (x + 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

struct SveFmaData {
    size_t vl_d, vl_w;
    size_t gn;              /* gather workspace elements (64 * vl_d) */
    uint64_t *seeds_f64;
    uint32_t *seeds_f32;
    uint64_t *m_f64, *a_f64;
    uint64_t *sm_f64, *sa_f64;
    uint32_t *m_f32, *a_f32;
    uint64_t *gather_src;   /* source pool */
    uint64_t *gather_idx;   /* u64 element indices (permuted) */
    /* scatter scratch deliberately NOT here: per-call (worker-private in
     * the test) — the sdcshield fix under validation. */
};

/* ---- scalar goldens AND SVE paths are all noinline: clang -O2 inlines
 * the hw chains into main and then elides them entirely (measured: .s
 * with zero fmla — the compares then read untouched malloc zero pages,
 * FAILS=192 at every tier). Same discipline as sleef_vla_dual's
 * golden_pass/compute_out noinline pair. ---- */
static void __attribute__((noinline))
f64_chain_golden(const struct SveFmaData *d, uint64_t *out)
{
    const size_t lanes = d->vl_d;
    for (size_t lane = 0; lane < lanes; ++lane) {
        uint64_t accw = d->seeds_f64[lane];
        double acc;
        memcpy(&acc, &accw, 8);
        for (size_t i = 0; i < CHAIN_STEPS; ++i) {
            double m, a;
            memcpy(&m, &d->m_f64[i * lanes + lane], 8);
            memcpy(&a, &d->a_f64[i * lanes + lane], 8);
            acc = fma(m, a, acc);
        }
        memcpy(&accw, &acc, 8);
        out[lane] = accw;
    }
}

static void __attribute__((noinline))
f64_special_golden(const struct SveFmaData *d, uint64_t *out)
{
    const size_t lanes = d->vl_d;
    for (size_t lane = 0; lane < lanes; ++lane) {
        uint64_t accw = d->seeds_f64[lane];
        double acc;
        memcpy(&acc, &accw, 8);
        for (size_t i = 0; i < SPECIAL_CHAIN_STEPS; ++i) {
            double m, a;
            memcpy(&m, &d->sm_f64[i * lanes + lane], 8);
            memcpy(&a, &d->sa_f64[i * lanes + lane], 8);
            acc = fma(m, a, acc);
        }
        memcpy(&accw, &acc, 8);
        out[lane] = accw;
    }
}

static void __attribute__((noinline))
f32_chain_golden(const struct SveFmaData *d, uint32_t *out)
{
    const size_t lanes = d->vl_w;
    for (size_t lane = 0; lane < lanes; ++lane) {
        uint32_t accw = d->seeds_f32[lane];
        float acc;
        memcpy(&acc, &accw, 4);
        for (size_t i = 0; i < CHAIN_STEPS; ++i) {
            float m, a;
            memcpy(&m, &d->m_f32[i * lanes + lane], 4);
            memcpy(&a, &d->a_f32[i * lanes + lane], 4);
            acc = fmaf(m, a, acc);
        }
        memcpy(&accw, &acc, 4);
        out[lane] = accw;
    }
}

/* ---- hardware chains (SVE, full runtime VL) ---- */
static void __attribute__((noinline)) f64_chain_hw(const struct SveFmaData *d, uint64_t *out)
{
    const size_t lanes = d->vl_d;
    const svbool_t pg = svptrue_b64();
    svfloat64_t acc = svld1_f64(pg, (const double *)d->seeds_f64);
    for (size_t i = 0; i < CHAIN_STEPS; ++i) {
        svfloat64_t m = svld1_f64(pg, (const double *)&d->m_f64[i * lanes]);
        svfloat64_t a = svld1_f64(pg, (const double *)&d->a_f64[i * lanes]);
        acc = svmla_f64_x(pg, acc, m, a);
    }
    svst1_f64(pg, (double *)out, acc);
}

static void __attribute__((noinline)) f64_special_chain_hw(const struct SveFmaData *d, uint64_t *out)
{
    const size_t lanes = d->vl_d;
    const svbool_t pg = svptrue_b64();
    svfloat64_t acc = svld1_f64(pg, (const double *)d->seeds_f64);
    for (size_t i = 0; i < SPECIAL_CHAIN_STEPS; ++i) {
        svfloat64_t m = svld1_f64(pg, (const double *)&d->sm_f64[i * lanes]);
        svfloat64_t a = svld1_f64(pg, (const double *)&d->sa_f64[i * lanes]);
        acc = svmla_f64_x(pg, acc, m, a);
    }
    svst1_f64(pg, (double *)out, acc);
}

static void __attribute__((noinline)) f32_chain_hw(const struct SveFmaData *d, uint32_t *out)
{
    const size_t lanes = d->vl_w;
    const svbool_t pg = svptrue_b32();
    svfloat32_t acc = svld1_f32(pg, (const float *)d->seeds_f32);
    for (size_t i = 0; i < CHAIN_STEPS; ++i) {
        svfloat32_t m = svld1_f32(pg, (const float *)&d->m_f32[i * lanes]);
        svfloat32_t a = svld1_f32(pg, (const float *)&d->a_f32[i * lanes]);
        acc = svmla_f32_x(pg, acc, m, a);
    }
    svst1_f32(pg, (float *)out, acc);
}

/* ---- category compare (fsu_byteexact_arm precedent) ---- */
static inline bool f64_lane_ok(uint64_t golden, uint64_t actual)
{
    double g, a;
    memcpy(&g, &golden, 8);
    memcpy(&a, &actual, 8);
    if (isnan(g)) return isnan(a);
    if (isinf(g)) return isinf(a) && ((g > 0) == (a > 0));
    if (isnan(a) || isinf(a)) return false;
    return golden == actual;
}

/* ---- gather/scatter round-trip, OUTPUT-POINTER form (the fix) ---- */
static void gather_scatter_golden(const struct SveFmaData *d, uint64_t *golden_out)
{
    for (size_t i = 0; i < d->gn; ++i) {
        double v;
        memcpy(&v, &d->gather_src[d->gather_idx[i]], 8);
        v = fma(v, v, 1.5);
        memcpy(&golden_out[d->gather_idx[i]], &v, 8);
    }
}

static void __attribute__((noinline)) gather_scatter_hw(const struct SveFmaData *d, uint64_t *dst_out)
{
    const size_t n = d->gn;
    const size_t lanes = d->vl_d;
    const svbool_t pg = svptrue_b64();
    const svfloat64_t one_half = svdup_f64(1.5);
    for (size_t off = 0; off < n; off += lanes) {
        svuint64_t vidx = svld1_u64(pg, &d->gather_idx[off]);
        svfloat64_t v = svld1_gather_u64index_f64(
            pg, (const double *)d->gather_src, vidx);
        v = svmla_f64_x(pg, one_half, v, v);
        svst1_scatter_u64index_f64(pg, (double *)dst_out, vidx, v);
    }
}

/* ---- FNV-1a channel B ---- */
static uint64_t fnv = 1469598103934665603ULL;
static void fnv_u64(uint64_t v)
{
    fnv ^= v;
    fnv *= 1099511628211ULL;
}

static unsigned g_fails = 0;

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "run";
    const int poison = (strcmp(mode, "poison") == 0);

    struct SveFmaData d;
    d.vl_d = svcntd();
    d.vl_w = svcntw();
    if (d.vl_d < 2 || d.vl_d > 16 || d.vl_w < 4 || d.vl_w > 32) {
        fprintf(stderr, "unsupported VL (vl_d=%zu vl_w=%zu)\n", d.vl_d, d.vl_w);
        return 3;
    }

    /* init mirror: per-lane seeds */
    d.seeds_f64 = malloc(d.vl_d * sizeof(uint64_t));
    d.seeds_f32 = malloc(d.vl_w * sizeof(uint32_t));
    for (size_t lane = 0; lane < d.vl_d; ++lane)
        d.seeds_f64[lane] = 0x3FF0000000000000ULL |
            (splitmix64(0xC0FFEE00ULL + lane) & 0x000FFFFFFFFFFFFFULL);
    for (size_t lane = 0; lane < d.vl_w; ++lane)
        d.seeds_f32[lane] = 0x3F800000U |
            ((uint32_t)splitmix64(0xC0FFEE00ULL + lane) & 0x007FFFFFU);

    /* init mirror: operand streams (pattern tables, deterministic) */
    const size_t n64 = CHAIN_STEPS * d.vl_d;
    const size_t ns64 = SPECIAL_CHAIN_STEPS * d.vl_d;
    const size_t n32 = CHAIN_STEPS * d.vl_w;
    d.m_f64 = malloc(n64 * 8);  d.a_f64 = malloc(n64 * 8);
    d.sm_f64 = malloc(ns64 * 8); d.sa_f64 = malloc(ns64 * 8);
    d.m_f32 = malloc(n32 * 4);  d.a_f32 = malloc(n32 * 4);
    for (size_t i = 0; i < n64; ++i) {
        d.m_f64[i] = F64_FINITE[(i * 7 + 1) % F64_FINITE_SIZE];
        d.a_f64[i] = F64_FINITE[(i * 5 + 3) % F64_FINITE_SIZE];
    }
    for (size_t i = 0; i < ns64; ++i) {
        d.sm_f64[i] = F64_SPECIAL[(i * 3 + 1) % F64_SPECIAL_SIZE];
        d.sa_f64[i] = F64_SPECIAL[(i * 5 + 2) % F64_SPECIAL_SIZE];
    }
    for (size_t i = 0; i < n32; ++i) {
        d.m_f32[i] = F32_FINITE[(i * 7 + 1) % F32_FINITE_SIZE];
        d.a_f32[i] = F32_FINITE[(i * 5 + 3) % F32_FINITE_SIZE];
    }

    /* init mirror: gather/scatter workspace + deterministic permutation */
    const size_t gn = 64 * d.vl_d;
    d.gn = gn;
    d.gather_src = malloc(gn * 8);
    d.gather_idx = malloc(gn * 8);
    for (size_t i = 0; i < gn; ++i) {
        d.gather_src[i] = d.seeds_f64[i % d.vl_d];
        d.gather_idx[i] = i;
    }
    for (size_t i = gn - 1; i > 0; --i) {
        size_t j = (size_t)(splitmix64(0xBEEF0000ULL + i) % (i + 1));
        uint64_t t = d.gather_idx[i];
        d.gather_idx[i] = d.gather_idx[j];
        d.gather_idx[j] = t;
    }

    /* run mirror: per-call (worker-private) scatter scratch — the fix */
    uint64_t *scatter_dst = malloc(gn * 8);
    uint64_t *scatter_golden = malloc(gn * 8);
    memset(scatter_dst, 0, gn * 8);

    uint64_t *gold64 = malloc(d.vl_d * 8);
    uint64_t *golds64 = malloc(d.vl_d * 8);
    uint32_t *gold32 = malloc(d.vl_w * 4);
    uint64_t *hw64 = malloc(d.vl_d * 8);
    uint64_t *hws64 = malloc(d.vl_d * 8);
    uint32_t *hw32 = malloc(d.vl_w * 4);

    /* The test's TEST_LOOP is a timed loop; the kernel runs a fixed small
     * number of full iterations (golden recompute + 4 workloads + reset). */
    for (int iter = 0; iter < 3; ++iter) {
        f64_chain_golden(&d, gold64);
        f64_special_golden(&d, golds64);
        f32_chain_golden(&d, gold32);
        if (poison && iter == 0) {
            gold64[1] ^= 1ULL;                 /* negative control */
            gold32[1] ^= 1U;
            /* special chain: category compare is payload-agnostic, so a
             * bit-flip on a NaN golden would not trip it — substitute a
             * value of the OPPOSITE category instead */
            double g;
            memcpy(&g, &golds64[1], 8);
            golds64[1] = isnan(g) ? 0x3FF0000000000000ULL
                                  : 0x7FF8000000000000ULL;
        }

        /* (1) f64 finite FMLA chain */
        f64_chain_hw(&d, hw64);
        for (size_t lane = 0; lane < d.vl_d; ++lane) {
            fnv_u64(hw64[lane]);
            if (hw64[lane] != gold64[lane]) {
                fprintf(stderr, "iter %d f64_chain lane %zu golden=%016llx "
                        "actual=%016llx\n", iter, lane,
                        (unsigned long long)gold64[lane],
                        (unsigned long long)hw64[lane]);
                ++g_fails;
            }
        }

        /* (2) f64 special-value chain (category compare) */
        f64_special_chain_hw(&d, hws64);
        for (size_t lane = 0; lane < d.vl_d; ++lane) {
            fnv_u64(hws64[lane]);
            if (!f64_lane_ok(golds64[lane], hws64[lane])) {
                fprintf(stderr, "iter %d f64_special lane %zu golden=%016llx "
                        "actual=%016llx\n", iter, lane,
                        (unsigned long long)golds64[lane],
                        (unsigned long long)hws64[lane]);
                ++g_fails;
            }
        }

        /* (3) f32 finite FMLA chain */
        f32_chain_hw(&d, hw32);
        for (size_t lane = 0; lane < d.vl_w; ++lane) {
            fnv_u64(hw32[lane]);
            if (hw32[lane] != gold32[lane]) {
                fprintf(stderr, "iter %d f32_chain lane %zu golden=%08x "
                        "actual=%08x\n", iter, lane, gold32[lane], hw32[lane]);
                ++g_fails;
            }
        }

        /* (4) gather/scatter round-trip (output-pointer kernels) */
        gather_scatter_hw(&d, scatter_dst);
        gather_scatter_golden(&d, scatter_golden);
        if (poison && iter == 0)
            scatter_golden[gn / 2] ^= 1ULL;    /* negative control */
        for (size_t i = 0; i < gn; ++i) {
            fnv_u64(scatter_dst[i]);
            if (scatter_dst[i] != scatter_golden[i]) {
                fprintf(stderr, "iter %d gather_scatter idx %zu golden=%016llx "
                        "actual=%016llx\n", iter, i,
                        (unsigned long long)scatter_golden[i],
                        (unsigned long long)scatter_dst[i]);
                ++g_fails;
            }
        }
        memset(scatter_dst, 0, gn * 8);        /* the test's per-iter reset */
    }

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
