/* dep_chain — W1.5b long-dependency-chain pressure probe kernel (int).
 *
 * Purpose (docs/gem5-fi/ooo/03-workloads.md, 长依赖链压力核):
 *   construct a large number of TRUE dependency chains (every instruction
 *   consumes the previous result, chained multiply-accumulate), so the
 *   hardware holds the same small set of live architectural registers for
 *   a long time and rename keeps allocating fresh physical destinations
 *   that cannot be freed until their chain step commits — pinning the int
 *   physical-register Free List at a low watermark.  Self-check = the
 *   cumulative chain results folded into one FINAL=<16hex> line
 *   (tools/classify.py _CHECKSUM_RE; the no-injection value is the golden,
 *   native == gem5).
 *
 * Structure:
 *   8 parallel chains carried in 8 live uint64 registers, one true-dependency
 *   multiply-accumulate step per chain per loop iteration:
 *       c_i = c_i * K_i + D_i        (loop-carried, per chain)
 *   K_i/D_i are compile-time 64-bit odd constants chosen so gcc cannot
 *   strength-reduce the product into shift/add sequences (large odd
 *   multipliers force a real MADD — verified post-build by objdump).
 *
 * Why this drains the int free list on the C3-OOO platform (measured by
 * W0.3a CHAOSProbe): AArch64 MADD is opClass IntMultOp (gem5
 * src/arch/arm/isa/insts/data64.isa) and the DefaultFUPool has 2 IntMultDiv
 * units at opLat=3, while rename is 4-wide.  The 8 chains complete at most
 * ~2 madds/cycle, so rename runs ahead of commit until the int freelist
 * (numPhysIntRegs=128 minus the initial arch mapping) is exhausted; steady
 * state keeps only a handful of int phys regs free (reg_chain, the W1.0
 * single-chain baseline, measured flIntLe8 = 99.5% of probe samples).
 * Density gate: flIntLe8 sampling share >= 1%.
 *
 * Determinism: unsigned 64-bit wraparound arithmetic only — no FP, no UB,
 * no environment dependence — so the native host run and gem5 SE produce a
 * byte-identical FINAL line.
 *
 * Size: STEPS iterations x ~11 committed instructions ≈ 19M dynamic
 * instructions — gem5 C3 SE in tens of seconds (measured hostSeconds
 * recorded in README.md), within the 60s W1 SE budget.
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#define NCHAIN 8
#define STEPS  1750000UL  /* sized for C3 SE hostSeconds 30-60s (measured) */

/* Large odd 64-bit multipliers/addends: strength reduction impossible. */
static const uint64_t K[NCHAIN] = {
    0x9e3779b97f4a7c15ULL, 0xbf58476d1ce4e5b9ULL,
    0x94d049bb133111ebULL, 0x2545f4914f6cdd1dULL,
    0x9e3779b185ebca87ULL, 0xc2b2ae3d27d4eb4fULL,
    0x165667b19e3779f9ULL, 0x27d4eb2f165667c5ULL,
};
static const uint64_t D[NCHAIN] = {
    0x123456789abcdef1ULL, 0x0fedcba987654321ULL,
    0xdeadbeefcafebabeULL, 0xbadc0ffee0ddf00dULL,
    0x5851f42d4c957f2dULL, 0x14057b7ef767814fULL,
    0x1f83d92ab734e2f1ULL, 0xc0ffee123456789bULL,
};

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
    /* 8 chain seeds — one live register per chain, held for the whole run */
    uint64_t c0 = 0x0123456789abcdefULL;
    uint64_t c1 = 0xfedcba9876543210ULL;
    uint64_t c2 = 0x13579bdf2468ace0ULL;
    uint64_t c3 = 0x0eca864213fd9753ULL;
    uint64_t c4 = 0xa5a5a5a55a5a5a5aULL;
    uint64_t c5 = 0x3c3c3c3cc3c3c3c3ULL;
    uint64_t c6 = 0x7f1e2d3c4b5a6978ULL;
    uint64_t c7 = 0x0f0f0f0ff0f0f0f0ULL;

    /* the long true-dependency chains: every step consumes the previous
     * step's register result (loop-carried through c0..c7) */
    for (uint64_t k = 0; k < STEPS; ++k) {
        c0 = c0 * K[0] + D[0];
        c1 = c1 * K[1] + D[1];
        c2 = c2 * K[2] + D[2];
        c3 = c3 * K[3] + D[3];
        c4 = c4 * K[4] + D[4];
        c5 = c5 * K[5] + D[5];
        c6 = c6 * K[6] + D[6];
        c7 = c7 * K[7] + D[7];
    }

    /* cumulative-result self-check: the 8 final chain values (each a chaotic
     * function of its whole history — any propagated flip changes them) */
    uint64_t final = 0x0123456789abcdefULL;
    final = fold(final, c0);
    final = fold(final, c1);
    final = fold(final, c2);
    final = fold(final, c3);
    final = fold(final, c4);
    final = fold(final, c5);
    final = fold(final, c6);
    final = fold(final, c7);
    final = fold(final, (uint64_t)STEPS);

    put("FINAL=");
    put_hex64(final);
    write(1, "\n", 1);
    return 0;
}
