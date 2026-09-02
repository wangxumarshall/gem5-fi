/* gemm_float_kernel — §2.6 D: FP32 GEMM (high-density multi-bit, median 12).
 * Build: gcc -static -O2 -o gemm_float_kernel gemm_float_kernel.c -lm
 */
#include <stdio.h>
#include <stdint.h>
#include <math.h>
#define N 16
static uint64_t cs = 0xcbf29ce484222325ULL;
int main(void) {
    static float A[N*N], B[N*N], C[N*N];
    for (int i = 0; i < N*N; i++) { A[i] = (float)(i*7+1)/3.0f; B[i] = (float)(i*5+2)/7.0f; }
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) {
            float s = 0;
            for (int k = 0; k < N; k++) s += A[i*N+k] * B[k*N+j];
            C[i*N+j] = s;
        }
    for (int i = 0; i < N*N; i += 7) { uint64_t b; __builtin_memcpy(&b, &C[i], 4); cs ^= b; cs *= 0x100000001b3ULL; }
    printf("%016llx\n", cs);
    return 0;
}
