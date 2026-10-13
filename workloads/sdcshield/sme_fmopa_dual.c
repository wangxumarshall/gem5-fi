/* sme_fmopa_dual.c — dual-channel extraction of sdcshield test
 * `sme_fmopa_stress_arm` (PR #237 seed-randomized form) for CHAOS/gem5
 * SE-O3 fault injection (plan 2026-10-13-sve-sme-fi-eval Task 5).
 *
 * Kernel (from the test's sme_fmopa_kernel): SMSTART sm/za; ZERO {za};
 * K_FMOPA rounds of FMOPA za0.s (outer-product accumulate, f32) over
 * per-round operand vectors; ZA readout via st1w {za0h.s[w12,0]} rows.
 *
 * Channels:
 *   A — byte-exact compare of the readout tile against a scalar fmaf
 *       golden recomputed from the SAME inputs with the same op order.
 *       HONEST BOUNDARY (F4): gem5 implements FMOPA as fplib mul+add
 *       (double rounding); where that diverges from single-rounding fmaf
 *       the compare would fire on an UNINJECTED run. The no-injection
 *       baseline therefore defines per-mode goldens for the FI campaign
 *       (checksum channel), and channel A's fmaf compare is reported
 *       alongside — a channel-A fire on an injected run is Detected only
 *       if the no-injection control for that mode is clean.
 *   B — FNV-1a over the readout tile bits (the primary FI oracle).
 *
 * Operands: |a|,|b| < 0.5625 (the test's bound: 64-round f32 sums stay
 * below 21 — no overflow/NaN, flipped bits survive).
 *   fixed  — (k*37+i*11)%64/64.0 - 0.28125 (pre-PR#237 formula)
 *   random — xorshift32-derived uniform in (-0.5625, 0.5625)
 *
 * argv: [fixed|random] [seed]
 * Build: clang -static -O2 -march=armv9-a+sve+sme -Wall -Wextra \
 *          -o sme_fmopa_dual sme_fmopa_dual.c -lm
 * Run:   gem5.opt configs/se/arm_chaos.py --cmd <bin> --sme_vl 4 \
 *          --workload_args "random 1"
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define N_F32_MAX   32     /* upper bound: SVL=1024bit => 32 f32 lanes */
#define K_FMOPA     64     /* outer-product rounds (SVL-independent) */

static uint32_t xs_state;
static uint32_t xs32(void)
{
    xs_state ^= xs_state << 13;
    xs_state ^= xs_state >> 17;
    xs_state ^= xs_state << 5;
    return xs_state;
}
static float rnd_abs_f32(void)   /* uniform [0, 0.5625) */
{
    return (float)(xs32() >> 8) / (float)(1u << 24) * 0.5625f;
}

static unsigned g_fails = 0;
static uint64_t fnv = 1469598103934665603ULL;
static void fnv_u32(uint32_t v)
{
    fnv ^= v & 0xFF;         fnv *= 1099511628211ULL;
    fnv ^= (v >> 8) & 0xFF;  fnv *= 1099511628211ULL;
    fnv ^= (v >> 16) & 0xFF; fnv *= 1099511628211ULL;
    fnv ^= (v >> 24) & 0xFF; fnv *= 1099511628211ULL;
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "random";
    const uint32_t seed = (argc > 2) ? (uint32_t)strtoul(argv[2], 0, 0) : 1;
    const int randomize = (strcmp(mode, "random") == 0);
    xs_state = seed ? seed : 1;

    /* Full-SVL support: n = f32 lanes of the runtime SVL (128..1024-bit
     * -> 4..32). All geometry below scales with n; the element-size
     * immediates (f32 = 4B) stay constant. */
    int64_t svl_bytes = 0;
    asm volatile("rdsvl %0, #1" : "=r"(svl_bytes));
    const int n = (int)(svl_bytes / 4);
    if (n < 2 || n > N_F32_MAX) {
        fprintf(stderr, "unsupported SVL %ld bytes\n", (long)svl_bytes);
        return 3;
    }
    const int n_lanes = n;

    /* Operand streams, layout [k * n + i] (the test's geometry). */
    static float a[K_FMOPA * N_F32_MAX], b[K_FMOPA * N_F32_MAX];
    for (int k = 0; k < K_FMOPA; ++k)
        for (int i = 0; i < n; ++i) {
            const size_t ki = (size_t)k * n + i;
            if (randomize) {
                a[ki] = (xs32() & 1 ? -1.0f : 1.0f) * rnd_abs_f32();
                b[ki] = (xs32() & 1 ? -1.0f : 1.0f) * rnd_abs_f32();
            } else {
                a[ki] = (float)(((k * 37 + i * 11) % 64) / 64.0 - 0.28125);
                b[ki] = (float)(((k * 53 + i * 29) % 64) / 64.0 - 0.28125);
            }
        }

    /* Scalar golden, same op order. SEMANTIC ADAPTATION (F4, empirically
     * confirmed by the first J1' run: random-mode fmaf golden mismatches
     * gem5's FMOPA on ~70% of tile cells): gem5 implements FMOPA as
     * fplibMul + fplibAdd — double rounding — so the in-sim golden uses
     * the same mul-then-add double rounding. On the fixed-mode discrete
     * 64-level grid both roundings coincide (FAILS=0 with fmaf too).
     * Real-hardware single-rounding correctness is the sdcshield test's
     * own fmaf golden (PR #237), a separate layer from this FI oracle. */
    static float golden[N_F32_MAX * N_F32_MAX];
    memset(golden, 0, sizeof golden);
    for (int k = 0; k < K_FMOPA; ++k)
        for (int r = 0; r < n; ++r)
            for (int c = 0; c < n; ++c)
                golden[(size_t)r * n + c] =
                    a[(size_t)k * n + r] * b[(size_t)k * n + c] +
                    golden[(size_t)r * n + c];

    /* SME kernel: one smstart/smstop window (the test's shape). */
    static float tile[N_F32_MAX * N_F32_MAX];
    {
        const float *pa = a, *pb = b;
        float *pt = tile;
        /* x15 = n (f32 lanes, runtime from SVL); the element-size shift
         * #2 (4 bytes/f32) is SVL-independent and stays an immediate. */
        asm volatile(
            "mov x1, %0\n\t"               /* a            */
            "mov x2, %1\n\t"               /* b            */
            "mov x3, %2\n\t"               /* tile out     */
            "mov x15, %3\n\t"              /* n lanes      */
            "smstart sm\n\t"
            "smstart za\n\t"
            "zero {za}\n\t"
            "ptrue p0.s\n\t"
            "ptrue p1.s\n\t"
            "mov x9, #0\n"                  /* k = 0        */
            "1:\n\t"
            "cmp x9, #64\n\t"
            "b.ge 2f\n\t"
            "mul x14, x9, x15\n\t"         /* k*n elements */
            "add x10, x1, x14, lsl #2\n\t"  /* &a[k*n]      */
            "add x11, x2, x14, lsl #2\n\t"  /* &b[k*n]      */
            "ld1w {z0.s}, p0/z, [x10]\n\t"
            "ld1w {z1.s}, p0/z, [x11]\n\t"
            "fmopa za0.s, p0/m, p1/m, z0.s, z1.s\n\t"
            "add x9, x9, #1\n\t"
            "b 1b\n"
            "2:\n\t"
            "mov x9, #0\n"                  /* row = 0      */
            "3:\n\t"
            "cmp x9, x15\n\t"
            "b.ge 4f\n\t"
            "mov w12, w9\n\t"
            "mul x13, x9, x15\n\t"
            "add x13, x3, x13, lsl #2\n\t"  /* &out[r*n]    */
            "st1w {za0h.s[w12, 0]}, p0, [x13]\n\t"
            "add x9, x9, #1\n\t"
            "b 3b\n"
            "4:\n\t"
            "smstop za\n\t"
            "smstop sm\n\t"
            : : "r"(pa), "r"(pb), "r"(pt), "r"((long)n_lanes)
            : "x1", "x2", "x3", "x9", "x10", "x11", "x13", "x14", "x15", "w12",
              "z0", "z1", "p0", "p1", "memory");
    }

    /* Channel A: byte-exact vs the scalar golden. */
    for (int i = 0; i < n * n; ++i) {
        fnv_u32(*(uint32_t *)&tile[i]);
        if (tile[i] != golden[i]) {
            if (g_fails == 0)
                fprintf(stderr, "tile mismatch @%d hw=%.9g sw=%.9g\n",
                        i, tile[i], golden[i]);
            ++g_fails;
        }
    }

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
