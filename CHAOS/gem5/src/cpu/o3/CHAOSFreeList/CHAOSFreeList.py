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
    #                it's a no-op (no UB).
    #   pop_wrong  : on getReg, return a different-but-LEGAL physReg id (same
    #                class, in [0,numPhys)) instead of the true front. The
    #                caller stores it as the dest physReg -> wrong mapping.
    mode = Param.String("mark_free", "mark_free | pop_wrong")

    probability = Param.Float(1.0,
        "per-getReg injection probability (use 1.0 with maxFaults=1)")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
