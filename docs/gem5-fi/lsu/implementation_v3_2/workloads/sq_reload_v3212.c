/* LSU v3.2.12 SQ-Reload workload (propagation-closure Task 10, shared by
   SQ01/SQ03/SP05): 128 iterations of store -> dmb ish -> same-address load.

   Why the load is a real post-drain reload on gem5 v25 O3 and not a
   same-cycle SQ forward: aarch64 `dmb ish` decodes with IsReadBarrier +
   IsWriteBarrier (arch/arm/isa/insts/misc64.isa). MemDepUnit::insert makes
   every younger load depend on the outstanding load-barrier SN
   (cpu/o3/mem_dep_unit.cc), and the barrier itself only executes once it
   reaches the commit head AND iewStage->hasStoresToWB() is false
   (cpu/o3/commit.cc commitHead) -- i.e. after the store has left the SQ and
   its write reached memory. The freed SQ entry cannot match in
   LSQUnit::read(), so the reload load is served from the L1D: a real
   memory-visibility consumer of the drained store bytes.

   Detection surface: SQ01 store-data (the drained write is the only source
   of the reloaded value), SQ03 SQ-state (drain/visibility timing), SP05
   drain staging. The reloaded value feeds a byte-wise FNV-1a checksum and
   an equality-dependent branch, so corruption lands in the checksum (SDC)
   or flips the control path. SE, AArch64, static. */
#include <stdio.h>
#include <stdint.h>

#define N 128

static volatile uint64_t buf[256];

static uint64_t fnv1a64(uint64_t h, uint64_t v)
{
    for (int b = 0; b < 8; b++) {
        h ^= (v >> (8 * b)) & 0xffu;
        h *= 1099511628211ULL;
    }
    return h;
}

int main(void)
{
    uint64_t h = 1469598103934665603ULL;
    uint64_t path = 0;

    for (int i = 0; i < N; i++) {
        uint64_t v = 0x73715f72656c6f61ULL
                   + (uint64_t)i * 0x0101010101010101ULL;
        buf[i] = v;                        /* the store */
        asm volatile("dmb ish" ::: "memory");
        uint64_t r = buf[i];               /* same-address reload */
        h = fnv1a64(h, r);
        if (r == v)
            path += 1;                     /* equal: memory delivered the bytes */
        else
            path = fnv1a64(path, r ^ v);   /* corrupt: control path diverges */
    }

    printf("checksum=0x%016llx\n", (unsigned long long)(h ^ path));
    return 0;
}
