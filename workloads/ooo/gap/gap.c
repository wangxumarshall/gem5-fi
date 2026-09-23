/* gap — W1.4a GAP semantic proxy kernel (bfs + pr).
 *
 * HONEST PROVENANCE ("GAP 语义代理（bfs/pr）", W1 plan Task 8 Step 1
 * decision, 2026-09-23):
 *   The upstream GAP benchmark suite (Beamer/Patterson/Dongarra,
 *   https://github.com/sbeamer/gapbs) targets native-scale graphs (R-MAT /
 *   kron graphs of 2^20+ vertices, GB-scale CSR) and is engineered around
 *   machine-scale memory bandwidth; cutting it down to fit the gem5 SE
 *   60 s hostSeconds budget would no longer be GAP.  Per the W1 plan this
 *   is a lightweight semantic proxy written from scratch, NOT vendored
 *   GAP:
 *     * fixed-seed LCG-generated directed graph in CSR form (every vertex
 *       has exactly DEGREE out-edges to LCG-uniform destinations — a
 *       random-graph stand-in for GAP's R-MAT graphs);
 *     * top-down BFS with a FIFO frontier (level-order traversal from
 *       fixed sources) — the GAP-bfs algorithm family;
 *     * scatter-form PageRank, fixed iteration count, double accumulation
 *       — the GAP-pr algorithm family.
 *   Self-check = BFS level-order hash + PageRank rank/convergence-residual
 *   hash folded into one FINAL=<16hex> line (tools/classify.py
 *   _CHECKSUM_RE); the no-injection value is the golden (native == gem5).
 *
 * Why this load (docs/gem5-fi/ooo/03-workloads.md GAP row: "邻接表下标取数，
 * 控制流不规则，边界/异常路径多"):
 *   the inner loops branch on data (level[w] already visited? scatter
 *   accumulate) whose outcomes the branch predictor cannot learn from the
 *   program text — the irregular-control-flow / mispredict-squash-recovery
 *   scenario (D36-D38 old-phys squash context) this workload is assigned
 *   to cover; the CSR colidx (512 KiB) + level/contrib arrays deliberately
 *   exceed the C3 64 KiB L1D / 512 KiB L2 working set so adjacency loads
 *   are genuine irregular cache misses.
 *
 * Determinism (native == gem5, byte-identical FINAL):
 *   graph generation, CSR build and BFS are int32/uint64 arithmetic;
 *   PageRank uses double mul/add only — no libm, no runtime division
 *   (tele/base_scale/init are compile-time constants), values stay
 *   ~1e-4 (no denormals), and the per-u product feeds memory scatter
 *   adds, giving gcc no mult+add pair to contract into FMA (verified
 *   post-build by objdump: 0 fmuladd sites in the kernel).
 *
 * Size: NVERT/DEGREE/BFS_RUNS/PR_ITERS calibrated for C3 SE hostSeconds
 * 30-60 s (measured values in workloads/ooo/README.md W1.4a record).
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#define NVERT    16384  /* 2^14 vertices — sized for the SE budget       */
#define DEGREE   8      /* exactly 8 out-edges per vertex (avg deg ~8)   */
#define NEDGE    (NVERT * DEGREE)
#define BFS_RUNS 2      /* fixed BFS sources                             */
#define PR_ITERS 2      /* fixed PageRank iterations                     */
#define DAMPING  0.85

static int32_t rowptr[NVERT + 1];
static int32_t colidx[NEDGE];
static int32_t level[NVERT];
static int32_t queue[NVERT];
static double pr_a[NVERT];
static double pr_b[NVERT];
static double contrib[NVERT];

/* fixed-seed LCG (same generator family as the other probe kernels) */
static uint64_t rng = 0x853c49e6748fea9bULL;
static uint64_t lcg_next(void)
{
    rng = rng * 6364136223846793005ULL + 1442695040888963407ULL;
    return rng;
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

/* deterministic 64-bit fold (same family as smoke.c / dep_chain.c) */
static uint64_t fold(uint64_t h, uint64_t v)
{
    h ^= v + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2);
    h ^= h >> 29;
    h *= 0xbf58476d1ce4e5b9ULL;
    h ^= h >> 32;
    return h;
}

static uint64_t bits_of(double d)
{
    uint64_t b;
    memcpy(&b, &d, sizeof(b));
    return b;
}

/* top-down BFS with a FIFO frontier: vertices are dequeued in level order,
 * and the hash folds (vertex, level) per dequeue plus a post-sweep over
 * the level vector — sensitive to any traversal / level perturbation. */
static uint64_t bfs_run(uint32_t src)
{
    uint64_t h = 0x9e3779b97f4a7c15ULL;

    for (uint32_t v = 0; v < NVERT; ++v)
        level[v] = -1;

    uint32_t head = 0, tail = 0;
    level[src] = 0;
    queue[tail++] = (int32_t)src;

    while (head < tail) {
        uint32_t u = (uint32_t)queue[head++];
        int32_t lu1 = level[u] + 1;
        h = fold(h, ((uint64_t)u << 32) | (uint32_t)lu1);
        for (int32_t e = rowptr[u]; e < rowptr[u + 1]; ++e) {
            uint32_t w = (uint32_t)colidx[e];
            if (level[w] < 0) {
                level[w] = lu1;
                queue[tail++] = (int32_t)w;
            }
        }
    }

    uint64_t lsum = 0;
    int32_t maxlv = 0;
    for (uint32_t v = 0; v < NVERT; ++v) {
        if (level[v] >= 0) {
            lsum += (uint64_t)((uint32_t)level[v] + 1u);
            if (level[v] > maxlv)
                maxlv = level[v];
        }
    }
    h = fold(h, lsum);
    h = fold(h, (uint64_t)tail);              /* reached vertex count */
    h = fold(h, (uint64_t)(uint32_t)maxlv);   /* eccentricity of src  */
    return h;
}

/* scatter-form PageRank: pr'[v] = (1-d)/N + d * sum_{u->v} pr[u]/deg(u).
 * The d*pr[u]/deg product is hoisted per source vertex and accumulated
 * into contrib[] through the CSR adjacency — double accumulation over
 * irregular indices.  Returns the final rank-vector hash and the L1
 * convergence residual (sum |pr' - pr| over the last iteration). */
static void pagerank(uint64_t *rank_hash_out, uint64_t *resid_bits_out)
{
    const double tele = (1.0 - DAMPING) / (double)NVERT;
    const double base_scale = DAMPING / (double)DEGREE;
    double *cur = pr_a, *nxt = pr_b;

    for (uint32_t v = 0; v < NVERT; ++v)
        cur[v] = 1.0 / (double)NVERT;

    for (uint32_t it = 0; it < PR_ITERS; ++it) {
        for (uint32_t v = 0; v < NVERT; ++v)
            contrib[v] = 0.0;
        for (uint32_t u = 0; u < NVERT; ++u) {
            double b = cur[u] * base_scale;
            for (int32_t e = rowptr[u]; e < rowptr[u + 1]; ++e)
                contrib[colidx[e]] += b;
        }
        for (uint32_t v = 0; v < NVERT; ++v)
            nxt[v] = tele + contrib[v];

        if (it + 1u == PR_ITERS) {
            double resid = 0.0;
            for (uint32_t v = 0; v < NVERT; ++v) {
                double d = nxt[v] - cur[v];
                resid += (d < 0.0) ? -d : d;
            }
            *resid_bits_out = bits_of(resid);
        }
        double *t = cur; cur = nxt; nxt = t;
    }

    uint64_t h = 0;
    for (uint32_t v = 0; v < NVERT; ++v)
        h = fold(h, bits_of(cur[v]));
    *rank_hash_out = h;
}

int main(void)
{
    /* ---- graph generation: fixed-seed LCG -> CSR ----
     * exact out-degree DEGREE per vertex (rowptr is the regular prefix
     * u*DEGREE), destinations uniform over [0, NVERT): self-loops and
     * duplicate edges are possible (harmless for BFS; PageRank treats
     * it as a multigraph) and fully deterministic. */
    for (uint32_t u = 0; u < NVERT; ++u)
        rowptr[u] = (int32_t)(u * DEGREE);
    rowptr[NVERT] = (int32_t)NEDGE;
    for (uint32_t e = 0; e < NEDGE; ++e)
        colidx[e] = (int32_t)((lcg_next() >> 33) & (NVERT - 1));

    /* ---- BFS: level-order traversal from fixed sources ---- */
    uint64_t bfs_hash = 0x243f6a8885a308d3ULL;
    for (uint32_t r = 0; r < BFS_RUNS; ++r) {
        uint32_t src = (r * 40993u + 12345u) & (NVERT - 1);
        bfs_hash = fold(bfs_hash, bfs_run(src));
    }

    /* ---- PageRank: fixed iterations, double accumulation ---- */
    uint64_t rank_hash = 0, resid_bits = 0;
    pagerank(&rank_hash, &resid_bits);

    uint64_t final = 0x0123456789abcdefULL;
    final = fold(final, bfs_hash);
    final = fold(final, rank_hash);
    final = fold(final, resid_bits);
    final = fold(final, ((uint64_t)NVERT << 32) | (uint64_t)NEDGE);
    final = fold(final, ((uint64_t)BFS_RUNS << 32) | (uint64_t)PR_ITERS);

    put("FINAL=");
    put_hex64(final);
    write(1, "\n", 1);
    return 0;
}
