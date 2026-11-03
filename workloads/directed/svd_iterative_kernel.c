/* svd_iterative_kernel — §2.6 D: iterative SVD (Jacobi, single-bit dominant).
 * Build: gcc -static -O2 -I ../ooo/polybench/utilities \
 *            -o svd_iterative_kernel svd_iterative_kernel.c -lm
 *
 * gem5-fi W6: the 16-hex FNV-1a line over the diagonal (eigenvalue)
 * doubles and the program's stdout are byte-for-byte unchanged. An optional
 * raw little-endian dump of the full fixed 8x8 live-out matrix is appended
 * for the element oracle; it is a no-op unless --array-dump=<path> (or the
 * POLYBENCH_ARRAY_DUMP environment variable) is given.
 */
#include <stdio.h>
#include <stdint.h>
#include <math.h>
#include <gem5fi_oracle.h>
#define N 8
static uint64_t cs = 0xcbf29ce484222325ULL;
int main(int argc, char **argv) {
    static double A[N*N];
    for (int i = 0; i < N*N; i++) A[i] = (double)(i*3+1)/2.0;
    for (int sweep = 0; sweep < 10; sweep++)
        for (int p = 0; p < N; p++)
            for (int q = p+1; q < N; q++) {
                double app = A[p*N+p], aqq = A[q*N+q], apq = A[p*N+q];
                double theta = (aqq - app) / (2.0 * fabs(apq));
                double t = copysign(1.0, theta) / (fabs(theta) + sqrt(theta*theta + 1.0));
                double c = 1.0/sqrt(t*t+1.0), s = t*c;
                for (int i = 0; i < N; i++) {
                    double aip = A[i*N+p], aiq = A[i*N+q];
                    A[i*N+p] = c*aip - s*aiq;
                    A[i*N+q] = s*aip + c*aiq;
                }
            }
    for (int i = 0; i < N; i++) { uint64_t b; __builtin_memcpy(&b, &A[i*N+i], 8); cs ^= b; cs *= 0x100000001b3ULL; }
    printf("%016llx\n", (unsigned long long)cs);

    /* gem5-fi W6: fixed full-matrix dump (row-major fp64, count N*N). */
    gem5fi_oracle_dump_from_argv(argc, argv, A,
                                 (unsigned long)N * (unsigned long)N, 8);
    return 0;
}
