/* sme_fmopa_za_dual.c — semantics-settling dual-channel kernel for the
 * all-VL Phase 2 P2 rework of sdcshield test sme_fmopa_za_arm.
 * Mirrors the REWORKED test asm (same-source): smstart za; zero {za};
 * 256-step FMOPA za0.s chain over per-step operand windows; mova
 * za0v.s[w12,0] readout; st1w. Settles the original test's two
 * never-validated choices empirically:
 *   (a) mova za0v.s[0,0] axis — the tileview .d probe says COLUMN 0, the
 *       test docblock claimed ROW 0; both goldens are computed and the
 *       run decides (byte-exact, per lane);
 *   (b) smstart za-only (no sm) sufficing for FMOPA — the stress twin
 *       uses sm+za; ADJUDICATED 2026-10-23 (gem5 25.1.0.1, tier-1 pilot):
 *       za-only reaches the FIRST fmopa and traps — gem5's SME model
 *       requires SVCR.SM for FMOPA (isa/formats smCheckCode,
 *       insts/sme.isa:298 smEnCheckCode) → SME access trap → vector
 *       VBAR+0x400 → SE-mode page fault panic at guest VA 0x400.
 *       za-only suffices only for the ZA-only ops it passed (zero {za},
 *       mova za0v). This kernel therefore switches to sm+za
 *       (sme_fmopa_dual.c:126-127/155-156 precedent); the sdcshield
 *       rework must use smstart sm+za (or bare smstart) as well.
 * Operands: exact small integers, window layout [s*cols + i]; every
 * product and accumulate is exactly representable in f32, so gem5's
 * fplib double-rounding (F4) coincides with real-hardware single
 * rounding — no F4 adaptation needed.
 * Channels: A = axis discrimination + byte-exact vs the winning golden;
 *           B = FNV-1a over the readout bits.
 * argv: [fixed|random] [seed]; exit 0 / 1 (fails) / 3 (unsupported SVL).
 * Build: gcc -static -O2 -march=armv9-a+sve+sme -Wall -Wextra
 * Run:   gem5.opt configs/se/arm_chaos.py --cpu O3 \
 *          --cmd workloads/sdcshield/sme_fmopa_za_dual \
 *          --sve_vl 4 --sme_vl 4 --workload_args "fixed 1"
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define COLS_MAX 32        /* SVL=1024-bit -> 32 f32 lanes */
#define STEPS    256       /* the test's MOPA_STEPS (SVL-independent) */

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
static void fnv_u32(uint32_t v)
{
    fnv ^= v & 0xFF;         fnv *= 1099511628211ULL;
    fnv ^= (v >> 8) & 0xFF;  fnv *= 1099511628211ULL;
    fnv ^= (v >> 16) & 0xFF; fnv *= 1099511628211ULL;
    fnv ^= (v >> 24) & 0xFF; fnv *= 1099511628211ULL;
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "fixed";
    const uint32_t seed = (argc > 2) ? (uint32_t)strtoul(argv[2], 0, 0) : 1;
    const int randomize = (strcmp(mode, "random") == 0);
    xs_state = seed ? seed : 1;

    int64_t svl_bytes = 0;
    asm volatile("rdsvl %0, #1" : "=r"(svl_bytes));
    const int cols = (int)(svl_bytes / 4);
    if (cols < 4 || cols > COLS_MAX) {
        fprintf(stderr, "unsupported SVL %ld bytes\n", (long)svl_bytes);
        return 3;
    }

    /* Exact-integer operand windows, layout [s*cols + i]. Row 0 and
       column 0 readouts differ by construction (a/b patterns differ). */
    static float a[STEPS * COLS_MAX], b[STEPS * COLS_MAX];
    for (int s = 0; s < STEPS; ++s)
        for (int i = 0; i < cols; ++i) {
            const size_t si = (size_t)s * cols + i;
            if (randomize) {
                a[si] = (float)((xs32() % 7) + 1);
                b[si] = (float)((xs32() % 5) + 1);
            } else {
                a[si] = (float)((si % 7) + 1);
                b[si] = (float)((si % 5) + 1);
            }
        }

    /* Both candidate goldens, exact integer accumulation:
       row 0:     g_row[c] = sum_s z0[0]*z1[c] = sum_s a[s*cols]*b[s*cols+c]
       column 0:  g_col[r] = sum_s z0[r]*z1[0] = sum_s a[s*cols+r]*b[s*cols] */
    static float g_row[COLS_MAX], g_col[COLS_MAX];
    for (int x = 0; x < cols; ++x)
        g_row[x] = g_col[x] = 0.0f;
    for (int s = 0; s < STEPS; ++s)
        for (int x = 0; x < cols; ++x) {
            const size_t s0 = (size_t)s * cols;
            g_row[x] += a[s0] * b[s0 + x];
            g_col[x] += a[s0 + x] * b[s0];
        }

    /* Same-source mirror of the reworked test asm: the window stride
       (cols * 4 bytes) is a REGISTER operand; element size stays fixed. */
    static float out[COLS_MAX];
    {
        const float *pa = a, *pb = b;
        float *po = out;
        long steps = STEPS;
        const size_t stride = (size_t)cols * sizeof(float);
        asm volatile(
            /* sm+za (not za-only): FMOPA requires streaming mode —
             * za-only was adjudicated illegal (traps), see docblock (b). */
            "smstart sm\n\t" "smstart za\n\t"
            "ptrue p0.s\n\t"
            "zero {za}\n\t"
            "mov w12, wzr\n\t"
            "1:\n\t"
            "ld1w {z0.s}, p0/z, [%[a]]\n\t"
            "ld1w {z1.s}, p0/z, [%[b]]\n\t"
            "add %[a], %[a], %[s]\n\t"
            "add %[b], %[b], %[s]\n\t"
            "fmopa za0.s, p0/m, p0/m, z0.s, z1.s\n\t"
            "subs %[n], %[n], #1\n\t"
            "b.ne 1b\n\t"
            "mova z2.s, p0/m, za0v.s[w12, 0]\n\t"
            "st1w {z2.s}, p0, [%[o]]\n\t"
            "smstop za\n\t" "smstop sm\n\t"
            : [a] "+r"(pa), [b] "+r"(pb), [n] "+r"(steps)
            : [o] "r"(po), [s] "r"(stride)
            : "z0", "z1", "z2", "p0", "w12", "memory", "cc");
    }

    for (int i = 0; i < cols; ++i) {
        uint32_t bits;
        memcpy(&bits, &out[i], sizeof bits);
        fnv_u32(bits);
    }

    int row_ok = 1, col_ok = 1;
    for (int i = 0; i < cols; ++i) {
        if (out[i] != g_row[i])
            row_ok = 0;
        if (out[i] != g_col[i])
            col_ok = 0;
    }
    const char *axis = row_ok ? "ROW" : (col_ok ? "COLUMN" : "NEITHER");

    if (row_ok && col_ok) {
        fprintf(stderr, "row/col goldens identical — seed %u degenerate, "
                        "rerun with another seed\n", seed);
        return 1;
    }
    if (!row_ok && !col_ok) {
        for (int i = 0; i < cols && i < 4; ++i)
            fprintf(stderr, "mismatch @%d hw=%.1f row=%.1f col=%.1f\n",
                    i, (double)out[i], (double)g_row[i], (double)g_col[i]);
        ++g_fails;
    }

    printf("sme_fmopa_za_dual: svl=%ld cols=%d axis=%s\n",
           (long)svl_bytes, cols, axis);
    printf("SDCSHIELD_FAILS=%u\n%016llx\n",
           g_fails, (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
