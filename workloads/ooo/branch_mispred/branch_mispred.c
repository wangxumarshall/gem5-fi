/* branch_mispred — W1.5a branch-misprediction-dense probe kernel.
 *
 * Purpose (docs/gem5-fi/ooo/03-workloads.md, branch_mispred_dense):
 *   construct a large number of data-dependent, unpredictable conditional
 *   branches (conditional-branch traversal over a randomly permuted array),
 *   deliberately driving the branch misprediction rate up so RAT/Rename
 *   checkpoints are frequently triggered and then recovered (branch
 *   mispredict squashes).  Self-check = accumulated checksum plus
 *   permutation statistics (result-array self-verification), printed as one
 *   FINAL=<16hex> line (tools/classify.py _CHECKSUM_RE; the no-injection
 *   value is the golden, native == gem5).
 *
 * Structure:
 *   1. Fixed-seed LCG (same Knuth 64-bit generator family as smoke.c) fills
 *      perm[0..4095] = 0..4095, then one full Fisher-Yates shuffle.
 *   2. BP_ROUNDS traversals.  Each round first re-shuffles a rotating
 *      512-entry window with the continuing LCG stream (per spec: seed
 *      shuffle over multiple rounds), so branch-outcome streams never
 *      repeat across rounds and no predictor can lock onto them; then it
 *      traverses the whole array doing five data-dependent conditional
 *      branches per element:
 *        B1 parity        if (v & 1)                — 50/50 random
 *        B2 threshold     if (v > thr)              — thr evolves from
 *                                                      branch outcomes
 *        B3 state parity  if ((v ^ st) & 0x10)      — mixes live state
 *        B4 mix parity    if ((v ^ (v >> 3)) & 4)
 *        B5 state parity  if (((v >> 1) ^ st) & 0x20)
 *      Every arm writes a *distinct* live global slot (sc[k], read back
 *      into the checksum) plus an accumulator update.  ARM64 has no
 *      predicated stores, so arms with stores cannot be if-converted to
 *      csel — these stay REAL conditional branches (verified post-build by
 *      objdump: conditional-branch vs csel count in the hot loop).
 *   3. Verification pass: permutation statistics (circular descents, fixed
 *      points, displacement xor-sum, O(K^2) inversion count over a fixed
 *      256-slice) plus all accumulators fold into the FINAL checksum.
 *
 * Determinism: unsigned integer arithmetic only — no FP, no UB, no
 * environment dependence — so the native host run and gem5 SE produce a
 * byte-identical FINAL line.
 *
 * Size: ~ten million dynamic instructions — gem5 C3 SE in tens of seconds
 * (measured hostSeconds recorded in README.md), within the 60s W1 SE
 * budget; density gate mispredicts/commits >= 5% (reg_chain baseline
 * ~0.001%).
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#define BP_N       4096u  /* permutation size (spec: 4096 items) */
#define BP_ROUNDS  48u    /* traversals (sized for C3 SE <= 60s) */
#define BP_WIN     512u   /* per-round re-shuffle window (rotating) */
#define BP_SLICE   256u   /* inversion-count slice (O(K^2) statistic) */

static uint32_t perm[BP_N];
static uint32_t sc[10];   /* live per-arm store targets (block csel) */

static uint64_t rng_state = 0x853c49e6748fea9bULL; /* fixed seed */

static uint32_t rnd(void)
{
    rng_state = rng_state * 6364136223846793005ULL
              + 1442695040888963407ULL;
    return (uint32_t)(rng_state >> 33);
}

/* Fisher-Yates inside perm[base .. base+len): the whole array stays a
 * permutation of 0..N-1, so the end-of-run permutation statistics remain
 * well-defined. */
static void shuffle_window(uint32_t base, uint32_t len)
{
    for (uint32_t k = len - 1; k > 0; --k) {
        uint32_t j = rnd() % (k + 1);
        uint32_t a = perm[base + k];
        uint32_t b = perm[base + j];
        perm[base + k] = b;
        perm[base + j] = a;
    }
}

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

/* deterministic 64-bit fold (hash_combine + splitmix-style finalizer) */
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
    uint64_t acc1 = 0, acc2 = 0, acc3 = 0, acc4 = 0;
    uint32_t st  = 0x1234567u;   /* live state, feeds B3/B4/B5 conditions */
    uint32_t thr = 2048u;        /* outcome-evolving threshold (B2) */

    /* 1. random permutation, fixed seed */
    for (uint32_t i = 0; i < BP_N; ++i)
        perm[i] = i;
    shuffle_window(0, BP_N);

    /* 2. traversals: data-dependent conditional branches over perm[] */
    for (uint32_t r = 0; r < BP_ROUNDS; ++r) {
        shuffle_window((r % (BP_N / BP_WIN)) * BP_WIN, BP_WIN);

        for (uint32_t i = 0; i < BP_N; ++i) {
            uint32_t v = perm[i];

            /* B1: parity of a permutation element — 50/50 random */
            if (v & 1u) {
                acc1 += v;
                sc[0] = v;
            } else {
                acc1 ^= (uint64_t)(v >> 1);
                sc[1] = v >> 2;
            }

            /* B2: threshold against an outcome-evolving threshold */
            if (v > thr) {
                acc2 += (uint64_t)v * 3u;
                thr = thr + 1u + (v & 7u);
                sc[2] = v;
            } else {
                acc2 ^= (uint64_t)(v >> 2);
                thr = thr - 1u - (v & 3u);
                sc[3] = v >> 3;
            }

            /* B3: parity mixed with live state */
            if ((v ^ st) & 0x10u) {
                acc3 += (uint64_t)v * st;
                sc[4] = v;
            } else {
                acc3 ^= (uint64_t)(v + st);
                sc[5] = v >> 4;
            }

            /* B4: bit-mix parity of the element */
            if ((v ^ (v >> 3)) & 4u) {
                acc4 += v + (v << 8);
                sc[6] = v;
            } else {
                acc4 -= v ^ (st >> 3);
                sc[7] = v >> 5;
            }

            /* B5: shifted parity mixed with live state */
            if (((v >> 1) ^ st) & 0x20u) {
                acc1 += (uint64_t)v * 5u;
                sc[8] = v;
            } else {
                acc3 -= (uint64_t)(v ^ st);
                sc[9] = v >> 6;
            }

            /* unconditional state update (keeps B3/B4/B5 conditions
             * data-dependent on the fresh element stream) */
            st = st * 3u + (v & 3u);
        }
    }

    /* 3. permutation statistics — the self-check surface (spec: 排列的统计量) */
    uint64_t descents = 0, fixedpts = 0, dispx = 0, inversions = 0;
    for (uint32_t i = 0; i < BP_N; ++i) {
        if (perm[i] > perm[(i + 1u) & (BP_N - 1u)])
            ++descents;                    /* circular descent count */
        if (perm[i] == i)
            ++fixedpts;                    /* fixed points */
        dispx += (perm[i] ^ i) & 0xffu;    /* displacement xor-sum */
    }
    for (uint32_t i = 0; i < BP_SLICE; ++i)
        for (uint32_t j = i + 1u; j < BP_SLICE; ++j)
            if (perm[i] > perm[j])
                ++inversions;              /* slice inversion count */

    /* fold everything into the FINAL checksum */
    uint64_t final = 0x0123456789abcdefULL;
    final = fold(final, acc1);
    final = fold(final, acc2);
    final = fold(final, acc3);
    final = fold(final, acc4);
    final = fold(final, (uint64_t)st);
    final = fold(final, (uint64_t)thr);
    final = fold(final, descents);
    final = fold(final, fixedpts);
    final = fold(final, dispx);
    final = fold(final, inversions);
    for (uint32_t k = 0; k < 10; ++k)
        final = fold(final, (uint64_t)sc[k]);

    put("FINAL=");
    put_hex64(final);
    put("\n");
    return 0;
}
