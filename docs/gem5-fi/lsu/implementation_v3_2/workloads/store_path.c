/* LSU workload W6 Store-Path — rebuilt v3.2 (original preserved in
   _original_v31/store_path.c).

   The v3.1 original wrote an 8-byte value at a+16384+i*4 for i=4095
   (end 32772 > sizeof(a)=32768), used misaligned raw pointer stores, and
   overlapped the 16/32/64-bit regions. This rebuild keeps the same target
   (a stream of stores through the SQ/L1D path) while making every region
   non-overlapping and in-bounds and every width store go through memcpy,
   which is defined for unaligned addresses. Region starts are deliberately
   odd so the store stream still exercises unaligned addresses. */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

static uint64_t fnv1a(const void *p, size_t n) {
    const uint8_t *b = p;
    uint64_t h = 1469598103934665603ULL;
    for (size_t i = 0; i < n; i++) { h ^= b[i]; h *= 1099511628211ULL; }
    return h;
}

int main(void) {
    static uint8_t a[32768];
    memset(a, 0, sizeof a);

    /* Region A: 4096 byte stores [0, 4096). */
    for (int i = 0; i < 4096; i++) a[i] = (uint8_t)i;

    /* Region B: 4096 unaligned 16-bit stores [4097, 12289). */
    for (int i = 0; i < 4096; i++) {
        uint16_t v = (uint16_t)(i * 3);
        memcpy(a + 4097 + i * 2, &v, sizeof v);
    }

    /* Region C: 2048 unaligned 32-bit stores [12291, 20483). */
    for (int i = 0; i < 2048; i++) {
        uint32_t v = (uint32_t)i * 7u;
        memcpy(a + 12291 + i * 4, &v, sizeof v);
    }

    /* Region D: 1024 unaligned 64-bit stores [20483, 28675). */
    for (int i = 0; i < 1024; i++) {
        uint64_t v = 0x0123456789abcdefULL ^ (uint64_t)i;
        memcpy(a + 20483 + i * 8, &v, sizeof v);
    }

    /* Region E: 4093 byte stores [28675, 32768) — ends exactly at the end. */
    for (int i = 0; i < 4093; i++) a[28675 + i] = (uint8_t)(i ^ 0x5a);

    /* Same-width byte update, no cross-width overlap. */
    for (int i = 0; i < 4096; i += 4) a[i + 1] ^= 0x5a;

    printf("checksum=0x%016llx\n", (unsigned long long)fnv1a(a, sizeof a));
    return 0;
}
