/* cholesky_numeric.c — method1 (Cholesky x[0]) FI target kernel.

 * Reproduces the method1 field signature: a sparse-Cholesky-like numeric
 * factorization where a floating-point accumulator (d0) lives ACROSS a
 * data-dependent indirect-addressing sub-loop (factorize_preordered's
 * @1dc fmadd d0 -> indirect sub-loop -> @250 fmsub d0 -> @2c0 fsqrt d0 ->
 * @2c8 str d0). An F5/RAT-residue fault that swaps d0's mapping mid-loop
 * returns the value of ANOTHER live variable -> multi-bit aliasing (method1
 * popcount 21-32, NOT a single-bit SEU).
 *
 * Two variants selectable by argv:
 *   numeric-only   (default): just the factorization (method1's 1.0% rate).
 *   compute-both  (argv[2]="both"): recompute the chain twice and cross-check
 *                  (method1's 0.27% rate — the 4x lower rate under redundancy).
 *   The numeric/compute ratio is method1's state-leak signature (target ∈[2,8]).
 *
 * Output: prints "x0_checksum=<16-hex> fails=N iters=N" where fails counts
 * mismatches between the factorization and a golden recompute. libc-only,
 * no vectorization (scalar FMA chain to keep d0 long-lived in a reg).
 *
 * Compile: gcc -static -O2 -o cholesky_numeric cholesky_numeric.c
 *   (avoid -ffast-math; we want IEEE754 determinism for golden recompute)
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <string.h>

/* matrix dimension. method1 field threshold N>=256; gem5 O3 uses
 * smaller N (64) for verifiability — the residue mechanism is N-independent. */
static int Nn = 64;
#define NZ (N*8) /* sparse: ~8 nonzeros/row */
#define MAXN 256  /* static array cap; Nn<=MAXN */

/* xorshift32 RNG for deterministic test matrices. */
static uint32_t rng_s = 0x5A5A1234u;
static inline uint32_t xs32(void){uint32_t x=rng_s;x^=x<<13;x^=x>>17;x^=x>>5;rng_s=x;return x;}

/* A simple symmetric positive-definite sparse matrix (CSC-ish, per-row
 * index+value arrays). Built so the Cholesky factor L has a long-lived
 * diagonal accumulator d0 that spans an indirect-addressing sub-loop. */
static int    col_idx[MAXN][8];
static double col_val[MAXN][8];
static double diag[MAXN];      /* diagonal of L (the d0 chain) */
static double Lrow[MAXN][MAXN];   /* dense lower triangle (small N, kept for golden) */

static void build_matrix(void) {
    for (int i = 0; i < Nn; i++) {
        for (int k = 0; k < 8; k++) {
            int j = (i + k + 1) % Nn;
            if (j <= i) j = (j + i + 1) % Nn;
            col_idx[i][k] = j;
            col_val[i][k] = (double)(xs32() % 1000) / 1000.0 + 0.1;
        }
        /* make SPD-ish: strong diagonal */
        col_val[i][0] = (double)(i + 10);
    }
}

/* numeric Cholesky factorization (left-looking). d0 = L[i][i] is the
 * long-lived accumulator: fmadd across the j<k sub-loop, fmsub to update,
 * fsqrt for the diagonal, str to store. A residue fault on d0 mid-loop
 * returns another variable's value -> multi-bit x[0] aliasing. */
static void factorize(double L[MAXN][MAXN]) {
    for (int k = 0; k < Nn; k++) {
        /* d0 lives across the j-loop (the indirect-addressing sub-loop).
         * Plain C (-O2 keeps the accumulator in a register across the loop,
         * modeling method1's cross-loop-live d0 without hard-binding a reg). */
        double d0 = 0.0;
        for (int j = 0; j < k; j++) {
            double s = 0.0;
            for (int t = 0; t < 8 && col_idx[j][t] < j; t++) {
                int c = col_idx[j][t];
                s += L[k][c] * L[j][c];
            }
            d0 -= s * L[j][k];   /* fmsub: d0 = d0 - s*L[j][k] */
        }
        double akk = col_val[k][0];
        d0 = akk - d0;
        d0 = sqrt(d0);
        diag[k] = d0;
        L[k][k] = d0;
        /* column update: L[i][k] = (A[i][k] - sum) / L[k][k] for i>k */
        for (int i = k+1; i < Nn; i++) {
            double s = 0.0;
            for (int j = 0; j < 8 && col_idx[i][j] < k; j++) {
                int c = col_idx[i][j];
                if (c < k) s += L[i][c] * L[k][c];
            }
            double aik = (i < Nn && k < 8) ? col_val[i][k % 8] : 0.0;
            L[i][k] = (aik - s) / d0;   /* d0 consumed here — residue reads */
        }
    }
}

/* Solve L * x = b (forward substitution), return x[0] — method1's corrupted
 * element. x[0] = (b[0]) / L[0][0] (one hop through the d0 diagonal chain). */
static double solve_x0(double L[MAXN][MAXN], double b[MAXN]) {
    double x0 = b[0] / L[0][0];
    return x0;
}

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 10;
    if (argc > 3) Nn = atoi(argv[3]);
    if (Nn > 256) Nn = 256;  /* static arrays cap */
    int both = (argc > 2 && strcmp(argv[2], "both") == 0);
    build_matrix();

    long fails = 0;
    uint64_t x0_acc = 0;   /* accumulate x[0] across iters for a checksum */
    for (long it = 0; it < iters; it++) {
        rng_s = (uint32_t)(0x9e3779b9u * (it + 1));
        build_matrix();

        double b[MAXN];
        for (int i = 0; i < Nn; i++) b[i] = (double)(xs32() % 1000) / 100.0;

        /* golden: factorize into a SEPARATE matrix Lg, no residue */
        static double Lg[MAXN][MAXN];
        memset(Lg, 0, sizeof(Lg));
        factorize(Lg);
        double x0_gold = solve_x0(Lg, b);

        double x0_run;
        if (both) {
            /* compute-both: re-factorize and cross-check (method1's 0.27%
             * path — redundant recompute suppresses state-leak SDC 4x) */
            static double L2[MAXN][MAXN];
            memset(L2, 0, sizeof(L2));
            factorize(L2);
            double x0_2 = solve_x0(L2, b);
            x0_run = x0_2;
            if (x0_2 != x0_gold) fails++;   /* cross-check mismatch */
        } else {
            /* numeric-only: single factorization (method1's 1.0% path) */
            static double L1[MAXN][MAXN];
            memset(L1, 0, sizeof(L1));
            factorize(L1);
            x0_run = solve_x0(L1, b);
            if (x0_run != x0_gold) fails++;
        }
        /* fold x0 into a 16-hex-ish checksum (low bits) */
        uint64_t bits;
        memcpy(&bits, &x0_run, sizeof(bits));
        x0_acc ^= bits * (it + 1);
    }
    /* print a 16-hex checksum of x0_acc for classify.py, plus fail count */
    printf("%016lx\n", x0_acc & 0xFFFFFFFFFFFFFFFFULL);
    fprintf(stderr, "iters=%ld fails=%ld variant=%s\n",
            iters, fails, both ? "compute-both" : "numeric-only");
    return (fails > 0) ? 1 : 0;
}
