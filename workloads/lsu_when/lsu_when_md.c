/* lsu_when_md.c — MD04/RP01 When-v2 contexts (Sheet 15, W7).
 *
 * Every variant carries two independent real-event families so both frozen
 * hooks can select their own eligible stream:
 *   * eight distinct full-coverage older-store / younger-load pairs whose
 *     late store data and early load address create real LSQ violations
 *     (MD04; distinct PCs are required because StoreSet trains a pair after
 *     its first violation);
 *   * partial-coverage store->load forwards (8-byte store, 4-byte load at
 *     +6) whose replay reschedule can be suppressed (RP01).
 *
 * Contexts change consumption, distance/occupancy, overwrite and control
 * speculation only; the access geometry above is kept.
 */
#include "when_common.h"

#define SMALL 64u
#define BIG 8192u

static volatile uint64_t big[BIG] __attribute__((aligned(4096)));
static volatile uint64_t a[SMALL] __attribute__((aligned(4096)));
static volatile uint64_t b[SMALL] __attribute__((aligned(4096)));
static volatile uint64_t d[SMALL] __attribute__((aligned(4096)));
static volatile uint64_t e[SMALL] __attribute__((aligned(4096)));
static volatile uint64_t idxd[SMALL] __attribute__((aligned(4096)));
static volatile uint64_t idxe[SMALL] __attribute__((aligned(4096)));
static volatile uint64_t aux[SMALL] __attribute__((aligned(4096)));
static volatile uint8_t cbuf[SMALL * 8u] __attribute__((aligned(4096)));

static inline uint64_t
late_value(unsigned i, unsigned r)
{
    uint64_t v = big[(i * 7919u + r * 104729u) & (BIG - 1u)];
    v ^= v >> 29;
    v *= 0xbf58476d1ce4e5b9ULL;
    v ^= v >> 32;
    return v;
}

#if CONTEXT == 3
#define WHEN_CONSUME(_x) do { \
        uint64_t _v = (_x); \
        __asm__ volatile("" : "+r"(_v) : : "memory"); \
        _v = 0x3c3c3c3c3c3c3c3cULL; \
        s = when_fnv(s, _v); } while (0)
#elif CONTEXT == 4
#define WHEN_CONSUME(_x) do { \
        uint64_t _v = (_x); \
        unsigned _j = (unsigned)((_v >> 6) & (SMALL - 1u)); \
        uint64_t _y = aux[_j]; \
        aux[_j] = _y ^ _v; \
        s = when_fnv(s, _v ^ _y); } while (0)
#elif CONTEXT == 5
#define WHEN_CONSUME(_x) do { \
        uint64_t _v = (_x); \
        if (when_hash64(_v) & 1ull) s = when_fnv(s, _v); \
        else s = when_fnv(s, _v ^ 0x99ULL); } while (0)
#else
#define WHEN_CONSUME(_x) do { \
        uint64_t _v = (_x); \
        s = when_fnv(s, _v); } while (0)
#endif

int
main(void)
{
    uint64_t s = 0x9e3779b97f4a7c15ULL ^ (uint64_t)CONTEXT;
    unsigned r, i;

    for (i = 0; i < BIG; i++)
        big[i] = when_hash64((uint64_t)i ^ 0x5a5a5a5a5a5a5a5aULL);
    for (i = 0; i < SMALL; i++) {
        a[i] = 0; b[i] = 0; d[i] = 0; e[i] = 0;
        idxd[i] = (i * 13u + 7u) & (SMALL - 1u);
        idxe[i] = (i * 29u + 11u) & (SMALL - 1u);
        aux[i] = 0x4000ULL + (uint64_t)i * 0x9e3779b97f4a7c15ULL;
    }
    for (i = 0; i < SMALL * 8u; i++)
        cbuf[i] = (uint8_t)i;

    for (r = 0; r < 2; r++) {
        /* L1: exact 8B/8B same-address pair, late store data. */
        for (i = 0; i < SMALL; i++) {
            uint64_t v = late_value(i, r);
            a[i] = v;
            __asm__ volatile("" ::: "memory");
            WHEN_CONSUME(a[i]);
            __asm__ volatile("" ::: "memory");
        }
        /* L2: 8B store at odd slot, 16B younger load. */
        for (i = 0; i + 1 < SMALL; i += 2) {
            uint64_t v = late_value(i + 1u, r + 3u);
            b[i + 1] = v;
            __asm__ volatile("" ::: "memory");
            unsigned __int128 pair =
                *(volatile unsigned __int128 *)(void *)&b[i];
            WHEN_CONSUME((uint64_t)pair);
            WHEN_CONSUME((uint64_t)(pair >> 64));
        }
        /* L3: unaligned 8B store overlapping the low 4 bytes of an 8B load. */
        for (i = 0; i + 16 < SMALL * 8u; i += 16) {
            uint64_t v = late_value(i, r + 5u);
            *(volatile uint64_t *)(void *)&cbuf[i + 4] = v;
            __asm__ volatile("" ::: "memory");
            WHEN_CONSUME(*(volatile uint64_t *)(void *)&cbuf[i]);
        }
        /* L4: store value from big, address from idxd. */
        for (i = 0; i < SMALL; i++) {
            uint64_t k = idxd[i];
            uint64_t v = late_value(i, r + 7u);
            d[k] = v;
            __asm__ volatile("" ::: "memory");
            WHEN_CONSUME(d[k]);
        }
        /* L5: 8B store in b, 16B younger load covering it. */
        for (i = 0; i + 1 < SMALL; i++) {
            uint64_t v = late_value(i, r + 9u);
            b[i] = v;
            __asm__ volatile("" ::: "memory");
            unsigned __int128 pair =
                *(volatile unsigned __int128 *)(void *)&b[i];
            WHEN_CONSUME((uint64_t)pair);
            WHEN_CONSUME((uint64_t)(pair >> 64));
        }
        /* L6: second late-address loop. */
        for (i = 0; i < SMALL; i++) {
            uint64_t k = idxe[i];
            uint64_t v = late_value(i, r + 11u);
            e[k] = v;
            __asm__ volatile("" ::: "memory");
            WHEN_CONSUME(e[k]);
        }
        /* L7: unaligned store at +2, load at +8 (2B overlap). */
        for (i = 0; i + 16 < SMALL * 8u; i += 16) {
            uint64_t v = late_value(i, r + 13u);
            *(volatile uint64_t *)(void *)&cbuf[i + 2] = v;
            __asm__ volatile("" ::: "memory");
            WHEN_CONSUME(*(volatile uint64_t *)(void *)&cbuf[i + 8]);
        }
        /* L8: 8B store at i+1, 16B younger load at i. */
        for (i = 0; i + 1 < SMALL; i++) {
            uint64_t v = late_value(i, r + 15u);
            a[i + 1] = v;
            __asm__ volatile("" ::: "memory");
            unsigned __int128 pair =
                *(volatile unsigned __int128 *)(void *)&a[i];
            WHEN_CONSUME((uint64_t)pair);
            WHEN_CONSUME((uint64_t)(pair >> 64));
        }

        /* Partial-coverage family for RP01: 8B store, 4B load at +6. */
        for (i = 0; i < SMALL * 4u; i++) {
            uint64_t v = late_value(i, r + 17u);
            *(volatile uint64_t *)(void *)(cbuf + i * 8u) = v;
            __asm__ volatile("" ::: "memory");
            WHEN_CONSUME(*(volatile uint32_t *)(void *)(cbuf + i * 8u + 6u));
            __asm__ volatile("" ::: "memory");
        }
    }

    when_put_hex(s);
    return 0;
}
