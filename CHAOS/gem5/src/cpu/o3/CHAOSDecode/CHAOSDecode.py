from m5.params import *
from m5.SimObject import SimObject

class CHAOSDecode(SimObject):
    type = 'CHAOSDecode'
    cxx_class = 'gem5::CHAOSDecode'
    cxx_header = "cpu/o3/CHAOSDecode/CHAOSDecode.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.14 decode-unit fault injector. Hooks rename.cc:1137 AFTER
    # flattenedDestIdx is set (per-INST, NOT shared staticInst — safe).
    # dest_reg_sub (F5): replace the dest arch reg index with another legal
    #   integer reg 0-30 (zhang-guan-li-dai on the DEST, not the mapping).
    # HONEST: srcRegIdx/imm/opClass are NOT done — srcRegIdx reads shared
    #   staticInst (unsafe to mutate); imm/opClass need StaticInst clone.
    #   dest_reg_sub is the safe per-inst subset (the _flatDestIdx array is
    #   per-DynInst).
    mode = Param.String("dest_reg_sub",
        "dest_reg_sub (F5): point the dest arch reg at another legal 0-30 reg")
    probability = Param.Float(1.0, "per-decode injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
