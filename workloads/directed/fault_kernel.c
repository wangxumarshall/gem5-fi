/* fault_kernel.c — CHAOSROB exc_suppress verification kernel.
 *
 * Produces a REPRODUCIBLE architectural fault (data abort via a deliberate
 * unmapped-address load). In gem5 SE, address 0 is unmapped -> the load
 * faults (Data Abort), the fault propagates to the DynInst, and commit
 * traps -> Crash (DUE). With CHAOSROB exc_suppress, the faulting DynInst's
 * `fault` is cleared before commit -> no trap -> the load returns whatever
 * garbage was in memData -> SDC.
 *
 * Native safety: argv[2] may pass a SAFE address (malloc'd) so native runs
 * don't segfault. In gem5, use the default fault addr 0 (unmapped in SE).
 *
 * Output: 16-hex checksum (stdout) + iters/fails (stderr).
 *   fails=0 with no fault (safe addr) = golden; exc_suppress on a faulting
 *   load changes the checksum -> SDC.
 *
 * Compile: gcc -static -O2 -o fault_kernel fault_kernel.c
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 100;
    /* fault_addr: 0 (unmapped in gem5 SE -> Data Abort) by default.
     * Pass a hex arg as argv[2] to use a safe (malloc'd) address for native. */
    void *fault_addr = (void *)0;  /* unmapped in gem5 SE */
    if (argc > 2 && argv[2][0] != '0') {
        /* safe mode: use a malloc'd address (native golden) */
        fault_addr = malloc(64);
        if (!fault_addr) return 2;
        memset(fault_addr, 0x5a, 64);
    }

    uint64_t acc = 0x1234567890abcdefULL;
    uint64_t fails = 0;
    for (long it = 0; it < iters; it++) {
        acc += (uint64_t)(it + 1) * 0x9e3779b9u;
        /* The faulting load: in gem5 SE (fault_addr=0), this Data-Aborts.
         * guarded by 'volatile' so it isn't optimized away. */
        volatile uint64_t *p = (volatile uint64_t *)fault_addr;
        uint64_t v = *p;   /* traps in gem5 unless exc_suppress clears it */
        acc += v;          /* if exc_suppress -> v is garbage -> checksum changes */
    }
    uint64_t checksum = acc ^ 0xCAFEBABEDEADBEEFULL;
    printf("%016lx\n", checksum & 0xFFFFFFFFFFFFFFFFULL);
    fprintf(stderr, "iters=%ld fails=%ld variant=fault_kernel\n", iters, fails);
    return 0;
}
