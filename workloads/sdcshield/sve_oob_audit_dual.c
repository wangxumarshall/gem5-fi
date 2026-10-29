/* sve_oob_audit_dual.c — dual-channel extraction of the four SVE
 * out-of-bounds fixes in sdcshield issues #312/#313/#314/#315 (branch
 * fix/sve-oob-audit-2026-10-29) for CHAOS/gem5 SE-O3.
 *
 *   A. iex_operand_combo_sve predicate clamps (#312): sve_rev loads/
 *      stores its 8-byte in/out/idx arrays under svwhilelt_b8(0,8)
 *      (was svptrue_b8 — an OOB read+write at every VL >= 128-bit);
 *      sve_clz uses svwhilelt_b64(0,1) (was svptrue_b64 — OOB from the
 *      512-bit tier up). Mirrored verbatim (noinline: keeps the svclz/
 *      svtbl chains off the constant-folding path, the e21b2afc
 *      discipline), checked vs __builtin_bswap64 / __builtin_clzll.
 *   B. partial_store_forwarding_sve broadcast load (#313): the val
 *      staging load now reuses the store predicate pg=whilelt_b8(0,sz)
 *      (was svptrue_b8 — an OOB read of bytes[8] at every tier).
 *      Mirrored: partial writes of 1/2/4/8 bytes at misaligned offsets,
 *      low sz bytes must equal val's low sz bytes, the rest must keep
 *      the 0xAA prefill.
 *   C. mrn_nuke_dense_sve tail slack (#314): count=16392 (== 8 mod 16,
 *      the knob trigger) with temp sized count+lanes (64B-rounded-up)
 *      so the unpredicated `ldr z` tail read stays in the allocation;
 *      predicated svst1 drops the slack values. Mirrored verbatim
 *      (inline-asm ldr z included), memcmp(dst, src) must be clean.
 *      At --sve_vl 8 (1024-bit, lanes=16) this reproduces the exact
 *      trigger geometry of the bug; other tiers run the divisible path.
 *   D. mesh_upi_sve_wide_asymm_read_{L3,only} cold-path index (#315):
 *      bad_vec = i + v*NEON_VECTOR_SIZE (was v*VECTOR_SIZE — a 4x
 *      amplified index whose data[bad_vec+0..3] read ran up to 128B
 *      past the buffer and printed the wrong vector's evidence).
 *      Mirrored: a forced store/reload inconsistency walks the fixed
 *      cold path; the post-hoc read must be in-bounds and land on the
 *      failing sub-vector's elements.
 *
 * Channel A: each section's result vs its scalar golden (byte-exact).
 * Channel B: FNV-1a over sampled section outputs.
 *
 * Honest scope: gem5 has no ASAN, so the REMOVED OOB accesses are
 * proven gone by construction (predicates/slack/indices bounded in the
 * mirrored source); this kernel proves the FIXED logic computes
 * correct results at every tier, including the tiers where the old
 * code was broken (every tier for A/B, 1024-bit for C, the cold path
 * for D).
 *
 * argv: [fixed|random|poison] [seed]   (defaults: random 1)
 * Output protocol: "SDCSHIELD_FAILS=<uint>" line, then a 16-hex FNV line.
 * exit = g_fails ? 1 : 0.
 *
 * Build: make sve_oob_audit_dual
 * Run:   gem5.opt configs/se/arm_chaos.py --cpu O3 --sve_vl {1,2,4,8} \
 *          --cmd workloads/sdcshield/sve_oob_audit_dual \
 *          --workload_args "random 1"
 */
#include <arm_sve.h>
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

static unsigned g_fails = 0;
static uint64_t fnv = 1469598103934665603ULL;
static void fnv_u64(uint64_t v)
{
    for (int i = 0; i < 8; ++i) {
        fnv ^= (v >> (8 * i)) & 0xFF;
        fnv *= 1099511628211ULL;
    }
}
static void fnv_bytes(const void *p, size_t n)
{
    const uint8_t *b = (const uint8_t *)p;
    for (size_t i = 0; i < n; ++i) {
        fnv ^= b[i];
        fnv *= 1099511628211ULL;
    }
}

static uint64_t xs_state = 1;
static uint64_t xs64(void)             /* xorshift64, seedable */
{
    xs_state ^= xs_state << 13;
    xs_state ^= xs_state >> 7;
    xs_state ^= xs_state << 17;
    return xs_state;
}

/* ================= Section A (#312) ================= */

__attribute__((noinline))
static uint64_t sve_rev_fixed(uint64_t v)
{
    uint8_t in[8], out[8];
    memcpy(in, &v, 8);
    static const uint8_t idx[8] = {7, 6, 5, 4, 3, 2, 1, 0};
    svbool_t pg = svwhilelt_b8((uint64_t)0, (uint64_t)8);   /* the fix */
    svuint8_t vi = svld1_u8(pg, in);
    svuint8_t vidx = svld1_u8(pg, idx);
    svuint8_t vo = svtbl_u8(vi, vidx);
    svst1_u8(pg, out, vo);
    uint64_t r;
    memcpy(&r, out, 8);
    return r;
}

__attribute__((noinline))
static uint64_t sve_clz_fixed(uint64_t v)
{
    uint64_t in[4], out[4];
    in[0] = v;
    svbool_t pg = svwhilelt_b64((uint64_t)0, (uint64_t)1);  /* the fix */
    svuint64_t vi = svld1_u64(pg, in);
    svst1_u64(pg, out, svclz_u64_x(pg, vi));
    return out[0];
}

static unsigned section_a(int randomize, int poison)
{
    static const uint64_t tab_fixed[16] = {
        0x0000000000000000ULL, 0xFFFFFFFFFFFFFFFFULL,
        0xAAAAAAAAAAAAAAAAULL, 0x5555555555555555ULL,
        0xCCCCCCCCCCCCCCCCULL, 0x3333333333333333ULL,
        0xF0F0F0F0F0F0F0F0ULL, 0x0F0F0F0F0F0F0F0FULL,
        0xFFFF0000FFFF0000ULL, 0x0000FFFF0000FFFFULL,
        0xFFFFFF00FFFFFF00ULL, 0x00FFFFFF00FFFFFFULL,
        0x8000000000000000ULL, 0x7FFFFFFFFFFFFFFFULL,
        0x0000000000000001ULL, 0xFFFFFFFFFFFFFFFEULL,
    };
    uint64_t tab[16];
    memcpy(tab, tab_fixed, sizeof tab);
    if (randomize)
        for (int i = 0; i < 16; ++i)
            tab[i] ^= xs64() & (i ? tab[i - 1] : 0x9E3779B97F4A7C15ULL);

    unsigned mism = 0;
    for (int i = 0; i < 16; ++i) {
        uint64_t hw = sve_rev_fixed(tab[i]);
        /* poison: a wrong-but-plausible golden (32-bit bswap) */
        uint64_t sw = (poison && i == 0)
                          ? (uint64_t)__builtin_bswap32((uint32_t)tab[i])
                          : __builtin_bswap64(tab[i]);
        if (hw != sw) {
            fprintf(stderr, "A/rev[%d] v=%016llx hw=%016llx sw=%016llx\n",
                    i, (unsigned long long)tab[i],
                    (unsigned long long)hw, (unsigned long long)sw);
            ++mism;
        }
        fnv_u64(hw);
    }
    for (int i = 0; i < 16; ++i) {
        uint64_t v = tab[i];
        if (v == 0)
            v = 1;                       /* keep clzll defined */
        uint64_t hw = sve_clz_fixed(v);
        uint64_t sw = v ? (uint64_t)__builtin_clzll(v) : 64;
        if (poison && i == 0)
            sw ^= 1;                     /* poison: off-by-one golden */
        if (hw != sw) {
            fprintf(stderr, "A/clz[%d] v=%016llx hw=%llu sw=%llu\n",
                    i, (unsigned long long)v,
                    (unsigned long long)hw, (unsigned long long)sw);
            ++mism;
        }
        fnv_u64(hw);
    }
    return mism;
}

/* ================= Section B (#313) ================= */

__attribute__((noinline))
static void sve_write_partial_fixed(uint8_t *addr, int sz, uint64_t val)
{
    svbool_t pg = svwhilelt_b8((uint64_t)0, (uint64_t)sz);
    uint8_t bytes[8];
    memcpy(bytes, &val, 8);
    svuint8_t v = svld1_u8(pg, bytes);   /* the fix: pg, not svptrue_b8 */
    svst1_u8(pg, addr, v);
}

static unsigned section_b(int randomize, int poison)
{
    uint8_t buf[256];
    memset(buf, 0xAA, sizeof buf);
    unsigned mism = 0;
    for (int k = 0; k < 8; ++k) {
        int sz = 1 << (k % 4);           /* 1/2/4/8 */
        size_t off = (size_t)(k * 17 + 3);   /* misaligned offsets */
        uint64_t val = randomize ? xs64()
                                 : 0x0123456789ABCDEFULL * (uint64_t)(k + 1);
        sve_write_partial_fixed(buf + off, sz, val);
        for (int b = 0; b < sz; ++b) {
            uint8_t want = (uint8_t)(val >> (8 * b));
            if (poison && k == 0 && b == 0)
                want ^= 0xFF;             /* poison: wrong expected byte */
            if (buf[off + b] != want) {
                fprintf(stderr, "B/wr k=%d b=%d got=%02x want=%02x\n",
                        k, b, buf[off + b], want);
                ++mism;
            }
        }
        /* the byte just past the partial write must keep the prefill */
        if (buf[off + sz] != 0xAA && off + sz < sizeof buf) {
            fprintf(stderr, "B/spill k=%d off=%zu sz=%d clobbered=%02x\n",
                    k, off, sz, buf[off + sz]);
            ++mism;
        }
    }
    fnv_bytes(buf, sizeof buf);
    return mism;
}

/* ================= Section C (#314) ================= */

static inline svuint64_t load_vec_sve(const void *addr)
{
    svuint64_t res;
    __asm__ volatile ("ldr %0, [%1]" : "=w"(res) : "r"(addr) : "memory");
    return res;
}

__attribute__((noinline))
static unsigned section_c(int poison)
{
    const size_t count = 16392;          /* == 8 mod 16: the trigger knob */
    const int lanes = svcntd();
    /* the fix: tail slack, 64B-rounded-up */
    const size_t temp_bytes =
        ((count + (size_t)lanes) * sizeof(uint64_t) + 63) & ~(size_t)63;
    uint64_t *src  = aligned_alloc(64, count * sizeof(uint64_t));
    uint64_t *temp = aligned_alloc(64, temp_bytes);
    uint64_t *dst  = aligned_alloc(64, count * sizeof(uint64_t));
    if (!src || !temp || !dst) {
        fprintf(stderr, "C: alloc failed\n");
        free(src); free(temp); free(dst);
        return 1;
    }
    for (size_t i = 0; i < count; ++i)
        src[i] = 0x9E3779B97F4A7C15ULL * (uint64_t)(i + 1);
    memset(temp, 0, temp_bytes);
    memset(dst, 0, count * sizeof(uint64_t));

    for (size_t base = 0; base < count; base += (size_t)lanes) {
        int n = (count - base < (size_t)lanes)
                    ? (int)(count - base) : lanes;
        svbool_t pg = svwhilelt_b64((uint64_t)0, (uint64_t)n);
        svst1_u64(pg, temp + base, svld1_u64(pg, src + base));
        svst1_u64(pg, dst + base, load_vec_sve(temp + base));
    }

    unsigned mism = 0;
    if (poison)
        dst[0] ^= 1;                      /* poison: forced miscompare */
    if (memcmp(dst, src, count * sizeof(uint64_t)) != 0) {
        fprintf(stderr, "C/miscompare count=%zu lanes=%d\n", count, lanes);
        ++mism;
    }
    /* FNV over head + tail windows (keeps gem5 runtime bounded) */
    fnv_bytes(dst, 16 * sizeof(uint64_t));
    fnv_bytes(dst + count - 32, 32 * sizeof(uint64_t));
    free(src); free(temp); free(dst);
    return mism;
}

/* ================= Section D (#315) ================= */

__attribute__((noinline))
static unsigned section_d(int poison)
{
    enum { NVS = 4, VS = 16 };           /* NEON_VECTOR_SIZE, VECTOR_SIZE */
    const size_t total = 256;            /* aligned to VS */
    static uint32_t data[256];
    uint32_t vals[VS], store_buf[VS];
    for (size_t i = 0; i < total; ++i)
        data[i] = (uint32_t)(0x01010101ULL * (uint64_t)(i + 1));

    /* forced inconsistency: block 3, sub-vector 2 — the only cold path */
    const size_t bad_i = 3 * VS;
    const int bad_v = 2;

    unsigned mism = 0;
    for (size_t i = 0; i < total; i += VS) {
        for (int v = 0; v < VS / NVS; ++v) {
            for (int b = 0; b < NVS; ++b)
                vals[v * NVS + b] = data[i + (size_t)v * NVS + b];
            memcpy(store_buf + v * NVS, vals + v * NVS, NVS * sizeof(uint32_t));
            if (i == bad_i && v == bad_v)
                store_buf[v * NVS] ^= 0x1;   /* injected store/reload SDC */
        }
        for (int v = 0; v < VS / NVS; ++v) {
            if (memcmp(store_buf + v * NVS, vals + v * NVS,
                       NVS * sizeof(uint32_t)) == 0)
                continue;                 /* consistent: hot path */
            /* cold path — the fix: sub-vector stride, not block stride */
            size_t bad_vec = i + (size_t)v * NVS;
            if (bad_vec + 3 > total - 1) {
                fprintf(stderr, "D/oob i=%zu v=%d bad_vec=%zu total=%zu\n",
                        i, v, bad_vec, total);
                ++mism;
            }
            for (int b = 0; b < 4; ++b) {
                uint32_t got = data[bad_vec + b];
                uint32_t want = data[i + (size_t)v * NVS + b];
                if (poison && b == 0)
                    want ^= 0xFFFF;       /* poison: wrong expected word */
                if (got != want) {
                    fprintf(stderr, "D/posthoc i=%zu v=%d b=%d got=%08x "
                            "want=%08x\n", i, v, b, got, want);
                    ++mism;
                }
            }
            /* the OLD formula here (i + v*VS) reads data[80..83] instead
             * of data[56..59] at this site, and data[total+32..35] at
             * (i=total-VS, v=3) — up to 128B past the buffer. */
        }
    }
    fnv_bytes(data, sizeof data);
    return mism;
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "random";
    const uint32_t seed = (argc > 2) ? (uint32_t)strtoul(argv[2], 0, 0) : 1;
    const int randomize = (strcmp(mode, "random") == 0);
    const int poison = (strcmp(mode, "poison") == 0);
    xs_state = seed ? seed : 1;

    g_fails += section_a(randomize || poison, poison);
    g_fails += section_b(randomize || poison, poison);
    g_fails += section_c(poison);
    g_fails += section_d(poison);

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
