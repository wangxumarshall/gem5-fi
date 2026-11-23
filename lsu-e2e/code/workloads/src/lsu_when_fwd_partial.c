/* lsu_when_fwd_partial.c — FW05 When-v2 contexts (Sheet 15, W8).
 *
 * E2E instrumented variant.  Marker discipline: a store marker is emitted
 * only AFTER the load that the original program performs next, so the
 * store->load forwarding window is never widened by observation code.
 */
#include "when_common.h"

#define N 160
#define NB 128

static volatile uint64_t buf[NB] __attribute__((aligned(4096)));
static volatile uint64_t aux[NB] __attribute__((aligned(4096)));
static volatile uint32_t slow[4096] __attribute__((aligned(4096)));

int
main(void)
{
    uint64_t s = 0x0d7c9b0a83625f1eULL ^ (uint64_t)CONTEXT;
    uint64_t ev = 0;
    unsigned i;

    for (i = 0; i < NB; i++) {
        buf[i] = 0;
        aux[i] = 0x8000ULL + (uint64_t)i * 0x9e3779b97f4a7c15ULL;
    }
    for (i = 0; i < 4096; i++)
        slow[i] = (uint32_t)when_hash64(i + 17u);

    SW_EV(ev, SW_PHASE, 1, 6, 0, 0);

#if CONTEXT == 1
    /* C01: three older stores to the same address, then the load. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t s1 = 0x3333333333333333ULL + i;
        uint64_t s2 = 0x1111111111111111ULL + (uint64_t)i;
        uint64_t s3 = 0x2222222222222222ULL + (uint64_t)i * 3u;
        uint64_t s4 = 0x4444444444444444ULL + (uint64_t)i * 5u;
        buf[(k + 1u) & (NB - 1u)] = s1;
        __asm__ volatile("" ::: "memory");
        buf[k] = s2;
        __asm__ volatile("" ::: "memory");
        buf[k] = s3;
        __asm__ volatile("" ::: "memory");
        buf[k] = s4;
        __asm__ volatile("" ::: "memory");
        uint64_t r = buf[k];
        SW_EV(ev, SW_LOAD, 6, (uint64_t)&buf[k], r, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 2, (uint64_t)&buf[(k + 1u) & (NB - 1u)], s1,
              SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 3, (uint64_t)&buf[k], s2, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 4, (uint64_t)&buf[k], s3, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 5, (uint64_t)&buf[k], s4, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, r);
        SW_EV(ev, SW_HASH, 7, r, hb, s);
    }
#elif CONTEXT == 2
    /* C02: same three candidate stores, but additional unrelated stores
     * change the SQ occupancy/dynamic distance. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t t1 = 0x7777777777777777ULL + i;
        uint64_t t2 = 0x6666666666666666ULL + i;
        uint64_t s1 = 0x3333333333333333ULL + i;
        uint64_t s2 = 0x1111111111111111ULL + (uint64_t)i;
        uint64_t s3 = 0x2222222222222222ULL + (uint64_t)i * 3u;
        uint64_t s4 = 0x4444444444444444ULL + (uint64_t)i * 5u;
        buf[(k + 3u) & (NB - 1u)] = t1;
        buf[(k + 5u) & (NB - 1u)] = t2;
        __asm__ volatile("" ::: "memory");
        buf[(k + 1u) & (NB - 1u)] = s1;
        __asm__ volatile("" ::: "memory");
        buf[k] = s2;
        __asm__ volatile("" ::: "memory");
        buf[k] = s3;
        __asm__ volatile("" ::: "memory");
        buf[k] = s4;
        __asm__ volatile("" ::: "memory");
        uint64_t r = buf[k];
        SW_EV(ev, SW_LOAD, 16, (uint64_t)&buf[k], r, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 10, (uint64_t)&buf[(k + 3u) & (NB - 1u)], t1,
              SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 11, (uint64_t)&buf[(k + 5u) & (NB - 1u)], t2,
              SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 12, (uint64_t)&buf[(k + 1u) & (NB - 1u)], s1,
              SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 13, (uint64_t)&buf[k], s2, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 14, (uint64_t)&buf[k], s3, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 15, (uint64_t)&buf[k], s4, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, r);
        SW_EV(ev, SW_HASH, 17, r, hb, s);
    }
#elif CONTEXT == 3
    /* C03: forwarded value overwritten; the drained reload is consumed. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t v1 = 0x1111111111111111ULL + (uint64_t)i;
        uint64_t v2 = 0x2222222222222222ULL + (uint64_t)i * 3u;
        buf[k] = v1;
        __asm__ volatile("" ::: "memory");
        buf[k] = v2;
        __asm__ volatile("" ::: "memory");
        uint64_t r = buf[k];
        SW_EV(ev, SW_LOAD, 22, (uint64_t)&buf[k], r, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 20, (uint64_t)&buf[k], v1, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 21, (uint64_t)&buf[k], v2, SW_AUX(i, 8));
        __asm__ volatile("" : "+r"(r) : : "memory");
        r = 0x5a5a5a5a5a5a5a5aULL;
        SW_EV(ev, SW_VALUE, 23, r, 0, SW_AUX(i, 0));
        __asm__ volatile("dmb ish" ::: "memory");
        uint64_t good = buf[k];
        SW_EV(ev, SW_LOAD, 24, (uint64_t)&buf[k], good, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, r ^ good);
        SW_EV(ev, SW_HASH, 25, r ^ good, hb, s);
    }
#elif CONTEXT == 4
    /* C04: forwarded value indexes the next access. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t v1 = 0x1111111111111111ULL + (uint64_t)i;
        uint64_t v2 = 0x2222222222222222ULL + (uint64_t)i * 3u;
        buf[k] = v1;
        __asm__ volatile("" ::: "memory");
        buf[k] = v2;
        __asm__ volatile("" ::: "memory");
        uint64_t r = buf[k];
        SW_EV(ev, SW_LOAD, 32, (uint64_t)&buf[k], r, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 30, (uint64_t)&buf[k], v1, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 31, (uint64_t)&buf[k], v2, SW_AUX(i, 8));
        unsigned j = (unsigned)((r >> 6) & (NB - 1u));
        uint64_t w = aux[j];
        SW_EV(ev, SW_LOAD, 33, (uint64_t)&aux[j], w, SW_AUX(i, j));
        aux[j] = w ^ r;
        SW_EV(ev, SW_STORE, 34, (uint64_t)&aux[j], w ^ r, SW_AUX(i, 8));
        __asm__ volatile("" ::: "memory");
        uint64_t hb = s;
        s = when_fnv(s, r ^ w);
        SW_EV(ev, SW_HASH, 35, r ^ w, hb, s);
    }
#else
    /* C05: speculative consumer with the same candidate pair. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t v1 = 0x1111111111111111ULL + (uint64_t)i;
        uint64_t v2 = 0x2222222222222222ULL + (uint64_t)i * 3u;
        buf[k] = v1;
        __asm__ volatile("" ::: "memory");
        buf[k] = v2;
        __asm__ volatile("" ::: "memory");
        uint32_t c = slow[(i * 43u) & 4095u];
        if (c & 1u) {
            uint64_t r = buf[k];
            SW_EV(ev, SW_LOAD, 44, (uint64_t)&buf[k], r, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 40, (uint64_t)&buf[k], v1, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 41, (uint64_t)&buf[k], v2, SW_AUX(i, 8));
            uint64_t hb = s;
            s = when_fnv(s, r);
            SW_EV(ev, SW_HASH, 46, r, hb, s);
        } else {
            uint64_t r = buf[k];
            SW_EV(ev, SW_LOAD, 45, (uint64_t)&buf[k], r, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 40, (uint64_t)&buf[k], v1, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 41, (uint64_t)&buf[k], v2, SW_AUX(i, 8));
            uint64_t hb = s;
            s = when_fnv(s, r ^ 0x77ULL);
            SW_EV(ev, SW_HASH, 47, r ^ 0x77ULL, hb, s);
        }
        SW_EV(ev, SW_LOAD, 42, (uint64_t)&slow[(i * 43u) & 4095u], c,
              SW_AUX(i, 4));
        SW_EV(ev, SW_BRANCH, 43, c, c & 1u, SW_AUX(i, 0));
    }
#endif

    SW_EV(ev, SW_OUTPUT, 99, s, 0, 0);
    when_put_hex(s);
    return 0;
}
