/* sve_rot_vla_dual.c — dual-channel extraction of the sdcshield test
 * `sve_rot_ldr_at_top_rowmajor_k7pattern` (PR #286 review round 1:
 * GPS tag 32-bit byte_off split) for CHAOS/gem5 SE four-tier runs.
 *
 * Mirrors the test's chain at its DEFAULT geometry (1024 VL slots —
 * the geometry under which the round-1 finding overflowed the legacy
 * 16b byte_off field at the 1024-bit tier):
 *
 *   fill   - sve_pattern_word, all four cells: P_ZERO/P_ONE/P_HIHAM
 *            are bitwise-identical to the pre-fix form (none of them
 *            touches the tag layout — P_HIHAM only reads byte_off
 *            parity, which absolute offsets keep at 0); P_RAND_GPS
 *            uses the FIXED 32-bit-split sve_gps_tag;
 *   golden - init form: asm z-ldr of srcA/srcB + rot_alu (i%4
 *            add/eor/and/orr _x) stored into expected;
 *   run    - two sweeps (ascending + descending, the test's sweep&1
 *            alternation): scratch z-ldr discard, srcA/srcB z-ldr,
 *            rot_alu, z-str into temp and dst;
 *   check  - memcmp(dst, expected) -> SDCSHIELD_FAILS.
 *
 * Channel B: FNV-1a over dst. The fill is a position function, so
 * the checksum is tier-DEPENDENT by design (no cross-tier identity is
 * expected or asserted — unlike sleef_vla_dual; the record is the
 * per-tier/per-pattern value plus FAILS=0).
 *
 * Channel C (the round-1 defect made measurable): tag uniqueness over
 * every (slot,lane) rand-fill word of srcA (which=0):
 *   - FIXED  32-bit split encoding: ZERO duplicate tags required at
 *     every tier — this is the fix under test;
 *   - LEGACY 16-bit encoding (byte_off truncated to its low 16b, the
 *     former always-0 gen field): duplicate count must be >0 exactly
 *     when max byte_off >= 65536 (true at 1024-bit/1024 slots:
 *     131064; false at 512-bit: 65528) — the negative control that
 *     keeps the finding measurable rather than asserted.
 *
 * argv: [zero|one|rand|hiham]  (default rand)
 * Build: make sve_rot_vla_dual
 * Run:   build/ARM/gem5.opt configs/se/arm_chaos.py \
 *          --cmd workloads/sdcshield/sve_rot_vla_dual --sve_vl 8 \
 *          --workload_args "rand"
 */
#include <arm_sve.h>
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#define SLOTS       1024   /* the test's default geometry */
#define VL_BYTES_MAX 128   /* 1024-bit tier */
#define WPS_MAX     (VL_BYTES_MAX / 8)

/* The FIXED tag: 32-bit byte_off split — low 16b in the classic field
 * (complement check unchanged), high 16b in the field the NEON tag
 * reserved for a generation counter. Mirrors the post-round-1
 * sdcshield sve_gps_tag(). */
static inline uint64_t gps_tag_fixed(uint64_t magic, uint64_t byte_off)
{
    return (magic                       << 48)
         | ((byte_off         & 0xFFFFULL) << 32)
         | ((~byte_off        & 0xFFFFULL) << 16)
         |  ((byte_off >> 16) & 0xFFFFULL);
}

/* The LEGACY tag: byte_off truncated to 16 bits, gen field 0 — the
 * pre-fix form whose mod-65536 aliasing the round-1 review found. */
static inline uint64_t gps_tag_legacy(uint64_t magic, uint64_t byte_off)
{
    return (magic                      << 48)
         | ((byte_off        & 0xFFFFULL) << 32)
         | ((~byte_off       & 0xFFFFULL) << 16);
}

enum K7Pattern { P_ZERO, P_ONE, P_RAND_GPS, P_HIHAM };

static uint64_t pattern_word(enum K7Pattern p, int which, uint64_t byte_off)
{
    switch (p) {
    case P_ZERO:     return 0x0000000000000000ULL;
    case P_ONE:      return 0xFFFFFFFFFFFFFFFFULL;
    case P_RAND_GPS: {
        const uint64_t magic = (which == 0) ? 0xA5A5ULL
                            : ((which == 1) ? 0x5A5AULL : 0x0F0FULL);
        return gps_tag_fixed(magic, byte_off);
    }
    case P_HIHAM: {
        uint64_t w = 0;
        for (int b = 0; b < 8; ++b) {
            const uint64_t nib =
                (((byte_off + (uint64_t)b) & 1) ? 0xAAULL : 0x55ULL);
            w |= (nib << (8 * b));
        }
        return w;
    }
    }
    return 0;
}

static inline svuint64_t load_vec(const void *addr)
{
    svuint64_t res;
    __asm__ volatile ("ldr %0, [%1]" : "=w"(res) : "r"(addr) : "memory");
    return res;
}

static inline void store_vec(void *addr, svuint64_t val)
{
    __asm__ volatile ("str %0, [%1]" :: "w"(val), "r"(addr) : "memory");
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

static unsigned g_fails = 0;
static uint64_t fnv = 1469598103934665603ULL;
static void fnv_u64(uint64_t v)
{
    for (int i = 0; i < 8; ++i) {
        fnv ^= (v >> (8 * i)) & 0xFF;
        fnv *= 1099511628211ULL;
    }
}

static int cmp_u64(const void *a, const void *b)
{
    const uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return (x > y) - (x < y);
}

static uint64_t tags[SLOTS * WPS_MAX];

/* Channel C: count duplicate tags among the rand-fill srcA words for
 * one encoding (fixed or legacy). */
static uint64_t count_dup_tags(int use_fixed, const uint64_t *srcA_words,
                               int slots, int wps, size_t vl_bytes)
{
    size_t n = 0;
    for (int i = 0; i < slots; ++i)
        for (int lane = 0; lane < wps; ++lane)
            tags[n++] = use_fixed
                ? gps_tag_fixed(0xA5A5ULL, (uint64_t)i * vl_bytes + (uint64_t)lane * 8)
                : gps_tag_legacy(0xA5A5ULL, (uint64_t)i * vl_bytes + (uint64_t)lane * 8);
    qsort(tags, n, sizeof(tags[0]), cmp_u64);
    uint64_t dups = 0;
    for (size_t k = 1; k < n; ++k)
        if (tags[k] == tags[k - 1])
            ++dups;
    (void)srcA_words;
    return dups;
}

static uint8_t srcA[SLOTS * VL_BYTES_MAX];
static uint8_t srcB[SLOTS * VL_BYTES_MAX];
static uint8_t scratch[SLOTS * VL_BYTES_MAX];
static uint8_t expected[SLOTS * VL_BYTES_MAX];
static uint8_t temp[SLOTS * VL_BYTES_MAX];
static uint8_t dst[SLOTS * VL_BYTES_MAX];

int main(int argc, char **argv)
{
    const char *cell = (argc > 1) ? argv[1] : "rand";
    enum K7Pattern p;
    if (!strcmp(cell, "zero"))          p = P_ZERO;
    else if (!strcmp(cell, "one"))      p = P_ONE;
    else if (!strcmp(cell, "rand"))     p = P_RAND_GPS;
    else if (!strcmp(cell, "hiham"))    p = P_HIHAM;
    else { fprintf(stderr, "unknown cell %s\n", cell); return 2; }

    const size_t vl_bytes = (size_t)svcntb();
    const int wps = (int)(vl_bytes / 8);
    if (vl_bytes < 16 || vl_bytes > VL_BYTES_MAX) {
        fprintf(stderr, "unsupported VL (%zu bytes)\n", vl_bytes);
        return 3;
    }
    const size_t buf = (size_t)SLOTS * vl_bytes;

    /* fill — the test's init form (position-addressed words) */
    for (int i = 0; i < SLOTS; ++i) {
        uint64_t *wa = (uint64_t *)(srcA + (size_t)i * vl_bytes);
        uint64_t *wb = (uint64_t *)(srcB + (size_t)i * vl_bytes);
        uint64_t *ws = (uint64_t *)(scratch + (size_t)i * vl_bytes);
        for (int lane = 0; lane < wps; ++lane) {
            const uint64_t base = (uint64_t)i * vl_bytes + (uint64_t)lane * 8;
            wa[lane] = pattern_word(p, 0, base);
            wb[lane] = pattern_word(p, 1, base);
            ws[lane] = pattern_word(p, 2, base);
        }
    }

    /* golden — the test's init-form rot_alu over asm z-ldr loads */
    for (int i = 0; i < SLOTS; ++i) {
        const size_t off = (size_t)i * vl_bytes;
        const svuint64_t a = load_vec(srcA + off);
        const svuint64_t b = load_vec(srcB + off);
        store_vec(expected + off, rot_alu(i, a, b));
    }

    /* run — asc+desc sweeps (the test's sweep&1 alternation) */
    for (uint64_t sweep = 0; sweep < 2; ++sweep) {
        const int ascending = (sweep & 1) == 0;
        for (int n = 0; n < SLOTS; ++n) {
            const int i = ascending ? n : (SLOTS - 1 - n);
            const size_t off = (size_t)i * vl_bytes;

            svuint64_t unused_x = load_vec(scratch + off);
            (void)unused_x;

            const svuint64_t a = load_vec(srcA + off);
            const svuint64_t b = load_vec(srcB + off);
            const svuint64_t res = rot_alu(i, a, b);

            store_vec(temp + off, res);
            store_vec(dst + off, res);
        }
        if (memcmp(dst, expected, buf) != 0) {
            for (size_t k = 0; k < buf; k += 8) {
                const uint64_t d = *(const uint64_t *)(dst + k);
                const uint64_t e = *(const uint64_t *)(expected + k);
                if (d != e) {
                    fprintf(stderr,
                            "sweep %lu mismatch @+%07zu (slot %zu lane %zu)"
                            " dst=%016llx expected=%016llx\n",
                            (unsigned long)sweep, k, k / vl_bytes,
                            (k % vl_bytes) / 8,
                            (unsigned long long)d, (unsigned long long)e);
                    ++g_fails;
                    break;
                }
            }
        }
    }

    /* Channel B: FNV-1a over dst (tier-dependent by design — the fill
     * is a position function; no cross-tier identity asserted). */
    for (size_t k = 0; k < buf; k += 8)
        fnv_u64(*(const uint64_t *)(dst + k));

    /* Channel C: tag uniqueness (rand cell only — the only cell that
     * carries GPS tags). */
    if (p == P_RAND_GPS) {
        const uint64_t dups_fixed =
            count_dup_tags(1, NULL, SLOTS, wps, vl_bytes);
        const uint64_t dups_legacy =
            count_dup_tags(0, NULL, SLOTS, wps, vl_bytes);
        const uint64_t max_off =
            (uint64_t)(SLOTS - 1) * vl_bytes + (uint64_t)(wps - 1) * 8;

        printf("TAG_DUPS fixed=%lu legacy=%lu max_byte_off=%lu\n",
               (unsigned long)dups_fixed, (unsigned long)dups_legacy,
               (unsigned long)max_off);

        if (dups_fixed != 0) {
            fprintf(stderr, "FIXED 32-bit split encoding aliased "
                            "(%lu dups) — the fix does not hold\n",
                    (unsigned long)dups_fixed);
            ++g_fails;
        }
        /* Negative control: the legacy encoding must alias exactly
         * when max byte_off crosses the 16b boundary. */
        if ((max_off >= 65536) != (dups_legacy > 0)) {
            fprintf(stderr, "legacy control out of calibre: max_off=%lu"
                            " dups=%lu\n", (unsigned long)max_off,
                    (unsigned long)dups_legacy);
            ++g_fails;
        }
    }

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
