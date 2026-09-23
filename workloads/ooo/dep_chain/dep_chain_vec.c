/* dep_chain_vec — W1.5b long-dependency-chain pressure kernel (NEON vec).
 *
 * Purpose (docs/gem5-fi/ooo/03-workloads.md, 长依赖链压力核 向量版):
 *   the vector variant of dep_chain: many TRUE vector accumulate chains
 *   (each FMLA consumes the previous FMLA's accumulator register), keeping
 *   the same small set of vector architectural registers live for the whole
 *   run while rename allocates a fresh VecRegClass physical destination per
 *   step that cannot be freed until commit — pinning the 48-entry vector
 *   free list (C3 physVec=48; NOTE the initial freelist is already tiny,
 *   see README W1.5b notes) at its floor and driving real vector rename
 *   traffic (stats: board.processor.cores.core.rename.vecLookups).
 *
 * Structure:
 *   12 parallel float32x4 chains, each step a lane-indexed fused
 *   multiply-accumulate (spec example form v0 = vfmaq_laneq_f32(v0,v1,v2,k)):
 *       c_i = vfmaq_laneq_f32(c_i, M_i, SV_j, lane)
 *   — c_i is BOTH source and destination: a true loop/step-carried
 *   dependency chain through the vector register.  Per-lane multipliers
 *   M_i[k] are exact dyadic fractions < 1 for lanes 0/1 (real multiply
 *   chains with distinct maps per lane) and exactly 1.0 for lanes 2/3
 *   (pure accumulate lanes — a perturbation there persists to the final
 *   checksum instead of contracting away).  Drive vectors SV_j (mixed-sign
 *   fractional floats) rotate per step so the orbits never stall.
 *
 *   The step block is fully macro-unrolled: 11 x SWEEP8 = 88 sweeps x 12
 *   chains = 1056 STATIC fmla sites per round (objdump gate: > 1000 fmla),
 *   wrapped in a ROUNDS-trip outer loop.
 *
 * Determinism (native == gem5, bit-exact):
 *   values stay bounded (|c| < ~1e7 << FLT_MAX; no NaN/Inf; no flush-to-
 *   zero anywhere), so every FMLA is an IEEE-754 correctly-rounded FUSED
 *   multiply-add.  gem5 executes fmla.4s via fplibMulAdd -> fp32_muladd
 *   (src/arch/arm/insts/fplib.cc:2211 — exact product, ONE rounding), and
 *   AArch64 hardware FMLA is fused with the same single rounding — the
 *   results are bit-identical for finite inputs.
 *
 * Size: ROUNDS x ~1400 committed instructions ≈ 6.3M dynamic instructions
 * — gem5 C3 SE in tens of seconds (measured hostSeconds in README.md),
 * within the 60s W1 SE budget.
 */
#include <arm_neon.h>
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#define NV     12        /* parallel float32x4 accumulate chains */
#define ROUNDS 4500      /* sized for C3 SE hostSeconds 30-60s (measured) */

/* per-chain multipliers: lanes 0/1 = distinct exact dyadics < 1 (real
 * multiply chains), lanes 2/3 = exactly 1.0f (persistent accumulate). */
static const float32x4_t M[NV] = {
    {(float)(1.0 - 1.0 / 32.0),  (float)(1.0 - 1.0 / 128.0), 1.0f, 1.0f},
    {(float)(1.0 - 3.0 / 32.0),  (float)(1.0 - 3.0 / 128.0), 1.0f, 1.0f},
    {(float)(1.0 - 5.0 / 32.0),  (float)(1.0 - 5.0 / 128.0), 1.0f, 1.0f},
    {(float)(1.0 - 7.0 / 32.0),  (float)(1.0 - 7.0 / 128.0), 1.0f, 1.0f},
    {(float)(1.0 - 9.0 / 32.0),  (float)(1.0 - 9.0 / 128.0), 1.0f, 1.0f},
    {(float)(1.0 - 11.0 / 32.0), (float)(1.0 - 11.0 / 128.0), 1.0f, 1.0f},
    {(float)(1.0 - 1.0 / 64.0),  (float)(1.0 - 1.0 / 256.0), 1.0f, 1.0f},
    {(float)(1.0 - 3.0 / 64.0),  (float)(1.0 - 3.0 / 256.0), 1.0f, 1.0f},
    {(float)(1.0 - 5.0 / 64.0),  (float)(1.0 - 5.0 / 256.0), 1.0f, 1.0f},
    {(float)(1.0 - 7.0 / 64.0),  (float)(1.0 - 7.0 / 256.0), 1.0f, 1.0f},
    {(float)(1.0 - 9.0 / 64.0),  (float)(1.0 - 9.0 / 256.0), 1.0f, 1.0f},
    {(float)(1.0 - 11.0 / 64.0), (float)(1.0 - 11.0 / 256.0), 1.0f, 1.0f},
};

/* drive vectors: mixed-sign fractional floats (non-terminating in binary
 * -> perpetual rounding churn, orbits never stall); roughly balanced so
 * the m=1.0 accumulate lanes random-walk slowly instead of trending. */
static const float32x4_t SV[8] = {
    { 0.100f, -0.350f,  1.100f, -2.300f},
    { 0.700f,  0.225f, -1.300f,  0.450f},
    {-0.175f,  0.825f,  2.300f, -1.150f},
    { 1.325f, -0.675f, -0.275f,  3.700f},
    {-2.725f,  1.975f,  0.625f, -0.825f},
    { 0.375f, -1.825f, -3.675f,  1.675f},
    { 2.925f,  0.525f,  0.875f, -0.125f},
    {-1.075f,  2.675f, -0.975f,  0.025f},
};

/* one true-dependency step on every chain; (a) selects the drive vector,
 * (b) the lane — both expand to compile-time constants. */
#define CH(i, a, b) \
    c[i] = vfmaq_laneq_f32(c[i], M[i], SV[(a) & 7], (b) & 3)

#define SWEEP(a, b) do { \
    CH(0, a, b);  CH(1, a, b);  CH(2, a, b);  CH(3, a, b); \
    CH(4, a, b);  CH(5, a, b);  CH(6, a, b);  CH(7, a, b); \
    CH(8, a, b);  CH(9, a, b);  CH(10, a, b); CH(11, a, b); \
} while (0)

#define SWEEP8(a, b) \
    SWEEP((a), (b));       SWEEP((a) + 1, (b) + 1); \
    SWEEP((a) + 2, (b) + 2); SWEEP((a) + 3, (b) + 3); \
    SWEEP((a) + 4, (b) + 4); SWEEP((a) + 5, (b) + 5); \
    SWEEP((a) + 6, (b) + 6); SWEEP((a) + 7, (b) + 7)

/* one round = 88 sweeps x 12 chains = 1056 static fmla sites */
#define ROUND() do { \
    SWEEP8(0, 0);  SWEEP8(8, 1);  SWEEP8(16, 2); SWEEP8(24, 3); \
    SWEEP8(32, 4); SWEEP8(40, 5); SWEEP8(48, 6); SWEEP8(56, 7); \
    SWEEP8(64, 0); SWEEP8(72, 1); SWEEP8(80, 2); \
} while (0)

static void put(const char *s){ write(1, s, strlen(s)); }

static void put_hex64(uint64_t v){
    char out[16];
    for (int i = 15; i >= 0; --i){
        unsigned d = v & 0xf;
        out[i] = d < 10 ? '0' + d : 'a' + d - 10;
        v >>= 4;
    }
    write(1, out, sizeof(out));
}

/* deterministic 64-bit fold (same family as branch_mispred.c / smoke.c) */
static uint64_t fold(uint64_t h, uint64_t v)
{
    h ^= v + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2);
    h ^= h >> 29;
    h *= 0xbf58476d1ce4e5b9ULL;
    h ^= h >> 32;
    return h;
}

int main(void)
{
    /* 12 chain seeds — one live vector register per chain, held all run */
    float32x4_t c[NV] = {
        { 1.0f,  2.0f,  3.0f,  4.0f},
        { 5.0f,  6.0f,  7.0f,  8.0f},
        { 9.0f, 10.0f, 11.0f, 12.0f},
        {13.0f, 14.0f, 15.0f, 16.0f},
        {17.0f, 18.0f, 19.0f, 20.0f},
        {21.0f, 22.0f, 23.0f, 24.0f},
        {25.0f, 26.0f, 27.0f, 28.0f},
        {29.0f, 30.0f, 31.0f, 32.0f},
        {33.0f, 34.0f, 35.0f, 36.0f},
        {37.0f, 38.0f, 39.0f, 40.0f},
        {41.0f, 42.0f, 43.0f, 44.0f},
        {45.0f, 46.0f, 47.0f, 48.0f},
    };

    for (uint32_t r = 0; r < ROUNDS; ++r)
        ROUND();

    /* cumulative-result self-check: all 48 lane bit-patterns fold into the
     * FINAL checksum (each lane is a chaotic function of its history) */
    uint32_t w[NV * 4];
    for (int i = 0; i < NV; ++i)
        vst1q_u32(&w[i * 4], vreinterpretq_u32_f32(c[i]));

    uint64_t final = 0x0123456789abcdefULL;
    for (int i = 0; i < NV * 4; ++i)
        final = fold(final, (uint64_t)w[i]);
    final = fold(final, (uint64_t)ROUNDS);

    put("FINAL=");
    put_hex64(final);
    write(1, "\n", 1);
    return 0;
}
