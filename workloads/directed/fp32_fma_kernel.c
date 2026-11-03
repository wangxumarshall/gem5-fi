/* fp32_fma_kernel — scalar FP32 FMA workload for FSU FP32 field gates.
 *
 *   for i: c[i] = a[i]*b[i] + d[i]   (IEEE binary32)
 *
 * Prints ARRAYHASH=<64hex> over c[] and ULP=<max_ulp> against an in-run
 * golden pass. Static AArch64, no libc. N configurable with -DN.
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

#ifndef N
#define N 65536
#endif

static float a[N], b[N], d[N], c_golden[N], c_check[N];

static void put(const char *s) { write(1, s, strlen(s)); }

static void put_u64(uint64_t v) {
    char buf[24]; int i = 23; buf[i--] = 0;
    if (!v) buf[i--] = '0';
    while (v) { buf[i--] = '0' + (v % 10); v /= 10; }
    write(1, buf + i + 1, 22 - i);
}

static void put_hex64(uint64_t v) {
    char buf[16];
    for (int i = 15; i >= 0; --i) {
        unsigned x = v & 0xf;
        buf[i] = x < 10 ? '0' + x : 'a' + x - 10;
        v >>= 4;
    }
    write(1, buf, 16);
}

static uint64_t ulp32(float x, float y) {
    if (x == y) return 0;
    uint32_t ux, uy;
    memcpy(&ux, &x, 4); memcpy(&uy, &y, 4);
    if ((ux >> 31) != (uy >> 31)) {
        uint32_t ax = ux & 0x7fffffffU, ay = uy & 0x7fffffffU;
        return (uint64_t)ax + ay + 1;
    }
    return ux > uy ? (uint64_t)(ux - uy) : (uint64_t)(uy - ux);
}

int main(void) {
    uint64_t s = 0x243F6A8885A308D3ULL;
    for (int i = 0; i < N; i++) {
        s = s * 6364136223846793005ULL + 1442695040888963407ULL;
        a[i] = (float)(s % 1000) * 0.001f + 0.5f;
        b[i] = (float)((s >> 17) % 1000) * 0.001f + 0.25f;
        d[i] = (float)((s >> 33) % 1000) * 0.001f - 0.5f;
    }
    for (int i = 0; i < N; i++) c_golden[i] = a[i] * b[i] + d[i];
    for (int i = 0; i < N; i++) c_check[i] = a[i] * b[i] + d[i];

    put("ARRAYHASH=");
    const unsigned char *p = (const unsigned char *)c_check;
    unsigned total = sizeof(c_check), q = (total + 3) / 4;
    for (int lane = 0; lane < 4; lane++) {
        uint64_t h = 1469598103934665603ULL ^ (0x9e3779b9ULL * lane);
        for (unsigned i = lane * q; i < (unsigned)(lane + 1) * q && i < total; i++) {
            h ^= p[i]; h *= 1099511628211ULL;
        }
        put_hex64(h);
    }
    put("\n");

    uint64_t maxulp = 0;
    for (int i = 0; i < N; i++) {
        uint64_t u = ulp32(c_check[i], c_golden[i]);
        if (u > maxulp) maxulp = u;
    }
    put("ULP="); put_u64(maxulp); put("\n");
    return 0;
}
