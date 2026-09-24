from m5.params import *
from m5.SimObject import SimObject

class CHAOSFreeList(SimObject):
    type = 'CHAOSFreeList'
    cxx_class = 'gem5::CHAOSFreeList'
    cxx_header = "cpu/o3/CHAOSFreeList/CHAOSFreeList.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.2 freelist modes:
    #   mark_free  : on getReg, RE-ADD a currently-ALLOCATED physReg (not free)
    #                back to the free list -> it gets re-handed-out later ->
    #                two arch regs share one phys reg -> history residue
    #                (method1 "其它计算数据覆盖 x[0]" signature). The re-added
    #                target MUST be validated allocated (isFree==false) else
    #                it's a no-op (no UB). D17 (ooo 04-design-matrix R18,
    #                空闲表·重复分配·固定间隔 F1/F2) rides this mode via the
    #                first_clock window mechanism.
    #   pop_wrong  : on getReg, return a different-but-LEGAL physReg id (same
    #                class, in [0,numPhys)) instead of the true front. The
    #                caller stores it as the dest physReg -> wrong mapping.
    #   mark_free_event (W4.5 D18, ooo 04-design-matrix R19, 空闲表·重复
    #                分配·事件触发): the SAME duplicate-allocation action as
    #                mark_free, but eligible ONLY when the int free-list
    #                remaining count (post-pop, i.e. at the getReg moment) is
    #                <= eventThreshold (default 8) — 精确瞄准"空闲表快见底"
    #                这个窗口. Both mark_free modes log the re-added idx AND
    #                watch for its re-hand-out (the DUPLICATE_ALLOCATION line
    #                = the second allocation evidence).
    # drop_release (W4 final D19, ooo 04-design-matrix R20, 空闲表·丢失
    # 释放, F1 "一次性触发持续影响"): a release that should have happened
    # does not — the freed physReg is NOT pushed back onto the free list
    # (hook: UnifiedFreeList::addReg, covering BOTH runtime release paths:
    # commit-time removeFromHistory + post-squash freeingInProgress drain).
    # One suppression = the int pool permanently shrinks by one for the
    # rest of the run; the exit-summary line (final_free_int) makes the
    # shrink provable against a zero-injection control. Expected dominant
    # outcome per the matrix: Timeout with a rising rename-stall precursor.
    # head_bitflip / head_bitflip2 (W4 final D20/D21, ooo 04-design-matrix
    # R21/R22, 空闲表头/尾指针·单/双比特翻转) — HONEST APPROXIMATION (spike
    # B: gem5 SimpleFreeList is a std::queue with NO explicit head/tail
    # pointer registers): the popped-front idx has 1 (D20) / 2 distinct
    # random (D21, F0) bits flipped — the id HANDED OUT is what a corrupted
    # head read would have returned. The true front is still consumed (the
    # skipped entries leak) and the flipped-to id may be currently
    # ALLOCATED (immediate duplicate) or still IN THE QUEUE (future
    # duplicate) — the two D20 observables. Out-of-range flip = honest
    # skip (logged, never clamped).
    # head_stuck (W4 final D22, ooo 04-design-matrix R23, 空闲表头/尾指针·
    # 卡死, F5) — HONEST APPROXIMATION (same std::queue finding): the
    # pre-approved "反复返回同项不真正 pop（头卡死）" proxy. Armed once at
    # the first in-window eligible getReg (stuck id = the then-front idx
    # with one random bit forced to a fixed polarity, raw freeze if out of
    # range); from then on EVERY getReg returns that SAME id and the queue
    # NEVER advances (no pop) — permanent fixed-pattern deviation /
    # continuous duplicate allocation. Exposure logging capped at the
    # first 10; the total lands in the exit summary.
    mode = Param.String("mark_free",
        "mark_free | pop_wrong | mark_free_event | drop_release | "
        "head_bitflip | head_bitflip2 | head_stuck")

    probability = Param.Float(1.0,
        "per-getReg injection probability (use 1.0 with maxFaults=1)")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    eventThreshold = Param.UInt64(8,
        "D18 mark_free_event: trigger only while the int freelist remaining "
        "count (post-pop) is <= this (04-design-matrix R19 建议 ≤8)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
