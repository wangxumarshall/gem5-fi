/* LSU 负载 R4-9-FSMC LSE 原子读改写探针（lse_rmw — O04/O05/O09 的 SE 载体）:
   LSE 原子（CAS / SWP / LDADD）数据面 + 完成面消费。

   WHY A NEW CARRIER (honest, do not reuse atomics_probe): atomics_probe.c uses
   **LDXR/STXR** (the Arm exclusive-monitor pair), which gem5 services through
   the LLSC `cmpAndSwap` path — NOT through `Packet::isAtomicOp()`. The
   O04/O05/O09 hooks fire on the LSE `SwapReq`+`isAtomicOp()` path
   (BaseCache::satisfyRequest, src/mem/cache/base.cc:1380-1419), which only
   LSE `cas`/`swp`/`ldadd` reach. Using atomics_probe would exercise a
   different code path and silently prove nothing (mapping carrier ≠ model —
   the R4-8-FSMC discipline).

   检测面设计（关键，O04/O05/O09 的激活口径都会落到本 oracle 上）:
     acc folds BOTH faces of every RMW:
       (a) the RETURNED old value  -> O04-a (old/new exchange) and O09-a
           (result-latch bit flip) corrupt exactly this face;
       (b) the POST-RMW memory value -> O05-a (update dropped) and O05-b
           (update applied twice) corrupt exactly this face;
     so a fault on either face makes the printed digest differ from the
     golden. Neither face is consumed twice, so each is independently
     attributable in a follow-up if needed.
   The digest is deterministic (no timing / retry counts folded in). */
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

#define N 8
static unsigned long cell[N];

int main(void)
{
    unsigned long acc = 0x51ed270b7ac4e613UL;
    unsigned i;

    for (i = 0; i < N; ++i)
        cell[i] = 0x1000UL + i;

    /* --- LSE CAS (compare-and-swap), 64-bit ---------------------------- */
    for (i = 0; i < N; ++i) {
        /* Arm CAS <Ws>, <Wt>, [<Xn>]: compare Xs with memory; if equal store
           Xs(=Ws)... precisely: if Xs == data then Mem = Xt; Xt := data (the
           OLD value is returned in the SAME register that carried the new
           value). So one "+r" output carries newvalue-in/oldvalue-out. */
        unsigned long compare = cell[i];        /* Ws (input only)   */
        unsigned long old     = compare + 0x11; /* Wt (in: new val)  */
        unsigned long ok;
        __asm__ volatile("cas %0, %1, [%2]"
                         : "+r"(old)            /* %0 = Wt */
                         : "r"(compare)         /* %1 = Ws */
                         , "r"(&cell[i])        /* %2 = Xn */
                         : "memory");
        ok = (compare == old) ? 1UL : 0UL;
        acc = fnv(acc, old);          /* (a) the returned face */
        acc = fnv(acc, ok);
        acc = fnv(acc, cell[i]);      /* (b) the post-RMW memory face */
    }

    /* --- LSE SWP (swap), 32-bit on a packed word ----------------------- */
    static uint32_t word = 0xdeadbeefu;
    for (i = 0; i < 4; ++i) {
        uint32_t newv = 0x01020304u + i;
        uint32_t old;
        /* SWP <Ws>, <Wt>, [<Xn>]: Ws = value to store (input); Wt receives
           the old memory value (output only). */
        __asm__ volatile("swp %w1, %w0, [%2]"
                         : "=r"(old)            /* %0 = Wt */
                         : "r"(newv)            /* %1 = Ws */
                         , "r"(&word)           /* %2 = Xn */
                         : "memory");
        acc = fnv(acc, (unsigned long)old);
        acc = fnv(acc, (unsigned long)word);
    }

    /* --- LSE LDADD (fetch-add), 64-bit --------------------------------- */
    for (i = 0; i < N; ++i) {
        unsigned long addend = 0x101UL + i;
        unsigned long old;
        /* LDADD <Ws>, <Wt>, [<Xn>]: Ws = addend (input); Wt receives the old
           memory value (output only). */
        __asm__ volatile("ldadd %1, %0, [%2]"
                         : "=r"(old)            /* %0 = Wt */
                         : "r"(addend)          /* %1 = Ws */
                         , "r"(&cell[i])        /* %2 = Xn */
                         : "memory");
        acc = fnv(acc, old);
        acc = fnv(acc, cell[i]);
    }

    /* --- final-state sweep: every cell + the packed word --------------- */
    for (i = 0; i < N; ++i)
        acc = fnv(acc, cell[i]);
    acc = fnv(acc, (unsigned long)word);

    put_hex(acc);
    return 0;
}
