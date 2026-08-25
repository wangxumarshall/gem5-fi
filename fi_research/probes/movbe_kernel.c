/* Minimal AArch64 SDC probe kernel mirroring reproduce-method2's movbe hot loop:
 * store immediately followed by reload of just-read input (store->load forwarding path).
 * Self-checks; exits 0 on pass, 1 on SDC detection. Pure libc, no main() deps. */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

#define N 16384  /* 64KB / 4 = 16384 words, cross-line footprint like movbe */

static uint32_t rng_state = 0x12345678u;
static inline uint32_t xorshift32(void) {
    uint32_t x = rng_state;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    rng_state = x; return x;
}

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 1000;
    uint32_t *input  = (uint32_t*)malloc(N * sizeof(uint32_t));
    uint32_t *swapped = (uint32_t*)malloc(N * sizeof(uint32_t));
    if (!input || !swapped) return 2;
    /* init once */
    for (int i = 0; i < N; i++) input[i] = xorshift32();

    long fails = 0;
    for (long it = 0; it < iters; it++) {
        /* re-seed input occasionally to vary pattern (SDC is data-sensitive) */
        if ((it & 63) == 0) { rng_state = (uint32_t)(0x9E3779B9u * (it+1)); for (int i=0;i<N;i++) input[i]=xorshift32(); }
        for (int i = 0; i < N; i++) {
            uint32_t v1 = input[i];                 /* 1st read */
            uint32_t bs = __builtin_bswap32(v1);    /* byte-swap (rev) — never feeds compare */
            swapped[i] = bs;                        /* store to DIFFERENT line */
            uint32_t v2 = __builtin_bswap32(bs);    /* folds to RELOAD of input[i] */
            if (v2 != v1) {                        /* catches reload != 1st read */
                fails++;
                if (fails <= 8) fprintf(stderr, "SDC@it=%ld i=%d golden=%08x actual=%08x xor=%08x\n",
                                        it, i, v1, v2, v1^v2);
            }
        }
    }
    free(input); free(swapped);
    printf("iters=%ld fails=%ld\n", iters, fails);
    return fails ? 1 : 0;
}
