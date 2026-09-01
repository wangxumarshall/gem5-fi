from m5.params import *
from m5.SimObject import SimObject

class CHAOSAddrPath(SimObject):
    type = "CHAOSAddrPath"
    cxx_class = "gem5::CHAOSAddrPath"
    cxx_header = "cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    mmu = Param.BaseMMU(NULL, "Target MMU (for the non-O3 translateTiming hook; NULL=O3 LSQ path only)")
    probability = Param.Float(0.0, "Per-load probability of zeroing a byte of the effAddr")
    byteOffset = Param.Int(7, "Which byte of effAddr to zero (7=MSB; -1=random)")
    firstClock = Param.UInt64(0, "First clock cycle eligible")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0 = unlimited)")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random)")
    writeLog = Param.Bool(True, "Write addr_path_injections.log")
