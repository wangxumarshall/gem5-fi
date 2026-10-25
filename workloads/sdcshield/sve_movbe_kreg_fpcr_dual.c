/* sve_movbe_kreg_fpcr_dual.c — dual-channel extraction of the three
 * value-relevant PR #288 review-round-2 fixes in sdcshield (branch
 * feat/p6-allvl, head lineage 672ed13e + R2 fix commits) for CHAOS/gem5
 * SE-O3:
 *
 *   A. movbe family full-width byte-swap round-trip (movbe_sve.cpp +
 *      movbe_dump_sve.cpp + movbe_dump_probe_{a..xn}_sve.cpp, 13 files):
 *      vidx_bytes is sized SVE_MAX_VECTOR_BYTES with the index loop and
 *      pg_batch freed of the 64-byte/16-lane caps, and in/out_bytes /
 *      restored sized to the architecture max. The old capped form built
 *      garbage indices (svld1 zero-fill) for lanes 16..31 at VL=1024 —
 *      a deterministic false SDC — and memcpy/svst1 wrote 128B into the
 *      64B staging buffers. Mirrored here: full-width vidx build, the
 *      bswap result checked against __builtin_bswap32 (catches a wrong
 *      but involutive table) plus the round-trip identity, with a tail
 *      batch (n < lanes).
 *   B. arm0102_kreg_mask rotating predicate compare-mask expansion
 *      (arm0102_kreg_mask_sve.cpp): the phase is now the sub-block index
 *      (base+sub)/4 (the old (base+sub)%4 was constantly 0 — the
 *      gt/eq-u/tst predicate paths were dead code), and the buffers
 *      carry svcntw() elements of tail slack for the asm full-width
 *      ldr z. Mirrored here verbatim: asm ldr z loads, pg4 sub-blocks,
 *      the 4-way svcmp/svsel expansion by rotating phase, the
 *      str z -> ldr z -> str z amplifier, tail batch included.
 *   C. sve_fpcr_cartesian tie-liveness block (sve_fpcr_cartesian_arm.cpp):
 *      the tie operands/result moved from 2-element stack arrays (an OOB
 *      full-width svld1/svst1 at every VL >= 128-bit) into the vl_w-sized
 *      operand vectors. Mirrored here: lane 0 = fma(1,1,2^-24) tie,
 *      lanes 1+ zero (fma(0,0,0) = +0), all lanes checked. Honest
 *      boundary: the 4-mode FPCR sweep is the test's own untouched
 *      semantics; this section validates the fixed geometry under the
 *      ambient RNE mode (tie rounds to 1.0).
 *
 * Channel A: each section's SVE result vs its scalar golden, byte-exact.
 * Channel B: FNV-1a over all section outputs.
 *
 * Honest scope: gem5 has no ASAN, so the REMOVED OOB accesses are proven
 * gone by construction (predicates/arrays bounded in the mirrored
 * source), not by detection; this kernel proves the FIXED logic computes
 * correct results at every tier, including the tiers (1024-bit for A,
 * every tier for B, every tier for C) where the old code was broken.
 *
 * argv: [fixed|random|poison] [seed]
 * Build: make sve_movbe_kreg_fpcr_dual
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

/* kreg_mask sub-block width (tests/cpu/sve/kreg/arm0102_kreg_mask_sve.cpp) */
#define KREG_SVE_SUBLANES 4

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

/* Section C compute, noinline: clang -O2 constant-folds the literal
 * operand fma chain when inlined (zero fmla in .s — the sve512_fma_dual
 * J1' lesson); the barrier keeps the fused multiply-add on the SVE
 * datapath exactly as the (GCC-built) test executes it. */
__attribute__((noinline))
static void fpcr_tie_compute(float *a, float *b, float *c, float *hw)
{
    svbool_t all = svptrue_b32();
    svfloat32_t va = svld1_f32(all, a);
    svfloat32_t vb = svld1_f32(all, b);
    svfloat32_t vc = svld1_f32(all, c);
    svfloat32_t vd = svmla_f32_x(all, vc, va, vb);
    svst1_f32(all, hw, vd);
}

/* ---- Section B helpers (verbatim mirrors of the fixed test) ---- */
static inline svuint32_t load_vec_sve(const void *addr) {
    svuint32_t res;
    /* asm 保证的加载 (core-179 配方; SVE ldr z 按 VL 全宽载, 计算用 pg4 截断) */
    __asm__ volatile ("ldr %0, [%1]" : "=w"(res) : "r"(addr) : "memory");
    return res;
}

static inline void store_vec_sve(void *addr, svuint32_t val) {
    svbool_t pg = svwhilelt_b32((uint64_t)0, (uint64_t)KREG_SVE_SUBLANES);
    svst1_u32(pg, (uint32_t *)addr, val);
}

/* 旋转比较掩码扩展: i%4 → eq/gt(signed)/eq-u/tst (逐字镜像) */
static inline svuint32_t kreg_expand_rotating(svbool_t pg, svuint32_t a, svuint32_t b, int i) {
    switch (i % 4) {
        case 0: {  /* eq (signed reinterpret) */
            svint32_t sa = svreinterpret_s32_u32(a), sb = svreinterpret_s32_u32(b);
            svbool_t p = svcmpeq_s32(pg, sa, sb);
            return svsel_u32(p, svdup_u32(0xFFFFFFFFu), svdup_u32(0));
        }
        case 1: {  /* gt (signed) */
            svint32_t sa = svreinterpret_s32_u32(a), sb = svreinterpret_s32_u32(b);
            svbool_t p = svcmpgt_s32(pg, sa, sb);
            return svsel_u32(p, svdup_u32(0xFFFFFFFFu), svdup_u32(0));
        }
        case 2: {  /* eq-u */
            svbool_t p = svcmpeq_u32(pg, a, b);
            return svsel_u32(p, svdup_u32(0xFFFFFFFFu), svdup_u32(0));
        }
        default: { /* tst: (a & b) != 0 */
            svbool_t p = svcmpne_n_u32(pg, svand_u32_x(pg, a, b), 0);
            return svsel_u32(p, svdup_u32(0xFFFFFFFFu), svdup_u32(0));
        }
    }
}

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "fixed";
    const uint64_t seed = (argc > 2) ? strtoull(argv[2], 0, 0) : 1;
    const int poison = (strcmp(mode, "poison") == 0);
    rng_state = seed * 0x2545F4914F6CDD1DULL + 0x9E3779B97F4A7C15ULL;

    const size_t wl = svcntw();          /* u32 lanes at the runtime VL */
    if (wl < 4 || wl > 32) {
        fprintf(stderr, "unsupported VL (svcntw=%zu)\n", wl);
        return 3;
    }

    /* ---------- Section A: movbe full-width bswap round-trip ---------- */
    {
        /* 4 full batches + a 6-element tail batch (n < lanes path). */
        const size_t count = 4 * wl + 6;
        uint32_t *input = malloc(count * 4);
        uint32_t *swapped = calloc(count, 4);
        uint32_t *roundtrp = calloc(count, 4);
        for (size_t i = 0; i < count; ++i)
            input[i] = (uint32_t)sm64();

        static const uint8_t idx4[4] = {3, 2, 1, 0};
        uint8_t vidx_bytes[SVE_MAX_VECTOR_BYTES];   /* fixed form: no 16-lane cap */
        for (size_t i = 0; i < wl; ++i)
            for (int b = 0; b < 4; ++b)
                vidx_bytes[i * 4 + b] = (uint8_t)(i * 4 + idx4[b]);
        svbool_t pg_batch = svwhilelt_b8((uint64_t)0, (uint64_t)wl * 4);
        svuint8_t vidx = svld1_u8(pg_batch, vidx_bytes);

        uint8_t in_bytes[SVE_MAX_VECTOR_BYTES];     /* fixed form: 256B */
        uint8_t out_bytes[SVE_MAX_VECTOR_BYTES];
        for (size_t base = 0; base < count; base += wl) {
            size_t n = (count - base < wl) ? count - base : wl;
            svbool_t pg = svwhilelt_b8((uint64_t)0, (uint64_t)(n * 4));
            memcpy(in_bytes, input + base, n * 4);
            svuint8_t vswapped = svtbl_u8(svld1_u8(pg, in_bytes), vidx);
            uint8_t sw_bytes[SVE_MAX_VECTOR_BYTES];
            svst1_u8(pg, sw_bytes, vswapped);
            memcpy(swapped + base, sw_bytes, n * 4);
            svuint8_t vrestored = svtbl_u8(vswapped, vidx);
            svst1_u8(pg, out_bytes, vrestored);
            memcpy(roundtrp + base, out_bytes, n * 4);
        }
        if (poison)
            swapped[1] ^= 0x000000ffu;              /* negative control */
        for (size_t i = 0; i < count; ++i) {
            uint32_t want_swap = __builtin_bswap32(input[i]);
            fnv_u32(swapped[i]);
            fnv_u32(roundtrp[i]);
            if (swapped[i] != want_swap) {
                fprintf(stderr, "A bswap idx %zu got=%08x want=%08x\n",
                        i, swapped[i], want_swap);
                ++g_fails;
            }
            if (roundtrp[i] != input[i]) {
                fprintf(stderr, "A roundtrip idx %zu got=%08x want=%08x\n",
                        i, roundtrp[i], input[i]);
                ++g_fails;
            }
        }
        free(input); free(swapped); free(roundtrp);
    }

    /* ---------- Section B: kreg_mask rotating predicate expansion ---------- */
    {
        const size_t count = 4 * wl + 6;            /* includes a tail batch */
        const size_t slack = wl;                    /* fixed form: tail slack */
        const size_t total = count + slack;
        uint32_t *srcA = malloc(total * 4);
        uint32_t *srcB = malloc(total * 4);
        uint32_t *temp = calloc(total, 4);
        uint32_t *dst  = calloc(total, 4);
        uint32_t *golden = malloc(count * 4);
        for (size_t i = 0; i < total; ++i) {
            srcA[i] = (uint32_t)sm64();
            srcB[i] = (uint32_t)sm64();
        }
        svbool_t pg4 = svwhilelt_b32((uint64_t)0, (uint64_t)KREG_SVE_SUBLANES);
        for (size_t base = 0; base < count; base += wl) {
            size_t n = (count - base < wl) ? count - base : wl;
            for (size_t sub = 0; sub < n; sub += KREG_SVE_SUBLANES) {
                svuint32_t a = load_vec_sve(srcA + base + sub);   /* ldr z */
                svuint32_t b = load_vec_sve(srcB + base + sub);   /* ldr z */
                /* fixed form: phase = sub-block index, not (base+sub)%4 */
                svuint32_t res = kreg_expand_rotating(
                    pg4, a, b, (int)((base + sub) / KREG_SVE_SUBLANES));
                store_vec_sve(temp + base + sub, res);
                store_vec_sve(dst + base + sub, load_vec_sve(temp + base + sub));
            }
        }
        for (size_t i = 0; i < count; ++i) {
            uint32_t x = srcA[i], y = srcB[i];
            int32_t sx = (int32_t)x, sy = (int32_t)y;
            switch ((i / KREG_SVE_SUBLANES) % 4) {
            case 0: golden[i] = (sx == sy) ? 0xFFFFFFFFu : 0; break;
            case 1: golden[i] = (sx >  sy) ? 0xFFFFFFFFu : 0; break;
            case 2: golden[i] = (x == y)  ? 0xFFFFFFFFu : 0; break;
            default: golden[i] = ((x & y) != 0) ? 0xFFFFFFFFu : 0; break;
            }
        }
        if (poison)
            golden[1] ^= 1u;                        /* negative control */
        for (size_t i = 0; i < count; ++i) {
            fnv_u32(dst[i]);
            if (dst[i] != golden[i]) {
                fprintf(stderr, "B kreg idx %zu phase %zu golden=%08x actual=%08x\n",
                        i, (i / KREG_SVE_SUBLANES) % 4, golden[i], dst[i]);
                ++g_fails;
            }
        }
        free(srcA); free(srcB); free(temp); free(dst); free(golden);
    }

    /* ---------- Section C: fpcr tie liveness, vector form ---------- */
    {
        float *a = calloc(wl, 4);                   /* fixed form: vl_w-sized */
        float *b = calloc(wl, 4);                   /* (was float ta[2] etc.) */
        float *c = calloc(wl, 4);
        float *hw = calloc(wl, 4);
        a[0] = 1.0f; b[0] = 1.0f; c[0] = 0x1p-24f;
        fpcr_tie_compute(a, b, c, hw);
        /* Ambient RNE: the exact tie 1 + 2^-24 rounds to 1.0 (the test's
         * r==1 (RP) case maps it to 0x1.000002p+0 — mode sweep is the
         * test's own untouched semantics, not mirrored here). */
        const float want0 = poison ? 0x1.000002p+0f : 0x1p+0f;
        for (size_t i = 0; i < wl; ++i) {
            float want = (i == 0) ? want0 : 0.0f;   /* lanes 1+: fma(0,0,0) */
            fnv_u32(*(uint32_t *)&hw[i]);
            if (hw[i] != want) {
                fprintf(stderr, "C tie lane %zu got=%a want=%a\n",
                        i, (double)hw[i], (double)want);
                ++g_fails;
            }
        }
        free(a); free(b); free(c); free(hw);
    }

    printf("SDCSHIELD_FAILS=%u\n", g_fails);
    printf("%016llx\n", (unsigned long long)fnv);
    return g_fails ? 1 : 0;
}
