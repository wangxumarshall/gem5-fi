/* smoke — W1.0 workloads/ooo framework smoke kernel.
 *
 * Purpose: minimal end-to-end check of the W1 workload build framework:
 *   make (-O2 -static -Wall -Wextra, zero warnings)
 *   -> static AArch64 ELF
 *   -> gem5 SE (configs/se/ooo_proxy.py --cpu O3)
 *   -> one FINAL=<16hex> checksum line, byte-identical across repeated
 *      gem5 runs and equal to the native host run (runner GOLDEN_IDS
 *      discipline: native == gem5, deterministic).
 *
 * Kernel: fixed-seed integer accumulation — an LCG-filled small buffer
 * (store path), a xorshift accumulation chain (the main loop), and a
 * fold-back pass over the buffer (load path). No entropy, no environment
 * dependence; the FINAL checksum is the self-check surface.
 *
 * Size: a few hundred K dynamic instructions — gem5 SE in ~1s, far under
 * the 60s W1 SE budget (measured hostSeconds recorded in README.md).
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#define SMOKE_ROUNDS 50000u
#define SMOKE_BUFSZ  256u

static uint64_t buf[SMOKE_BUFSZ];

static void put(const char *s){ write(1, s, strlen(s)); }

static void put_hex64(uint64_t v){
    char out[16];
    for (int i = 15; i >= 0; --i){
        unsigned d = v & 0xf;
        out[i] = d < 10 ? '0' + d : 'a' + d - 10;
        v >>= 4;
    }
    write(1, out, sizeof(out));
}

int main(void){
    /* fixed seed — deterministic on host and in gem5 alike */
    uint64_t acc = 0x0123456789abcdefULL;

    /* fill a small buffer via LCG (store path) */
    for (uint32_t i = 0; i < SMOKE_BUFSZ; ++i){
        acc = acc * 6364136223846793005ULL + 1442695040888963407ULL;
        buf[i] = acc;
    }
    /* fixed-seed accumulation chain (main loop; compiler cannot fold) */
    for (uint32_t i = 0; i < SMOKE_ROUNDS; ++i){
        acc ^= acc << 13;
        acc ^= acc >> 7;
        acc ^= acc << 17;
        acc += 0x9e3779b97f4a7c15ULL;
    }
    /* fold the buffer back in (load path) */
    for (uint32_t i = 0; i < SMOKE_BUFSZ; ++i)
        acc ^= buf[i] * 0x9e3779b97f4a7c15ULL + (uint64_t)i;

    put("FINAL=");
    put_hex64(acc);
    put("\n");
    return 0;
}
