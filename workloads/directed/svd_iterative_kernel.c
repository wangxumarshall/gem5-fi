/* svd_iterative_kernel — §2.6 D: iterative SVD (Jacobi, single-bit dominant).
 * Build: gcc -static -O2 -o svd_iterative_kernel svd_iterative_kernel.c -lm
 */
#include <stdio.h>
#include <stdint.h>
#include <math.h>
#define N 8
static uint64_t cs = 0xcbf29ce484222325ULL;
int main(void) {
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
    printf("%016llx\n", cs);
    return 0;
}
