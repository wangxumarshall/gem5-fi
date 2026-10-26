/* LSU 负载 R4-9-FSMC 屏障探针（barrier_probe — O06/O07 的 SE 载体）:
   store->DMB->load 序列 + DSB，外加数据面消费。

   WHAT THIS CARRIER DOES / DOES NOT PROVE (honest):
     The O06/O07 hook node is the O3 MemDepUnit's barrier-SN bookkeeping
     (insertBarrierSN / completeInst — see src/cpu/o3/chaos_barrier_hook.hh).
     A barrier instruction only reaches that bookkeeping if it is flagged
     IsReadBarrier|IsWriteBarrier; on ARM those flags are carried by DMB/DSB.
     This workload therefore exists to (a) emit a DENSE, deterministic stream
     of DMB/DSB instructions so an O06/O07 census/pilot actually has a
     non-empty eligible stream (a carrier that never executes a barrier would
     yield attempted=0 and prove nothing), and (b) provide a stable golden
     digest for the UNINJECTED control arm.
     It does NOT prove the injected semantics by itself: single-core SE has no
     real memory reordering, so O06-a's "later accesses pass the barrier"
     cannot show up as a litmus violation in-process — that classification is
     the campaign's (SDC vs Timeout vs Masked) job on the injected run. The
     ordering pair below is written so the two directions are independently
     consumable, which is what a future multi-core FS arm would need.

   Deterministic: no timing, no retry counters in the digest. */
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

#define N 16
static volatile unsigned long flag;
static unsigned long payload[N];

/* The barrier forms are emitted by GCC's own memory-ordering builtins so the
   ISA selection is the compiler's (aarch64: dmb ish / dsb ish), and the
   IsReadBarrier|IsWriteBarrier flags are attached by the ARM ISA decoder. */
#define BARRIER_DMB()  __asm__ volatile("dmb ish" ::: "memory")
#define BARRIER_DSB()  __asm__ volatile("dsb ish" ::: "memory")

int main(void)
{
    unsigned long acc = 0x3fa9c60e5b7182d4UL;
    unsigned i;

    for (i = 0; i < N; ++i)
        payload[i] = 0x2000UL + i;
    flag = 0;

    /* store -> DMB -> load: the classic publish/consume ordering pair. */
    for (i = 0; i < N; ++i) {
        unsigned long observed;
        payload[i] += 0x33;
        BARRIER_DMB();                       /* release: payload before flag */
        flag = i + 1;
        BARRIER_DMB();                       /* acquire: flag before payload */
        observed = payload[i];
        acc = fnv(acc, observed);
        acc = fnv(acc, flag);
    }

    /* DSB between two phases: everything in flight must have completed. */
    BARRIER_DSB();
    for (i = 0; i < N; ++i)
        acc = fnv(acc, payload[i] ^ (flag + i));
    BARRIER_DSB();

    /* final sweep over the data face */
    for (i = 0; i < N; ++i)
        acc = fnv(acc, payload[i]);

    put_hex(acc);
    return 0;
}
