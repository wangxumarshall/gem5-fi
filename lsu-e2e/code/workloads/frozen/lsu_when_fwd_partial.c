/* lsu_when_fwd_partial.c — FW05 When-v2 contexts (Sheet 15, W8).
 *
 * FW05's frozen implementation selects between an older and a younger
 * same-address store candidate at a full-coverage forward.  Each context
 * keeps several real store candidates in the SQ and varies only the
 * consumption/speculation conditions:
 *   C01 baseline: three older candidates then a load
 *   C02 changed dynamic distance / candidate count
 *   C03 forwarded value overwritten; post-drain reload consumed
 *   C04 forwarded value feeds a second address/consumer
 *   C05 speculative consumer branch
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
    unsigned i;

    for (i = 0; i < NB; i++) {
        buf[i] = 0;
        aux[i] = 0x8000ULL + (uint64_t)i * 0x9e3779b97f4a7c15ULL;
    }
    for (i = 0; i < 4096; i++)
        slow[i] = (uint32_t)when_hash64(i + 17u);

#if CONTEXT == 1
    /* C01: three older stores to the same address, then the load. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        buf[(k + 1u) & (NB - 1u)] = 0x3333333333333333ULL + i;
        __asm__ volatile("" ::: "memory");
        buf[k] = 0x1111111111111111ULL + (uint64_t)i;
        __asm__ volatile("" ::: "memory");
        buf[k] = 0x2222222222222222ULL + (uint64_t)i * 3u;
        __asm__ volatile("" ::: "memory");
        buf[k] = 0x4444444444444444ULL + (uint64_t)i * 5u;
        __asm__ volatile("" ::: "memory");
        s = when_fnv(s, buf[k]);
    }
#elif CONTEXT == 2
    /* C02: same three candidate stores, but additional unrelated stores
     * change the SQ occupancy/dynamic distance. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        buf[(k + 3u) & (NB - 1u)] = 0x7777777777777777ULL + i;
        buf[(k + 5u) & (NB - 1u)] = 0x6666666666666666ULL + i;
        __asm__ volatile("" ::: "memory");
        buf[(k + 1u) & (NB - 1u)] = 0x3333333333333333ULL + i;
        __asm__ volatile("" ::: "memory");
        buf[k] = 0x1111111111111111ULL + (uint64_t)i;
        __asm__ volatile("" ::: "memory");
        buf[k] = 0x2222222222222222ULL + (uint64_t)i * 3u;
        __asm__ volatile("" ::: "memory");
        buf[k] = 0x4444444444444444ULL + (uint64_t)i * 5u;
        __asm__ volatile("" ::: "memory");
        s = when_fnv(s, buf[k]);
    }
#elif CONTEXT == 3
    /* C03: forwarded value overwritten; the drained reload is consumed. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        buf[k] = 0x1111111111111111ULL + (uint64_t)i;
        __asm__ volatile("" ::: "memory");
        buf[k] = 0x2222222222222222ULL + (uint64_t)i * 3u;
        __asm__ volatile("" ::: "memory");
        uint64_t r = buf[k];
        __asm__ volatile("" : "+r"(r) : : "memory");
        r = 0x5a5a5a5a5a5a5a5aULL;
        __asm__ volatile("dmb ish" ::: "memory");
        uint64_t good = buf[k];
        s = when_fnv(s, r ^ good);
    }
#elif CONTEXT == 4
    /* C04: forwarded value indexes the next access. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        buf[k] = 0x1111111111111111ULL + (uint64_t)i;
        __asm__ volatile("" ::: "memory");
        buf[k] = 0x2222222222222222ULL + (uint64_t)i * 3u;
        __asm__ volatile("" ::: "memory");
        uint64_t r = buf[k];
        unsigned j = (unsigned)((r >> 6) & (NB - 1u));
        uint64_t w = aux[j];
        aux[j] = w ^ r;
        __asm__ volatile("" ::: "memory");
        s = when_fnv(s, r ^ w);
    }
#else
    /* C05: speculative consumer with the same candidate pair. */
    for (i = 0; i < N; i++) {
        unsigned k = i & (NB - 1u);
        buf[k] = 0x1111111111111111ULL + (uint64_t)i;
        __asm__ volatile("" ::: "memory");
        buf[k] = 0x2222222222222222ULL + (uint64_t)i * 3u;
        __asm__ volatile("" ::: "memory");
        uint32_t c = slow[(i * 43u) & 4095u];
        if (c & 1u) {
            uint64_t r = buf[k];
            s = when_fnv(s, r);
        } else {
            uint64_t r = buf[k];
            s = when_fnv(s, r ^ 0x77ULL);
        }
    }
#endif

    when_put_hex(s);
    return 0;
}
