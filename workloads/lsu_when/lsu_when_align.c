/* lsu_when_align.c — DA04 When-v2 contexts (Sheet 15, W8).
 *
 * DA04's frozen rule is a 4-byte store byte-enable mask with lane 0
 * cleared (`chaos_da04::eligible`: size == 4 and a full mask).  Every
 * context therefore performs real 4-byte stores; only offset/width
 * variation, overwrite, dependency and control consumption change.
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
    unsigned i;

    for (i = 0; i < NB * 4u + 64u; i++)
        area[i] = (uint8_t)(i * 7u + 3u);
    for (i = 0; i < 128; i++)
        aux[i] = 0xa000ULL + (uint64_t)i * 0x9e3779b97f4a7c15ULL;

#if CONTEXT == 1
    /* C01: aligned 4-byte store, barrier, same-address 4-byte reload. */
    for (i = 0; i < N; i++) {
        uint32_t v = (uint32_t)(i * 2654435761u);
        *(volatile uint32_t *)(void *)(area + i * 4u) = v;
        __asm__ volatile("dmb ish" ::: "memory");
        uint32_t r = *(volatile uint32_t *)(void *)(area + i * 4u);
        s = when_fnv(s, r);
    }
#elif CONTEXT == 2
    /* C02: changed legal access shape: unaligned 4-byte stores at +1,
     * still a full 4-byte byte-enable mask. */
    for (i = 0; i < N; i++) {
        uint32_t v = (uint32_t)(i * 2246822519u + 1u);
        *(volatile uint32_t *)(void *)(area + i * 4u + 1u) = v;
        __asm__ volatile("dmb ish" ::: "memory");
        uint32_t r = *(volatile uint32_t *)(void *)(area + i * 4u + 1u);
        s = when_fnv(s, r);
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
        s = when_fnv(s, r);
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
        s = when_fnv(s, (uint64_t)r ^ y);
    }
#else
    /* C05: control consumer after the store's memory effect is visible;
     * a committed store is never treated as reversible. */
    for (i = 0; i < N; i++) {
        uint32_t v = (uint32_t)(i * 2654435761u);
        *(volatile uint32_t *)(void *)(area + i * 4u) = v;
        __asm__ volatile("dmb ish" ::: "memory");
        uint32_t r = *(volatile uint32_t *)(void *)(area + i * 4u);
        if (r & 8u)
            s = when_fnv(s, r);
        else
            s = when_fnv(s, r ^ 0x1u);
    }
#endif

    when_put_hex(s);
    return 0;
}
