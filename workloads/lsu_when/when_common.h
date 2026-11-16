/* when_common.h — shared helpers for the LSU When-v2 5x3 context workloads.
 *
 * Every variant is a freestanding-style, deterministic AArch64 SE program
 * compiled with the host gcc (-O2 -static).  The only output is
 * "checksum=0x%016llx\n" on stdout; a missing or different line is an oracle
 * failure.  CONTEXT (1..5) selects the Sheet-15 scenario.
 */
#ifndef LSU_WHEN_COMMON_H
#define LSU_WHEN_COMMON_H

#include <stdint.h>
#include <stddef.h>

#ifndef CONTEXT
#define CONTEXT 1
#endif

static inline uint64_t
when_fnv(uint64_t h, uint64_t v)
{
    for (int b = 0; b < 8; b++) {
        h ^= (v >> (8 * b)) & 0xffu;
        h *= 1099511628211ULL;
    }
    return h;
}

static inline uint64_t
when_fnv_bytes(const volatile uint8_t *p, size_t n)
{
    uint64_t h = 1469598103934665603ULL;
    for (size_t i = 0; i < n; i++) {
        h ^= p[i];
        h *= 1099511628211ULL;
    }
    return h;
}

/* Linux AArch64 raw write(2): x0=fd, x1=buf, x2=len, x8=64.  No libc. */
static inline long
when_write(long fd, const void *buf, unsigned long len)
{
    register long x0 __asm__("x0") = fd;
    register long x1 __asm__("x1") = (long)buf;
    register long x2 __asm__("x2") = (long)len;
    register long x8 __asm__("x8") = 64;
    __asm__ volatile("svc #0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x8)
                     : "memory", "cc");
    return x0;
}

static inline void
when_put_hex(uint64_t v)
{
    char buf[16];
    for (int i = 15; i >= 0; --i) {
        unsigned d = (unsigned)(v & 0xf);
        buf[i] = d < 10 ? (char)('0' + d) : (char)('a' + d - 10);
        v >>= 4;
    }
    (void)when_write(1, buf, 16);
    (void)when_write(1, "\n", 1);
}

/* Deterministic pseudo-random bit used by the C05 speculation scenes. */
static inline uint64_t
when_hash64(uint64_t x)
{
    x ^= x >> 30;
    x *= 0xbf58476d1ce4e5b9ULL;
    x ^= x >> 27;
    x *= 0x94d049bb133111ebULL;
    x ^= x >> 31;
    return x;
}

#endif
