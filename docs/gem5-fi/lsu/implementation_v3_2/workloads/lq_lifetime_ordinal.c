/* lq_lifetime_ordinal — LQ04 explicit-anchor workload (LSU v3.2.10).
 *
 * Freestanding AArch64 program: no libc, no dynamic loader.  The ELF entry
 * _start (lq_lifetime_ordinal.S) performs the first five data loads of the
 * process — the five anchors A1..A5 of anchor_tbl — and passes them to
 * main(a,b,c,d,e).  Each anchor feeds a different consumer so the five
 * dynamic contexts (PC, address, data, destination register, consumer) stay
 * distinct.
 *
 * Oracle: one stdout line "checksum=0x%016llx\n" whose value is
 * s ^ fnv1a(arr, 4096) (same combination rule as the archived lq_lifetime);
 * main returns that value (discarded by _start, which always exits 0 via
 * the raw exit syscall).  If the 64-byte 0xA5 guard is corrupted the program
 * prints "guard_fail\n", suppresses the checksum line and returns 2, so the
 * oracle fails loudly.  All output goes through the raw write syscall.
 */

#include <stdint.h>
#include <stddef.h>

/* Linux AArch64 raw write(2): fd/buf/len in x0-x2, syscall number 64 in x8.
 * The kernel returns the result in x0 and the error flag in x1. */
static long raw_write(long fd, const void *buf, unsigned long len)
{
    register long x0 __asm__("x0") = fd;
    register long x1 __asm__("x1") = (long)buf;
    register long x2 __asm__("x2") = (long)len;
    register long x8 __asm__("x8") = 64;

    __asm__ volatile("svc #0"
                     : "+r"(x0), "+r"(x1)
                     : "r"(x2), "r"(x8)
                     : "memory", "cc");
    return x0;
}

static uint64_t fnv1a(const volatile uint8_t *p, size_t n)
{
    uint64_t h = 1469598103934665603ULL;

    for (size_t i = 0; i < n; i++) {
        h ^= p[i];
        h *= 1099511628211ULL;
    }
    return h;
}

uint64_t main(uint64_t a, uint64_t b, uint64_t c, uint64_t d, uint64_t e)
{
    static volatile uint8_t arr[4096];
    static volatile uint8_t guard[64];
    uint64_t s = a * 3u + (b ^ 0x9e37u) + (c << 7) + (d >> 5) + (e & 0xffffu);
    uint64_t chk;

    for (int i = 0; i < 4096; i++)
        arr[i] = (uint8_t)(i * 7 + 3);
    for (int i = 0; i < 64; i++)
        guard[i] = 0xA5;

    for (int r = 0; r < 64; r++) {
        int idx = (r * 97 + 13) & 4095;
        uint8_t v = arr[idx];
        uint8_t w = arr[(idx + 64) & 4095];

        s += v * 3u + w;
        if ((r & 7) == 0)
            s ^= 0x9e3779b97f4a7c15ULL;
        __asm__ volatile("" ::: "memory");
    }

    for (int i = 0; i < 64; i++) {
        if (guard[i] != 0xA5) {
            static const char gf[] = "guard_fail\n";

            raw_write(1, gf, sizeof(gf) - 1);
            return 2;
        }
    }

    chk = s ^ fnv1a(arr, sizeof arr);

    {
        static const char prefix[] = "checksum=0x";
        static const char hex[] = "0123456789abcdef";
        char buf[28];
        char *p = buf;

        for (size_t i = 0; i < sizeof(prefix) - 1; i++)
            *p++ = prefix[i];
        for (int k = 15; k >= 0; k--)
            *p++ = hex[(chk >> (4 * k)) & 0xf];
        *p++ = '\n';
        raw_write(1, buf, (unsigned long)(p - buf));
    }

    return chk;
}
