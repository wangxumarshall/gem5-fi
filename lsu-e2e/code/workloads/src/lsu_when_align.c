/* lsu_when_align.c — DA04 When-v2 contexts (Sheet 15, W8).
 *
 * E2E instrumented variant.  Store markers are emitted only after the
 * reload, keeping the 4-byte store -> reload adjacency intact.
 */
#include "when_common.h"

#define N 192
#define NB 1024

static volatile uint8_t area[NB * 4u + 64u] __attribute__((aligned(4096)));
static volatile uint64_t aux[128] __attribute__((aligned(4096)));

int
main(void)
{
    uint64_t s = 0xda04da04da04da04ULL ^ (uint64_t)CONTEXT;
    uint64_t ev = 0;
    unsigned i;

    for (i = 0; i < NB * 4u + 64u; i++)
        area[i] = (uint8_t)(i * 7u + 3u);
    for (i = 0; i < 128; i++)
        aux[i] = 0xa000ULL + (uint64_t)i * 0x9e3779b97f4a7c15ULL;

    SW_EV(ev, SW_PHASE, 1, 7, 0, 0);

#if CONTEXT == 1
    /* C01: aligned 4-byte store, barrier, same-address 4-byte reload. */
    for (i = 0; i < N; i++) {
        uint32_t v = (uint32_t)(i * 2654435761u);
        *(volatile uint32_t *)(void *)(area + i * 4u) = v;
        __asm__ volatile("dmb ish" ::: "memory");
        uint32_t r = *(volatile uint32_t *)(void *)(area + i * 4u);
        SW_EV(ev, SW_LOAD, 3, (uint64_t)(area + i * 4u), r, SW_AUX(i, 4));
        SW_EV(ev, SW_STORE, 2, (uint64_t)(area + i * 4u), v, SW_AUX(i, 4));
        uint64_t hb = s;
        s = when_fnv(s, r);
        SW_EV(ev, SW_HASH, 4, r, hb, s);
    }
#elif CONTEXT == 2
    /* C02: changed legal access shape: unaligned 4-byte stores at +1,
     * still a full 4-byte byte-enable mask. */
    for (i = 0; i < N; i++) {
        uint32_t v = (uint32_t)(i * 2246822519u + 1u);
        *(volatile uint32_t *)(void *)(area + i * 4u + 1u) = v;
        __asm__ volatile("dmb ish" ::: "memory");
        uint32_t r = *(volatile uint32_t *)(void *)(area + i * 4u + 1u);
        SW_EV(ev, SW_LOAD, 11, (uint64_t)(area + i * 4u + 1u), r,
              SW_AUX(i, 4));
        SW_EV(ev, SW_STORE, 10, (uint64_t)(area + i * 4u + 1u), v,
              SW_AUX(i, 4));
        uint64_t hb = s;
        s = when_fnv(s, r);
        SW_EV(ev, SW_HASH, 12, r, hb, s);
    }
#elif CONTEXT == 3
    /* C03: overwrite: a correct 4-byte store to the same address follows
     * the faulted one before any reload. */
    for (i = 0; i < N; i++) {
        uint32_t v = (uint32_t)(i * 2654435761u);
        *(volatile uint32_t *)(void *)(area + i * 4u) = v;
        __asm__ volatile("" ::: "memory");
        uint32_t good = v ^ 0xa5a5a5a5u;
        *(volatile uint32_t *)(void *)(area + i * 4u) = good;
        __asm__ volatile("dmb ish" ::: "memory");
        uint32_t r = *(volatile uint32_t *)(void *)(area + i * 4u);
        SW_EV(ev, SW_LOAD, 22, (uint64_t)(area + i * 4u), r, SW_AUX(i, 4));
        SW_EV(ev, SW_STORE, 20, (uint64_t)(area + i * 4u), v, SW_AUX(i, 4));
        SW_EV(ev, SW_STORE, 21, (uint64_t)(area + i * 4u), good,
              SW_AUX(i, 4));
        uint64_t hb = s;
        s = when_fnv(s, r);
        SW_EV(ev, SW_HASH, 23, r, hb, s);
    }
#elif CONTEXT == 4
    /* C04: the reloaded value indexes the next 4-byte access. */
    for (i = 0; i < N; i++) {
        uint32_t v = (uint32_t)(i * 2654435761u);
        *(volatile uint32_t *)(void *)(area + i * 4u) = v;
        __asm__ volatile("dmb ish" ::: "memory");
        uint32_t r = *(volatile uint32_t *)(void *)(area + i * 4u);
        unsigned j = (r ^ (r >> 13)) & 127u;
        uint64_t y = aux[j];
        aux[j] = y ^ r;
        SW_EV(ev, SW_LOAD, 31, (uint64_t)(area + i * 4u), r, SW_AUX(i, 4));
        SW_EV(ev, SW_STORE, 30, (uint64_t)(area + i * 4u), v, SW_AUX(i, 4));
        SW_EV(ev, SW_LOAD, 32, (uint64_t)&aux[j], y, SW_AUX(i, j));
        SW_EV(ev, SW_STORE, 33, (uint64_t)&aux[j], y ^ r, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, (uint64_t)r ^ y);
        SW_EV(ev, SW_HASH, 34, (uint64_t)r ^ y, hb, s);
    }
#else
    /* C05: control consumer after the store's memory effect is visible;
     * a committed store is never treated as reversible. */
    for (i = 0; i < N; i++) {
        uint32_t v = (uint32_t)(i * 2654435761u);
        *(volatile uint32_t *)(void *)(area + i * 4u) = v;
        __asm__ volatile("dmb ish" ::: "memory");
        uint32_t r = *(volatile uint32_t *)(void *)(area + i * 4u);
        if (r & 8u) {
            SW_EV(ev, SW_LOAD, 41, (uint64_t)(area + i * 4u), r,
                  SW_AUX(i, 4));
            SW_EV(ev, SW_STORE, 40, (uint64_t)(area + i * 4u), v,
                  SW_AUX(i, 4));
            uint64_t hb = s;
            s = when_fnv(s, r);
            SW_EV(ev, SW_HASH, 43, r, hb, s);
        } else {
            SW_EV(ev, SW_LOAD, 41, (uint64_t)(area + i * 4u), r,
                  SW_AUX(i, 4));
            SW_EV(ev, SW_STORE, 40, (uint64_t)(area + i * 4u), v,
                  SW_AUX(i, 4));
            uint64_t hb = s;
            s = when_fnv(s, r ^ 0x1u);
            SW_EV(ev, SW_HASH, 44, r ^ 0x1u, hb, s);
        }
        SW_EV(ev, SW_BRANCH, 42, r, r & 8u, SW_AUX(i, 0));
    }
#endif

    SW_EV(ev, SW_OUTPUT, 99, s, 0, 0);
    when_put_hex(s);
    return 0;
}
