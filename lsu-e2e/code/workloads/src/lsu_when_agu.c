/* lsu_when_agu.c — A01/A03 When-v2 contexts (Sheet 15, W1).
 *
 * E2E instrumented variant: identical arithmetic to the frozen source; the
 * only addition is the read-free sw_mark4 event stream (see when_common.h).
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
    uint64_t ev = 0;
    unsigned i;

    for (i = 0; i < N; i++) {
        a[i] = 0x1000ULL + (uint64_t)i * 0x0123456789abcdefULL;
        b[i] = 0x9000ULL + (uint64_t)i * 0xfedcba9876543210ULL;
    }
    for (i = 0; i < 4096; i++)
        cold[i] = (uint32_t)(when_hash64((uint64_t)i) ^ 0xa5a5a5a5u);

    SW_EV(ev, SW_PHASE, 1, 1, 0, 0);

#if CONTEXT == 1
    /* C01: baseline activation: load -> direct checksum consumer. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        SW_EV(ev, SW_LOAD, 2, (uint64_t)&a[i], v, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, v);
        SW_EV(ev, SW_HASH, 3, v, hb, s);
    }
#elif CONTEXT == 2
    /* C02: legal activation variation: register-index and displacement
     * forms, all 8-byte GPR loads from the same object. */
    for (i = 0; i < N; i++) {
        unsigned j = (i * 7u) & (N - 1u);
        uint64_t v = *(volatile uint64_t *)((const volatile char *)a
                                            + (uint64_t)j * 8u);
        SW_EV(ev, SW_LOAD, 4, (uint64_t)&((const volatile char *)a)[(uint64_t)j * 8u],
              v, SW_AUX(i, j));
        uint64_t hb = s;
        s = when_fnv(s, v);
        SW_EV(ev, SW_HASH, 6, v, hb, s);
        j = (i * 13u + 5u) & (N - 1u);
        uint64_t w = b[j];
        SW_EV(ev, SW_LOAD, 5, (uint64_t)&b[j], w, SW_AUX(i, j));
        hb = s;
        s = when_fnv(s, w);
        SW_EV(ev, SW_HASH, 6, w, hb, s);
    }
#elif CONTEXT == 3
    /* C03: weak consumption: the load still executes, but the value is
     * overwritten before any checksum/address use. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        SW_EV(ev, SW_LOAD, 7, (uint64_t)&a[i], v, SW_AUX(i, 8));
        __asm__ volatile("" : "+r"(v) : : "memory");
        v = 0x5a5a5a5a5a5a5a5aULL;
        SW_EV(ev, SW_VALUE, 8, v, 0, SW_AUX(i, 0));
        uint64_t hb = s;
        s = when_fnv(s, v);
        SW_EV(ev, SW_HASH, 9, v, hb, s);
    }
#elif CONTEXT == 4
    /* C04: enhanced data dependency: loaded value indexes a second load,
     * which is then consumed. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        SW_EV(ev, SW_LOAD, 10, (uint64_t)&a[i], v, SW_AUX(i, 8));
        unsigned j = (unsigned)((v >> 3) & (N - 1u));
        uint64_t w = b[j];
        SW_EV(ev, SW_LOAD, 11, (uint64_t)&b[j], w, SW_AUX(i, j));
        uint64_t hb = s;
        s = when_fnv(s, w);
        SW_EV(ev, SW_HASH, 12, w, hb, s);
    }
#else
    /* C05: control/speculation: a slow cold load drives an unpredictable
     * branch; each direction contains several 8-byte loads. */
    for (i = 0; i < N; i++) {
        uint32_t c = cold[(i * 37u) & 4095u];
        SW_EV(ev, SW_LOAD, 13, (uint64_t)&cold[(i * 37u) & 4095u], c,
              SW_AUX(i, 4));
        __asm__ volatile("" ::: "memory");
        if (c & 1u) {
            uint64_t v0 = a[i], v1 = a[(i + 1u) & (N - 1u)];
            uint64_t v2 = a[(i + 2u) & (N - 1u)];
            SW_EV(ev, SW_LOAD, 15, (uint64_t)&a[i], v0, SW_AUX(i, 8));
            SW_EV(ev, SW_LOAD, 16, (uint64_t)&a[(i + 1u) & (N - 1u)], v1,
                  SW_AUX(i, 8));
            SW_EV(ev, SW_LOAD, 17, (uint64_t)&a[(i + 2u) & (N - 1u)], v2,
                  SW_AUX(i, 8));
            uint64_t hb = s;
            s = when_fnv(s, v0 ^ v1 ^ v2);
            SW_EV(ev, SW_HASH, 21, v0 ^ v1 ^ v2, hb, s);
        } else {
            uint64_t v0 = b[i], v1 = b[(i + 3u) & (N - 1u)];
            uint64_t v2 = b[(i + 4u) & (N - 1u)];
            SW_EV(ev, SW_LOAD, 18, (uint64_t)&b[i], v0, SW_AUX(i, 8));
            SW_EV(ev, SW_LOAD, 19, (uint64_t)&b[(i + 3u) & (N - 1u)], v1,
                  SW_AUX(i, 8));
            SW_EV(ev, SW_LOAD, 20, (uint64_t)&b[(i + 4u) & (N - 1u)], v2,
                  SW_AUX(i, 8));
            uint64_t hb = s;
            s = when_fnv(s, v0 ^ v1 ^ v2);
            SW_EV(ev, SW_HASH, 22, v0 ^ v1 ^ v2, hb, s);
        }
        SW_EV(ev, SW_BRANCH, 14, c, c & 1u, SW_AUX(i, 0));
    }
#endif

    SW_EV(ev, SW_OUTPUT, 99, s, 0, 0);
    when_put_hex(s);
    return 0;
}
