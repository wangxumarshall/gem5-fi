/* lsu_when_md.c — MD04/RP01 When-v2 contexts (Sheet 15, W7).
 *
 * E2E instrumented variant.  Marker discipline: every store marker is
 * emitted after the dependent load/consume, so the violation and
 * partial-coverage windows are not widened by observation code.
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
#define WHEN_CONSUME_EV(ev, _x, _b, _it) do { \
        uint64_t _v = (_x); \
        SW_EV(ev, SW_VALUE, (_b) + 2, _v, 0, SW_AUX(_it, 0)); \
        _v = 0x3c3c3c3c3c3c3c3cULL; \
        SW_EV(ev, SW_VALUE, (_b) + 3, _v, 0, SW_AUX(_it, 0)); \
        uint64_t _hb = s; \
        s = when_fnv(s, _v); \
        SW_EV(ev, SW_HASH, (_b) + 4, _v, _hb, s); } while (0)
#elif CONTEXT == 4
#define WHEN_CONSUME_EV(ev, _x, _b, _it) do { \
        uint64_t _v = (_x); \
        unsigned _j = (unsigned)((_v >> 6) & (SMALL - 1u)); \
        uint64_t _y = aux[_j]; \
        SW_EV(ev, SW_LOAD, (_b) + 2, (uint64_t)&aux[_j], _y, \
              SW_AUX(_it, _j)); \
        aux[_j] = _y ^ _v; \
        SW_EV(ev, SW_STORE, (_b) + 3, (uint64_t)&aux[_j], _y ^ _v, \
              SW_AUX(_it, 8)); \
        uint64_t _hb = s; \
        s = when_fnv(s, _v ^ _y); \
        SW_EV(ev, SW_HASH, (_b) + 4, _v ^ _y, _hb, s); } while (0)
#elif CONTEXT == 5
#define WHEN_CONSUME_EV(ev, _x, _b, _it) do { \
        uint64_t _v = (_x); \
        uint64_t _c = when_hash64(_v) & 1ull; \
        if (_c) { \
            uint64_t _hb = s; \
            s = when_fnv(s, _v); \
            SW_EV(ev, SW_HASH, (_b) + 3, _v, _hb, s); \
        } else { \
            uint64_t _hb = s; \
            s = when_fnv(s, _v ^ 0x99ULL); \
            SW_EV(ev, SW_HASH, (_b) + 4, _v ^ 0x99ULL, _hb, s); \
        } \
        SW_EV(ev, SW_BRANCH, (_b) + 2, _v, _c, SW_AUX(_it, 0)); } while (0)
#else
#define WHEN_CONSUME_EV(ev, _x, _b, _it) do { \
        uint64_t _v = (_x); \
        uint64_t _hb = s; \
        s = when_fnv(s, _v); \
        SW_EV(ev, SW_HASH, (_b) + 2, _v, _hb, s); } while (0)
#endif

int
main(void)
{
    uint64_t s = 0x9e3779b97f4a7c15ULL ^ (uint64_t)CONTEXT;
    uint64_t ev = 0;
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

    SW_EV(ev, SW_PHASE, 1, 8, 0, 0);

    for (r = 0; r < 2; r++) {
        /* L1: exact 8B/8B same-address pair, late store data. */
        for (i = 0; i < SMALL; i++) {
            uint64_t v = late_value(i, r);
            a[i] = v;
            __asm__ volatile("" ::: "memory");
            uint64_t lv = a[i];
            SW_EV(ev, SW_LOAD, 101, (uint64_t)&a[i], lv, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 100, (uint64_t)&a[i], v, SW_AUX(i, 8));
            WHEN_CONSUME_EV(ev, lv, 100, i);
            __asm__ volatile("" ::: "memory");
        }
        /* L2: 8B store at odd slot, 16B younger load. */
        for (i = 0; i + 1 < SMALL; i += 2) {
            uint64_t v = late_value(i + 1u, r + 3u);
            b[i + 1] = v;
            __asm__ volatile("" ::: "memory");
            unsigned __int128 pair =
                *(volatile unsigned __int128 *)(void *)&b[i];
            uint64_t lo = (uint64_t)pair, hi = (uint64_t)(pair >> 64);
            SW_EV(ev, SW_LOAD, 201, (uint64_t)&b[i], lo, SW_AUX(i, 8));
            SW_EV(ev, SW_LOAD, 202, (uint64_t)&b[i], hi, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 200, (uint64_t)&b[i + 1], v, SW_AUX(i, 8));
            WHEN_CONSUME_EV(ev, lo, 200, i);
            WHEN_CONSUME_EV(ev, hi, 250, i);
        }
        /* L3: unaligned 8B store overlapping the low 4 bytes of an 8B load. */
        for (i = 0; i + 16 < SMALL * 8u; i += 16) {
            uint64_t v = late_value(i, r + 5u);
            *(volatile uint64_t *)(void *)&cbuf[i + 4] = v;
            __asm__ volatile("" ::: "memory");
            uint64_t lv = *(volatile uint64_t *)(void *)&cbuf[i];
            SW_EV(ev, SW_LOAD, 301, (uint64_t)&cbuf[i], lv, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 300, (uint64_t)&cbuf[i + 4], v,
                  SW_AUX(i, 8));
            WHEN_CONSUME_EV(ev, lv, 300, i);
        }
        /* L4: store value from big, address from idxd. */
        for (i = 0; i < SMALL; i++) {
            uint64_t k = idxd[i];
            uint64_t v = late_value(i, r + 7u);
            d[k] = v;
            __asm__ volatile("" ::: "memory");
            uint64_t lv = d[k];
            SW_EV(ev, SW_LOAD, 401, (uint64_t)&d[k], lv, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 400, (uint64_t)&d[k], v, SW_AUX(i, 8));
            WHEN_CONSUME_EV(ev, lv, 400, i);
        }
        /* L5: 8B store in b, 16B younger load covering it. */
        for (i = 0; i + 1 < SMALL; i++) {
            uint64_t v = late_value(i, r + 9u);
            b[i] = v;
            __asm__ volatile("" ::: "memory");
            unsigned __int128 pair =
                *(volatile unsigned __int128 *)(void *)&b[i];
            uint64_t lo = (uint64_t)pair, hi = (uint64_t)(pair >> 64);
            SW_EV(ev, SW_LOAD, 501, (uint64_t)&b[i], lo, SW_AUX(i, 8));
            SW_EV(ev, SW_LOAD, 502, (uint64_t)&b[i], hi, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 500, (uint64_t)&b[i], v, SW_AUX(i, 8));
            WHEN_CONSUME_EV(ev, lo, 500, i);
            WHEN_CONSUME_EV(ev, hi, 550, i);
        }
        /* L6: second late-address loop. */
        for (i = 0; i < SMALL; i++) {
            uint64_t k = idxe[i];
            uint64_t v = late_value(i, r + 11u);
            e[k] = v;
            __asm__ volatile("" ::: "memory");
            uint64_t lv = e[k];
            SW_EV(ev, SW_LOAD, 601, (uint64_t)&e[k], lv, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 600, (uint64_t)&e[k], v, SW_AUX(i, 8));
            WHEN_CONSUME_EV(ev, lv, 600, i);
        }
        /* L7: unaligned store at +2, load at +8 (2B overlap). */
        for (i = 0; i + 16 < SMALL * 8u; i += 16) {
            uint64_t v = late_value(i, r + 13u);
            *(volatile uint64_t *)(void *)&cbuf[i + 2] = v;
            __asm__ volatile("" ::: "memory");
            uint64_t lv = *(volatile uint64_t *)(void *)&cbuf[i + 8];
            SW_EV(ev, SW_LOAD, 701, (uint64_t)&cbuf[i + 8], lv,
                  SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 700, (uint64_t)&cbuf[i + 2], v,
                  SW_AUX(i, 8));
            WHEN_CONSUME_EV(ev, lv, 700, i);
        }
        /* L8: 8B store at i+1, 16B younger load at i. */
        for (i = 0; i + 1 < SMALL; i++) {
            uint64_t v = late_value(i, r + 15u);
            a[i + 1] = v;
            __asm__ volatile("" ::: "memory");
            unsigned __int128 pair =
                *(volatile unsigned __int128 *)(void *)&a[i];
            uint64_t lo = (uint64_t)pair, hi = (uint64_t)(pair >> 64);
            SW_EV(ev, SW_LOAD, 801, (uint64_t)&a[i], lo, SW_AUX(i, 8));
            SW_EV(ev, SW_LOAD, 802, (uint64_t)&a[i], hi, SW_AUX(i, 8));
            SW_EV(ev, SW_STORE, 800, (uint64_t)&a[i + 1], v, SW_AUX(i, 8));
            WHEN_CONSUME_EV(ev, lo, 800, i);
            WHEN_CONSUME_EV(ev, hi, 850, i);
        }

        /* Partial-coverage family for RP01: 8B store, 4B load at +6. */
        for (i = 0; i < SMALL * 4u; i++) {
            uint64_t v = late_value(i, r + 17u);
            *(volatile uint64_t *)(void *)(cbuf + i * 8u) = v;
            __asm__ volatile("" ::: "memory");
            uint32_t lv = *(volatile uint32_t *)(void *)(cbuf + i * 8u + 6u);
            SW_EV(ev, SW_LOAD, 901, (uint64_t)(cbuf + i * 8u + 6u), lv,
                  SW_AUX(i, 4));
            SW_EV(ev, SW_STORE, 900, (uint64_t)(cbuf + i * 8u), v,
                  SW_AUX(i, 8));
            WHEN_CONSUME_EV(ev, (uint64_t)lv, 900, i);
            __asm__ volatile("" ::: "memory");
        }
    }

    SW_EV(ev, SW_OUTPUT, 99, s, 0, 0);
    when_put_hex(s);
    return 0;
}
