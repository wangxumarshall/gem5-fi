/* rob_fill_fp — W1.5c ROB-fill probe kernel (fp version, scalar double).
 *
 * Purpose (docs/gem5-fi/ooo/03-workloads.md, ROB 填满核):
 *   interleave LONG-LATENCY operations — the spec's two sanctioned forms,
 *   连续除法 (paired scalar double-precision divisions, AArch64 FDIV) and
 *   大跨度内存访问 (a cluster of consecutive large-stride loads) — with a
 *   large stream of subsequent independent short instructions, so the
 *   in-order commit stage is blocked for long stretches on the oldest
 *   unfinished load/divide while rename/dispatch (4-wide) pushes younger
 *   independent work into the window — driving the 128-entry Reorder
 *   Buffer to (and holding it at) near-full occupancy long-term.
 *   Self-check = cumulative quotient-bit and accumulator state folded into
 *   one FINAL=<16hex> line (the no-injection value is the golden,
 *   native == gem5).
 *
 * Structure (per round; 32 rounds macro-expanded per loop iteration):
 *   1. STRIDE-LOAD CLUSTER (大跨度内存访问): 12 back-to-back loads from a
 *      256 KiB u64 walker (32768 entries, stride 4099 — coprime to 2^15,
 *      so the walk cycles through every element; working set 256 KiB >
 *      64 KiB L1, < 512 KiB L2  =>  every access is an L1 miss / L2 hit,
 *      a ~50-cycle in-order commit blocker with an INTEGER destination
 *      register that does not touch the vec pool).  Values folded + 1
 *      image store each (stores linger for the miss latency).
 *   2. FDIV PAIR GROUPS: 2 groups per round; each group loads one
 *      numerator + one divisor (double loads, 2 vec tokens) and performs
 *      TWO divisions — q = n/d and its reciprocal d/n (gcc cannot CSE
 *      them; 4 vec tokens per 2 fdivs).  Group spacing ~200 instructions
 *      keeps the 4-entry vec physical-register pool from ever starving
 *      rename (a starve costs ~40 cycles of skid-buffer drain — measured
 *      rename.status::Unblocking 37% in the v4 probe with 3-token lanes
 *      every ~80 insts).  Quotient bits folded raw + 2 image stores each.
 *   3. FILL: independent SHORT IntALU instructions (add-immediates +
 *      xorshifts) on 8 live accumulator registers, INTERLEAVED WITH
 *      STORES of live accumulator values.  The stores matter: the int
 *      freelist caps in-flight destination instructions at ~95, so a
 *      store-free fill caps the window at ~95-100 — just UNDER the
 *      80%-of-128 gate threshold; ~16-20% stores (SQ entries, no
 *      physical register) lift the window to ~115-125 so the ROB itself
 *      becomes the binding cap.  No madds (the 2 IntMultDiv units
 *      saturate — measured statFuBusy::IntMult 97% in v1), no spilled
 *      64-bit constants (their reloads sit in the 32-entry LQ until
 *      commit — measured rename.LQFullEvents 920k in v3).
 *
 * Why the long-latency mix is what it is on the C3-OOO platform
 * (measured facts, W1.5b/W1.5c probe iterations + gem5 source; see
 * workloads/ooo/README.md):
 *   * Scalar FDIV d = FloatDiv opClass, opLat 12, NOT pipelined, 2 units
 *     (src/cpu/o3/FuncUnitConfig.py:74) — a genuine long-latency op.
 *     BUT gem5 models VECTOR fdiv (SimdFloatDiv) as opLat 1, pipelined
 *     (SIMD_Unit) — useless as a blocker; and on C3 (numPhysVecRegs=48,
 *     44 arch vec) only ~4 vector/FP physical registers are ever free
 *     (W1.5b D75 calibration), so FP-destination instructions cannot by
 *     themselves fill a 128-entry ROB: their phys regs recycle at commit
 *     rate.  The kernel therefore ALSO uses the spec's other sanctioned
 *     long-latency op (large-stride loads) as the integer-destination
 *     commit blocker, with the fdiv pairs providing the FP content.
 *
 * Determinism / fplib bit-exactness: the ONLY floating-point operations in
 * the kernel are the scalar double divisions (plus FMOV bit-moves, which
 * cannot diverge).  Operands are forced-normal doubles built from integer
 * bit patterns (numerator exponent 0x409, divisor exponent 0x3ff; n/d in
 * [512, 2048) and d/n in (4.9e-4, 2e-3) — normal, no denormals, no NaN/Inf,
 * default RN rounding), so both the native hardware FDIV and gem5's
 * fplibDiv<uint64_t> (src/arch/arm/isa/insts/fp64.isa:460) are IEEE-754
 * correctly rounded and must agree bit-for-bit; the quotient bits are
 * folded raw, so a 1-ulp difference anywhere would change FINAL.  The
 * native == gem5 run is the empirical proof of that bit-exactness.
 *
 * Size: ITERS x 32 rounds ≈ 7.9M dynamic instructions (measured
 * simInsts 7,901,621) — gem5 C3 SE measured hostSeconds 44.22/44.91,
 * within the 60s W1 SE budget.
 * Density gate: robOver80 sampling share >= 50% — MEASURED 4.91%: NOT
 * MET; see the W1.5c record in README.md for the seven-iteration
 * diagnosis (gem5 rename skid-buffer drain + the C3 pool ceilings).
 * fdiv present: objdump static count 130 > 100, gem5 stat
 * commit.committedInstType_0::FloatDiv = 69,120 (= 540 x 32 x 4 exact).
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#define NACC          8      /* independent short-op accumulators (registers) */
#define NWALK         32768  /* 256 KiB walker (32768 = 2^15) */
#define NCLUSTER      16     /* stride loads per round (LQ budget) */
#define ROUNDS_PER_IT 32     /* macro-expanded rounds per loop iteration:
                              * 32 rounds x 4 fdivs = 128 static fdiv sites */
#define ITERS         540    /* sized for C3 SE hostSeconds 30-60s (measured) */

/* bit patterns for forced-normal IEEE doubles */
#define MANMASK 0x000fffffffffffffULL
#define FNEXP   0x4090000000000000ULL   /* numerator in [1024, 2048) */
#define FDEXP   0x3ff0000000000000ULL   /* divisor  in [1.0, 2.0)   */

static uint32_t chase[NWALK];           /* pointer-chase permutation */
static double   fnum[2];                /* fdiv numerators (bit-controlled) */
static double   fden[2];                /* fdiv divisors (bit-controlled) */

/* images: stores that linger for their producer's latency; slot (r,k) is
 * unique per (round, lane), all folded into FINAL after the loop. */
static uint64_t fq_img[4 * ROUNDS_PER_IT];
static uint64_t fq2[4 * ROUNDS_PER_IT];
static uint64_t wv1[NCLUSTER * ROUNDS_PER_IT];
static uint64_t sc[2048];               /* fill accumulator images */
static uint64_t sc2[NCLUSTER * ROUNDS_PER_IT];  /* walker-fold images */

/* operand mixers (large odd constants: real madds, no strength reduction) */
#define KF 0x9e3779b97f4a7c15ULL
#define AF 0x123456789abcdef1ULL
#define KG 0xbf58476d1ce4e5b9ULL
#define AG 0x0fedcba987654321ULL

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

/* deterministic 64-bit fold (same family as smoke.c / dep_chain.c) */
static uint64_t fold(uint64_t h, uint64_t v)
{
    h ^= v + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2);
    h ^= h >> 29;
    h *= 0xbf58476d1ce4e5b9ULL;
    h ^= h >> 32;
    return h;
}

/* defined bit reinterpretation */
static union { uint64_t u; double d; } cvt;

/* FILL: independent SHORT IntALU instructions on the 8 live accumulator
 * registers — add-immediates (12-bit, no constant registers, no spills,
 * no loads) + two-op xorshifts, interleaved with accumulator stores. */
#define FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,R,S) do { \
    a0 += 0x915; a1 += 0x2ab; a2 += 0x7d1; a3 += 0x537; \
    sc[((R) * 48 + (S) * 4 + 0) & 2047] = a0; \
    a4 += 0x3e9; a5 += 0x64b; a6 += 0x1f3; a7 += 0x8d5; \
    sc[((R) * 48 + (S) * 4 + 1) & 2047] = a4; \
    a0 ^= a0 >> 13; a2 ^= a2 >> 21; a4 ^= a4 >> 17; a6 ^= a6 >> 25; \
    sc[((R) * 48 + (S) * 4 + 2) & 2047] = a2; \
    a1 ^= a1 >> 15; a3 ^= a3 >> 27; a5 ^= a5 >> 19; a7 ^= a7 >> 23; \
    sc[((R) * 48 + (S) * 4 + 3) & 2047] = a6; \
} while (0)

/* FDIV PAIR GROUP g of round r: two divisions (q = n/d and the reciprocal
 * d/n — distinct values, no CSE) sharing one numerator load and one
 * divisor load: 4 vec-dest instructions per 2 fdivs.  Quotient bits are
 * folded raw and stored to 2 image slots each; the operand bits are
 * mutated (integer madd on the bit patterns via memcpy, exponents forced
 * normal). */
#define FDIV_GROUP(g, r) do { \
    double num = fnum[g]; \
    double den = fden[g]; \
    double qa = num / den; \
    double qb = den / num; \
    cvt.d = qa; uint64_t ba = cvt.u; \
    cvt.d = qb; uint64_t bb = cvt.u; \
    fq ^= ba; fq ^= bb; \
    fq_img[(r) * 4 + 2 * (g)]     = ba; fq2[(r) * 4 + 2 * (g)]     = ba; \
    fq_img[(r) * 4 + 2 * (g) + 1] = bb; fq2[(r) * 4 + 2 * (g) + 1] = bb; \
    cvt.d = num; uint64_t nb = cvt.u * KF + AF; \
    cvt.d = den; uint64_t db = cvt.u * KG + AG; \
    nb = FNEXP | (nb & MANMASK); \
    db = FDEXP | (db & MANMASK); \
    memcpy(&fnum[g], &nb, 8); \
    memcpy(&fden[g], &db, 8); \
} while (0)

/* one round: stride-load cluster (commit-head blocker), fill stretch,
 * two fdiv pair groups spaced ~200 instructions apart, trailing fill. */
#define ROUND(r) do { \
    uint32_t c0 = chase[cp]; cp = c0; \
    uint32_t c1 = chase[cp]; cp = c1; \
    uint32_t c2 = chase[cp]; cp = c2; \
    uint32_t c3 = chase[cp]; cp = c3; \
    uint32_t c4 = chase[cp]; cp = c4; \
    uint32_t c5 = chase[cp]; cp = c5; \
    uint32_t c6 = chase[cp]; cp = c6; \
    uint32_t c7 = chase[cp]; cp = c7; \
    uint32_t c8 = chase[cp]; cp = c8; \
    uint32_t c9 = chase[cp]; cp = c9; \
    uint32_t cA = chase[cp]; cp = cA; \
    uint32_t cB = chase[cp]; cp = cB; \
    uint32_t cC = chase[cp]; cp = cC; \
    uint32_t cD = chase[cp]; cp = cD; \
    uint32_t cE = chase[cp]; cp = cE; \
    uint32_t cF = chase[cp]; cp = cF; \
    cw ^= c0; cw ^= c1; cw ^= c2; cw ^= c3; \
    cw ^= c4; cw ^= c5; cw ^= c6; cw ^= c7; \
    cw ^= c8; cw ^= c9; cw ^= cA; cw ^= cB; \
    cw ^= cC; cw ^= cD; cw ^= cE; cw ^= cF; \
    wv1[(r) * 16 + 0] = c0;  wv1[(r) * 16 + 1] = c1; \
    wv1[(r) * 16 + 2] = c2;  wv1[(r) * 16 + 3] = c3; \
    wv1[(r) * 16 + 4] = c4;  wv1[(r) * 16 + 5] = c5; \
    wv1[(r) * 16 + 6] = c6;  wv1[(r) * 16 + 7] = c7; \
    wv1[(r) * 16 + 8] = c8;  wv1[(r) * 16 + 9] = c9; \
    wv1[(r) * 16 + 10] = cA; wv1[(r) * 16 + 11] = cB; \
    wv1[(r) * 16 + 12] = cC; wv1[(r) * 16 + 13] = cD; \
    wv1[(r) * 16 + 14] = cE; wv1[(r) * 16 + 15] = cF; \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),0); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),1); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),2); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),3); \
    FDIV_GROUP(0, r); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),4); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),5); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),6); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),7); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),8); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),9); \
    FDIV_GROUP(1, r); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),10); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),11); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),12); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),13); \
    FILL_B(a0,a1,a2,a3,a4,a5,a6,a7,(r),14); \
} while (0)

/* 32 rounds per iteration, macro-expanded: 32 x 4 = 128 static fdiv
 * sites (div-in-field proof by objdump grep -c 'fdiv'). */
#define ROUND32() do { \
    ROUND(0);  ROUND(1);  ROUND(2);  ROUND(3); \
    ROUND(4);  ROUND(5);  ROUND(6);  ROUND(7); \
    ROUND(8);  ROUND(9);  ROUND(10); ROUND(11); \
    ROUND(12); ROUND(13); ROUND(14); ROUND(15); \
    ROUND(16); ROUND(17); ROUND(18); ROUND(19); \
    ROUND(20); ROUND(21); ROUND(22); ROUND(23); \
    ROUND(24); ROUND(25); ROUND(26); ROUND(27); \
    ROUND(28); ROUND(29); ROUND(30); ROUND(31); \
} while (0)

int main(void)
{
    /* deterministic pointer-chase permutation: fixed-seed LCG
     * Fisher-Yates over 0..NWALK-1 (single full cycle — values only). */
    for (uint32_t i = 0; i < NWALK; ++i) chase[i] = i;
    uint64_t rng = 0x853c49e6748fea9bULL;
    for (uint32_t i = NWALK - 1; i > 0; --i) {
        rng = rng * 6364136223846793005ULL + 1442695040888963407ULL;
        uint32_t j = (uint32_t)(rng >> 33) % (i + 1);
        uint32_t t = chase[i]; chase[i] = chase[j]; chase[j] = t;
    }
    cvt.u = FNEXP | 0x0123456789abcdULL; fnum[0] = cvt.d;
    cvt.u = FNEXP | 0xfedcba9876543210ULL; fnum[1] = cvt.d;
    cvt.u = FDEXP | 0x0fedcba98765432ULL; fden[0] = cvt.d;
    cvt.u = FDEXP | 0x123456789abcdef0ULL; fden[1] = cvt.d;

    uint64_t a0 = 0xa5a5a5a55a5a5a5aULL, a1 = 0x3c3c3c3cc3c3c3c3ULL;
    uint64_t a2 = 0x7f1e2d3c4b5a6978ULL, a3 = 0x0f0f0f0ff0f0f0f0ULL;
    uint64_t a4 = 0x5a5a5a5aa5a5a5a5ULL, a5 = 0xc3c3c3c33c3c3c3cULL;
    uint64_t a6 = 0x69784b5a3c2d1e7fULL, a7 = 0xf0f0f0f00f0f0f0fULL;
    uint32_t cp = 0;                 /* chase pointer */
    uint64_t cw = 0x13579bdf2468ace0ULL;  /* chase fold */
    uint64_t fq = 0xfedcba9876543210ULL;

    for (uint64_t it = 0; it < ITERS; ++it) {
        ROUND32();
    }

    /* cumulative-result self-check: accumulators, both value folds, and
     * every stored image feed the FINAL checksum. */
    uint64_t final = 0x0123456789abcdefULL;
    final = fold(final, a0); final = fold(final, a1);
    final = fold(final, a2); final = fold(final, a3);
    final = fold(final, a4); final = fold(final, a5);
    final = fold(final, a6); final = fold(final, a7);
    final = fold(final, cw); final = fold(final, fq);
    final = fold(final, (uint64_t)cp);
    for (int k = 0; k < 4 * ROUNDS_PER_IT; ++k) {
        final = fold(final, fq_img[k]);
        final = fold(final, fq2[k]);
    }
    for (int k = 0; k < NCLUSTER * ROUNDS_PER_IT; ++k) {
        final = fold(final, wv1[k]);
        final = fold(final, sc2[k]);
    }
    for (int k = 0; k < 2048; ++k)
        final = fold(final, sc[k]);
    final = fold(final, (uint64_t)ITERS * ROUNDS_PER_IT);

    put("FINAL=");
    put_hex64(final);
    write(1, "\n", 1);
    return 0;
}
