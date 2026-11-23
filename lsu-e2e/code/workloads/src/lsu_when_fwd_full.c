/* lsu_when_fwd_full.c — FW02 When-v2 contexts (Sheet 15, W4).
 *
 * E2E instrumented variant.  Marker discipline: a store marker is emitted
 * only AFTER the load that the original program performs next, so the
 * store->load forwarding window is never widened by observation code.
 */
#include "when_common.h"

#define N 192
#define NB 256

static volatile uint64_t buf[NB] __attribute__((aligned(4096)));
static volatile uint64_t aux[NB] __attribute__((aligned(4096)));
static volatile uint32_t slow[4096] __attribute__((aligned(4096)));

int
main(void)
{
    uint64_t s = 0x5f1e4d7c9b0a8362ULL ^ (uint64_t)CONTEXT;
    uint64_t ev = 0;
    unsigned i;

    for (i = 0; i < NB; i++) {
        buf[i] = 0;
        aux[i] = 0x6000ULL + (uint64_t)i * 0x9e3779b97f4a7c15ULL;
    }
    for (i = 0; i < 4096; i++)
        slow[i] = (uint32_t)when_hash64(i);

    SW_EV(ev, SW_PHASE, 1, 5, 0, 0);

#if CONTEXT == 1
    /* C01: store then immediate same-address load (full forwarding). */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t v = 0xa000ULL + (uint64_t)i * 0x1111111111111111ULL;
        buf[k] = v;
        __asm__ volatile("" ::: "memory");
        uint64_t r = buf[k];
        SW_EV(ev, SW_LOAD, 3, (uint64_t)&buf[k], r, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 2, (uint64_t)&buf[k], v, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, r);
        SW_EV(ev, SW_HASH, 4, r, hb, s);
    }
#elif CONTEXT == 2
    /* C02: vary the store/load dynamic distance while keeping a real
     * full-coverage older store in the SQ. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t v = 0xb000ULL + (uint64_t)i;
        uint64_t v7 = v ^ 0x11ULL;
        uint64_t v13 = v ^ 0x22ULL;
        buf[k] = v;
        buf[(k + 7u) & (NB - 1u)] = v7;
        buf[(k + 13u) & (NB - 1u)] = v13;
        __asm__ volatile("" ::: "memory");
        uint64_t r = buf[k];
        SW_EV(ev, SW_LOAD, 13, (uint64_t)&buf[k], r, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 10, (uint64_t)&buf[k], v, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 11, (uint64_t)&buf[(k + 7u) & (NB - 1u)], v7,
              SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 12, (uint64_t)&buf[(k + 13u) & (NB - 1u)], v13,
              SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, r);
        SW_EV(ev, SW_HASH, 14, r, hb, s);
    }
#elif CONTEXT == 3
    /* C03: the forwarded load's value is overwritten; only the reload
     * after the store drains is consumed. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t v = 0xc000ULL + (uint64_t)i * 3u;
        buf[k] = v;
        __asm__ volatile("" ::: "memory");
        uint64_t r = buf[k];
        SW_EV(ev, SW_LOAD, 21, (uint64_t)&buf[k], r, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 20, (uint64_t)&buf[k], v, SW_AUX(i, 8));
        __asm__ volatile("" : "+r"(r) : : "memory");
        r = 0x5a5a5a5a5a5a5a5aULL;
        SW_EV(ev, SW_VALUE, 22, r, 0, SW_AUX(i, 0));
        __asm__ volatile("dmb ish" ::: "memory");
        uint64_t good = buf[k];
        SW_EV(ev, SW_LOAD, 23, (uint64_t)&buf[k], good, SW_AUX(i, 8));
        uint64_t hb = s;
        s = when_fnv(s, r ^ good);
        SW_EV(ev, SW_HASH, 24, r ^ good, hb, s);
    }
#elif CONTEXT == 4
    /* C04: forwarded value feeds a pointer/index dependency chain. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t v = 0xd000ULL + (uint64_t)i * 5u;
        buf[k] = v;
        __asm__ volatile("" ::: "memory");
        uint64_t r = buf[k];
        SW_EV(ev, SW_LOAD, 31, (uint64_t)&buf[k], r, SW_AUX(i, 8));
        SW_EV(ev, SW_STORE, 30, (uint64_t)&buf[k], v, SW_AUX(i, 8));
        unsigned j = (unsigned)((r >> 4) & (NB - 1u));
        uint64_t w = aux[j];
        SW_EV(ev, SW_LOAD, 32, (uint64_t)&aux[j], w, SW_AUX(i, j));
        aux[j] = w + r;
        SW_EV(ev, SW_STORE, 33, (uint64_t)&aux[j], w + r, SW_AUX(i, 8));
        __asm__ volatile("" ::: "memory");
        uint64_t hb = s;
        s = when_fnv(s, r ^ w);
        SW_EV(ev, SW_HASH, 34, r ^ w, hb, s);
    }
#else
    /* C05: speculative consumer: an unpredictable branch carries the
     * same-address load in both directions. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t v = 0xe000ULL + (uint64_t)i * 7u;
        buf[k] = v;
        __asm__ volatile("" ::: "memory");
        uint32_t c = slow[(i * 31u) & 4095u];
        if (c & 1u) {
            uint64_t r = buf[k];
            SW_EV(ev, SW_LOAD, 43, (uint64_t)&buf[k], r, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 40, (uint64_t)&buf[k], v, SW_AUX(i, 8));
            uint64_t hb = s;
            s = when_fnv(s, r);
            SW_EV(ev, SW_HASH, 45, r, hb, s);
        } else {
            uint64_t r = buf[k];
            SW_EV(ev, SW_LOAD, 44, (uint64_t)&buf[k], r, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 40, (uint64_t)&buf[k], v, SW_AUX(i, 8));
            uint64_t hb = s;
            s = when_fnv(s, r ^ 0x99ULL);
            SW_EV(ev, SW_HASH, 46, r ^ 0x99ULL, hb, s);
        }
        SW_EV(ev, SW_LOAD, 41, (uint64_t)&slow[(i * 31u) & 4095u], c,
              SW_AUX(i, 4));
        SW_EV(ev, SW_BRANCH, 42, c, c & 1u, SW_AUX(i, 0));
    }
#endif

    SW_EV(ev, SW_OUTPUT, 99, s, 0, 0);
    when_put_hex(s);
    return 0;
}
