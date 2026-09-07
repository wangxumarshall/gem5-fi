/* smulh_adds_kernel — §5.10D Task 2.3: integer negative-control kernel.
 *
 * Two integer-only instruction-form anchors (inline asm so the exact A64
 * forms are guaranteed, not compiler-choice):
 *   1. SMULH  — signed multiply-high (x_h = (x*y)>>64): the HIGH 64 bits
 *      of a 128-bit product, chained through a data register.
 *   2. ADDS→B.cond — an add that SETS the flags (NZCV) followed by a
 *      conditional branch on the result: a fault in the flag computation
 *      (or in the add) diverts the control flow -> checksum divergence.
 *
 * Integer path intact (method1's negative control): P_SDC(Int) should be
 * << P_SDC(FSU/forwarding) per §5.10's quantified contrast.
 * Build: gcc -static -O2 -o smulh_adds_kernel smulh_adds_kernel.c
 */
#include <stdio.h>
#include <stdint.h>
static uint64_t cs = 0xcbf29ce484222325ULL;
int main(void) {
    uint64_t acc = 0x0123456789abcdefULL;
    int64_t h = 0x1234567890abcdefLL;
    uint64_t path = 0;
    for (int i = 0; i < 10000; i++) {
        /* SMULH chained in a register pinned via inline asm */
        __asm__ volatile(
            "smulh %[h], %[h], %[m]\n"
            : [h]"+r"(h)
            : [m]"r"((int64_t)(i | 1))
        );
        /* ADDS sets flags; B.cond picks one of two accumulation paths —
           a corrupted flag (or add result) diverts the path */
        uint64_t v = (uint64_t)h + (uint64_t)i;
        __asm__ volatile(
            "adds %[v], %[v], %[c]\n"
            "b.vs 1f\n"
            "mov %[p], #0\n"
            "b 2f\n"
            "1: mov %[p], #1\n"
            "2:\n"
            : [v]"+r"(v), [p]"=r"(path)
            : [c]"r"((uint64_t)0x7ffffffffffffff0ULL)
            : "cc"
        );
        acc = acc * 31 + v + (path ? 0x9e3779b97f4a7c15ULL : 1ULL);
    }
    cs ^= acc ^ (uint64_t)h; cs *= 0x100000001b3ULL;
    printf("%016llx\n", cs);
    return 0;
}
