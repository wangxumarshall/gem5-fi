/* lsu_when_lq.c — LQ04 When-v2 contexts (Sheet 15, W2).
 *
 * E2E instrumented variant: identical arithmetic to the frozen source; the
 * only addition is the read-free sw_mark4 event stream.
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
    uint64_t ev = 0;
    unsigned i;

    for (i = 0; i < N; i++) {
        a[i] = 0x2000ULL + (uint64_t)i * 0x9e3779b97f4a7c15ULL;
        b[i] = 0x7000ULL + (uint64_t)i * 0xbf58476d1ce4e5b9ULL;
    }
    for (i = 0; i < COLD; i++)
        cold[i] = when_hash64((uint64_t)i);

    SW_EV(ev, SW_PHASE, 1, 2, 0, 0);

#if CONTEXT == 1
    /* C01: baseline LQ lifetime: L1-resident loads, direct consumer. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        SW_EV(ev, SW_LOAD, 2, (uint64_t)&a[i], v, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, v);
        SW_EV(ev, SW_HASH, 3, v, hb, s);
    }
#elif CONTEXT == 2
    /* C02: changed activation conditions: alternating cold misses and
     * queued L1 hits keep entries alive while requests are outstanding. */
    for (i = 0; i < N; i++) {
        uint64_t v = cold[(i * 8191u) & (COLD - 1u)];
        SW_EV(ev, SW_LOAD, 4, (uint64_t)&cold[(i * 8191u) & (COLD - 1u)], v,
              SW_AUX(i, 8));
        uint64_t w = a[i];
        SW_EV(ev, SW_LOAD, 5, (uint64_t)&a[i], w, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, v ^ w);
        SW_EV(ev, SW_HASH, 6, v ^ w, hb, s);
    }
#elif CONTEXT == 3
    /* C03: weak consumption: entry lifetime is observed but the result is
     * overwritten before use. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        SW_EV(ev, SW_LOAD, 7, (uint64_t)&a[i], v, SW_AUX(i, 8));
        __asm__ volatile("" : "+r"(v) : : "memory");
        v = 0x3c3c3c3c3c3c3c3cULL;
        SW_EV(ev, SW_VALUE, 8, v, 0, SW_AUX(i, 0));
        uint64_t hb = s;
        s = when_fnv(s, v);
        SW_EV(ev, SW_HASH, 9, v, hb, s);
    }
#elif CONTEXT == 4
    /* C04: enhanced dependency: chained loads through the loaded value. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        SW_EV(ev, SW_LOAD, 10, (uint64_t)&a[i], v, SW_AUX(i, 8));
        unsigned j = (unsigned)((v >> 4) & (N - 1u));
        uint64_t w = b[j];
        SW_EV(ev, SW_LOAD, 11, (uint64_t)&b[j], w, SW_AUX(i, j));
        uint64_t hb = s;
        s = when_fnv(s, w);
        SW_EV(ev, SW_HASH, 12, w, hb, s);
    }
#else
    /* C05: control/speculation: slow cold condition selects between two
     * load-carrying paths. */
    for (i = 0; i < N; i++) {
        uint64_t c = cold[(i * 29u) & (COLD - 1u)];
        SW_EV(ev, SW_LOAD, 13, (uint64_t)&cold[(i * 29u) & (COLD - 1u)], c,
              SW_AUX(i, 8));
        __asm__ volatile("" ::: "memory");
        if (c & 1ull) {
            uint64_t v = a[i];
            SW_EV(ev, SW_LOAD, 15, (uint64_t)&a[i], v, SW_AUX(i, 8));
            uint64_t hb = s;
            s = when_fnv(s, v);
            SW_EV(ev, SW_HASH, 17, v, hb, s);
        } else {
            uint64_t v = b[i];
            SW_EV(ev, SW_LOAD, 16, (uint64_t)&b[i], v, SW_AUX(i, 8));
            uint64_t hb = s;
            s = when_fnv(s, v ^ 0x55ULL);
            SW_EV(ev, SW_HASH, 18, v ^ 0x55ULL, hb, s);
        }
        SW_EV(ev, SW_BRANCH, 14, c, c & 1ull, SW_AUX(i, 0));
    }
#endif

    SW_EV(ev, SW_OUTPUT, 99, s, 0, 0);
    when_put_hex(s);
    return 0;
}
