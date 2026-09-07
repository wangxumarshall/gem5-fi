/* gemm_double_kernel — §5.6D Task 2.1: FP64 GEMM (method3 anchor target:
 * single-bit flip in the double accumulate path, popcount median 28
 * comparable). Scalar chain: built with -fno-tree-vectorize so the
 * accumulate stays in scalar FADD/FMUL (a NEON-vectorized build would put
 * the chain in VecRegClass and the FSU single-bit spectrum would change).
 * Build: gcc -static -O2 -fno-tree-vectorize -o gemm_double_kernel gemm_double_kernel.c -lm
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#define N 32
static uint64_t cs = 0xcbf29ce484222325ULL;
int main(void) {
    static int32_t A[N*N], B[N*N];
    static double C[N*N];
    /* deterministic integer operands -> exact double representations
       (no host-vs-gem5 rounding ambiguity) */
    static uint32_t st = 0xC0FFEE11u;
    for (int i=0;i<N*N;i++){ st^=st<<13; st^=st>>17; st^=st<<5; A[i]=(int32_t)(st%2001)-1000;
                             st^=st<<13; st^=st>>17; st^=st<<5; B[i]=(int32_t)(st%2001)-1000; }
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) {
            double s = 0;
            for (int k = 0; k < N; k++) s += (double)A[i*N+k] * (double)B[k*N+j];
            C[i*N+j] = s;
        }
    /* fold the bit patterns (any flip in any accumulator lane lands in the
       fold with high probability) */
    for (int i = 0; i < N*N; i += 7) {
        uint64_t b; __builtin_memcpy(&b, &C[i], 8);
        cs ^= b ^ (b>>32); cs *= 0x100000001b3ULL;
    }
    printf("%016llx\n", cs);
    return 0;
}
