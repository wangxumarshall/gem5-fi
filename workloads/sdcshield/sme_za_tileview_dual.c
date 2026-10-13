/* sme_za_tileview_dual.c — dual-channel extraction of sdcshield test
 * `sme_za_tileview_arm` (PR #237 seed-randomized form) for CHAOS/gem5
 * SE-O3 fault injection (plan 2026-10-13-sve-sme-fi-eval Task 6).
 *
 * Kernel (the test's ZA tile-view semantics, f64 at SVL=512):
 *   - load row-major a into za0h via ld1d {za0h.d[w12, 0]}
 *   - round trip  : st1d {za0h.d[w12, 0]}  -> byte-identical a
 *   - transpose   : st1d {za0v.d[w12, 0]}  -> column w12 = a's row image
 *   - slice shift : za0h.d[r, 1] read      -> row written via r+1 mod n
 * Tiles are pure data permutations — no rounding — so channel A is a
 * direct byte-exact permutation golden (unlike the FMOPA kernel, no
 * semantic adaptation is needed).
 *
 *   fixed  — (i*131+j)%977 + 0.5*(i+1) exact doubles (pre-PR#237)
 *   random — (xorshift64()%1024)*64 + (i*n+j) exact distinct integers
 *            (the PR #237 injective-index form)
 *
 * argv: [fixed|random] [seed]
 * Build: clang -static -O2 -march=armv9-a+sve+sme -Wall -Wextra \
 *          -o sme_za_tileview_dual sme_za_tileview_dual.c -lm
 * Run:   gem5.opt configs/se/arm_chaos.py --cmd <bin> --sme_vl 4 \
 *          --workload_args "random 1"
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define N_D_MAX 16  /* upper bound: SVL=1024bit => 16 f64 slices */

static uint64_t xs_state;
static uint64_t xs64(void)
{
    xs_state ^= xs_state << 13;
    xs_state ^= xs_state >> 7;
    xs_state ^= xs_state << 17;
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

/* One smstart/smstop window performing the three views of a into the
 * three output tiles (row-major [r*n + c]). Registers follow the test's
 * kernel shape: w12 slice select, x1 base of the source row. */
static void za_tileview_kernel(const double *a, double *id_a, double *tr_a,
                               double *rot_a, int n)
{
    asm volatile(
        "mov x0, %0\n\t"               /* a              */
        "mov x1, %1\n\t"               /* id_a           */
        "mov x2, %2\n\t"               /* tr_a           */
        "mov x3, %3\n\t"               /* rot_a          */
        "mov x4, %4\n\t"               /* n (runtime)    */
        "smstart sm\n\t"
        "smstart za\n\t"
        "zero {za}\n\t"
        "ptrue p0.d\n\t"
        "mov x9, #0\n"                  /* row = 0        */
        "1:\n\t"
        "cmp x9, x4\n\t"
        "b.ge 2f\n\t"
        "mov w12, w9\n\t"
        "mul x14, x9, x4\n\t"
        "add x10, x0, x14, lsl #3\n\t"   /* &a[r*n] */
        "ld1d {za0h.d[w12, 0]}, p0/z, [x10]\n\t"
        "add x9, x9, #1\n\t"
        "b 1b\n"
        "2:\n\t"
        "mov x9, #0\n"                  /* horizontal readout */
        "3:\n\t"
        "cmp x9, x4\n\t"
        "b.ge 4f\n\t"
        "mov w12, w9\n\t"
        "mul x14, x9, x4\n\t"
        "add x13, x1, x14, lsl #3\n\t"
        "st1d {za0h.d[w12, 0]}, p0, [x13]\n\t"
        "add x9, x9, #1\n\t"
        "b 3b\n"
        "4:\n\t"
        "mov x9, #0\n"                  /* vertical (transpose) readout */
        "5:\n\t"
        "cmp x9, x4\n\t"
        "b.ge 6f\n\t"
        "mov w12, w9\n\t"
        "mul x14, x9, x4\n\t"
        "add x13, x2, x14, lsl #3\n\t"
        "st1d {za0v.d[w12, 0]}, p0, [x13]\n\t"
        "add x9, x9, #1\n\t"
        "b 5b\n"
        "6:\n\t"
        "mov x9, #0\n"                  /* slice-shift readout: za0h.d[r,1] */
        "7:\n\t"
        "cmp x9, x4\n\t"
        "b.ge 8f\n\t"
        "mov w12, w9\n\t"
        "mul x14, x9, x4\n\t"
        "add x13, x3, x14, lsl #3\n\t"
        "st1d {za0h.d[w12, 1]}, p0, [x13]\n\t"
        "add x9, x9, #1\n\t"
        "b 7b\n"
        "8:\n\t"
        "smstop za\n\t"
        "smstop sm\n\t"
        : : "r"(a), "r"(id_a), "r"(tr_a), "r"(rot_a), "r"((long)n)
        : "x4", "x9", "x10", "x13", "x14", "w12", "w14", "w15", "p0", "memory");
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "random";
    const uint64_t seed = (argc > 2) ? strtoull(argv[2], 0, 0) : 1;
    const int randomize = (strcmp(mode, "random") == 0);
    xs_state = seed ? seed : 1;

    /* Full-SVL support: n = f64 slices of the runtime SVL (128..1024-bit
     * -> 2..16). The element-size shift #3 (8 bytes/f64) is
     * SVL-independent and stays an immediate. */
    int64_t svl_bytes = 0;
    asm volatile("rdsvl %0, #1" : "=r"(svl_bytes));
    const int n = (int)(svl_bytes / 8);
    if (n < 2 || n > N_D_MAX) {
        fprintf(stderr, "unsupported SVL %ld bytes\n", (long)svl_bytes);
        return 3;
    }

    static double a[N_D_MAX * N_D_MAX], id_a[N_D_MAX * N_D_MAX],
                  tr_a[N_D_MAX * N_D_MAX], rot_a[N_D_MAX * N_D_MAX];
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < n; ++j) {
            const size_t ij = (size_t)i * n + j;
            if (randomize)
                a[ij] = (double)((xs64() % 1024) * 64 + (i * n + j));
            else
                a[ij] = (double)((i * 131 + j) % 977) + 0.5 * (i + 1);
        }

    za_tileview_kernel(a, id_a, tr_a, rot_a, n);

    /* Channel A: permutation goldens, byte-exact. */
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < n; ++j) {
            const size_t ij = (size_t)i * n + j;
            const size_t ji = (size_t)j * n + i;
            const size_t rot = (size_t)((i + 1) % n) * n + j;
            fnv_u64(*(uint64_t *)&id_a[ij]);
            fnv_u64(*(uint64_t *)&tr_a[ij]);
            fnv_u64(*(uint64_t *)&rot_a[ij]);
            if (id_a[ij] != a[ij]) {
                if (g_fails == 0)
                    fprintf(stderr, "id mismatch @(%d,%d)\n", i, j);
                ++g_fails;
            }
            if (tr_a[ij] != a[ji]) {
                if (g_fails == 0)
                    fprintf(stderr, "transpose mismatch @(%d,%d)\n", i, j);
                ++g_fails;
            }
            if (rot_a[ij] != a[rot]) {
                if (g_fails == 0)
                    fprintf(stderr, "slice-shift mismatch @(%d,%d)\n", i, j);
                ++g_fails;
            }
        }

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
