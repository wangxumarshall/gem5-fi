/* sleef_vla_dual.c — dual-channel extraction of sdcshield test `sleef_sve`
 * (PR #286 true-VLA migration, all-VL Phase 2 P5) for gem5 SE-O3 all-VL
 * functional validation (merge blocker for feat/sleef-eigen-allvl).
 *
 * The validated artifact is the vendored SLEEF 3.9.0 SVE library ITSELF:
 * this kernel links the SAME libsleef.a machine code the sdcshield
 * tests_sve_vla library links (sdcshield third-party/sleef/install;
 * archive disassembly re-verified at kernel-authoring time: the FMA-variant
 * SVE member is pure VLA — 13 cntd / 21 cntp / 6 rdvl, ZERO pattern-immediate
 * ptrue, i.e. no -msve-vector-bits fixed-width residue).
 *
 * Same-source mirror of sleef_sve.cpp (tests/cpu/sleef/sleef_sve.cpp):
 *   - input construction: the test's exact domain mappings over u53
 *     uniforms (trig [-pi,pi] / exp [-20,20) / log positive; float tier
 *     narrowed with the test's 1e-30f log offset)
 *   - loop shape: i += svcntd()/svcntw() stepping with svwhilelt_b64/b32
 *     tail-truncated predicates — exact at EVERY runtime VL
 *   - the 12-function matrix, in the test's own order:
 *       double u10 : sin/cos/exp/log
 *       float  u10 : sin/cos/exp/log
 *       double u35 : sin/cos/log/exp2 (u35 SVE has no exp; exp2 is the
 *                    independent FMA-chain stand-in)
 *
 * NELEMS=1028: inside the test's nelems knob domain (>=128, multiple of 4)
 * and chosen == 4 (mod 32) so the svwhilelt tails ACTIVELY truncate at the
 * 256/512/1024-bit tiers (float/double tails of 4 lanes); at 128-bit a
 * multiple-of-4 count never tails — exactly the test's documented alignment
 * nicety. The historical ELEMS=1024 would exercise zero tails at every tier.
 *
 * Channel A (golden, the test's init-vs-run structure): pass 1 computes all
 *   goldens with the SLEEF SVE kernels (mirrors sleef_compute_goldens),
 *   checks the test's finiteness canary bounds, then pass 2 recomputes into
 *   the od/of scratch (mirrors the run-side compute-out) and byte-compares
 *   per family (the test's memcmp_or_fail semantics, counted instead of
 *   aborting). CSE note: SLEEF_CONST is __attribute__((const)), so the two
 *   passes live in two __attribute__((noinline)) functions — a single
 *   function would let clang -O2 elide the second SLEEF call sequence and
 *   the compare would validate nothing.
 *
 * Channel B (checksum): FNV-1a over every pass-2 output lane in fixed
 *   family order. Cross-tier byte-identity anchor: fixed inputs are
 *   position-deterministic and random inputs are xs64-seeded, so lane
 *   VALUES are identical at every VL; per-lane-pure kernels then force the
 *   checksum to be bit-identical across all four VL tiers for a given
 *   mode+seed — the PR's cross-tier byte-identity claim is judged HERE
 *   (a tier-dependent checksum is a FAIL-grade finding, not noise).
 *
 *   fixed  — position-deterministic u53 (splitmix64 step of the element
 *            index, seed-free) through the test's exact domain mappings
 *   random — xs64() >> 11 / 2^53 (the test's uniform01 form), seed=argv[2]
 *
 * argv: [fixed|random] [seed]
 * Build: make sleef_vla_dual (Makefile adds the vendored-SLEEF include/lib
 *        paths and mirrors the test TU's -march=armv8.2-a+sve)
 * Run:   gem5.opt configs/se/arm_chaos.py --cmd <bin> --sve_vl 4 \
 *          --workload_args "random 1"
 */
#include <arm_sve.h>
#include <sleef.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* per-family element count — see header: 1028 == 4 (mod 32), inside the
 * test's knob domain, tails actively truncate at 256/512/1024-bit */
#define NELEMS 1028

static uint64_t xs_state;
static uint64_t xs64(void)
{
    xs_state ^= xs_state << 13;
    xs_state ^= xs_state >> 7;
    xs_state ^= xs_state << 17;
    return xs_state;
}

/* the test's uniform01, verbatim mapping (top 53 bits over 2^53) */
static double uniform01(void)
{
    return (double)(xs64() >> 11) / 9007199254740992.0;
}

/* fixed mode: position-deterministic u53 — one splitmix64 step of the
 * element index (seed-free, well-spread), same /2^53 mapping */
static double uniform01_pos(int i)
{
    uint64_t h = (uint64_t)i + 0x9E3779B97F4A7C15ULL;
    h ^= h >> 30; h *= 0xBF58476D1CE4E5B9ULL;
    h ^= h >> 27; h *= 0x94D049BB133111EBULL;
    h ^= h >> 31;
    return (double)(h >> 11) / 9007199254740992.0;
}

static unsigned g_fails = 0;
static uint64_t fnv = 1469598103934665603ULL;
static void fnv_u64(uint64_t v)
{
    for (int i = 0; i < 8; ++i) {
        fnv ^= (v >> (8 * i)) & 0xFF;
        fnv *= 1099511628211ULL;
    }
}
static void fnv_u32(uint32_t v)
{
    for (int i = 0; i < 4; ++i) {
        fnv ^= (v >> (8 * i)) & 0xFF;
        fnv *= 1099511628211ULL;
    }
}

/* shared input/output state (the test's sleef_test_data arrays, flattened) */
static double xd_trig[NELEMS], xd_exp[NELEMS], xd_log[NELEMS];
static float  xf_trig[NELEMS], xf_exp[NELEMS], xf_log[NELEMS];
static double gd_sin[NELEMS], gd_cos[NELEMS], gd_exp[NELEMS], gd_log[NELEMS];
static float  gf_sin[NELEMS], gf_cos[NELEMS], gf_exp[NELEMS], gf_log[NELEMS];
static double gd_sin35[NELEMS], gd_cos35[NELEMS], gd_log35[NELEMS],
              gd_exp2_35[NELEMS];
static double od[NELEMS];
static float  of[NELEMS];

/* Fill the input arrays with the test's exact domain mappings — same
 * per-domain loop order as sleef_fill_inputs (trig-d, exp-d, log-d,
 * trig-f, exp-f, log-f; one uniform per element, float tier narrows the
 * same double u the test narrows). */
static void fill_inputs(int randomize)
{
    for (int i = 0; i < NELEMS; ++i) {
        double u = randomize ? uniform01() : uniform01_pos(i);
        xd_trig[i] = (u * 2.0 - 1.0) * 3.141592653589793;   /* [-pi, pi] */
    }
    for (int i = 0; i < NELEMS; ++i) {
        double u = randomize ? uniform01() : uniform01_pos(i);
        xd_exp[i] = (u * 2.0 - 1.0) * 20.0;                 /* [-20, 20) */
    }
    for (int i = 0; i < NELEMS; ++i) {
        double u = randomize ? uniform01() : uniform01_pos(i);
        xd_log[i] = (u + 1.0e-300) * 1.0e10;                /* positive   */
    }
    for (int i = 0; i < NELEMS; ++i) {
        float u = (float)(randomize ? uniform01() : uniform01_pos(i));
        xf_trig[i] = (u * 2.0f - 1.0f) * 3.14159265f;       /* [-pi, pi]  */
    }
    for (int i = 0; i < NELEMS; ++i) {
        float u = (float)(randomize ? uniform01() : uniform01_pos(i));
        xf_exp[i] = (u * 2.0f - 1.0f) * 20.0f;              /* [-20, 20)  */
    }
    for (int i = 0; i < NELEMS; ++i) {
        float u = (float)(randomize ? uniform01() : uniform01_pos(i));
        xf_log[i] = (u + 1.0e-30f) * 1.0e10f;               /* positive   */
    }
}

/* Pass 1 — the test's sleef_compute_goldens, verbatim loop shapes and
 * call order (u35 lines re-load their inputs exactly like the test).
 * noinline: keeps clang -O2 from merging this pass with pass 2 across the
 * __attribute__((const)) SLEEF calls. */
static void __attribute__((noinline)) golden_pass(void)
{
    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svfloat64_t x = svld1_f64(pg, &xd_trig[i]);
        svst1_f64(pg, &gd_sin[i], Sleef_sindx_u10sve(x));
        svst1_f64(pg, &gd_cos[i], Sleef_cosdx_u10sve(x));
        x = svld1_f64(pg, &xd_exp[i]);
        svst1_f64(pg, &gd_exp[i], Sleef_expdx_u10sve(x));
        x = svld1_f64(pg, &xd_log[i]);
        svst1_f64(pg, &gd_log[i], Sleef_logdx_u10sve(x));
        /* u35 second tier: same inputs, the OTHER polynomial implementation */
        svst1_f64(pg, &gd_sin35[i],
                  Sleef_sindx_u35sve(svld1_f64(pg, &xd_trig[i])));
        svst1_f64(pg, &gd_cos35[i],
                  Sleef_cosdx_u35sve(svld1_f64(pg, &xd_trig[i])));
        svst1_f64(pg, &gd_log35[i],
                  Sleef_logdx_u35sve(svld1_f64(pg, &xd_log[i])));
        /* u35 has NO exp — exp2 is the independent-chain stand-in */
        svst1_f64(pg, &gd_exp2_35[i],
                  Sleef_exp2dx_u35sve(svld1_f64(pg, &xd_exp[i])));
    }
    for (int i = 0; i < NELEMS; i += (int)svcntw()) {
        const svbool_t pgf = svwhilelt_b32((uint64_t)i, (uint64_t)NELEMS);
        svfloat32_t x = svld1_f32(pgf, &xf_trig[i]);
        svst1_f32(pgf, &gf_sin[i], Sleef_sinfx_u10sve(x));
        svst1_f32(pgf, &gf_cos[i], Sleef_cosfx_u10sve(x));
        x = svld1_f32(pgf, &xf_exp[i]);
        svst1_f32(pgf, &gf_exp[i], Sleef_expfx_u10sve(x));
        x = svld1_f32(pgf, &xf_log[i]);
        svst1_f32(pgf, &gf_log[i], Sleef_logfx_u10sve(x));
    }
}

/* The test's init-time finiteness tripwire, same bounds: a NaN/Inf golden
 * would make the byte-exact comparison meaningless (NaN != NaN). */
static void canary_d(const char *name, const double *g, double lo, double hi)
{
    for (int i = 0; i < NELEMS; ++i)
        if (!(g[i] >= lo && g[i] <= hi)) { /* NaN fails both, like != chain */
            fprintf(stderr, "%s golden not finite/in-range @%d: %a\n",
                    name, i, g[i]);
            ++g_fails;
        }
}
static void canary_f(const char *name, const float *g, float lo, float hi)
{
    for (int i = 0; i < NELEMS; ++i)
        if (!(g[i] >= lo && g[i] <= hi)) {
            fprintf(stderr, "%s golden not finite/in-range @%d: %a\n",
                    name, i, (double)g[i]);
            ++g_fails;
        }
}

/* per-family byte-exact compare (memcmp_or_fail semantics, counted) +
 * channel-B FNV update, double tier */
static void check_d(const char *name, const double *out, const double *gold)
{
    for (int i = 0; i < NELEMS; ++i) {
        uint64_t a, b;
        memcpy(&a, &out[i], sizeof(a));
        memcpy(&b, &gold[i], sizeof(b));
        fnv_u64(a);
        if (a != b) {
            if (g_fails == 0)
                fprintf(stderr, "%s mismatch @%d: out=%016llx gold=%016llx\n",
                        name, i, (unsigned long long)a,
                        (unsigned long long)b);
            ++g_fails;
        }
    }
}
/* float tier */
static void check_f(const char *name, const float *out, const float *gold)
{
    for (int i = 0; i < NELEMS; ++i) {
        uint32_t a, b;
        memcpy(&a, &out[i], sizeof(a));
        memcpy(&b, &gold[i], sizeof(b));
        fnv_u32(a);
        if (a != b) {
            if (g_fails == 0)
                fprintf(stderr, "%s mismatch @%d: out=%08x gold=%08x\n",
                        name, i, a, b);
            ++g_fails;
        }
    }
}

/* Pass 2 — the test's run-side compute-out: per-family loops into the
 * thread-scratch-equivalent od/of, then the byte-exact compare. Same
 * noinline rationale as golden_pass. Family order = the run loop's. */
static void __attribute__((noinline)) compute_out(void)
{
    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_sindx_u10sve(svld1_f64(pg, &xd_trig[i])));
    }
    check_d("sin double sve", od, gd_sin);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_cosdx_u10sve(svld1_f64(pg, &xd_trig[i])));
    }
    check_d("cos double sve", od, gd_cos);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_expdx_u10sve(svld1_f64(pg, &xd_exp[i])));
    }
    check_d("exp double sve", od, gd_exp);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_logdx_u10sve(svld1_f64(pg, &xd_log[i])));
    }
    check_d("log double sve", od, gd_log);

    for (int i = 0; i < NELEMS; i += (int)svcntw()) {
        const svbool_t pgf = svwhilelt_b32((uint64_t)i, (uint64_t)NELEMS);
        svst1_f32(pgf, &of[i],
                  Sleef_sinfx_u10sve(svld1_f32(pgf, &xf_trig[i])));
    }
    check_f("sin float sve", of, gf_sin);

    for (int i = 0; i < NELEMS; i += (int)svcntw()) {
        const svbool_t pgf = svwhilelt_b32((uint64_t)i, (uint64_t)NELEMS);
        svst1_f32(pgf, &of[i],
                  Sleef_cosfx_u10sve(svld1_f32(pgf, &xf_trig[i])));
    }
    check_f("cos float sve", of, gf_cos);

    for (int i = 0; i < NELEMS; i += (int)svcntw()) {
        const svbool_t pgf = svwhilelt_b32((uint64_t)i, (uint64_t)NELEMS);
        svst1_f32(pgf, &of[i],
                  Sleef_expfx_u10sve(svld1_f32(pgf, &xf_exp[i])));
    }
    check_f("exp float sve", of, gf_exp);

    for (int i = 0; i < NELEMS; i += (int)svcntw()) {
        const svbool_t pgf = svwhilelt_b32((uint64_t)i, (uint64_t)NELEMS);
        svst1_f32(pgf, &of[i],
                  Sleef_logfx_u10sve(svld1_f32(pgf, &xf_log[i])));
    }
    check_f("log float sve", of, gf_log);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_sindx_u35sve(svld1_f64(pg, &xd_trig[i])));
    }
    check_d("sin35 double sve", od, gd_sin35);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_cosdx_u35sve(svld1_f64(pg, &xd_trig[i])));
    }
    check_d("cos35 double sve", od, gd_cos35);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_logdx_u35sve(svld1_f64(pg, &xd_log[i])));
    }
    check_d("log35 double sve", od, gd_log35);

    for (int i = 0; i < NELEMS; i += (int)svcntd()) {
        const svbool_t pg = svwhilelt_b64((uint64_t)i, (uint64_t)NELEMS);
        svst1_f64(pg, &od[i],
                  Sleef_exp2dx_u35sve(svld1_f64(pg, &xd_exp[i])));
    }
    check_d("exp2_35 double sve", od, gd_exp2_35);
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "random";
    const uint64_t seed = (argc > 2) ? strtoull(argv[2], 0, 0) : 1;
    const int randomize = (strcmp(mode, "random") == 0);
    xs_state = seed ? seed : 1;

    /* all-VL gate: 128..1024-bit (svcntb 16..128 bytes), like the test's
     * arm64_require_sve_vl(128, 1024) range check */
    const uint64_t vl_bytes = svcntb();
    if (vl_bytes < 16 || vl_bytes > 128) {
        fprintf(stderr, "unsupported VL %llu bytes\n",
                (unsigned long long)vl_bytes);
        return 3;
    }

    /* geometry line -> stderr (stdout stays the 2-line convention) */
    fprintf(stderr,
            "sleef_vla_dual: mode=%s seed=%llu nelems=%d vl_bytes=%llu "
            "svcntd=%u svcntw=%u\n",
            mode, (unsigned long long)seed, NELEMS,
            (unsigned long long)vl_bytes,
            (unsigned)svcntd(), (unsigned)svcntw());

    fill_inputs(randomize);
    golden_pass();

    /* finiteness canary on the goldens — the test's exact bounds */
    canary_d("sin u10", gd_sin, -1.0, 1.0);
    canary_d("cos u10", gd_cos, -1.0, 1.0);
    canary_d("exp u10", gd_exp, 0.0, 1.0e300);
    canary_d("log u10", gd_log, -1.0e300, 1.0e300);
    canary_f("sin u10f", gf_sin, -1.0f, 1.0f);
    canary_f("cos u10f", gf_cos, -1.0f, 1.0f);
    canary_f("exp u10f", gf_exp, 0.0f, 1.0e30f);
    canary_f("log u10f", gf_log, -1.0e30f, 1.0e30f);
    canary_d("sin u35", gd_sin35, -1.0, 1.0);
    canary_d("cos u35", gd_cos35, -1.0, 1.0);
    canary_d("log u35", gd_log35, -1.0e300, 1.0e300);
    canary_d("exp2 u35", gd_exp2_35, 0.0, 1.0e7);

    compute_out();

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
