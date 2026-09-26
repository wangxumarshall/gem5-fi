/* LSU 负载 W5 SQ-Forward (06-workloads r7):
   同地址与部分重叠 store-to-load forwarding、不同字节掩码、
   地址晚到/数据晚到、alias、replay。
   用途：SQ 注入器(S01-S13)与 LQ 注入器(L01-L04)的定向验证负载。SE。
   检测面：forwarding 路径的数据腐蚀 → 校验和变化（SDC）或崩溃。 */
#include <unistd.h>
#include <stdint.h>
#include <string.h>

static void put_hex(unsigned long v){
    char buf[16];
    for (int i=15;i>=0;--i){ unsigned d = v & 0xf; buf[i]=d<10?'0'+d:'a'+d-10; v>>=4; }
    write(1,buf,16); write(1,"\n",1);
}

static inline unsigned long fnv(unsigned long acc, unsigned long v){
    acc ^= v; acc *= 0x100000001b3UL; return acc;
}

#define N 32
static unsigned long buf[N];

int main(void)
{
    unsigned long acc = 0x5f1e4d7c9b0a8362UL;
    unsigned i;

    /* 1. full-overlap forwarding: store then immediately load same addr */
    for (i = 0; i < N; ++i) {
        buf[i] = 0xA000UL + i * 0x1111111111111111UL;
        acc = fnv(acc, buf[i]);  /* load right after store = forward */
    }

    /* 2. partial-overlap forwarding: store 8B, load 4B at +2 */
    for (i = 0; i < 8; ++i) {
        buf[i] = 0xB000UL + i;
        uint32_t *p = (uint32_t *)((char *)&buf[i] + 2);
        acc = fnv(acc, *p);
    }

    /* 3. byte-mask forwarding: store 1 byte, then load full word */
    { unsigned char *bp = (unsigned char *)buf;
      for (i = 0; i < 16; ++i) { bp[i] = (unsigned char)(0xC0 + i); }
      for (i = 0; i < 2; ++i) acc = fnv(acc, buf[i]); }

    /* 4. alias: two stores to overlapping addresses, then load */
    { buf[0] = 0xD111UL; buf[1] = 0xD222UL;
      unsigned long *p = (unsigned long *)((char *)buf + 4);
      *p = 0xD333UL;  /* overlaps buf[0] high half and buf[1] low half */
      acc = fnv(acc, buf[0]); acc = fnv(acc, buf[1]); }

    /* 5. store-to-load with dependency chain (prevents reordering) */
    { unsigned long prev = 0xE000UL;
      for (i = 0; i < 8; ++i) {
          buf[i] = prev + i;
          prev = buf[i];
          acc = fnv(acc, prev);
      } }

    /* 6. interleaved store/load pairs (exercises SQ draining) */
    for (i = 0; i < N/2; ++i) {
        buf[i] = buf[i + N/2] = 0xF000UL + i;
        acc = fnv(acc, buf[i]);
    }

    /* 7. memset+memcmp pattern (bulk store then bulk load) */
    memset(buf, 0x5A, sizeof(buf));
    for (i = 0; i < N; ++i) acc = fnv(acc, buf[i]);

    put_hex(acc);
    return 0;
}
