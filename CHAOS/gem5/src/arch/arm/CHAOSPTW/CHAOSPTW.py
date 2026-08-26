from m5.params import *
from m5.SimObject import SimObject

class CHAOSPTW(SimObject):
    type = "CHAOSPTW"
    cxx_class = "gem5::CHAOSPTW"
    cxx_header = "arch/arm/CHAOSPTW/CHAOSPTW.hh"

    mmu = Param.BaseMMU(NULL, "Target MMU (whose table-walker to hook)")
    probability = Param.Float(0.0, "Per-descriptor-fetch probability of bit-flipping the PTE")
    bitsToChange = Param.Int(1, "Bits to flip when faultMask=0")
    faultMask = Param.UInt32(0, "Explicit 8-bit mask (0=random bitsToChange)")
    byteOffset = Param.Int(-1, "Byte in the descriptor to flip (-1=random)")
    ptwEcc = Param.Bool(False, "Model PTW array ECC (H7: corrects single-bit)")
    firstClock = Param.UInt64(0, "First cycle eligible")
    lastClock = Param.UInt64(0, "Last cycle (0=unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0=unlimited)")
    rngSeed = Param.UInt64(0, "RNG seed (0=random)")
    writeLog = Param.Bool(True, "Write ptw_injections.log")
