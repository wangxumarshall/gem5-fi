/* FW05 directed workload: two distinct 8-byte stores to the same address
   followed by an 8-byte load, close enough that both stores are still in
   the store queue when the load forwards. The younger store is gem5's true
   forwarding source; the older store is the FW05 alternative. The two
   stores write different values, so a wrong-source forward changes the
   checksum. */
#include <stdio.h>
#include <stdint.h>

static uint64_t fnv1a(const void *p, size_t n) {
    const uint8_t *b = p;
    uint64_t h = 1469598103934665603ULL;
    for (size_t i = 0; i < n; i++) { h ^= b[i]; h *= 1099511628211ULL; }
    return h;
}

int main(void) {
    static uint64_t buf[64];
    /* A cold array whose load delays the target load (address dependency)
       and whose in-order commit blocks the stores from leaving the SQ. */
    static uint64_t slow[1 << 20];
    uint64_t s = 0;
    for (int i = 0; i < 2000; i++) {
        /* Commit cannot pass this branch until the cold load returns;
           the X stores below execute but stay in the SQ. */
        if (slow[(i * 4096) & ((1 << 20) - 1)] == 0xdeadbeefULL)
            s ^= 1;
        volatile uint64_t *p = &buf[i & 63];
        /* An older unrelated store keeps the X stores away from the
           store-WB head, so the older X stores are real SQ candidates. */
        volatile uint64_t *z = &buf[(i + 7) & 63];
        *z = 0x3333333333333333ULL + (uint64_t)i;
        asm volatile("" ::: "memory");
        *p = 0x1111111111111111ULL + (uint64_t)i;
        asm volatile("" ::: "memory");
        *p = 0x2222222222222222ULL + (uint64_t)i * 3;
        asm volatile("" ::: "memory");
        *p = 0x4444444444444444ULL + (uint64_t)i * 5;
        asm volatile("" ::: "memory");
        *p = 0x5555555555555555ULL + (uint64_t)i * 7;
        s += *p;
        asm volatile("" ::: "memory");
    }
    printf("checksum=0x%016llx\n",
           (unsigned long long)(s ^ fnv1a(buf, sizeof buf)));
    return 0;
}
