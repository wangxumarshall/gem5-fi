/* sparse_cg_kernel.c — real sparse linear-system solver (conjugate gradient).
 *
 * Author : gem5-fi project contributors (2026).
 * License: original code authored for this repository; distributed under
 *          the same terms as the rest of gem5-fi (see CLAUDE.md).
 *
 * W6 artifact contract (NOT an SpMV proxy)
 *   * fixed SPD sparse system: 16x16 five-point Laplacian,
 *     A = 4*I - (north+south+east+west), N = 16*16 = 256.
 *   * fixed right-hand side b = A * x_true with
 *     x_true[i] = 1 + ((i*7+3) % 11) / 11, so the exact solution is known.
 *   * actual conjugate-gradient solve from x0 = 0 with a fixed maximum
 *     iteration count (400) and deterministic FP operations. No rand().
 *   * live-out array: the solution vector x (fp32, row-major, count 256).
 *   * prints "RESIDUAL=<relative residual>" and
 *     "FINAL=<16hex>" = FNV-1a 64 over the raw fp32 bytes of x.
 *   * optional raw little-endian dump of x via --array-dump=<path> (or
 *     POLYBENCH_ARRAY_DUMP); no-op otherwise. FINAL is unchanged.
 *
 * Build (reproducible):
 *   gcc -O2 -static -Wall -Wextra -I ../ooo/polybench/utilities \
 *       -o sparse_cg_kernel sparse_cg_kernel.c -lm
 */
#include <stdio.h>
#include <stdint.h>
#include <math.h>
#include <gem5fi_oracle.h>

#define GRID 16
#define CG_N (GRID * GRID)
#define CG_MAXIT 400
#define CG_TOL 1.0e-7f

static float x[CG_N];
static float b[CG_N];
static float r[CG_N];
static float p[CG_N];
static float ap[CG_N];

/* y = A*x for the fixed five-point Laplacian (SPD). */
static void matvec(const float *v, float *y)
{
    int i, j;
    for (i = 0; i < GRID; i++) {
        for (j = 0; j < GRID; j++) {
            int idx = i * GRID + j;
            float s = 4.0f * v[idx];
            if (i > 0)        s -= v[idx - GRID];
            if (i < GRID - 1) s -= v[idx + GRID];
            if (j > 0)        s -= v[idx - 1];
            if (j < GRID - 1) s -= v[idx + 1];
            y[idx] = s;
        }
    }
}

static float dot(const float *a, const float *c)
{
    float s = 0.0f;
    int i;
    for (i = 0; i < CG_N; i++)
        s += a[i] * c[i];
    return s;
}

int main(int argc, char **argv)
{
    float rsold, rsnew, residual = 0.0f;
    int i, k;

    /* Fixed SPD system: b = A * x_true. */
    {
        int gi, gj;
        for (gi = 0; gi < GRID; gi++)
            for (gj = 0; gj < GRID; gj++) {
                int idx = gi * GRID + gj;
                x[idx] = 1.0f + (float)((idx * 7 + 3) % 11) / 11.0f;
            }
        matvec(x, b);
    }

    /* Conjugate gradient from x0 = 0. */
    for (i = 0; i < CG_N; i++) {
        x[i] = 0.0f;
        r[i] = b[i];
        p[i] = r[i];
    }
    rsold = dot(r, r);
    for (k = 0; k < CG_MAXIT; k++) {
        float alpha, beta;
        float denom;
        matvec(p, ap);
        denom = dot(p, ap);
        if (!(denom > 0.0f))  /* SPD guarantees > 0; refuse to divide by 0 */
            break;
        alpha = rsold / denom;
        for (i = 0; i < CG_N; i++) {
            x[i] += alpha * p[i];
            r[i] -= alpha * ap[i];
        }
        rsnew = dot(r, r);
        residual = sqrtf(rsnew);
        if (residual <= CG_TOL)
            break;
        beta = rsnew / rsold;
        for (i = 0; i < CG_N; i++)
            p[i] = r[i] + beta * p[i];
        rsold = rsnew;
    }

    {
        float bnorm = sqrtf(dot(b, b));
        double rel = bnorm > 0.0f ? (double)(residual / bnorm) : 0.0;
        printf("RESIDUAL=%.9e\n", rel);
    }

    {
        const unsigned char *q = (const unsigned char *)x;
        uint64_t h = 0xcbf29ce484222325ULL;
        unsigned long fi;
        for (fi = 0; fi < sizeof(float) * (unsigned long)CG_N; fi++) {
            h ^= q[fi];
            h *= 0x100000001b3ULL;
        }
        printf("FINAL=%016llx\n", (unsigned long long)h);
    }

    gem5fi_oracle_dump_from_argv(argc, argv, x,
                                 (unsigned long)CG_N, sizeof(float));
    return 0;
}
