/*
 * md04_violations_v332.c — LSU v3.3.2 P0-3 / MD04 context workload.
 *
 * Goal: produce >= 5 eligible store->younger-load memory-dependence
 * violation pairs inside main (v3.3.1 replay_dependency had N_ROI = 1).
 *
 * Mechanism exploited (source-verified):
 *   - LSQUnit::read() skips an older store whose SQEntry::size() == 0,
 *     and SQEntry::size() is only set in LSQUnit::write() when the store
 *     actually executes (lsq_unit.cc:2107).  A younger load therefore
 *     executes past an older same-address store that has not executed yet.
 *   - When that store later executes, LSQUnit::executeStore ->
 *     checkViolations() sees the younger load with a valid effective
 *     address and reports the store->load violation (M5PanicFault), which
 *     is exactly the MD04 hook site.
 *
 * To make the race repeat every iteration instead of occasionally, the
 * store's *data* depends on a load from a 1 MiB array (cold/L2 traffic,
 * long latency) while the younger load's address only depends on the loop
 * index (ready immediately).  The result is a late store and an early
 * younger load, i.e. a real violation on essentially every iteration.
 *
 * Several loops with distinct store/load PCs and varied offsets/sizes are
 * used so the eligible-pair census has multiple distinct contexts.  The
 * StoreSet predictor (mem_dep_unit/store_set) trains one (store PC, load
 * PC) pair after its first violation, which makes each distinct pair worth
 * about one eligible event; the workload therefore needs >= 5 distinct
 * in-main pairs:
 *   L1: 8B store buf_a[i]             -> 8B younger load buf_a[i]
 *   L2: 8B store buf_b[i*2+1]         -> 16B younger __int128 load buf_b[i*2]
 *   L3: 8B unaligned store c5[i*16+4] -> 8B younger load c5[i*16] (4B overlap)
 *   L4: 8B store buf_d[k]             -> 8B younger load buf_d[k] (late addr)
 *   L5: 8B store buf_b[i]             -> 16B younger __int128 load buf_b[i]
 *   L6: 8B store buf_a2[k]            -> 8B younger load buf_a2[k] (late addr)
 *   L7: 8B unaligned store c5[i*16+2] -> 8B younger load c5[i*16+8] (2B overlap)
 *   L8: 8B store buf_a[i+1]           -> 16B younger __int128 load buf_a[i]
 *
 * All arrays are volatile so -O2 keeps every access; memory barriers keep
 * the store before the younger load at the source level (the race is a
 * hardware ordering event, not a compiler reordering).
 */

#include <stdio.h>
#include <stdint.h>
#include <stddef.h>

#define SMALL 256u           /* 2 KiB : L1D-resident store/load target   */
#define BIG   16384u         /* 128 KiB : late-data source (L2/DRAM)     */

static volatile uint64_t src_big[BIG];
static volatile uint64_t buf_a[SMALL];
static volatile uint64_t buf_b[SMALL];
static volatile unsigned char buf_c[SMALL * 8u];
static volatile uint64_t buf_d[SMALL];
static volatile uint64_t idx_d[SMALL];
static volatile uint64_t buf_e[SMALL];
static volatile uint64_t idx_e[SMALL];

static uint64_t
fnv1a(const void *p, size_t n)
{
    const uint8_t *b = (const uint8_t *)p;
    uint64_t h = 1469598103934665603ULL;
    for (size_t i = 0; i < n; i++) {
        h ^= b[i];
        h *= 1099511628211ULL;
    }
    return h;
}

int
main(void)
{
    /* Deterministic input construction (16B stores: not MD04-eligible). */
    for (uint64_t i = 0; i < BIG; i++)
        src_big[i] = (i * 0x9E3779B97F4A7C15ULL) ^ (i >> 7);
    for (uint64_t i = 0; i < SMALL; i++) {
        buf_a[i] = i;
        buf_b[i] = ~i;
        buf_d[i] = 0;
        idx_d[i] = (i * 13u + 7u) & (SMALL - 1u);
        buf_e[i] = 0;
        idx_e[i] = (i * 29u + 11u) & (SMALL - 1u);
    }
    for (uint64_t i = 0; i < SMALL * 8u; i++)
        buf_c[i] = (unsigned char)i;

    uint64_t sum = 0;

    /* L1: exact 8B/8B same-address pair, late store data. */
    for (int r = 0; r < 4; r++) {
        for (uint64_t i = 0; i < SMALL; i++) {
            uint64_t v = src_big[(i * 7919u + (uint64_t)r * 104729u)
                                 & (BIG - 1u)];
            buf_a[i] = v;                       /* older store (late data) */
            __asm__ __volatile__("" ::: "memory");
            sum += buf_a[i];                    /* younger load (early addr) */
            __asm__ __volatile__("" ::: "memory");
        }
    }

    /* L2: 8B store at odd slot, 16B younger load covering two slots. */
    for (int r = 0; r < 4; r++) {
        for (uint64_t i = 0; i + 1 < SMALL; i += 2) {
            uint64_t v = src_big[(i * 6151u + (uint64_t)r * 65537u + 3u)
                                 & (BIG - 1u)];
            buf_b[i + 1] = v;                   /* 8B store at buf_b[i+1]  */
            __asm__ __volatile__("" ::: "memory");
            unsigned __int128 pair =
                *(volatile unsigned __int128 *)(void *)&buf_b[i];
            sum += (uint64_t)pair + (uint64_t)(pair >> 64);
            __asm__ __volatile__("" ::: "memory");
        }
    }

    /* L3: unaligned 8B store overlapping the low 4 bytes of an 8B load. */
    for (int r = 0; r < 4; r++) {
        for (uint64_t i = 0; i + 16 < SMALL * 8u; i += 16) {
            uint64_t v = src_big[(i * 4099u + (uint64_t)r * 32771u + 5u)
                                 & (BIG - 1u)];
            *(volatile uint64_t *)(void *)&buf_c[i + 4] = v;  /* +4 unaligned */
            __asm__ __volatile__("" ::: "memory");
            sum += *(volatile uint64_t *)(void *)&buf_c[i];   /* low 8B */
            __asm__ __volatile__("" ::: "memory");
        }
    }

    /* L4: store value from big array, address from idx_d (also loaded). */
    for (int r = 0; r < 4; r++) {
        for (uint64_t i = 0; i < SMALL; i++) {
            uint64_t k = idx_d[i];
            uint64_t v = src_big[(i * 3571u + (uint64_t)r * 45007u + 9u)
                                 & (BIG - 1u)];
            buf_d[k] = v;                       /* older store (late data) */
            __asm__ __volatile__("" ::: "memory");
            sum += buf_d[k];                    /* younger load */
            __asm__ __volatile__("" ::: "memory");
        }
    }

    /* L5: 8B store in buf_b, 16B younger load covering it (same slot). */
    for (int r = 0; r < 4; r++) {
        for (uint64_t i = 0; i + 1 < SMALL; i++) {
            uint64_t v = src_big[(i * 5449u + (uint64_t)r * 20011u + 13u)
                                 & (BIG - 1u)];
            buf_b[i] = v;                       /* older 8B store */
            __asm__ __volatile__("" ::: "memory");
            unsigned __int128 pair =
                *(volatile unsigned __int128 *)(void *)&buf_b[i];
            sum += (uint64_t)pair + (uint64_t)(pair >> 64);
            __asm__ __volatile__("" ::: "memory");
        }
    }

    /* L6: second late-address loop (different PCs and arrays). */
    for (int r = 0; r < 4; r++) {
        for (uint64_t i = 0; i < SMALL; i++) {
            uint64_t k = idx_e[i];
            uint64_t v = src_big[(i * 9001u + (uint64_t)r * 30011u + 17u)
                                 & (BIG - 1u)];
            buf_e[k] = v;                       /* older store (late data) */
            __asm__ __volatile__("" ::: "memory");
            sum += buf_e[k];                    /* younger load */
            __asm__ __volatile__("" ::: "memory");
        }
    }

    /* L7: 8B unaligned store at +2 overlaps the tail of an 8B load at +8. */
    for (int r = 0; r < 4; r++) {
        for (uint64_t i = 0; i + 16 < SMALL * 8u; i += 16) {
            uint64_t v = src_big[(i * 2357u + (uint64_t)r * 12347u + 19u)
                                 & (BIG - 1u)];
            *(volatile uint64_t *)(void *)&buf_c[i + 2] = v;  /* +2 unaligned */
            __asm__ __volatile__("" ::: "memory");
            sum += *(volatile uint64_t *)(void *)&buf_c[i + 8];  /* 2B overlap */
            __asm__ __volatile__("" ::: "memory");
        }
    }

    /* L8: 8B store at slot i+1, 16B younger load starting at slot i. */
    for (int r = 0; r < 4; r++) {
        for (uint64_t i = 0; i + 1 < SMALL; i++) {
            uint64_t v = src_big[(i * 7001u + (uint64_t)r * 50021u + 23u)
                                 & (BIG - 1u)];
            buf_a[i + 1] = v;                   /* older 8B store */
            __asm__ __volatile__("" ::: "memory");
            unsigned __int128 pair =
                *(volatile unsigned __int128 *)(void *)&buf_a[i];
            sum += (uint64_t)pair + (uint64_t)(pair >> 64);
            __asm__ __volatile__("" ::: "memory");
        }
    }

    uint64_t digest = 0;
    digest ^= fnv1a((const void *)buf_a, sizeof(buf_a));
    digest ^= fnv1a((const void *)buf_b, sizeof(buf_b));
    digest ^= fnv1a((const void *)buf_c, sizeof(buf_c));
    digest ^= fnv1a((const void *)buf_d, sizeof(buf_d));
    digest ^= fnv1a((const void *)buf_e, sizeof(buf_e));
    printf("checksum=0x%016llx\n",
           (unsigned long long)(sum ^ digest));
    return 0;
}
