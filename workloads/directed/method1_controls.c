/* method1 control kernels — design doc §2.2 D, the 4 controls that
 * individually do NOT trigger method1 (the "负反馈复现" P_SDC ratio ≈4×).
 *
 * These are SEPARATE small programs selected by argv[1]:
 *   pure_fma   : pure scalar FMA loop (no cdiv branch, no indirect, no
 *                long-lived cross-loop accumulator, no malloc/free).
 *   pure_spmv  : sparse-matrix-vector multiply (indirect indexing but
 *                no cdiv / no cross-loop accumulator).
 *   pure_gather: gather/scatter pattern (indirect, no cdiv).
 *   tri_solve  : triangular solve (has division + indirect but no rank-1
 *                FMA cross-loop accumulator, no malloc/free per column).
 *
 * Each prints a 16-hex checksum. Under a CHAOSRenameMap/CHAOSFreeList single
 * fault, method1 predicts these controls each have a LOWER SDC rate than
 * cholesky_numeric's numeric phase (the ≈4× ratio). The campaign compares.
 *
 * Build: gcc -static -O2 -o method1_controls method1_controls.c -lm
 * Run:   method1_controls <pure_fma|pure_spmv|pure_gather|tri_solve>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define N 16

static unsigned long lcg_state = 0x9e3779b97f4a7c15UL;
static unsigned long lcg_next(void) {
    lcg_state = lcg_state * 6364136223846793005UL + 1442695040888963407UL;
    return lcg_state >> 32;
}

static unsigned long long fold(const double *v, int n) {
    unsigned long long cs = 0xcbf29ce484222325ULL;
    for (int i = 0; i < n; i++) {
        unsigned long long bits;
        __builtin_memcpy(&bits, &v[i], sizeof(bits));
        cs ^= bits; cs *= 0x100000001b3ULL;
    }
    return cs;
}

/* pure_fma: scalar FMA chain, NO cdiv branch, NO indirect, NO cross-loop
 * accumulator (each A[i] independent). */
static unsigned long long pure_fma(void) {
    static double A[N], B[N], C[N];
    for (int i = 0; i < N; i++) { A[i] = (double)(lcg_next()%7)/3.0; B[i] = (double)(lcg_next()%7)/3.0; }
    for (int iter = 0; iter < 100; iter++)
        for (int i = 0; i < N; i++)
            C[i] = A[i] * B[i] + C[i];   /* pure FMA, per-i independent */
    return fold(C, N);
}

/* pure_spmv: CSR sparse matrix-vector multiply — indirect indexing but
 * NO cdiv, NO cross-loop accumulator. */
static unsigned long long pure_spmv(void) {
    static double val[4*N], x[N], y[N];
    static int col[4*N], rowptr[N+1];
    int nz = 0; rowptr[0] = 0;
    for (int i = 0; i < N; i++) {
        x[i] = (double)(lcg_next()%7)/3.0; y[i] = 0.0;
        int deg = 1 + (int)(lcg_next()%4);
        for (int k = 0; k < deg && nz < 4*N; k++, nz++) {
            val[nz] = (double)(lcg_next()%7)/3.0;
            col[nz] = (int)(lcg_next()%N);   /* indirect index */
        }
        rowptr[i+1] = nz;
    }
    for (int i = 0; i < N; i++)
        for (int k = rowptr[i]; k < rowptr[i+1]; k++)
            y[i] += val[k] * x[col[k]];   /* spmv FMA, indirect */
    return fold(y, N);
}

/* pure_gather: gather pattern — indirect reads, NO cdiv, NO FMA accumulator. */
static unsigned long long pure_gather(void) {
    static double base[N], idx[N], out[N];
    for (int i = 0; i < N; i++) { base[i] = (double)(lcg_next()%7); idx[i] = (double)(lcg_next()%N); }
    for (int i = 0; i < N; i++)
        out[i] = base[(int)idx[i]];   /* pure gather, no FMA */
    return fold(out, N);
}

/* tri_solve: lower-triangular solve Lx=b — division + indirect but
 * NO rank-1 FMA cross-loop accumulator, NO malloc/free per column. */
static unsigned long long tri_solve(void) {
    static double L[N][N], b[N], x[N];
    for (int i = 0; i < N; i++) {
        b[i] = (double)(lcg_next()%7)/3.0;
        for (int j = 0; j <= i; j++) L[i][j] = (double)(lcg_next()%7)/3.0 + ((i==j)?(double)N:0.0);
    }
    for (int i = 0; i < N; i++) {
        double s = b[i];
        for (int j = 0; j < i; j++) s -= L[i][j] * x[j];  /* no cross-loop acc */
        x[i] = s / L[i][i];   /* division (no sqrt cdiv) */
    }
    return fold(x, N);
}

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: %s <pure_fma|pure_spmv|pure_gather|tri_solve>\n", argv[0]); return 1; }
    unsigned long long cs;
    if (!strcmp(argv[1], "pure_fma")) cs = pure_fma();
    else if (!strcmp(argv[1], "pure_spmv")) cs = pure_spmv();
    else if (!strcmp(argv[1], "pure_gather")) cs = pure_gather();
    else if (!strcmp(argv[1], "tri_solve")) cs = tri_solve();
    else { fprintf(stderr, "unknown kernel: %s\n", argv[1]); return 1; }
    printf("%016llx\n", cs);
    return 0;
}
