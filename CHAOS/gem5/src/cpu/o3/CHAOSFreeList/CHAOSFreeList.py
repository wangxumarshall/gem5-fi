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

    # W7.3 (ooo 04-design-matrix D72-D77 merged rows, VecRegClass freelist
    # family): the register class whose free list the injector targets.
    #   int (default): IntRegClass — every W4 mode's original behavior,
    #                  byte-identical logs.
    #   vec          : VecRegClass — D74 mark_free / D75 mark_free_event /
    #                  D77 drop_release merged rows (all 7 modes get the
    #                  class-parameterized pool/id/threshold helpers).
    # Platform fact (W1.2, C3-verified): AArch64 gem5 v25 renames scalar
    # FP (D/S regs) through VecRegClass — FloatRegClass is inert — so the
    # north-star's scalar-FP freelist rows D72/D73/D76 are MERGED into the
    # vec class (04-matrix D62's own merge clause); there is deliberately
    # NO "float" value.
    targetClass = Param.String("int",
        "int | vec — which class freelist to corrupt (W7.3 VecRegClass "
        "family, D72-D77 merged rows)")

    probability = Param.Float(1.0,
        "per-getReg injection probability (use 1.0 with maxFaults=1)")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    eventThreshold = Param.UInt64(8,
        "D18 mark_free_event: trigger only while the int freelist remaining "
        "count (post-pop) is <= this (04-design-matrix R19 建议 ≤8)")
    # W7.3 D75 (向量空闲表·重复分配·事件触发): the VEC-class threshold,
    # used INSTEAD of eventThreshold when targetClass=vec. DOCUMENTED
    # DEVIATION from 04's "建议 ≤6 项，按 48 项池容量等比例设置": that
    # assumed ~32 mapped arch regs, but the actual C3 platform maps 44
    # arch vec regs (V0-V31 + Special 8 + Interleave 4, regs/vec.hh:83)
    # out of 48 phys — the vec free pool STARTS at 4 and never exceeds it
    # (W1.5b measured; 48-44=4), so a ≤6 threshold would be ALWAYS true
    # (degenerate to the D74 fixed-interval semantics). Re-derived default
    # 0 = "pool drained" (post-pop free==0, the pop consumed the last free
    # vec reg — the W1.5b recommendation for isolating the genuine
    # pressure window); set 2 for a half-slack window (2 of initial 4).
    eventThresholdVec = Param.UInt64(0,
        "D75 mark_free_event vec: trigger only while the VEC freelist "
        "remaining count (post-pop) is <= this (default 0 = pool drained; "
        "re-derived from 04's ≤6 per the W1.5b initial-free-4 calibration)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
