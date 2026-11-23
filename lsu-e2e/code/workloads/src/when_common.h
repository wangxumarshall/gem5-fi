/* when_common.h — E2E-instrumented shared helpers.
 *
 * Identical arithmetic semantics to the frozen When-v2 header.  The only
 * addition is a read-free software marker: every event writes four values
 * into the reserved architectural register x28 with plain `mov` instructions.
 *
 * Why this is non-invasive:
 *   * the workloads are compiled with -ffixed-x28, so the compiler never
 *     allocates x28 for program state; the marker cannot perturb a live
 *     application value.
 *   * the marker emits only ALU instructions.  It performs no load and no
 *     store, so it cannot enter any LSU injector's eligible-event stream and
 *     cannot perturb an LSU queue, forward, replay or cache event.
 *   * gem5's read-only CHAOSCommitTrace v2 records, for each committed
 *     instruction, its DynInst seqNum, PC, opcode and destination value.
 *     The four `mov x28` rows therefore carry a real dynamic-instruction
 *     identity for every software event.
 *
 * Marker payload: (tag, a, b, c).
 *   tag = type[63:56] | site[55:32] | sequence[31:0]
 * The sequence is a register-resident counter owned by main(), so it adds no
 * memory traffic either.
 */
#ifndef LSU_WHEN_COMMON_H
#define LSU_WHEN_COMMON_H

#include <stdint.h>
#include <stddef.h>

#ifndef CONTEXT
#define CONTEXT 1
#endif

/* ---- marker event types ------------------------------------------------ */
#define SW_LOAD   0x11
#define SW_STORE  0x12
#define SW_HASH   0x13
#define SW_BRANCH 0x14
#define SW_OUTPUT 0x15
#define SW_PHASE  0x16
#define SW_VALUE  0x17
#define SW_CHECK  0x18

#define SW_TAG(type, site, seq) \
    ((((uint64_t)(type)) << 56) | (((uint64_t)(site)) << 32) | \
     ((uint64_t)(seq) & 0xffffffffULL))

static inline __attribute__((always_inline)) void
sw_mark4(uint64_t tag, uint64_t a, uint64_t b, uint64_t c)
{
    register uint64_t r0 __asm__("x0") = tag;
    register uint64_t r1 __asm__("x1") = a;
    register uint64_t r2 __asm__("x2") = b;
    register uint64_t r3 __asm__("x3") = c;
    __asm__ volatile("mov x28, %0\n\t"
                     "mov x28, %1\n\t"
                     "mov x28, %2\n\t"
                     "mov x28, %3\n\t"
                     :: "r"(r0), "r"(r1), "r"(r2), "r"(r3)
                     : "x28", "memory");
}

#define SW_EV(ev, type, site, a, b, c) \
    do { \
        sw_mark4(SW_TAG((type), (site), (ev)), \
                 (uint64_t)(a), (uint64_t)(b), (uint64_t)(c)); \
        (ev)++; \
    } while (0)

/* aux encodings for LOAD/STORE events: iteration in the high word. */
#define SW_AUX(iter, extra) \
    ((((uint64_t)(iter)) << 32) | ((uint64_t)(extra) & 0xffffffffULL))

/* ---- original arithmetic helpers (unchanged) --------------------------- */
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
    register long x2 __asm__("x2") = len;
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
