/* fpu_special_sve_dual.c — dual-channel extraction of sdcshield test
 * `fpu_special_values_sve` (PR #237 seed-randomized form) for CHAOS/gem5
 * SE-O3 fault injection (plan 2026-10-13-sve-sme-fi-eval Task 3).
 *
 * Channel A (detection semantics, from the test): sweep svmla_f32_x /
 * svmla_f64_x over the special-value cartesian product on all SVE lanes;
 * per-lane compare vs fmaf/fma — NaN-class-only when either side is NaN
 * (IEEE leaves NaN payload propagation implementation-defined), byte-exact
 * otherwise. First mismatch increments g_fails (report_fail semantics
 * adapted to counting; detection-neutral).
 *
 * Channel B (independent oracle): FNV-1a over every hw lane result —
 * separates Escape (clean channel-A check, wrong state) from Masked.
 *
 * Input modes (PR #237 before/after):
 *   fixed  — the original 12-value fixed IEEE specials table
 *   random — 12 fixed specials + 4 RNG-generated finite values (xorshift32,
 *            seeded, reproducible; models the framework-RNG randomization)
 *
 * argv: [fixed|random] [seed]   (defaults: random 1)
 * Output protocol: "SDCSHIELD_FAILS=<uint>" line, then a 16-hex FNV line.
 * exit = g_fails ? 1 : 0.
 *
 * Build: clang -static -O2 -march=armv9-a+sve+sme -o fpu_special_sve_dual \
 *          fpu_special_sve_dual.c -lm
 * Run:   gem5.opt configs/se/arm_chaos.py --cmd <bin> --sve_vl 4 \
 *          --workload_args "random 1"
 */
#include <arm_sve.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

static uint32_t xs_state;
static uint32_t xs32(void)               /* xorshift32, seedable */
{
    xs_state ^= xs_state << 13;
    xs_state ^= xs_state >> 17;
    xs_state ^= xs_state << 5;
    return xs_state;
}
static float rnd_f32(void)               /* finite |v| < 1 */
{
    return (xs32() & 1 ? -1.0f : 1.0f) *
           (float)(xs32() >> 8) / (float)(1u << 24);
}
static double rnd_f64(void)
{
    return (xs32() & 1 ? -1.0 : 1.0) *
           (double)(xs32() >> 8) / (double)(1u << 24);
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

/* std::numeric_limits replacements for a freestanding-friendly static C. */
static float  stdnumeric_denorm_min_f32(void) { return 1.401298464324817e-45f; }
static float  stdnumeric_max_f32(void)        { return 3.4028234663852886e+38f; }
static float  stdnumeric_min_f32(void)        { return 1.1754943508222875e-38f; }
static double stdnumeric_denorm_min_f64(void) { return 4.9406564584124654e-324; }
static double stdnumeric_max_f64(void)        { return 1.7976931348623157e+308; }
static double stdnumeric_min_f64(void)        { return 2.2250738585072014e-308; }

static const int NUM_SPECIALS_FIXED = 12;
static const int NUM_SPECIALS_RAND  = 16;

static void build_specials_f32(float *t, int n, int randomize)
{
    t[0]  = NAN;
    t[1]  = __builtin_nansf("");
    t[2]  = INFINITY;
    t[3]  = -INFINITY;
    t[4]  = 0.0f;
    t[5]  = -0.0f;
    t[6]  =  stdnumeric_denorm_min_f32();
    t[7]  = -stdnumeric_denorm_min_f32();
    t[8]  =  stdnumeric_max_f32();
    t[9]  = -stdnumeric_max_f32();
    t[10] =  stdnumeric_min_f32();
    t[11] = -stdnumeric_min_f32();
    for (int i = 12; i < n; ++i)
        t[i] = randomize ? rnd_f32() : 0.5f * (i - 11); /* fixed-mode tail
                                            is inert: n stays 12 there */
}
static void build_specials_f64(double *t, int n, int randomize)
{
    t[0]  = NAN;
    t[1]  = __builtin_nans("");
    t[2]  = INFINITY;
    t[3]  = -INFINITY;
    t[4]  = 0.0;
    t[5]  = -0.0;
    t[6]  =  stdnumeric_denorm_min_f64();
    t[7]  = -stdnumeric_denorm_min_f64();
    t[8]  =  stdnumeric_max_f64();
    t[9]  = -stdnumeric_max_f64();
    t[10] =  stdnumeric_min_f64();
    t[11] = -stdnumeric_min_f64();
    for (int i = 12; i < n; ++i)
        t[i] = randomize ? rnd_f64() : 0.25 * (i - 11);
}

static uint32_t bits_of_f32(float f) { uint32_t u; memcpy(&u, &f, 4); return u; }
static uint64_t bits_of_f64(double d) { uint64_t u; memcpy(&u, &d, 8); return u; }

static int sweep_f32(const float *a_t, const float *b_t, const float *c_t, int n)
{
    int mismatches = 0;
    const int lanes = (int)svcntw();
    float hwv[32];
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < n; ++j)
            for (int k = 0; k < n; ++k) {
                const float a = a_t[i], b = b_t[j], c = c_t[k];
                svbool_t pg = svptrue_b32();
                svfloat32_t vd = svmla_f32_x(pg, svdup_f32(c),
                                             svdup_f32(a), svdup_f32(b));
                svst1_f32(pg, hwv, vd);
                const float sw = fmaf(a, b, c);
                const uint32_t sw_bits = bits_of_f32(sw);
                for (int lane = 0; lane < lanes && lane < 32; ++lane) {
                    fnv_u64(bits_of_f32(hwv[lane]) ^ 0xDEADBEEF);
                    const bool hw_nan = isnan(hwv[lane]);
                    const bool sw_nan = isnan(sw);
                    const bool ok = (hw_nan || sw_nan) ? (hw_nan && sw_nan)
                                    : (bits_of_f32(hwv[lane]) == sw_bits);
                    if (!ok && mismatches == 0)
                        fprintf(stderr,
                                "f32 mismatch a=%08x b=%08x c=%08x "
                                "hw=%08x sw=%08x\n",
                                bits_of_f32(a), bits_of_f32(b), bits_of_f32(c),
                                bits_of_f32(hwv[lane]), sw_bits);
                    mismatches += !ok;
                }
            }
    return mismatches;
}

static int sweep_f64(const double *a_t, const double *b_t, const double *c_t, int n)
{
    int mismatches = 0;
    const int lanes = (int)svcntd();
    double hwv[16];
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < n; ++j)
            for (int k = 0; k < n; ++k) {
                const double a = a_t[i], b = b_t[j], c = c_t[k];
                svbool_t pg = svptrue_b64();
                svfloat64_t vd = svmla_f64_x(pg, svdup_f64(c),
                                             svdup_f64(a), svdup_f64(b));
                svst1_f64(pg, hwv, vd);
                const double sw = fma(a, b, c);
                const uint64_t sw_bits = bits_of_f64(sw);
                for (int lane = 0; lane < lanes && lane < 16; ++lane) {
                    fnv_u64(bits_of_f64(hwv[lane]) ^ 0xFEEDFACE);
                    const bool hw_nan = isnan(hwv[lane]);
                    const bool sw_nan = isnan(sw);
                    const bool ok = (hw_nan || sw_nan) ? (hw_nan && sw_nan)
                                    : (bits_of_f64(hwv[lane]) == sw_bits);
                    if (!ok && mismatches == 0)
                        fprintf(stderr,
                                "f64 mismatch a=%016lx b=%016lx c=%016lx "
                                "hw=%016lx sw=%016lx\n",
                                bits_of_f64(a), bits_of_f64(b), bits_of_f64(c),
                                bits_of_f64(hwv[lane]), sw_bits);
                    mismatches += !ok;
                }
            }
    return mismatches;
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "random";
    const uint32_t seed = (argc > 2) ? (uint32_t)strtoul(argv[2], 0, 0) : 1;
    const int randomize = (strcmp(mode, "random") == 0);
    const int n = randomize ? NUM_SPECIALS_RAND : NUM_SPECIALS_FIXED;
    xs_state = seed ? seed : 1;

    float a32[16], b32[16], c32[16];
    double a64[16], b64[16], c64[16];
    /* independent draws per table, as the test builds each table fresh */
    build_specials_f32(a32, n, randomize);
    build_specials_f32(b32, n, randomize);
    build_specials_f32(c32, n, randomize);
    build_specials_f64(a64, n, randomize);
    build_specials_f64(b64, n, randomize);
    build_specials_f64(c64, n, randomize);

    g_fails += sweep_f32(a32, b32, c32, n);
    g_fails += sweep_f64(a64, b64, c64, n);

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
