/* mov_heavy — method1 move-elimination kernel (design doc §2.2 D, §2.2 C
 * grid "move elimination" cell).
 *
 * A workload dominated by MOV Xd,Xn (register-to-register copies) that the
 * O3 rename engine may move-eliminate (map Xd's entry to Xn's physReg without
 * a PRF write). A CHAOSRenameMap fault on the map entry of a MOV-eliminated
 * pair propagates to BOTH the source and dest arch reg reads (the method1
 * move-elimination injection cell).
 *
 * Builds a checksum chain via many MOVs (X = X; acc = acc + stride*X; repeat)
 * so a faulted map entry in the MOV chain has a measurable chance to affect
 * the final 16-hex checksum.
 *
 * Build: gcc -static -O2 -o mov_heavy mov_heavy.c
 */
#include <stdio.h>

#define N 4096

int main(void) {
    /* Use volatile to keep the compiler from DCE'ing the MOVs (we WANT the
     * move/elimination path exercised, not optimized away). */
    volatile long acc = 0;
    long a[N], b[N];
    for (int i = 0; i < N; i++) { a[i] = (long)(i + 1); b[i] = 0; }
    /* MOV-heavy loop: copy a[i]->b[i] (MOV Xd,Xn) then fold into acc. */
    for (int i = 0; i < N; i++) {
        long t = a[i];      /* load source */
        b[i] = t;            /* MOV copy (dest <- src) */
        long t2 = b[i];      /* re-read dest (forces the mov to be visible) */
        acc += t2;           /* fold */
    }
    /* FNV-1a-ish 16-hex checksum of acc + b (sensitive to any propagated
     * bit error in the MOV chain). */
    unsigned long long cs = 0xcbf29ce484222325ULL;
    unsigned long long bits;
    bits = (unsigned long long)acc;
    cs ^= bits; cs *= 0x100000001b3ULL;
    for (int i = 0; i < N; i += 64) {
        bits = (unsigned long long)b[i];
        cs ^= bits; cs *= 0x100000001b3ULL;
    }
    printf("%016llx\n", cs);
    return 0;
}
