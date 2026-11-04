/*
 * fp_branch_squash_probe — FSU FR07-HOOK squash/replay gate workload.
 *
 * Deliberately unpredictable data-dependent branches select between two FP
 * kernels. Each mispredict squashes the speculative FP instructions that
 * follow it, giving the PRF-WB hook a real squash window to cancel. Output is
 * a deterministic 256-bit array hash (two FNV-1a passes) so native and gem5
 * goldens are byte-identical.
 *
 * Gate-only artifact: not an official RunID and never counted in 519.
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define N 4096
#define M (1u << 18)   /* 1 MiB pointer-chase index (beyond L2) */

static float a[N], b[N], c[N], d[N];
static unsigned chase[M];

static uint64_t fnv64(const void *p, size_t n, uint64_t h)
{
    const unsigned char *s = (const unsigned char *)p;
    for (size_t i = 0; i < n; i++) {
        h ^= s[i];
        h *= 1099511628211ULL;
    }
    return h;
}

int main(void)
{
    uint64_t s = 0x123456789abcdefULL;
    for (unsigned i = 0; i < M; i++)
        chase[i] = (unsigned)(i * 2654435761u) & (M - 1);
    for (int i = 0; i < N; i++) {
        s ^= s << 13; s ^= s >> 7; s ^= s << 17;
        b[i] = (float)((int)(s & 0x3ff) - 512) / 64.0f;
        c[i] = (float)((int)((s >> 10) & 0x3ff) - 512) / 128.0f;
        d[i] = (float)((int)((s >> 20) & 0xff) - 128) / 32.0f;
        a[i] = 0.0f;
    }
    for (int i = 0; i < N; i++) {
        s ^= s << 13; s ^= s >> 7; s ^= s << 17;
        /* The branch depends on a dependent-load chain, so it resolves late;
         * the FP op on the predicted path can execute and then be squashed. */
        unsigned idx = (unsigned)s & (M - 1);
        for (int k = 0; k < 32; k++)
            idx = chase[(idx ^ (unsigned)(s >> (k * 5))) & (M - 1)];
        if ((idx ^ (unsigned)s) & 1) {
            a[i] = b[i] * c[i] + d[i];
        } else {
            a[i] = b[i] + d[i] * c[i];
        }
    }
    uint64_t h1 = fnv64(a, sizeof(a), 1469598103934665603ULL);
    uint64_t h2 = fnv64(a, sizeof(a), 0x9e3779b97f4a7c15ULL);
    printf("ARRAYHASH=%016llx%016llx%016llx%016llx\n",
           (unsigned long long)h1, (unsigned long long)h2,
           (unsigned long long)~h1, (unsigned long long)~h2);
    printf("DONE\n");
    return 0;
}
