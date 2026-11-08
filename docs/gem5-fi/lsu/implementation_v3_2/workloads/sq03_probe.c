/* SQ03_Propagation_Probe (v3.2.9, exploratory; NOT one of the 60 samples).
 *
 * Each iteration stores a distinct 64-bit value to an address and then
 * loads the same address in program order, consuming the loaded value in
 * an accumulating checksum and a dependent branch.  The question the probe
 * answers: can an early SQ03 _canWB (writeback permission) make the store
 * data visible to the later load earlier than normal, or does the load
 * always forward from the SQ with identical data?
 *
 * volatile prevents the compiler from folding the load into a register.
 */
#include <stdint.h>
#include <stdio.h>

#define N 128
static volatile uint64_t buf[256];

int
main(void)
{
    uint64_t acc = 0x9e3779b97f4a7c15ULL;
    uint64_t path = 0;

    for (int i = 0; i < N; ++i) {
        uint64_t v = (uint64_t)i * 0x100000001b3ULL ^ 0x5a5a5a5a5a5a5a5aULL;
        uint64_t idx = (uint64_t)i & 255u;

        buf[idx] = v;                 /* store */
        uint64_t got = buf[idx];      /* same-address later load */
        acc ^= got + 0x9e3779b97f4a7c15ULL + (acc << 6) + (acc >> 2);
        if (got == v)
            path += 1;                /* dependent branch/consumer */
        else
            path += 0x1000;
    }

    uint64_t checksum = acc ^ (path * 0x9e3779b97f4a7c15ULL);
    printf("checksum=0x%016llx\n", (unsigned long long)checksum);
    return 0;
}
