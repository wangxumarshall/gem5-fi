/* stencil_axis_dual.c — dual-channel extraction of sdcshield test
 * `sve512_stencil_axis_arm` (PR #237 seed-randomized form) for CHAOS/gem5
 * SE-O3 fault injection (plan 2026-10-13-sve-sme-fi-eval Task 4).
 *
 * Channel A: the SVE stencil-accumulation kernel (svmla over the two
 * radius-offset vectors, exactly the test's axis_generic_16x2 shape:
 * res += 0.125 * (src[coord-r] + src[coord+r]) per r, both directions
 * valid at coord=10/RADIUS=6) compared bit-exactly against the runtime
 * scalar reference. Exactness: all terms are integer multiples of 1/8,
 * per-call increment < 12*0.125*512 = 768 and the ITERS-scaled result
 * stays below 2^53 — order-independent accumulation, bit-exact equality
 * (same proof as the sdcshield test).
 *
 *   fixed  — src[i] = i % B_TILE + 1 (the pre-PR#237 pattern) with the
 *            analytic expected 1.5*ITERS*(j+1)
 *   random — src[i] = 1 + xorshift32()%256 (the PR #237 form) with the
 *            runtime scalar reference
 *
 * Channel B: FNV-1a over the hardware result lanes.
 *
 * ITERS is sized for gem5 O3 (~seconds per run; the sdcshield test's 1e8
 * inner iterations are a real-hardware timed-loop quantity).
 *
 * argv: [fixed|random] [seed]
 * Build: clang -static -O2 -march=armv9-a+sve+sme -Wall -Wextra \
 *          -o stencil_axis_dual stencil_axis_dual.c -lm
 * Run:   gem5.opt configs/se/arm_chaos.py --cmd <bin> --sve_vl 4 \
 *          --workload_args "random 1"
 */
#include <arm_sve.h>
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#define RADIUS  6
#define B_TILE_MAX  32   /* upper bound: VL=1024bit => 2*16 lanes */
#define COORD   10
#define EXTENT  56
#define STRIDE  64
#define ITERS   2000

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
static void fnv_u64(uint64_t v)
{
    for (int i = 0; i < 8; ++i) {
        fnv ^= (v >> (8 * i)) & 0xFF;
        fnv *= 1099511628211ULL;
    }
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "random";
    const uint32_t seed = (argc > 2) ? (uint32_t)strtoul(argv[2], 0, 0) : 1;
    const int randomize = (strcmp(mode, "random") == 0);
    xs_state = seed ? seed : 1;

    /* Full-VL support: the kernel writes two result vectors (res0+res1),
     * so the tile width is bt = 2*svcntd() f64 lanes (VL=128..1024-bit
     * -> 4..32). All layout offsets below scale with bt. */
    const int bt = (int)(2 * svcntd());
    if (bt < 4 || bt > B_TILE_MAX) {
        fprintf(stderr, "unsupported VL (bt=%d)\n", bt);
        return 3;
    }

    /* Layout: [extent][stride][B_TILE] doubles (the test's geometry). */
    static double src[EXTENT * STRIDE * B_TILE_MAX];
    const size_t src_n = (size_t)EXTENT * STRIDE * bt;
    for (size_t i = 0; i < src_n; ++i)
        src[i] = randomize ? (double)(1 + xs32() % 256)
                           : (double)(i % bt + 1);
    const double *s_base = src + COORD * STRIDE * bt;

    /* Runtime scalar reference (PR #237 run-side logic): per lane j one
     * kernel call adds sum_r 0.125*(src[coord-r][j] + src[coord+r][j]). */
    double expected[B_TILE_MAX];
    for (int j = 0; j < bt; ++j) expected[j] = 0.0;
    for (size_t r = 1; r <= RADIUS; ++r) {
        const ptrdiff_t off = (ptrdiff_t)(r * STRIDE) * bt;
        for (int j = 0; j < bt; ++j) {
            double delta = 0.0;
            if (COORD >= (int)r)
                delta += s_base[-off + j];
            if (COORD + r < EXTENT)
                delta += s_base[+off + j];
            expected[j] += 0.125 * delta;
        }
    }
    if (!randomize) {
        /* fixed mode degenerates to the pre-PR#237 analytic formula —
         * assert the reference agrees with it (kernel self-check). */
        for (int j = 0; j < bt; ++j)
            if (expected[j] != 1.5 * (double)(j + 1)) {
                fprintf(stderr, "scalar ref != analytic at lane %d: %f vs %f\n",
                        j, expected[j], 1.5 * (double)(j + 1));
                ++g_fails;
            }
    }
    for (int j = 0; j < bt; ++j)
        expected[j] *= (double)ITERS;

    /* The accumulation kernel: ITERS rounds of the two-vector svmla
     * pattern (res0/res1 accumulate; 0.125 coefficients). */
    const svbool_t ptrue = svptrue_b64();
    const int LANES = (int)svcntd();
    double coeff[RADIUS + 1] = {};
    for (size_t r = 1; r <= RADIUS; ++r) coeff[r] = 0.125;
    svfloat64_t res0 = svdup_f64(0.0);
    svfloat64_t res1 = svdup_f64(0.0);

    for (int it = 0; it < ITERS; ++it) {
        for (size_t r = 1; r <= RADIUS; ++r) {
            const ptrdiff_t off = (ptrdiff_t)(r * STRIDE) * bt;
            const svfloat64_t c = svdup_f64(coeff[r]);
            if (COORD >= (int)r) {
                res0 = svmla_f64_m(ptrue, res0,
                                   svld1_f64(ptrue, s_base - off), c);
                res1 = svmla_f64_m(ptrue, res1,
                                   svld1_f64(ptrue, s_base - off + LANES), c);
            }
            if (COORD + r < EXTENT) {
                res0 = svmla_f64_m(ptrue, res0,
                                   svld1_f64(ptrue, s_base + off), c);
                res1 = svmla_f64_m(ptrue, res1,
                                   svld1_f64(ptrue, s_base + off + LANES), c);
            }
        }
    }

    double result[B_TILE_MAX];
    svst1_f64(ptrue, result, res0);
    svst1_f64(ptrue, result + LANES, res1);

    for (int j = 0; j < bt; ++j) {
        fnv_u64(*(uint64_t *)&result[j]);
        if (result[j] != expected[j]) {
            fprintf(stderr, "lane %2d result=%.1f expected=%.1f\n",
                    j, result[j], expected[j]);
            ++g_fails;
        }
    }

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
