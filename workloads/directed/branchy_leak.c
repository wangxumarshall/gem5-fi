/* branchy_leak.c — CHAOSROB spec_leak verification kernel.
 * Alternating unpredictable branches (data-dependent xorshift) force
 * frequent mispredicts -> squashes. spec_leak skips the squashed insts'
 * dest physReg freelist return -> later instructions read the leaked
 * wrong-path value -> checksum differs from golden.
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

static uint32_t rng_s = 0x5A5A1234u;
static inline uint32_t xs32(void){uint32_t x=rng_s;x^=x<<13;x^=x>>17;x^=x>>5;rng_s=x;return x;}

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 100;
    uint64_t acc = 0;
    for (long i = 0; i < iters; i++) {
        uint32_t r = xs32();
        /* data-dependent branch: unpredictable -> mispredicts -> squashes */
        if (r & 0x80000000u) {
            acc += r * 3;
        } else {
            acc ^= r;
        }
        /* dest physReg live across the branch (spec_leak target) */
        uint64_t t = acc + (uint64_t)(i + 1);
        acc = t ^ (r >> 3);
    }
    printf("%016lx\n", acc & 0xFFFFFFFFFFFFFFFFULL);
    fprintf(stderr, "iters=%ld fails=0 variant=branchy_leak\n", iters);
    return 0;
}
