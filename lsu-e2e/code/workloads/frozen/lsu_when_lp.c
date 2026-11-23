/* lsu_when_lp.c — LP01 When-v2 contexts (Sheet 15, W5).
 *
 * LP01 corrupts byte lane 0 of an L1D load response.  Every context issues
 * real data loads; only width/alignment, consumption, dependency and
 * speculation change.
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
    unsigned i;

    for (i = 0; i < NB; i++) {
        a[i] = 0x5000ULL + (uint64_t)i * 0x9e3779b97f4a7c15ULL;
        aux[i] = 0x9000ULL + (uint64_t)i * 0xbf58476d1ce4e5b9ULL;
    }
    for (i = 0; i < 4096; i++)
        cold[i] = (uint32_t)when_hash64(i + 3u);

#if CONTEXT == 1
    /* C01: baseline 8-byte load responses consumed directly. */
    for (i = 0; i < N; i++)
        s = when_fnv(s, a[i]);
#elif CONTEXT == 2
    /* C02: changed access width/alignment; still data-load responses. */
    for (i = 0; i < N; i++) {
        uint32_t w = *(volatile uint32_t *)(void *)((const volatile char *)a
                                                    + (uint64_t)i * 4u);
        uint64_t v = *(volatile uint64_t *)(void *)((const volatile char *)a
                                                    + (uint64_t)i * 8u + 8u);
        s = when_fnv(s, (uint64_t)w ^ v);
    }
#elif CONTEXT == 3
    /* C03: response value overwritten before any consumer. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        __asm__ volatile("" : "+r"(v) : : "memory");
        v = 0x6b6b6b6b6b6b6b6bULL;
        s = when_fnv(s, v);
    }
#elif CONTEXT == 4
    /* C04: load result feeds a second address and a multilevel consumer. */
    for (i = 0; i < N; i++) {
        uint64_t v = a[i];
        unsigned j = (unsigned)((v >> 3) & (NB - 1u));
        uint64_t w = aux[j];
        aux[j] = w ^ v;
        s = when_fnv(s, w ^ v);
    }
#else
    /* C05: speculated load on an unpredictable cold-conditioned branch. */
    for (i = 0; i < N; i++) {
        uint32_t c = cold[(i * 53u) & 4095u];
        if (c & 1u) {
            uint64_t v = a[i];
            s = when_fnv(s, v);
        } else {
            uint64_t v = a[(i + 1u) & (NB - 1u)];
            s = when_fnv(s, v ^ 0x33ULL);
        }
    }
#endif

    when_put_hex(s);
    return 0;
}
