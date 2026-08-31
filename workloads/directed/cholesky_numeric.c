/* cholesky_numeric — method1 anchor kernel (design doc §2.2 D).
 *
 * Cholesky decomposition of a small SPD matrix, NUMERIC phase only:
 *   - cdiv:  1/sqrt(pivot) + division, with a CONDITIONAL branch on pivot sign
 *            (the cdiv branch that method1 cdiv is named for).
 *   - rank-1 update: FMA loop over the trailing submatrix (j,k inner).
 *   - long-lived accumulator: the running sum across the inner j-loop lives
 *            in a register across many FMAs (the "跨内层循环长存活累加器"
 *            that method1's history-residue corrupts).
 *   - indirect indexing: matrix accessed via computed indices (A[i*N+k]).
 *   - malloc/free workspace per column (method1's "每次 malloc/free 工作区").
 *
 * Designed so a fault in the rename map (map_bitflip / f5_substitute pointing
 * an arch reg at the WRONG physReg) has a measurable chance to propagate to
 * the final 16-hex checksum — the method1 "其它计算数据覆盖 x[0]" signature.
 *
 * Deterministic (fixed seed matrix). Golden 16-hex checksum on stdout.
 * Build: gcc -static -O2 -o cholesky_numeric cholesky_numeric.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define N 16

/* tiny deterministic LCG (no libc rand state dependence) */
static unsigned long lcg_state = 0x12345678UL;
static unsigned long lcg_next(void) {
    lcg_state = lcg_state * 6364136223846793005UL + 1442695040888963407UL;
    return lcg_state >> 32;
}

/* build a symmetric positive-definite matrix: A = B*B^T + N*I */
static void build_spd(double A[N][N]) {
    double B[N][N];
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            B[i][j] = (double)((lcg_next() % 7) - 3) / 3.0;  /* [-1,1) */
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            double s = 0.0;
            for (int k = 0; k < N; k++) s += B[i][k] * B[j][k];
            A[i][j] = s + ((i == j) ? (double)N : 0.0);  /* SPD */
        }
    }
}

/* in-place Cholesky (right-looking, numeric phase). Returns a 64-bit
 * checksum of the resulting lower-triangular L. */
static unsigned long long cholesky(double A[N][N]) {
    for (int k = 0; k < N; k++) {
        /* cdiv: pivot step. Conditional branch on pivot validity
         * (method1 cdiv branch). */
        double pivot = A[k][k];
        if (pivot <= 0.0) {  /* cdiv conditional branch */
            /* degenerate pivot — fall back (shouldn't happen for SPD, but
             * the branch is the point: a faulted reg here changes control) */
            pivot = 1.0;
        }
        double inv_sqrt = 1.0 / sqrt(pivot);
        A[k][k] = inv_sqrt;  /* store 1/sqrt(L[k][k]) */

        /* workspace alloc/free per column (method1 malloc/free workspace) */
        double *col = (double *)malloc(sizeof(double) * (N - k - 1));
        for (int i = k + 1; i < N; i++)
            col[i - k - 1] = A[i][k] * inv_sqrt;

        /* rank-1 update of trailing submatrix — LONG-LIVED accumulator
         * across the j loop (method1's cross-inner-loop accumulator). */
        for (int i = k + 1; i < N; i++) {
            double Aik = col[i - k - 1];  /* indirect: via workspace */
            for (int j = k + 1; j < N; j++) {
                /* FMA into A[i][j]; the accumulator Aij lives across j */
                double Aij = A[i][j];
                Aij -= Aik * A[j][k];     /* rank-1 update FMA */
                A[i][j] = Aij;
            }
            A[i][k] = Aik;  /* store scaled column entry */
        }
        free(col);
    }
    /* checksum: fold L into a 64-bit hash (deterministic, sensitive to any
     * bit change in the result — method1 multi-bit aliasing detectable). */
    unsigned long long cs = 0xcbf29ce484222325ULL;  /* FNV-1a basis */
    for (int i = 0; i < N; i++)
        for (int j = 0; j <= i; j++) {
            unsigned long long bits;
            double v = A[i][j];
            /* bitwise fold of the double's IEEE754 bits (sign/exp/mantissa) */
            __builtin_memcpy(&bits, &v, sizeof(bits));
            cs ^= bits;
            cs *= 0x100000001b3ULL;
        }
    return cs;
}

int main(void) {
    double A[N][N];
    build_spd(A);
    unsigned long long cs = cholesky(A);
    printf("%016llx\n", cs);
    return 0;
}
