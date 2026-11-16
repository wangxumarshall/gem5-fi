/* lsu_when_fwd_full.c — FW02 When-v2 contexts (Sheet 15, W4).
 *
 * Every context contains a real older-store / younger-load pair with full
 * address-range coverage; the fault hook (forwarding decision) is unchanged.
 *   C01 baseline forward-and-consume
 *   C02 varied dynamic distance / SQ occupancy, still full coverage
 *   C03 forwarded value overwritten before use; the post-drain reload is
 *       the consumed source
 *   C04 forwarded value indexes the next access
 *   C05 load executed on a speculated branch path
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
    unsigned i;

    for (i = 0; i < NB; i++) {
        buf[i] = 0;
        aux[i] = 0x6000ULL + (uint64_t)i * 0x9e3779b97f4a7c15ULL;
    }
    for (i = 0; i < 4096; i++)
        slow[i] = (uint32_t)when_hash64(i);

#if CONTEXT == 1
    /* C01: store then immediate same-address load (full forwarding). */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t v = 0xa000ULL + (uint64_t)i * 0x1111111111111111ULL;
        buf[k] = v;
        __asm__ volatile("" ::: "memory");
        s = when_fnv(s, buf[k]);
    }
#elif CONTEXT == 2
    /* C02: vary the store/load dynamic distance while keeping a real
     * full-coverage older store in the SQ. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t v = 0xb000ULL + (uint64_t)i;
        buf[k] = v;
        buf[(k + 7u) & (NB - 1u)] = v ^ 0x11ULL;
        buf[(k + 13u) & (NB - 1u)] = v ^ 0x22ULL;
        __asm__ volatile("" ::: "memory");
        s = when_fnv(s, buf[k]);
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
        __asm__ volatile("" : "+r"(r) : : "memory");
        r = 0x5a5a5a5a5a5a5a5aULL;
        __asm__ volatile("dmb ish" ::: "memory");
        uint64_t good = buf[k];
        s = when_fnv(s, r ^ good);
    }
#elif CONTEXT == 4
    /* C04: forwarded value feeds a pointer/index dependency chain. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        uint64_t v = 0xd000ULL + (uint64_t)i * 5u;
        buf[k] = v;
        __asm__ volatile("" ::: "memory");
        uint64_t r = buf[k];
        unsigned j = (unsigned)((r >> 4) & (NB - 1u));
        uint64_t w = aux[j];
        aux[j] = w + r;
        __asm__ volatile("" ::: "memory");
        s = when_fnv(s, r ^ w);
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
            s = when_fnv(s, r);
        } else {
            uint64_t r = buf[k];
            s = when_fnv(s, r ^ 0x99ULL);
        }
    }
#endif

    when_put_hex(s);
    return 0;
}
