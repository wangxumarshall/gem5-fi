/* neon_fp32_lane_kernel — 4x FP32 NEON lane FMA workload.
 *
 *   for i in steps of 4: c[i:i+4] = d[i:i+4] + a[i:i+4]*b[i:i+4]
 *   using float32x4_t (AArch64 ASIMD 128-bit, 4 x 32-bit lanes).
 *
 * The oracle is the full ARRAYHASH over c[] plus ULP vs an in-run golden
 * pass. Per-lane 64-bit FNV hashes (LANEHASH0..3) make a lane-targeted
 * fault visible without inferring it from the aggregate hash.
 *
 * Static AArch64, no libc. N must be a multiple of 4; -DN configurable.
 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>
#include <arm_neon.h>

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

static uint64_t lane_hash(const float *v, int lane) {
    uint64_t h = 1469598103934665603ULL ^ (0x9e3779b9ULL * (lane + 1));
    for (int i = lane; i < N; i += 4) {
        uint32_t u;
        memcpy(&u, &v[i], 4);
        for (int k = 0; k < 4; k++) {
            h ^= (u >> (8 * k)) & 0xffU;
            h *= 1099511628211ULL;
        }
    }
    return h;
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

    for (int i = 0; i < N; i += 4) {
        float32x4_t va = vld1q_f32(a + i);
        float32x4_t vb = vld1q_f32(b + i);
        float32x4_t vd = vld1q_f32(d + i);
        float32x4_t vc = vfmaq_f32(vd, va, vb);
        vst1q_f32(c_check + i, vc);
    }

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

    for (int lane = 0; lane < 4; lane++) {
        char name[16] = "LANEHASH0=";
        name[8] = '0' + lane;
        put(name); put_hex64(lane_hash(c_check, lane)); put("\n");
    }
    return 0;
}
