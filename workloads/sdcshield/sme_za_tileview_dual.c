/* sme_za_tileview_dual.c — dual-channel extraction of sdcshield test
 * `sme_za_tileview_arm` (PR #242 full-SVL + injective-formula form) for
 * CHAOS/gem5 SE-O3 fault injection (plan 2026-10-13-sve-sme-fi-eval Task 6).
 *
 * Kernel (the test's ZA tile-view semantics, f64 at runtime SVL):
 *   - load row-major a into za0h via ld1d {za0h.d[w12, 0]}
 *   - round trip  : st1d {za0h.d[w12, 0]}  -> byte-identical a
 *   - transpose   : st1d {za0v.d[w12, 0]}  -> column w12 = a's row image
 *   - slice shift : za0h.d[r, 1] read      -> row written via r+1 mod n
 *   - za1h isolation: load b into za1h, round-trip, then re-read za0h —
 *     a must be unchanged (za0/za1 write isolation)
 * Tiles are pure data permutations — no rounding — so channel A is a
 * direct byte-exact permutation golden (unlike the FMOPA kernel, no
 * semantic adaptation is needed).
 *
 *   fixed  — (i*131+j)%977 + 0.5*(i+1) exact doubles (pre-PR#237);
 *            b = same + 2^52 offset (disjoint value range)
 *   random — ((xs64() >> 21) * 256 + (i*n+j)) exact doubles, and b the
 *            same expression + 2^52 — the PR #242 injective form:
 *            multiplier 256 > max position index n^2-1 = 255 keeps the
 *            decomposition unique, and b's [2^52, 2^52 + 2^51) never
 *            intersects a's [0, 2^51)
 *
 * Same-source note: the kernel below is a mirror of the test's naked
 * function — one struct in x0, all parameters ldr'd to fixed registers
 * (n into x8), so the compiler never assigns an input to a register the
 * asm then clobbers (the inline-asm form let clang pin n to x30/LR,
 * which faulted under gem5; fixed here by mirroring the test's shape).
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

/* Mirror of the test's SmeZaParams: one struct pointer in x0. */
struct ZaParams {
    const double *a;
    const double *b;
    double *id_a;   /* za0h round trip of a           */
    double *tr_a;   /* za0v vertical read = transpose */
    double *rot_a;  /* za0h.d[r, 1] read              */
    double *id_b;   /* za1h round trip of b           */
    double *id_a2;  /* za0h re-read after za1h writes */
    long n;         /* f64 per slice (runtime SVL)    */
};

/* Mirror of the test's naked kernel: five phases against the zero {za}
 * baseline — za0h load, id/tr/slice-shift readout, then b into za1h and
 * the isolation re-read. All row offsets are row*n elements, lsl #3
 * scaled (8 bytes/f64), the exact addressing shape the test uses. */
__attribute__((naked))
static void za_tileview_kernel(const struct ZaParams *p)
{
    asm volatile(
        "ldr x1, [x0, #0]\n\t"
        "ldr x2, [x0, #8]\n\t"
        "ldr x3, [x0, #16]\n\t"
        "ldr x4, [x0, #24]\n\t"
        "ldr x5, [x0, #32]\n\t"
        "ldr x6, [x0, #40]\n\t"
        "ldr x7, [x0, #48]\n\t"
        "ldr x8, [x0, #56]\n\t"     /* n (runtime)   */
        "smstart sm\n\t"
        "smstart za\n\t"
        "zero {za}\n\t"
        "ptrue p0.d\n\t"
        "mov x9, #0\n"
        "1:\n\t"
        "cmp x9, x8\n\t"
        "b.ge 2f\n\t"
        "mov w12, w9\n\t"
        "mul x10, x9, x8\n\t"
        "ld1d {za0h.d[w12, 0]}, p0/z, [x1, x10, lsl #3]\n\t"
        "add x9, x9, #1\n\t"
        "b 1b\n"
        "2:\n\t"
        "mov x9, #0\n"
        "3:\n\t"
        "cmp x9, x8\n\t"
        "b.ge 4f\n\t"
        "mov w12, w9\n\t"
        "mul x10, x9, x8\n\t"
        "st1d {za0h.d[w12, 0]}, p0, [x3, x10, lsl #3]\n\t"
        "st1d {za0v.d[w12, 0]}, p0, [x4, x10, lsl #3]\n\t"
        "st1d {za0h.d[w12, 1]}, p0, [x5, x10, lsl #3]\n\t"
        "add x9, x9, #1\n\t"
        "b 3b\n"
        "4:\n\t"
        "mov x9, #0\n"
        "5:\n\t"
        "cmp x9, x8\n\t"
        "b.ge 6f\n\t"
        "mov w12, w9\n\t"
        "mul x10, x9, x8\n\t"
        "ld1d {za1h.d[w12, 0]}, p0/z, [x2, x10, lsl #3]\n\t"
        "add x9, x9, #1\n\t"
        "b 5b\n"
        "6:\n\t"
        "mov x9, #0\n"
        "7:\n\t"
        "cmp x9, x8\n\t"
        "b.ge 8f\n\t"
        "mov w12, w9\n\t"
        "mul x10, x9, x8\n\t"
        "st1d {za1h.d[w12, 0]}, p0, [x6, x10, lsl #3]\n\t"
        "st1d {za0h.d[w12, 0]}, p0, [x7, x10, lsl #3]\n\t"
        "add x9, x9, #1\n\t"
        "b 7b\n"
        "8:\n\t"
        "smstop za\n\t"
        "smstop sm\n\t"
        "ret\n"
    );
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

    static double a[N_D_MAX * N_D_MAX], b[N_D_MAX * N_D_MAX],
                  id_a[N_D_MAX * N_D_MAX], tr_a[N_D_MAX * N_D_MAX],
                  rot_a[N_D_MAX * N_D_MAX], id_b[N_D_MAX * N_D_MAX],
                  id_a2[N_D_MAX * N_D_MAX];
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < n; ++j) {
            const size_t ij = (size_t)i * n + j;
            if (randomize) {
                /* PR #242 injective form (same as the test): top 43
                 * random bits * 256 + position index; b offset by 2^52
                 * into a disjoint range. */
                a[ij] = (double)((xs64() >> 21) * 256 + (i * n + j));
                b[ij] = (double)((xs64() >> 21) * 256 + (i * n + j))
                      + 4503599627370496.0;
            } else {
                a[ij] = (double)((i * 131 + j) % 977) + 0.5 * (i + 1);
                b[ij] = a[ij] + 4503599627370496.0;
            }
        }

    struct ZaParams p = { a, b, id_a, tr_a, rot_a, id_b, id_a2, n };
    za_tileview_kernel(&p);

    /* Channel A: permutation goldens, byte-exact. The checksum hashes
     * all five output tiles (5*n*n doubles), matching the test's five
     * memcmp phases. */
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < n; ++j) {
            const size_t ij = (size_t)i * n + j;
            const size_t ji = (size_t)j * n + i;
            const size_t rot = (size_t)((i + 1) % n) * n + j;
            fnv_u64(*(uint64_t *)&id_a[ij]);
            fnv_u64(*(uint64_t *)&tr_a[ij]);
            fnv_u64(*(uint64_t *)&rot_a[ij]);
            fnv_u64(*(uint64_t *)&id_b[ij]);
            fnv_u64(*(uint64_t *)&id_a2[ij]);
            if (id_a[ij] != a[ij]) {
                if (g_fails == 0)
                    fprintf(stderr, "id mismatch @(%d,%d)\n", i, j);
                ++g_fails;
            }
            if (id_b[ij] != b[ij]) {
                if (g_fails == 0)
                    fprintf(stderr, "za1 isolation mismatch @(%d,%d)\n", i, j);
                ++g_fails;
            }
            if (id_a2[ij] != a[ij]) {
                if (g_fails == 0)
                    fprintf(stderr, "za0 re-read mismatch @(%d,%d)\n", i, j);
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
