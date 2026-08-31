/* branchy_reduce — §2.3 D kernel: high branch density + dependency chain.
 *
 * Designed to create speculative-path squash traffic (conditional branches that
 * mispredict) so CHAOSROB's spec_leak / entry_bitflip on squash-relevant
 * entries has a measurable chance to affect the final 16-hex checksum.
 * Builds a reduction over a seeded array with a data-dependent branch in the
 * inner loop (mispredict-prone), plus a dependency chain across iterations.
 *
 * Build: gcc -static -O2 -o branchy_reduce branchy_reduce.c
 */
#include <stdio.h>

#define N 8192

static unsigned long lcg = 0xdeadbeefcafebabeUL;
static unsigned long nx(void){ lcg = lcg*6364136223846793005UL + 1442695040888963407UL; return lcg>>32; }

int main(void) {
    static long a[N], b[N];
    for (int i = 0; i < N; i++) { a[i] = (long)(nx()%64) - 32; b[i] = 0; }
    long acc = 0;
    /* data-dependent branch (mispredict-prone) + dependency chain on acc */
    for (int i = 0; i < N; i++) {
        long x = a[i];
        if (x & 1) {            /* unpredictable conditional branch */
            b[i] = x + acc;     /* dependency chain across iter (acc) */
            acc = b[i] * 3;
        } else {
            b[i] = x - acc;
            acc = b[i] * 5;
        }
        acc ^= (x << 1);
    }
    unsigned long long cs = 0xcbf29ce484222325ULL;
    unsigned long long bits;
    bits = (unsigned long long)acc; cs ^= bits; cs *= 0x100000001b3ULL;
    for (int i = 0; i < N; i += 128) { bits = (unsigned long long)b[i]; cs ^= bits; cs *= 0x100000001b3ULL; }
    printf("%016llx\n", cs);
    return 0;
}
