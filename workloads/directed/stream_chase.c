/* LSU 负载 W10 STREAM+PointerChase (06-workloads r12):
   STREAM Copy/Scale/Add/Triad 加随机 pointer chase；检查数组 hash 与遍历节点数。
   用途：带宽、MSHR、预取、AGU 注入器定向验证。SE。
   golden = fnv-1a checksum of all output arrays + chase node count. */
#include <unistd.h>
#include <stdint.h>

static void put_hex(unsigned long v){
    char buf[16];
    for (int i=15;i>=0;--i){ unsigned d = v & 0xf; buf[i]=d<10?'0'+d:'a'+d-10; v>>=4; }
    write(1,buf,16); write(1,"\n",1);
}
static inline unsigned long fnv(unsigned long a, unsigned long v){
    a ^= v; a *= 0x100000001b3UL; return a;
}

#define N (64*1024/8)   /* 64KiB per array (2× L1D, fits L2) */
static unsigned long a[N], b[N], c[N];

int main(void)
{
    unsigned long acc = 0x572ea411501a7ce5UL;
    unsigned i;

    for (i = 0; i < N; ++i) { a[i] = i + 1; b[i] = i * 2; c[i] = 0; }

    /* 1. STREAM Copy: c = a */
    for (i = 0; i < N; ++i) c[i] = a[i];
    for (i = 0; i < N; i += 8) acc = fnv(acc, c[i]);

    /* 2. STREAM Scale: b = 3*c */
    for (i = 0; i < N; ++i) b[i] = 3 * c[i];
    for (i = 0; i < N; i += 8) acc = fnv(acc, b[i]);

    /* 3. STREAM Add: c = a + b */
    for (i = 0; i < N; ++i) c[i] = a[i] + b[i];
    for (i = 0; i < N; i += 8) acc = fnv(acc, c[i]);

    /* 4. STREAM Triad: a = b + 2*c */
    for (i = 0; i < N; ++i) a[i] = b[i] + 2 * c[i];
    for (i = 0; i < N; i += 8) acc = fnv(acc, a[i]);

    /* 5. Random pointer chase: 512 hops through a permutation */
    { unsigned idx = 0; unsigned count = 0;
      for (i = 0; i < N; ++i) b[i] = (i + 1) % N;  /* cycle */
      /* randomize: xor-shift shuffle */
      for (i = N - 1; i > 0; --i) {
          unsigned j = (unsigned)(b[i-1] * 2654435761UL) % (i + 1);
          unsigned long tmp = b[i]; b[i] = b[j]; b[j] = tmp;
      }
      for (i = 0; i < 512; ++i) { idx = (unsigned)b[idx]; ++count; }
      acc = fnv(acc, count);
      acc = fnv(acc, b[idx]); }

    put_hex(acc);
    return 0;
}
