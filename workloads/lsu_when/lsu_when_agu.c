/* lsu_when_agu.c — A01/A03 When-v2 contexts (Sheet 15, W1).
 *
 * The target hook is the original AGU/PRE effective-address site; each
 * context keeps the same 8-byte GPR load stream but changes only the
 * activation/consumption conditions:
 *   C01 baseline load -> checksum
 *   C02 alternate legal addressing forms (base+index / displacement)
 *   C03 load value overwritten before any real consumer
 *   C04 loaded value feeds the next address (pointer-style chain)
 *   C05 branch-speculated loads (both directions carry 8-byte loads)
 *
 * Nothing here defines a fault; the injector owns that semantics.
 */
#include "when_common.h"

#define N 192

static volatile uint64_t a[N] __attribute__((aligned(4096)));
static volatile uint64_t b[N] __attribute__((aligned(4096)));
static volatile uint32_t cold[4096] __attribute__((aligned(4096)));

int
main(void)
{
    uint64_t s = 0x42ee1ce4d4e55eedULL ^ (uint64_t)CONTEXT;
    unsigned i;

    for (i = 0; i < N; i++) {
        a[i] = 0x1000ULL + (uint64_t)i * 0x0123456789abcdefULL;
        b[i] = 0x9000ULL + (uint64_t)i * 0xfedcba9876543210ULL;
    }
    for (i = 0; i < 4096; i++)
        cold[i] = (uint32_t)(when_hash64((uint64_t)i) ^ 0xa5a5a5a5u);

#if CONTEXT == 1
    /* C01: baseline activation: load -> direct checksum consumer. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        s = when_fnv(s, v);
    }
#elif CONTEXT == 2
    /* C02: legal activation variation: register-index and displacement
     * forms, all 8-byte GPR loads from the same object. */
    for (i = 0; i < N; i++) {
        unsigned j = (i * 7u) & (N - 1u);
        uint64_t v = *(volatile uint64_t *)((const volatile char *)a
                                            + (uint64_t)j * 8u);
        s = when_fnv(s, v);
        j = (i * 13u + 5u) & (N - 1u);
        uint64_t w = b[j];
        s = when_fnv(s, w);
    }
#elif CONTEXT == 3
    /* C03: weak consumption: the load still executes, but the value is
     * overwritten before any checksum/address use. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        __asm__ volatile("" : "+r"(v) : : "memory");
        v = 0x5a5a5a5a5a5a5a5aULL;
        s = when_fnv(s, v);
    }
#elif CONTEXT == 4
    /* C04: enhanced data dependency: loaded value indexes a second load,
     * which is then consumed. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        unsigned j = (unsigned)((v >> 3) & (N - 1u));
        uint64_t w = b[j];
        s = when_fnv(s, w);
    }
#else
    /* C05: control/speculation: a slow cold load drives an unpredictable
     * branch; each direction contains several 8-byte loads. */
    for (i = 0; i < N; i++) {
        uint32_t c = cold[(i * 37u) & 4095u];
        __asm__ volatile("" ::: "memory");
        if (c & 1u) {
            uint64_t v0 = a[i], v1 = a[(i + 1u) & (N - 1u)];
            uint64_t v2 = a[(i + 2u) & (N - 1u)];
            s = when_fnv(s, v0 ^ v1 ^ v2);
        } else {
            uint64_t v0 = b[i], v1 = b[(i + 3u) & (N - 1u)];
            uint64_t v2 = b[(i + 4u) & (N - 1u)];
            s = when_fnv(s, v0 ^ v1 ^ v2);
        }
    }
#endif

    when_put_hex(s);
    return 0;
}
