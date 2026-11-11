/* LSU 负载 W4 SQ-Forward — v3.3 implementation fix (proposal, NOT promoted
   to the frozen formal W4 ELF without researcher approval).
   Same designed scenarios as sq_forward.c, but every array access is
   `volatile`: at -O2 GCC folds a store immediately followed by a load of the
   same non-volatile array element, which removed ALL data loads from main in
   the frozen ELF (1 load / 15 stores). The FW02/FW05/SQ01/SQ03/SP05/SP06
   models need a real load-after-store pair to feed the forwarding decision.
   Detection surface is unchanged: checksum change (SDC) or crash. */
#include <unistd.h>
#include <stdint.h>

static void put_hex(unsigned long v){
    char buf[16];
    for (int i=15;i>=0;--i){ unsigned d = v & 0xf; buf[i]=d<10?'0'+d:'a'+d-10; v>>=4; }
    write(1,buf,16); write(1,"\n",1);
}

static inline unsigned long fnv(unsigned long acc, unsigned long v){
    acc ^= v; acc *= 0x100000001b3UL; return acc;
}

#define N 32
static volatile unsigned long buf[N];

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
        volatile uint32_t *p = (volatile uint32_t *)((volatile char *)&buf[i] + 2);
        acc = fnv(acc, *p);
    }

    /* 3. byte-mask forwarding: store 1 byte, then load full word */
    { volatile unsigned char *bp = (volatile unsigned char *)buf;
      for (i = 0; i < 16; ++i) { bp[i] = (unsigned char)(0xC0 + i); }
      for (i = 0; i < 2; ++i) acc = fnv(acc, buf[i]); }

    /* 4. alias: two stores to overlapping addresses, then load */
    { buf[0] = 0xD111UL; buf[1] = 0xD222UL;
      volatile unsigned long *p = (volatile unsigned long *)((volatile char *)buf + 4);
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

    /* 7. bulk store then bulk load */
    for (i = 0; i < N; ++i) buf[i] = 0x5A5A5A5A5A5A5A5AUL;
    for (i = 0; i < N; ++i) acc = fnv(acc, buf[i]);

    put_hex(acc);
    return 0;
}
