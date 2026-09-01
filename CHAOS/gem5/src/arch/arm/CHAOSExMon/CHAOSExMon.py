from m5.params import *
from m5.SimObject import SimObject

class CHAOSExMon(SimObject):
    type = 'CHAOSExMon'
    cxx_class = 'gem5::CHAOSExMon'
    cxx_header = "arch/arm/CHAOSExMon/CHAOSExMon.hh"

    isa = Param.BaseISA(NULL, "Target BaseISA (the ArmISA; reached via cpu->isa[0])")

    # §2.4 exclusive-monitor fault injector. Hooks ISA::handleLockedWrite
    # (the STXR success/failure decision). mode:
    #   stxr_force_success: a STXR that would fail (lock_flag false / addr
    #     mismatch) is forced to succeed (the exclusive monitor's 'open↔
    #     exclusive' state is corrupted -> 本该失败的 STXR 成功). Models
    #     atomic-operation isolation violation (a race won that shouldn't).
    #   stxr_force_fail: a STXR that would succeed is forced to fail.
    mode = Param.String("stxr_force_success",
        "stxr_force_success | stxr_force_fail")
    probability = Param.Float(1.0, "per-handleLockedWrite injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
