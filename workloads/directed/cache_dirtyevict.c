/* LSU 负载 W6 Cache-DirtyEvict (06-workloads r8):
   working set=0.5×/1×/2×L1D; 读改写、dirty eviction、writeback、
   conflict set、共享行 false sharing。用途：Cache 注入器(C01-C15)定向验证。SE。
   golden = fnv-1a checksum of all read-back values. */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

static void put_hex(unsigned long v){
    char buf[16];
    for (int i=15;i>=0;--i){ unsigned d = v & 0xf; buf[i]=d<10?'0'+d:'a'+d-10; v>>=4; }
    write(1,buf,16); write(1,"\n",1);
}
static inline unsigned long fnv(unsigned long a, unsigned long v){
    a ^= v; a *= 0x100000001b3UL; return a;
}

/* L1D = 32KiB 2-way = 16KiB/set → conflict set = same index, 2 ways.
   0.5×L1D = 16KiB (fits) · 1× = 32KiB (boundary) · 2× = 64KiB (thrash) */
#define L1D (32*1024)
#define HALF (L1D/2)        /* 16KiB */
#define FULL (L1D)          /* 32KiB */
#define DOUBLE (L1D*2)      /* 64KiB */
static unsigned long buf[DOUBLE/8];

int main(void)
{
    unsigned long acc = 0xc0ffee16d1ce5eedUL;
    unsigned i;

    /* 1. 0.5×L1D: fits in cache, all hits after warm-up */
    for (i = 0; i < HALF/8; ++i) buf[i] = i + 1;
    for (i = 0; i < HALF/8; ++i) acc = fnv(acc, buf[i]);

    /* 2. 1×L1D: boundary — some evictions */
    for (i = HALF/8; i < FULL/8; ++i) buf[i] = i + 2;
    for (i = 0; i < FULL/8; ++i) acc = fnv(acc, buf[i]);

    /* 3. 2×L1D: thrash — every access evicts (L1D is 2-way) */
    for (i = FULL/8; i < DOUBLE/8; ++i) buf[i] = i + 3;
    for (i = 0; i < DOUBLE/8; i += 2) acc = fnv(acc, buf[i]);

    /* 4. read-modify-write (dirty lines: writeback on eviction) */
    for (i = 0; i < HALF/8; ++i) buf[i] += 0x100;
    for (i = 0; i < HALF/8; ++i) acc = fnv(acc, buf[i]);

    /* 5. conflict set: same cache index (stride = 16KiB = set stride) */
    for (i = 0; i < 8; ++i) {
        unsigned long *p = (unsigned long *)((char *)buf + i * L1D);
        *p = i * 0x1111;
        acc = fnv(acc, *p);
    }

    /* 6. false sharing pattern: writes to adjacent 8B words (same line) */
    for (i = 0; i < 64; ++i) buf[i] = 0xF000 + i;

    put_hex(acc);
    return 0;
}
