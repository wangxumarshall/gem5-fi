/* lsu_when_lp.c — LP01 When-v2 contexts (Sheet 15, W5).
 *
 * E2E instrumented variant: identical arithmetic to the frozen source; the
 * only addition is the read-free sw_mark4 event stream.
 */
#include "when_common.h"

#define N 192
#define NB 2048

static volatile uint64_t a[NB] __attribute__((aligned(4096)));
static volatile uint32_t cold[4096] __attribute__((aligned(4096)));
static volatile uint64_t aux[NB] __attribute__((aligned(4096)));

int
main(void)
{
    uint64_t s = 0x1010feedface0101ULL ^ (uint64_t)CONTEXT;
    uint64_t ev = 0;
    unsigned i;

    for (i = 0; i < NB; i++) {
        a[i] = 0x5000ULL + (uint64_t)i * 0x9e3779b97f4a7c15ULL;
        aux[i] = 0x9000ULL + (uint64_t)i * 0xbf58476d1ce4e5b9ULL;
    }
    for (i = 0; i < 4096; i++)
        cold[i] = (uint32_t)when_hash64(i + 3u);

    SW_EV(ev, SW_PHASE, 1, 3, 0, 0);

#if CONTEXT == 1
    /* C01: baseline 8-byte load responses consumed directly. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        SW_EV(ev, SW_LOAD, 2, (uint64_t)&a[i], v, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, v);
        SW_EV(ev, SW_HASH, 3, v, hb, s);
    }
#elif CONTEXT == 2
    /* C02: changed access width/alignment; still data-load responses. */
    for (i = 0; i < N; i++) {
        uint32_t w = *(volatile uint32_t *)(void *)((const volatile char *)a
                                                    + (uint64_t)i * 4u);
        SW_EV(ev, SW_LOAD, 4, (uint64_t)&((const volatile char *)a)[(uint64_t)i * 4u],
              w, SW_AUX(i, 4));
        uint64_t v = *(volatile uint64_t *)(void *)((const volatile char *)a
                                                    + (uint64_t)i * 8u + 8u);
        SW_EV(ev, SW_LOAD, 5,
              (uint64_t)&((const volatile char *)a)[(uint64_t)i * 8u + 8u], v,
              SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, (uint64_t)w ^ v);
        SW_EV(ev, SW_HASH, 6, (uint64_t)w ^ v, hb, s);
    }
#elif CONTEXT == 3
    /* C03: response value overwritten before any consumer. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        SW_EV(ev, SW_LOAD, 7, (uint64_t)&a[i], v, SW_AUX(i, 8));
        __asm__ volatile("" : "+r"(v) : : "memory");
        v = 0x6b6b6b6b6b6b6b6bULL;
        SW_EV(ev, SW_VALUE, 8, v, 0, SW_AUX(i, 0));
        uint64_t hb = s;
        s = when_fnv(s, v);
        SW_EV(ev, SW_HASH, 9, v, hb, s);
    }
#elif CONTEXT == 4
    /* C04: load result feeds a second address and a multilevel consumer. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        SW_EV(ev, SW_LOAD, 10, (uint64_t)&a[i], v, SW_AUX(i, 8));
        unsigned j = (unsigned)((v >> 3) & (NB - 1u));
        uint64_t w = aux[j];
        SW_EV(ev, SW_LOAD, 11, (uint64_t)&aux[j], w, SW_AUX(i, j));
        aux[j] = w ^ v;
        SW_EV(ev, SW_STORE, 12, (uint64_t)&aux[j], w ^ v, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, w ^ v);
        SW_EV(ev, SW_HASH, 13, w ^ v, hb, s);
    }
#else
    /* C05: speculated load on an unpredictable cold-conditioned branch. */
    for (i = 0; i < N; i++) {
        uint32_t c = cold[(i * 53u) & 4095u];
        SW_EV(ev, SW_LOAD, 14, (uint64_t)&cold[(i * 53u) & 4095u], c,
              SW_AUX(i, 4));
        if (c & 1u) {
            uint64_t v = a[i];
            SW_EV(ev, SW_LOAD, 16, (uint64_t)&a[i], v, SW_AUX(i, 8));
            uint64_t hb = s;
            s = when_fnv(s, v);
            SW_EV(ev, SW_HASH, 18, v, hb, s);
        } else {
            uint64_t v = a[(i + 1u) & (NB - 1u)];
            SW_EV(ev, SW_LOAD, 17, (uint64_t)&a[(i + 1u) & (NB - 1u)], v,
                  SW_AUX(i, 8));
            uint64_t hb = s;
            s = when_fnv(s, v ^ 0x33ULL);
            SW_EV(ev, SW_HASH, 19, v ^ 0x33ULL, hb, s);
        }
        SW_EV(ev, SW_BRANCH, 15, c, c & 1u, SW_AUX(i, 0));
    }
#endif

    SW_EV(ev, SW_OUTPUT, 99, s, 0, 0);
    when_put_hex(s);
    return 0;
}
