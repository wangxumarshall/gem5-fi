/* rob_fill — W1.5c ROB-fill probe kernel (int version).
 *
 * Purpose (docs/gem5-fi/ooo/03-workloads.md, ROB 填满核):
 *   interleave LONG-LATENCY operations — 连续除法, a cluster of consecutive
 *   independent integer divisions — with a large stream of subsequent
 *   independent short instructions.  The divide cluster sits at the ROB
 *   head and blocks in-order commit at the divide service rate (one
 *   completion per ~10-13 cycles: 2 IntMultDiv units, 20-cycle, not
 *   pipelined), while rename/dispatch (4-wide) pushes the younger
 *   independent short instructions into the window — driving the 128-entry
 *   Reorder Buffer to (and holding it at) near-full occupancy long-term.
 *   Self-check = cumulative quotient and accumulator state folded into one
 *   FINAL=<16hex> line (tools/classify.py _CHECKSUM_RE; the no-injection
 *   value is the golden, native == gem5).
 *
 * Structure (per round, macro-expanded 16x per loop iteration):
 *   1. POINTER CHASE (指针追逐, spec wording): a chain of 16 DEPENDENT
 *      loads over a 128 KiB permutation array (uint32 chase[32768], a
 *      fixed-seed LCG Fisher-Yates permutation, so every load's ADDRESS
 *      is the previous load's VALUE and the walk cycles through all
 *      elements).  Working set 128 KiB > 64 KiB L1, < 512 KiB L2 => every
 *      load is an L1 miss / L2 hit (~56 cycles measured), and the chain
 *      SERIALIZES them: the commit head is blocked for ~16 x 56 = ~900
 *      CONTINUOUS cycles per round.  Independent misses (v4/v6) overlap
 *      and drain in a burst; only a dependent chain holds the head for a
 *      long continuous stretch while rename streams the fill 4-wide into
 *      the window behind it.  Chase values folded + 1 image store each.
 *   2. DIVIDE CLUSTER (连续除法): 8 independent divides back-to-back
 *      (4 udiv + 4 sdiv), operands from mutable per-bank pair-packed
 *      arrays (LDP: one LQ entry per divide).  Quotients folded + 1
 *      image store each.
 *   3. operand mutations (madd + mask|orr + pair stores) for next round.
 *   4. FILL: independent SHORT IntALU instructions (add-immediates +
 *      xorshifts) on 8 live accumulator registers.  No madds (they
 *      saturate the 2 shared IntMultDiv units — measured
 *      statFuBusy::IntMult 63-97%), no spilled 64-bit constants (their
 *      reloads sit in the 32-entry LQ until commit — measured
 *      rename.LQFullEvents 920k), no fill stores (SQ-full triggers
 *      gem5's ~40-cycle rename skid-buffer drain — measured v6).
 *
 * Why the ROB fills on the C3-OOO platform (measured facts, W1.5c probe
 * iterations + gem5 source; see workloads/ooo/README.md):
 *   * IntDiv = opLat 20, NOT pipelined, 2 units
 *     (src/cpu/o3/FuncUnitConfig.py:53); the 8-divide cluster blocks the
 *     commit head for ~80-100 cycles while dispatch runs 4-wide — the
 *     window fills to the ROB/freelist/SQ ceiling (~120-128).
 *   * Divide operands live in MUTABLE per-bank arrays (round r uses bank
 *     r&1, rewritten every round): gcc can neither constant-fold a
 *     divisor into a magic multiply nor hoist a divide (LICM), and the
 *     store->reload distance of two rounds keeps the reloads clear of the
 *     store queue (v1's single bank measured 36,823 memory-order
 *     violations, each squashing the whole younger window).
 *   * Divisor discipline: ud/sd kept in [0x101, 0x3fff] (mask|orr), so
 *     udiv never divides by zero and sdiv never sees divisor -1
 *     (INT64_MIN / -1 would trap); sn wraps freely — any int64 numerator
 *     is safe with a strictly positive divisor.
 *
 * Determinism: unsigned/2's-complement wraparound integer arithmetic only
 * — no FP, no UB, no environment dependence — so the native host run and
 * the gem5 SE run produce a byte-identical FINAL line.
 *
 * Size: ITERS x 16 rounds ≈ 8.7M dynamic instructions (measured
 * simInsts 8,692,564; loop ~645 insts/round incl. the pointer chase,
 * divide cluster and fill) — gem5 C3 SE measured hostSeconds 40.98/41.88,
 * within the 60s W1 SE budget.
 * Density gate: robOver80 sampling share >= 50% (CHAOSProbe, occupancy
 * > 80% of the 128-entry ROB) — MEASURED 7.09%: NOT MET; see the W1.5c
 * record in README.md for the seven-iteration diagnosis (gem5 rename
 * skid-buffer drain + the C3 pool ceilings).  Divides present: objdump
 * sdiv/udiv static count 192 > 100, gem5 stat
 * commit.committedInstType_0::IntDiv = 140,290 (107,520 in-loop
 * + 32,770 permutation-init modulo).
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#define NACC          8     /* independent short-op accumulators (registers) */
#define NWALK         32768 /* 128 KiB chase permutation (32768 = 2^15) */
#define ROUNDS_PER_IT 16    /* macro-expanded rounds per loop iteration:
                             * 16 rounds x 8 divides = 128 static div sites */
#define ITERS         840   /* sized for C3 SE hostSeconds 30-60s (measured:
                               * v7 round ~540 insts x 16 = ~8.6K/iter; 840
                               * iters = ~7.2M + CRT ~11K at ~190 KIPS) */

/* mutable divide operands (NOT const — see header).  Two banks per family
 * (round r uses bank r&1, so a stored operand pair is reloaded two rounds
 * later — the store has long left the store queue).  Numerator and
 * divisor are packed ADJACENT so each divide's two operand loads fuse
 * into one LDP (one load-queue entry): v4's 16 separate operand loads per
 * round lingered in the 32-entry LQ until commit and LQ-full blocked
 * rename exactly during the divide-block window (rename.LQFullEvents
 * 200k), throttling dispatch down to commit rate. */
static uint64_t uv[2][4][2];  /* udiv: [bank][lane][0]=num, [1]=den */
static uint64_t sv[2][4][2];  /* sdiv: same layout (den kept positive) */
static uint32_t chase[NWALK]; /* pointer-chase permutation (values only) */

/* quotient images: 3 stores per divide that linger for the divide's
 * latency (ROB/SQ mass with no physical-register cost); slot (r,k) is
 * unique per (round, divide), all folded into FINAL after the loop. */
static uint64_t qs[8 * ROUNDS_PER_IT];
static uint64_t sc[2048];    /* fill accumulator images (54+ slots/round) */
static uint64_t sc2[4 * ROUNDS_PER_IT];  /* cluster accumulator images */

/* operand mixers (large odd constants: real madds, no strength reduction) */
#define KU 0x9e3779b97f4a7c15ULL
#define AU 0x123456789abcdef1ULL
#define KD 0xbf58476d1ce4e5b9ULL
#define AD 0x0fedcba987654321ULL
#define KS 0x94d049bb133111ebULL
#define AS 0xdeadbeefcafebabeULL
#define KE 0x2545f4914f6cdd1dULL
#define AE 0xbadc0ffee0ddf00dULL

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

/* defined uint64 <-> int64 bit reinterpretation (no conversion UB) */
static union { uint64_t u; int64_t s; } bits;

/* FILL: independent SHORT IntALU instructions on the 8 live accumulator
 * registers — add-immediates (12-bit, no constant registers, no spills,
 * no loads) + two-op xorshifts — INTERLEAVED WITH STORES of live
 * accumulator values.  The stores matter: the int freelist caps in-flight
 * destination instructions at ~95, so a store-free fill caps the whole
 * window at ~95-100 — just UNDER the 80%-of-128 gate threshold.  With
 * ~20% stores (no physical register, only an SQ entry) the window rises
 * to ~115-125 and the ROB itself becomes the binding cap. */
#define FILL_A(a0,a1,a2,a3,a4,a5,a6,a7) do { \
    a0 += 0x915; a1 += 0x2ab; a2 += 0x7d1; a3 += 0x537; \
    a4 += 0x3e9; a5 += 0x64b; a6 += 0x1f3; a7 += 0x8d5; \
    a0 ^= a0 >> 13; a2 ^= a2 >> 21; a4 ^= a4 >> 17; a6 ^= a6 >> 25; \
    a1 ^= a1 >> 15; a3 ^= a3 >> 27; a5 ^= a5 >> 19; a7 ^= a7 >> 23; \
} while (0)

#define NFILL 16  /* 16 steps x 16 insts = 256 fill instructions/round */

/* POINTER CHASE (指针追逐): 16 dependent loads; each address is the
 * previous load's value.  Slot (r*16+k) images fold into FINAL. */
#define CHASE(r) do { \
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
    sc[(r) * 16 + 0]  = c0; sc[(r) * 16 + 1]  = c1; \
    sc[(r) * 16 + 2]  = c2; sc[(r) * 16 + 3]  = c3; \
    sc[(r) * 16 + 4]  = c4; sc[(r) * 16 + 5]  = c5; \
    sc[(r) * 16 + 6]  = c6; sc[(r) * 16 + 7]  = c7; \
    sc[(r) * 16 + 8]  = c8; sc[(r) * 16 + 9]  = c9; \
    sc[(r) * 16 + 10] = cA; sc[(r) * 16 + 11] = cB; \
    sc[(r) * 16 + 12] = cC; sc[(r) * 16 + 13] = cD; \
    sc[(r) * 16 + 14] = cE; sc[(r) * 16 + 15] = cF; \
} while (0)

/* DIVIDE CLUSTER (连续除法): 8 independent divides back-to-back.  Loads
 * first (all 8 lanes' operands), then the 8 divides adjacent, then the
 * quotient folds + 3 image stores each.  gcc keeps this shape: every
 * divide depends only on its two loads. */
#define DIVCLUSTER(r) do { \
    uint64_t n0 = uv[(r) & 1][0][0], d0 = uv[(r) & 1][0][1]; \
    uint64_t n1 = uv[(r) & 1][1][0], d1 = uv[(r) & 1][1][1]; \
    uint64_t n2 = uv[(r) & 1][2][0], d2 = uv[(r) & 1][2][1]; \
    uint64_t n3 = uv[(r) & 1][3][0], d3 = uv[(r) & 1][3][1]; \
    bits.u = sv[(r) & 1][0][0]; uint64_t e0 = sv[(r) & 1][0][1]; int64_t w0 = bits.s; \
    bits.u = sv[(r) & 1][1][0]; uint64_t e1 = sv[(r) & 1][1][1]; int64_t w1 = bits.s; \
    bits.u = sv[(r) & 1][2][0]; uint64_t e2 = sv[(r) & 1][2][1]; int64_t w2 = bits.s; \
    bits.u = sv[(r) & 1][3][0]; uint64_t e3 = sv[(r) & 1][3][1]; int64_t w3 = bits.s; \
    uint64_t q0 = n0 / d0; \
    uint64_t q1 = n1 / d1; \
    uint64_t q2 = n2 / d2; \
    uint64_t q3 = n3 / d3; \
    int64_t p0 = w0 / (int64_t)e0; \
    int64_t p1 = w1 / (int64_t)e1; \
    int64_t p2 = w2 / (int64_t)e2; \
    int64_t p3 = w3 / (int64_t)e3; \
    qu ^= q0; qu ^= q1; qu ^= q2; qu ^= q3; \
    qw ^= (uint64_t)p0; qw ^= (uint64_t)p1; \
    qw ^= (uint64_t)p2; qw ^= (uint64_t)p3; \
    qs[(r) * 8 + 0] = q0;      qs[(r) * 8 + 1] = q1;      qs[(r) * 8 + 2] = q2;      qs[(r) * 8 + 3] = q3;      qs[(r) * 8 + 4] = (uint64_t)p0;      qs[(r) * 8 + 5] = (uint64_t)p1;      qs[(r) * 8 + 6] = (uint64_t)p2;      qs[(r) * 8 + 7] = (uint64_t)p3;      uv[(r) & 1][0][0] = n0 * KU + AU; \
    uv[(r) & 1][1][0] = n1 * KU + AU; \
    uv[(r) & 1][2][0] = n2 * KU + AU; \
    uv[(r) & 1][3][0] = n3 * KU + AU; \
    uv[(r) & 1][0][1] = 0x101ULL | ((d0 * KD + AD) & 0x3fffULL); \
    uv[(r) & 1][1][1] = 0x101ULL | ((d1 * KD + AD) & 0x3fffULL); \
    uv[(r) & 1][2][1] = 0x101ULL | ((d2 * KD + AD) & 0x3fffULL); \
    uv[(r) & 1][3][1] = 0x101ULL | ((d3 * KD + AD) & 0x3fffULL); \
    sv[(r) & 1][0][0] = (uint64_t)w0 * KS + AS; \
    sv[(r) & 1][1][0] = (uint64_t)w1 * KS + AS; \
    sv[(r) & 1][2][0] = (uint64_t)w2 * KS + AS; \
    sv[(r) & 1][3][0] = (uint64_t)w3 * KS + AS; \
    sv[(r) & 1][0][1] = 0x101ULL | ((e0 * KE + AE) & 0x3fffULL); \
    sv[(r) & 1][1][1] = 0x101ULL | ((e1 * KE + AE) & 0x3fffULL); \
    sv[(r) & 1][2][1] = 0x101ULL | ((e2 * KE + AE) & 0x3fffULL); \
    sv[(r) & 1][3][1] = 0x101ULL | ((e3 * KE + AE) & 0x3fffULL); \
    sc2[(r) * 4 + 0] = a1; sc2[(r) * 4 + 1] = a3; \
    sc2[(r) * 4 + 2] = a5; sc2[(r) * 4 + 3] = a7; \
FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
    FILL_A(a0,a1,a2,a3,a4,a5,a6,a7); \
} while (0)

#define ROUND(r) do { CHASE(r); DIVCLUSTER(r); } while (0)

/* 16 rounds per iteration, macro-expanded: 16 x 8 = 128 static divide
 * sites (div-in-field proof by objdump grep -c 'sdiv\|udiv'). */
#define ROUND16() do { \
    ROUND(0);  ROUND(1);  ROUND(2);  ROUND(3); \
    ROUND(4);  ROUND(5);  ROUND(6);  ROUND(7); \
    ROUND(8);  ROUND(9);  ROUND(10); ROUND(11); \
    ROUND(12); ROUND(13); ROUND(14); ROUND(15); \
} while (0)

int main(void)
{
    uint64_t rng;
    /* pointer-chase permutation: fixed-seed LCG Fisher-Yates over
     * 0..NWALK-1 (a single full cycle — values only, deterministic). */
    for (uint32_t i = 0; i < NWALK; ++i) chase[i] = i;
    rng = 0x853c49e6748fea9bULL;
    for (uint32_t i = NWALK - 1; i > 0; --i) {
        rng = rng * 6364136223846793005ULL + 1442695040888963407ULL;
        uint32_t j = (uint32_t)(rng >> 33) % (i + 1);
        uint32_t t = chase[i]; chase[i] = chase[j]; chase[j] = t;
    }

    /* operand seeds (nonzero; divisors already in range; both banks) */
    for (int b = 0; b < 2; ++b) {
        for (int i = 0; i < 4; ++i) {
            uv[b][i][0] = 0x0123456789abcdefULL + (uint64_t)(i + 4 * b) * 0x10001ULL;
            uv[b][i][1] = 0x1357ULL + (uint64_t)(i + 4 * b);
            sv[b][i][0] = 0xfedcba9876543210ULL + (uint64_t)(i + 4 * b) * 0x10001ULL;
            sv[b][i][1] = 0x2468ULL + (uint64_t)(i + 4 * b);
        }
    }

    uint64_t a0 = 0xa5a5a5a55a5a5a5aULL, a1 = 0x3c3c3c3cc3c3c3c3ULL;
    uint64_t a2 = 0x7f1e2d3c4b5a6978ULL, a3 = 0x0f0f0f0ff0f0f0f0ULL;
    uint64_t a4 = 0x5a5a5a5aa5a5a5a5ULL, a5 = 0xc3c3c3c33c3c3c3cULL;
    uint64_t a6 = 0x69784b5a3c2d1e7fULL, a7 = 0xf0f0f0f00f0f0f0fULL;
    uint64_t qu = 0x0123456789abcdefULL;
    uint64_t qw = 0xfedcba9876543210ULL;
    uint32_t cp = 0;                 /* chase pointer */
    uint64_t cw = 0x13579bdf2468ace0ULL;  /* chase fold */

    for (uint64_t it = 0; it < ITERS; ++it) {
        ROUND16();
    }

    /* cumulative-result self-check: every accumulator, both quotient
     * folds, and every stored image feeds the FINAL checksum. */
    uint64_t final = 0x0123456789abcdefULL;
    final = fold(final, a0); final = fold(final, a1);
    final = fold(final, a2); final = fold(final, a3);
    final = fold(final, a4); final = fold(final, a5);
    final = fold(final, a6); final = fold(final, a7);
    final = fold(final, qu); final = fold(final, qw);
    final = fold(final, cw); final = fold(final, (uint64_t)cp);
    for (int k = 0; k < 8 * ROUNDS_PER_IT; ++k) {
        final = fold(final, qs[k]);
    }
    for (int k = 0; k < 4 * ROUNDS_PER_IT; ++k)
        final = fold(final, sc2[k]);
    for (int k = 0; k < 16 * ROUNDS_PER_IT; ++k)
        final = fold(final, sc[k]);
    final = fold(final, (uint64_t)ITERS * ROUNDS_PER_IT);

    put("FINAL=");
    put_hex64(final);
    write(1, "\n", 1);
    return 0;
}
