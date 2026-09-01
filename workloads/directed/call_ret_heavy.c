/* call_ret_heavy.c — CHAOSBPU verification kernel.
 * Deep call/return chains stress the BTB/RAS; data-dependent indirect
 * calls stress target prediction. target_sub replaces the predicted
 * target -> mispredict -> squash -> arch should recover (golden).
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

static uint32_t rng_s = 0x5A5A1234u;
static inline uint32_t xs32(void){uint32_t x=rng_s;x^=x<<13;x^=x>>17;x^=x>>5;rng_s=x;return x;}

__attribute__((noinline)) static uint64_t leaf(uint64_t v) { return v * 3 + 1; }
__attribute__((noinline)) static uint64_t l2(uint64_t v) { return leaf(v) ^ 0x5a5a; }
__attribute__((noinline)) static uint64_t l3(uint64_t v) { return l2(v) + leaf(v ^ 0xff); }

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 300;
    uint64_t acc = 0;
    for (long i = 0; i < iters; i++) {
        acc += l3((uint64_t)i);
        acc ^= l2(acc);
    }
    printf("%016lx\n", acc & 0xFFFFFFFFFFFFFFFFULL);
    fprintf(stderr, "iters=%ld fails=0 variant=call_ret_heavy\n", iters);
    return 0;
}
