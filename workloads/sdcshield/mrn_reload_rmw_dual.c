/* mrn_reload_rmw_dual.c — dual-channel extraction of the PR #288
 * review-round-3 mrn-family capacity fixes in sdcshield (branch
 * feat/p6-allvl, head lineage 52c2d755 + R3 fix commits) for CHAOS/gem5
 * SE-O3:
 *
 *   A. mrn_reloaded_sve.cpp three-width store->immediate-reload: the
 *      spill buffers are sized SVE_MAX_VECTOR_BYTES (u8) /
 *      SVE_MAX_VECTOR_BYTES/4 (u32) / SVE_MAX_VECTOR_BYTES/8 (u64) —
 *      the old got[64]/got[16]/got[8] were overrun by the full-width
 *      svst1 spill at every VL > 512-bit (svcntb()=128 / svcntw()=32 /
 *      svcntd()=16 at 1024-bit). Mirrored here: the same per-batch
 *      svst1(temp) -> svld1(temp) -> svst1(got) -> scalar compare
 *      chain at all three widths, tail batch included (n < lanes).
 *   B. mrn_rmw_sve.cpp / mrn_rmw_dump_sve.cpp rotating-op RMW: the
 *      phase staging buffer is sized SVE_MAX_VECTOR_BYTES/8 — the old
 *      phase[8] was written past by the fill loop and read past by the
 *      full-width svld1_u64 at every VL > 512-bit (svcntd()=16), which
 *      fed garbage phase values to the predicate dispatch (a false SDC
 *      on healthy silicon). Mirrored here: the (base+k)%4 phase
 *      predicate dispatch over add/sub/xor/and, svst1(temp) ->
 *      svld1(temp) -> svst1(dst), golden per element, tail batch
 *      included.
 *
 * Channel A: each section's SVE result vs its scalar golden, byte-exact.
 * Channel B: FNV-1a over all section outputs.
 *
 * Honest scope: gem5 has no ASAN, so the REMOVED OOB accesses are
 * proven gone by construction (spill/phase staging sized to the
 * architecture max in the mirrored source); this kernel proves the
 * fixed logic computes correct results at every tier, including the
 * 1024-bit tier where the old code was broken.
 *
 * argv: [fixed|random|poison] [seed]
 * Build: make mrn_reload_rmw_dual
 * Run:   gem5.opt configs/se/arm_chaos.py --cpu O3 --sve_vl {1,2,4,8} \
 *          --cmd <bin> --workload_args "random 1"
 */
#include <arm_sve.h>
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#ifndef SVE_MAX_VECTOR_BYTES
#define SVE_MAX_VECTOR_BYTES 256
#endif

static uint64_t rng_state;
static uint64_t sm64(void)
{
    uint64_t z = (rng_state += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static uint64_t fnv = 1469598103934665603ULL;
static void fnv_u32(uint32_t v) { fnv ^= v; fnv *= 1099511628211ULL; }

static unsigned g_fails = 0;

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "fixed";
    const uint64_t seed = (argc > 2) ? strtoull(argv[2], 0, 0) : 1;
    const int poison = (strcmp(mode, "poison") == 0);
    rng_state = seed * 0x2545F4914F6CDD1DULL + 0x9E3779B97F4A7C15ULL;

    const size_t bl = svcntb();         /* u8  lanes at the runtime VL */
    const size_t wl = svcntw();         /* u32 lanes */
    const size_t dl = svcntd();         /* u64 lanes */
    if (wl < 4 || wl > 32) {
        fprintf(stderr, "unsupported VL (svcntw=%zu)\n", wl);
        return 3;
    }

    /* ---------- Section A: mrn_reloaded three-width reload ---------- */
    {
        /* 4 full batches + a 6-element tail batch (n < lanes path) per
         * width; 8-bit width uses 32 + 6 so the tail is reached fast. */
        const size_t count8 = 4 * bl + 6;
        const size_t count32 = 4 * wl + 6;
        const size_t count64 = 4 * dl + 6;

        uint8_t *src8 = malloc(count8);
        uint8_t *temp8 = calloc(count8, 1);
        for (size_t i = 0; i < count8; ++i) src8[i] = (uint8_t)sm64();
        uint8_t got8[SVE_MAX_VECTOR_BYTES];        /* fixed form: 256B */
        for (size_t base = 0; base < count8; base += bl) {
            size_t n = (count8 - base < bl) ? count8 - base : bl;
            svbool_t pg = svwhilelt_b8((uint64_t)0, (uint64_t)n);
            svst1_u8(pg, temp8 + base, svld1_u8(pg, src8 + base));
            svst1_u8(pg, got8, svld1_u8(pg, temp8 + base));
            for (size_t i = 0; i < n; ++i) {
                if (poison && base == 0 && i == 1)
                    got8[i] ^= 0xff;               /* negative control */
                fnv_u32(got8[i]);
                if (got8[i] != src8[base + i]) {
                    fprintf(stderr, "A8 idx %zu got=%02x want=%02x\n",
                            base + i, got8[i], src8[base + i]);
                    ++g_fails;
                }
            }
        }
        free(src8); free(temp8);

        uint32_t *src32 = malloc(count32 * 4);
        uint32_t *temp32 = calloc(count32, 4);
        for (size_t i = 0; i < count32; ++i) src32[i] = (uint32_t)sm64();
        uint32_t got32[SVE_MAX_VECTOR_BYTES / 4];  /* fixed form: 64 el */
        for (size_t base = 0; base < count32; base += wl) {
            size_t n = (count32 - base < wl) ? count32 - base : wl;
            svbool_t pg = svwhilelt_b32((uint64_t)0, (uint64_t)n);
            svst1_u32(pg, temp32 + base, svld1_u32(pg, src32 + base));
            svst1_u32(pg, got32, svld1_u32(pg, temp32 + base));
            for (size_t i = 0; i < n; ++i) {
                if (poison && base == 0 && i == 1)
                    got32[i] ^= 0x000000ffu;       /* negative control */
                fnv_u32(got32[i]);
                if (got32[i] != src32[base + i]) {
                    fprintf(stderr, "A32 idx %zu got=%08x want=%08x\n",
                            base + i, got32[i], src32[base + i]);
                    ++g_fails;
                }
            }
        }
        free(src32); free(temp32);

        uint64_t *src64 = malloc(count64 * 8);
        uint64_t *temp64 = calloc(count64, 8);
        for (size_t i = 0; i < count64; ++i) src64[i] = sm64();
        uint64_t got64[SVE_MAX_VECTOR_BYTES / 8];  /* fixed form: 32 el */
        for (size_t base = 0; base < count64; base += dl) {
            size_t n = (count64 - base < dl) ? count64 - base : dl;
            svbool_t pg = svwhilelt_b64((uint64_t)0, (uint64_t)n);
            svst1_u64(pg, temp64 + base, svld1_u64(pg, src64 + base));
            svst1_u64(pg, got64, svld1_u64(pg, temp64 + base));
            for (size_t i = 0; i < n; ++i) {
                if (poison && base == 0 && i == 1)
                    got64[i] ^= 1ull;              /* negative control */
                fnv_u32((uint32_t)got64[i]);
                fnv_u32((uint32_t)(got64[i] >> 32));
                if (got64[i] != src64[base + i]) {
                    fprintf(stderr, "A64 idx %zu got=%016llx want=%016llx\n",
                            base + i, (unsigned long long)got64[i],
                            (unsigned long long)src64[base + i]);
                    ++g_fails;
                }
            }
        }
        free(src64); free(temp64);
    }

    /* ---------- Section B: mrn_rmw rotating-op RMW ---------- */
    {
        const size_t count = 4 * dl + 6;           /* includes a tail batch */
        uint64_t *srcA = malloc(count * 8);
        uint64_t *srcB = malloc(count * 8);
        uint64_t *temp = calloc(count, 8);
        uint64_t *dst  = calloc(count, 8);
        for (size_t i = 0; i < count; ++i) {
            srcA[i] = sm64();
            srcB[i] = sm64();
        }
        for (size_t base = 0; base < count; base += dl) {
            size_t n = (count - base < dl) ? count - base : dl;
            svbool_t pg = svwhilelt_b64((uint64_t)0, (uint64_t)n);
            svuint64_t va = svld1_u64(pg, srcA + base);
            svuint64_t vb = svld1_u64(pg, srcB + base);
            svuint64_t r_add = svadd_u64_x(pg, va, vb);
            svuint64_t r_sub = svsub_u64_x(pg, va, vb);
            svuint64_t r_eor = sveor_u64_x(pg, va, vb);
            svuint64_t r_and = svand_u64_x(pg, va, vb);
            /* fixed form: phase staging sized to the architecture max
             * (was uint64_t phase[8] — overrun at every VL > 512-bit) */
            uint64_t phase[SVE_MAX_VECTOR_BYTES / 8];
            for (size_t k = 0; k < n; ++k) phase[k] = (base + k) % 4;
            svuint64_t vphase = svld1_u64(pg, phase);
            svuint64_t res = svsel_u64(svcmpeq_n_u64(pg, vphase, 0), r_add,
                          svsel_u64(svcmpeq_n_u64(pg, vphase, 1), r_sub,
                          svsel_u64(svcmpeq_n_u64(pg, vphase, 2), r_eor, r_and)));
            svst1_u64(pg, temp + base, res);
            svst1_u64(pg, dst + base, svld1_u64(pg, temp + base));
        }
        if (poison)
            dst[1] ^= 1ull;                        /* negative control */
        for (size_t i = 0; i < count; ++i) {
            uint64_t want;
            switch (i % 4) {
            case 0: want = srcA[i] + srcB[i]; break;
            case 1: want = srcA[i] - srcB[i]; break;
            case 2: want = srcA[i] ^ srcB[i]; break;
            default: want = srcA[i] & srcB[i]; break;
            }
            fnv_u32((uint32_t)dst[i]);
            fnv_u32((uint32_t)(dst[i] >> 32));
            if (dst[i] != want) {
                fprintf(stderr, "B rmw idx %zu phase %zu golden=%016llx "
                        "actual=%016llx\n", i, i % 4,
                        (unsigned long long)want,
                        (unsigned long long)dst[i]);
                ++g_fails;
            }
        }
        free(srcA); free(srcB); free(temp); free(dst);
    }

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
