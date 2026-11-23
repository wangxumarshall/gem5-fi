/* lsu_when_lq.c — LQ04 When-v2 contexts (Sheet 15, W2).
 *
 * The hook site is the LQ entry lifetime.  All contexts issue real data
 * loads; only the pressure, consumption and speculation conditions change.
 */
#include "when_common.h"

#define N 192
#define COLD 32768

static volatile uint64_t a[N] __attribute__((aligned(4096)));
static volatile uint64_t b[N] __attribute__((aligned(4096)));
static volatile uint64_t cold[COLD] __attribute__((aligned(4096)));

int
main(void)
{
    uint64_t s = 0x1e4d7c9b0a8362f1ULL ^ (uint64_t)CONTEXT;
    unsigned i;

    for (i = 0; i < N; i++) {
        a[i] = 0x2000ULL + (uint64_t)i * 0x9e3779b97f4a7c15ULL;
        b[i] = 0x7000ULL + (uint64_t)i * 0xbf58476d1ce4e5b9ULL;
    }
    for (i = 0; i < COLD; i++)
        cold[i] = when_hash64((uint64_t)i);

#if CONTEXT == 1
    /* C01: baseline LQ lifetime: L1-resident loads, direct consumer. */
    for (i = 0; i < N; i++)
        s = when_fnv(s, a[i]);
#elif CONTEXT == 2
    /* C02: changed activation conditions: alternating cold misses and
     * queued L1 hits keep entries alive while requests are outstanding. */
    for (i = 0; i < N; i++) {
        uint64_t v = cold[(i * 8191u) & (COLD - 1u)];
        uint64_t w = a[i];
        s = when_fnv(s, v ^ w);
    }
#elif CONTEXT == 3
    /* C03: weak consumption: entry lifetime is observed but the result is
     * overwritten before use. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        __asm__ volatile("" : "+r"(v) : : "memory");
        v = 0x3c3c3c3c3c3c3c3cULL;
        s = when_fnv(s, v);
    }
#elif CONTEXT == 4
    /* C04: enhanced dependency: chained loads through the loaded value. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        unsigned j = (unsigned)((v >> 4) & (N - 1u));
        uint64_t w = b[j];
        s = when_fnv(s, w);
    }
#else
    /* C05: control/speculation: slow cold condition selects between two
     * load-carrying paths. */
    for (i = 0; i < N; i++) {
        uint64_t c = cold[(i * 29u) & (COLD - 1u)];
        __asm__ volatile("" ::: "memory");
        if (c & 1ull) {
            uint64_t v = a[i];
            s = when_fnv(s, v);
        } else {
            uint64_t v = b[i];
            s = when_fnv(s, v ^ 0x55ULL);
        }
    }
#endif

    when_put_hex(s);
    return 0;
}
