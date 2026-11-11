/*
 * replay_partial_v332.c -- RP01 (LSU v3.3.2) partial-overlap store->load
 * workload.
 *
 * Goal: deterministically produce >=5 distinct PartialAddrRangeCoverage
 * store->load events (LSQUnit::read() partial branch, lsq_unit.cc:1993).
 *
 * Geometry per iteration i (i = 0 .. 255):
 *   - an 8-byte store at  buf + 8*i        covers bytes [8i, 8i+8)
 *   - a 4-byte load  at  buf + 8*i + 6     covers bytes [8i+6, 8i+10)
 * The load's range is NOT contained in the store's range (2 bytes overlap,
 * 2 bytes outside), so lsq_unit.cc computes PartialAddrRangeCoverage, not
 * FullAddrRangeCoverage. A 4-byte load at +2 would be fully covered by the
 * 8-byte store and would NOT take the partial branch.
 *
 * The stored value depends on a long multiply/xor chain so the store data
 * is not ready for ~tens of cycles; the load address is ready immediately,
 * so the load executes while the 8-byte store is still in the store queue
 * (not completed) -- the partial-forward reschedule event RP01 selects.
 * The loaded 4 bytes feed the checksum, so a corrupted load is observable
 * through the application oracle.
 *
 * Deterministic: fixed loop count, no randomness, no input, no threads.
 */
#include <stdint.h>
#include <stdio.h>

#define NITER 256
#define CHAIN 16

static volatile uint8_t buf[NITER * 8 + 16] __attribute__((aligned(64)));

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
main(int argc, char **argv)
{
    (void)argv;
    /* Runtime-derived seed keeps the compiler from constant-folding the
     * chain (argc is 1 in both the SE and the host run, but the compiler
     * cannot rely on it). */
    uint64_t seed = 0x9E3779B97F4A7C15ULL ^ (uint64_t)argc;
    uint64_t s = 0;

    for (unsigned i = 0; i < NITER; i++) {
        uint64_t d = ((uint64_t)i * 0x9E3779B97F4A7C15ULL) ^ seed;

        /* Long dependent chain: the 8-byte store's data is not ready for
         * many cycles, keeping the store in the SQ while the younger load
         * executes. */
        for (unsigned k = 0; k < CHAIN; k++) {
            d ^= d >> 30;
            d *= 0xBF58476D1CE4E5B9ULL;
            d ^= d >> 27;
        }

        /* 8-byte store at buf + 8*i */
        *((volatile uint64_t *)(void *)(buf + i * 8)) = d;

        asm volatile("" ::: "memory");

        /* 4-byte load at buf + 8*i + 6: overlaps the store in its last
         * 2 bytes only -> PartialAddrRangeCoverage. */
        uint32_t w = *((volatile uint32_t *)(void *)(buf + i * 8 + 6));

        s ^= w;
        s *= 1099511628211ULL;
    }

    printf("checksum=0x%016llx\n",
           (unsigned long long)(s ^ fnv1a((const void *)buf, sizeof buf)));
    return 0;
}
