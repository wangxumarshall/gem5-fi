/*
 * harp_roi_spike.c — Task 0.2 spike workload (Harpocrates coverage plan).
 *
 * Verifies that m5ops workbegin/workend ROI markers are visible in gem5
 * SE mode on aarch64. Kept in-repo as the reference encoding for
 * tools/harp_wrap.py (Task 1.1).
 *
 * Encoding (CHAOS/gem5/util/m5/src/abi/arm64/m5op.S):
 *     .long 0xff000110 | (func << 16)     -- func lands in bits 23:16
 *     M5OP_WORK_BEGIN = 0x5a -> .inst 0xff5a0110
 *     M5OP_WORK_END   = 0x5b -> .inst 0xff5b0110
 * (gem5/src/arch/arm/isa/insts/m5ops.isa:41 reads func = bits(23,16);
 *  putting func at bits 15:8 (e.g. 0xff005a10) silently dispatches
 *  M5OP_ARM (func=0) and the marker is lost -- measured, not guessed.)
 *
 * ABI (RegABI64 simcall): X0 = workid, X1 = threadid.
 *
 * Proven on 2026-09-16 (gem5 25.1.0.1, two_level_taishan.py baseline):
 *   pseudo_inst::workbegin(1, 0) @ tick 16698220
 *   pseudo_inst::workend(1, 0)   @ tick 16700530
 *   system.cpu.numWorkItemsStarted   = 1
 *   system.cpu.numWorkItemsCompleted = 1
 *
 * Build (host is aarch64, native):
 *   gcc -static -O2 -o harp_roi_spike tools/harp_roi_spike.c
 */
#include <stdio.h>
#include <stdint.h>

static inline void m5_workbegin(uint64_t workid, uint64_t tid)
{
    register uint64_t x0 __asm__("x0") = workid;
    register uint64_t x1 __asm__("x1") = tid;
    __asm__ volatile(".inst 0xff5a0110" : "+r"(x0) : "r"(x1) : "memory");
}

static inline void m5_workend(uint64_t workid, uint64_t tid)
{
    register uint64_t x0 __asm__("x0") = workid;
    register uint64_t x1 __asm__("x1") = tid;
    __asm__ volatile(".inst 0xff5b0110" : "+r"(x0) : "r"(x1) : "memory");
}

int main(void)
{
    uint64_t acc = 0;

    printf("pre-roi\n");
    m5_workbegin(1, 0);
    for (int i = 0; i < 200000; i++)
        acc += (uint64_t)i * 0x9E3779B97F4A7C15ULL;
    m5_workend(1, 0);
    printf("post-roi acc=%llu\n", (unsigned long long)acc);
    return 0;
}
