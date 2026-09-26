/* LSU 负载 W8 Prefetch-Stride (06-workloads r10):
   正/负/交错 stride、随机 pointer chase、跨页 stride、训练后变步长、
   需求/预取竞争。用途：预取器注入器(P01-P09)定向验证。SE。
   golden = fnv-1a checksum of all accessed values. */
#include <unistd.h>
#include <stdint.h>
#include <stdlib.h>

static void put_hex(unsigned long v){
    char buf[16];
    for (int i=15;i>=0;--i){ unsigned d = v & 0xf; buf[i]=d<10?'0'+d:'a'+d-10; v>>=4; }
    write(1,buf,16); write(1,"\n",1);
}
static inline unsigned long fnv(unsigned long a, unsigned long v){
    a ^= v; a *= 0x100000001b3UL; return a;
}

#define SZ (256*1024)  /* 256KiB: fits in 1MiB L2, exceeds 32KiB L1D */
static unsigned long arr[SZ/8];

int main(void)
{
    unsigned long acc = 0x0feedface1616beefUL;
    for (unsigned i = 0; i < SZ/8; ++i) arr[i] = 0x10000UL + i;

    /* 1. positive stride 64B (8 longs) — classic stride prefetch pattern */
    for (unsigned i = 0; i < SZ/8; i += 8) acc = fnv(acc, arr[i]);

    /* 2. negative stride 128B */
    for (int i = SZ/8 - 1; i >= 0; i -= 16) acc = fnv(acc, arr[i]);

    /* 3. interleaved stride (two streams) */
    for (unsigned i = 0; i < SZ/16; i += 4) {
        acc = fnv(acc, arr[i]);
        acc = fnv(acc, arr[i + SZ/32]);
    }

    /* 4. pointer chase (random — defeats stride prefetcher) */
    { unsigned idx = 17;
      for (unsigned i = 0; i < 256; ++i) {
          idx = (idx * 31 + 7) % (SZ/8);
          acc = fnv(acc, arr[idx]);
      } }

    /* 5. cross-page stride (4KiB apart = 512 longs) */
    for (unsigned i = 0; i < SZ/8; i += 512) acc = fnv(acc, arr[i]);

    /* 6. train-then-switch stride (64B for half, then 256B) */
    for (unsigned i = 0; i < SZ/16; i += 8) acc = fnv(acc, arr[i]);
    for (unsigned i = SZ/16; i < SZ/8; i += 32) acc = fnv(acc, arr[i]);

    put_hex(acc);
    return 0;
}
