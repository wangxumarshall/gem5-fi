# CHAOSCov — Harpocrates coverage instrumentation (harp plan Task 1.2).
#
# Single-run hardware-coverage measurement for the Harpocrates reproduction
# (ISCA'24 §II-D / Micro'26 "Coverage, Detection, and Fault Models"):
#   - ACE lifetime analysis for bit-array structures (IRF now; L1D/LSQ next)
#   - IBR (input bit ratio) for functional units
# ROI is gated by m5ops workbegin/workend (harp_wrap.py inserts the markers;
# encoding proven in tools/harp_roi_spike.c).
#
# This skeleton (Task 1.2) wires: SimObject + ROI state machine + stats
# registration + detail dump. Per-structure collectors land in Tasks 2-4.
from m5.params import *
from m5.proxy import *
from m5.SimObject import SimObject


class CHAOSCov(SimObject):
    type = "CHAOSCov"
    cxx_class = "gem5::CHAOSCov"
    cxx_header = "CHAOSCov/CHAOSCov.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    targetCache = Param.BaseCache(NULL,
        "Cache whose blocks are ACE-analyzed (Task 3.1; typically the "
        "L1D. NULL = cache analysis disabled)")
    cacheNumBlocks = Param.UInt32(0,
        "Number of blocks in targetCache (AVF denominator; passed from "
        "the config because BaseTags::numBlocks is protected — 0 = "
        "derive at runtime via Cache::getTags() friend-free fallback: "
        "size / blockSize)")
    # --- SDC-ED Task 2.2: additional caches with independent ledgers ---
    # Each entry gets its own block-ACE ledger (l2c* stats aggregate over
    # the extras; the L1D targetCache keeps the legacy l1d* stats).
    extraTargetCaches = VectorParam.BaseCache([],
        "Additional caches to ACE-analyze with independent ledgers "
        "(SDC-ED L2C unit; e.g. [system.l2cache])")
    extraCacheNumBlocks = VectorParam.Int([],
        "Block counts for extraTargetCaches (AVF denominators), "
        "same order")
    sqEntries = Param.UInt32(0,
        "Store-queue entry count (Task 3.2 AVF denominator; passed from "
        "the config — LSQ::SQEntries is not public to C++ clients)")

    # --- SDC-ED Task 2.1: IBR denominator parameterization (Layer C) ---
    # FU instance counts per class [IntAdd, IntMul, FPAdd, FPMul]; defaults
    # are the TaiShan v110 fu_pool.py implementation values. A CPU profile
    # (configs/cpu-profiles/*.yaml) overrides these — see the config glue
    # in smoke_test/configs/two_level_taishan.py (--cov-profile).
    ibrFuCounts = VectorParam.Int([3, 1, 2, 2],
        "FU instance counts per IBR class [IntAdd, IntMul, FPAdd, FPMul]")
    ibrFuWidths = VectorParam.Int([128, 128, 256, 256],
        "Full input width (bits) per IBR class [IntAdd, IntMul, FPAdd, "
        "FPMul] (IntAdd/IntMul 2x64; FP 2x128 NEON lanes)")

    # --- ROI gating ---
    roiMode = Param.String(
        "m5ops",
        "ROI selection: 'm5ops' (workbegin/workend markers; the paper-"
        "aligned choice) | 'cycles' (roiBeginCycle..roiEndCycle) | 'all' "
        "(entire run)")
    roiBeginCycle = Param.UInt64(0, "ROI begin cycle (roiMode='cycles')")
    roiEndCycle = Param.UInt64(0, "ROI end cycle (roiMode='cycles'; 0 = end)")

    # --- detail dump (advice engine input, Task 6) ---
    writeDetail = Param.Bool(
        True, "Write harp_cov_detail.log (per-structure counters, "
        "per-phys-reg occupancy histogram, per-opclass issue mix — the "
        "evidence base for mutation advice)")
