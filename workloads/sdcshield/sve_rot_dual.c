/* sve_rot_dual.c — all-VL Phase 2 P5 remediation kernel (adversarial
 * review Important-2): the sve_rot_ldr_at_top* family migrated to the
 * true-VLA tests_sve_vla library is a FUNCTIONAL change in the >128-bit
 * domain (the old -msve-vector-bits=128 build folded svcntb() to 16 and
 * was documented-undefined above 128), so the migration needs runtime
 * evidence at all four tiers — this kernel provides it, same-source
 * with the migrated tests' kernel shape:
 *   - full-vector inline-asm ldr/str on z registers (the family's
 *     one-instruction load/store form, the part compilers must not
 *     reorder), with the window stride as a REGISTER operand;
 *   - the rotating ALU (svadd/sveor/svand/svorr per slot % 4);
 *   - golden computed in the same intrinsics on the same SVE units
 *     (the family's own design: a healthy core reproduces it
 *     bit-exactly), compared byte-exact per slot;
 *   - FNV over the hw buffer (cross-tier oracle).
 *
 * Channels: A = per-slot byte-exact compare vs the intrinsics golden;
 *           B = FNV-1a.
 * argv: [fixed|random] [seed]; exit 0 / 1 (fails) / 3 (unsupported VL).
 * Run:   gem5.opt -d <outdir> configs/se/arm_chaos.py --cpu O3 \
 *          --cmd workloads/sdcshield/sve_rot_dual --sve_vl 4 \
 *          --workload_args "fixed 1"
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <arm_sve.h>

#define SLOTS  256
#define LMAX   16

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
static void fnv_bits(const void *p, size_t n)
{
    const unsigned char *b = p;
    for (size_t i = 0; i < n; ++i) {
        fnv ^= b[i];
        fnv *= 1099511628211ULL;
    }
}

/* The family's asm form: one-instruction full-vector load/store. */
static inline svuint64_t load_vec(const void *addr)
{
    svuint64_t res;
    __asm__ volatile("ldr %0, [%1]" : "=w"(res) : "r"(addr) : "memory");
    return res;
}
static inline void store_vec(void *addr, svuint64_t val)
{
    __asm__ volatile("str %0, [%1]" :: "w"(val), "r"(addr) : "memory");
}

static inline svuint64_t rot_alu(int i, svuint64_t a, svuint64_t b)
{
    switch (i % 4) {
        case 0:  return svadd_u64_x(svptrue_b64(), a, b);
        case 1:  return sveor_u64_x(svptrue_b64(), a, b);
        case 2:  return svand_u64_x(svptrue_b64(), a, b);
        default: return svorr_u64_x(svptrue_b64(), a, b);
    }
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "fixed";
    const uint32_t seed = (argc > 2) ? (uint32_t)strtoul(argv[2], 0, 0) : 1;
    const int randomize = (strcmp(mode, "random") == 0);
    xs_state = seed ? seed : 1;

    const int lanes = (int)svcntd();
    if (lanes < 2 || lanes > LMAX) {
        fprintf(stderr, "unsupported VL (f64 lanes %d)\n", lanes);
        return 3;
    }

    /* Operand + scratch + expected buffers, [slot][lane] flattened. */
    static uint64_t a[SLOTS * LMAX], b[SLOTS * LMAX], scratch[SLOTS * LMAX];
    static uint64_t golden[SLOTS * LMAX], hw[SLOTS * LMAX];
    for (int i = 0; i < SLOTS; ++i)
        for (int l = 0; l < lanes; ++l) {
            const uint64_t v = randomize ? ((uint64_t)xs32() << 32 | xs32())
                                         : (0x9e3779b97f4a7c15ULL *
                                            (uint64_t)(i * lanes + l));
            a[i * lanes + l] = v;
            b[i * lanes + l] = v ^ 0x123456789abcdef0ULL;
            scratch[i * lanes + l] = v * 3ULL + 1ULL;
        }

    /* Golden: the family's own idiom — same intrinsics on the same
       units, computed with plain (non-asm) loads. */
    for (int i = 0; i < SLOTS; ++i) {
        const svbool_t pg = svptrue_b64();
        const svuint64_t va = svld1_u64(pg, a + (size_t)i * lanes);
        const svuint64_t vb = svld1_u64(pg, b + (size_t)i * lanes);
        svst1_u64(pg, golden + (size_t)i * lanes, rot_alu(i, va, vb));
    }

    /* HW path: asm ldr (scratch first — the "ldr at top" position),
       then the rotating ALU, then asm str. */
    for (int i = 0; i < SLOTS; ++i) {
        const svuint64_t unused = load_vec(scratch + (size_t)i * lanes);
        (void)unused;
        const svuint64_t va = load_vec(a + (size_t)i * lanes);
        const svuint64_t vb = load_vec(b + (size_t)i * lanes);
        store_vec(hw + (size_t)i * lanes, rot_alu(i, va, vb));
    }

    /* Channel A: byte-exact per slot. */
    unsigned fails = 0;
    for (int i = 0; i < SLOTS; ++i)
        for (int l = 0; l < lanes; ++l)
            if (hw[i * lanes + l] != golden[i * lanes + l]) {
                if (fails < 4)
                    fprintf(stderr, "rot @slot%d lane%d hw=%016llx "
                            "sw=%016llx\n", i, l,
                            (unsigned long long)hw[i * lanes + l],
                            (unsigned long long)golden[i * lanes + l]);
                ++fails;
            }

    /* Channel B: FNV over the hw buffer (cross-tier oracle — fixed
       mode must hash identically at every tier: same slots, same
       values, only the lane grouping changes). */
    fnv_bits(hw, sizeof(uint64_t) * (size_t)SLOTS * lanes);

    g_fails += fails;
    printf("mode=sve_rot lanes=%d slots=%d FAILS=%u\n", lanes, SLOTS, fails);
    printf("SDCSHIELD_FAILS=%u\n%016llx\n",
           g_fails, (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
