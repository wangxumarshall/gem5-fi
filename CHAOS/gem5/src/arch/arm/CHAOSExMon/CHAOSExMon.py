from m5.params import *
from m5.SimObject import SimObject

class CHAOSExMon(SimObject):
    type = 'CHAOSExMon'
    cxx_class = 'gem5::CHAOSExMon'
    cxx_header = "arch/arm/CHAOSExMon/CHAOSExMon.hh"

    isa = Param.BaseISA(NULL, "Target BaseISA (the ArmISA; reached via cpu->isa[0])")
    cpu = Param.BaseCPU(NULL, "Owning CPU (for clockPeriod-correct inWindow; NULL = 1GHz fallback)")

    # §2.4 exclusive-monitor fault injector. Hooks ISA::handleLockedWrite
    # (the STXR success/failure decision) and — for the W8 O-series —
    # ISA::handleLockedRead (the reservation placement). mode:
    #   stxr_force_success: a STXR that would fail (lock_flag false / addr
    #     mismatch) is forced to succeed (the exclusive monitor's 'open↔
    #     exclusive' state is corrupted -> 本该失败的 STXR 成功). Models
    #     atomic-operation isolation violation (a race won that shouldn't).
    #   stxr_force_fail: a STXR that would succeed is forced to fail.
    #   o01_monitor_addr_bitflip (W8 O01, LSU 03): one architecturally-
    #     visible bit (>=6, cacheBlockMask'd) of LOCKADDR XORed at
    #     handleLockedRead — the reservation mismatches the STXR block;
    #     data untouched (retry absorbs => Masked; livelock => Timeout).
    #   o02_monitor_state_corrupt (W8 O02): 50% clear LOCKFLAG (valid清零),
    #     50% repoint LOCKADDR at the neighboring 64B block (伪造/旧值
    #     proxy; gem5 monitor = flag+addr only — version/granule don't
    #     exist, documented).
    mode = Param.String("stxr_force_success",
        "stxr_force_success | stxr_force_fail | o01_monitor_addr_bitflip | "
        "o02_monitor_state_corrupt")
    probability = Param.Float(1.0, "per-handleLockedWrite injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
    # LSU W8 (05 r2-r8): event-normalized trigger tier; "off" = legacy.
    # O-series (exclusive monitor/atomic) — works in SE (unlike TLB).
    # Multi-core semantics (O05-O07) require FS multi-core infrastructure.
    lsuTier = Param.String("off", "off | F0 | F1 | F2 | F3 | F4 | F5 | F6")
    lsuWarmupEvents = Param.UInt64(0, "eligible events skipped before arming")
    lsuSpanEvents = Param.UInt64(1000, "F0 uniform window size")
