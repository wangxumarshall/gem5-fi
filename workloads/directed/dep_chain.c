/* S8-1 dep_chain: register dependency chain (producer -> consumer) for
 * IQ wake_omit/wake_phase verification. Each iteration: acc = acc + i,
 * v = acc + 1 (v depends on acc — a serial dependency chain). A missed
 * wakeup stalls the dependent; a deferred wakeup delays it by one cycle.
 * The checksum folds both, so any architectural divergence shows. */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 10000;
    register uint64_t acc __asm__("x9") = 0;
    register uint64_t v __asm__("x10") = 0;
    uint64_t golden = 0;
    for (long i = 0; i < iters; i++) {
        __asm__ volatile(
            "add %0, %0, %2\n"
            "add %1, %0, %3\n"     /* v depends on acc (chain) */
            : "+r"(acc), "+r"(v)
            : "r"((uint64_t)i), "r"((uint64_t)1)
            : /* no clobber */);
        golden += (uint64_t)i;
    }
    uint64_t acc_out = acc, v_out = v;
    uint64_t golden_v = golden + 1;   /* v = final-round acc + 1 */
    long fails = (acc_out != golden) || (v_out != golden_v) ? 1 : 0;
    printf("iters=%ld fails=%ld acc=%016lx v=%016lx golden=%016lx golden_v=%016lx\n",
           iters, fails, acc_out, v_out, golden, golden_v);
    return fails ? 1 : 0;
}
