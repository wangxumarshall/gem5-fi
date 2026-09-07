/* fma_reduction_kernel — §5.6D Task 2.2: FMA 归约放大系数 kernel.
 *
 * A chained fused multiply-add reduction over a deterministic array:
 * acc = fma(a[i], b[i], acc) repeated — measures how a single-bit fault
 * in the FMA pipeline amplifies through the reduction chain (each
 * subsequent fma propagates AND scales the error by the operand
 * magnitude — the amplification-factor anchor for §5.6D).
 *
 * Scalar chain: built with -fno-tree-vectorize so the reduction stays in
 * scalar FMADD (NEON-vectorized would move it to VecRegClass lanes and
 * change the FSU spectrum).
 * Build: gcc -static -O2 -fno-tree-vectorize -o fma_reduction_kernel fma_reduction_kernel.c -lm
 */
#include <stdio.h>
#include <stdint.h>
#include <math.h>
#define N 4096
static uint64_t cs = 0xcbf29ce484222325ULL;
int main(void) {
    static double a[N], b[N];
    /* deterministic exact-representable operands (integers < 2^20):
       products up to 2^40 and partial sums up to ~2^53 stay exact in
       double, so a SINGLE corrupted bit anywhere in the chain shifts the
       final sum by an exactly-measurable power of two (amplification =
       observable, not absorbed by rounding) */
    for (int i = 0; i < N; i++) { a[i] = (double)((i*7+1) & 0xFFFFF); b[i] = (double)((i*5+3) & 0xFFFFF); }
    double acc = 0.0;
    for (int i = 0; i < N; i++)
        acc = fma(a[i], b[i], acc);
    uint64_t bits; __builtin_memcpy(&bits, &acc, 8);
    cs ^= bits ^ (bits >> 32); cs *= 0x100000001b3ULL;
    printf("%016llx\n", cs);
    return 0;
}
