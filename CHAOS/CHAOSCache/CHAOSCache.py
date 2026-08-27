from m5.params import *
from m5.proxy import *
from m5.SimObject import SimObject

class CHAOSCache(SimObject):
    type = 'CHAOSCache'
    cxx_header = "mem/cache/CHAOSCache/CHAOSCache.hh"
    cxx_class = 'gem5::CHAOSCache'
    target_cache = Param.Cache("Cache da corrompere")
    probability = Param.Float(0.0, "Probability (between 0 and 1) of injecting faults")
    bitsToChange = Param.Int(-1, "Bit to modify per byte")
    faultMask = Param.String("0", "Bit mask to be applied to the target cache packet value")
    corruptionSize = Param.Int(1, "Bytes to modify")
    firstClock = Param.UInt64(0, "Clock cycle after which fault injection starts")
    lastClock = Param.UInt64(0, "Clock cycle after which fault injection stops")
    faultType = Param.String("random", "Fault type: bit_flip, stuck_at_zero, stuck_at_one")
    tickToClockRatio = Param.Int(1000, "Ratio between tick and clock cycle (tick/cycle)")
    bitFlipProb = Param.Float(0.9, "Probability (between 0 and 1) of injecting a bit flip fault on 'random' fault type")
    stuckAtZeroProb = Param.Float(0.05, "Probability (between 0 and 1) of injecting a stuck-at-zero fault on 'random' fault type")
    stuckAtOneProb = Param.Float(0.05, "Probability (between 0 and 1) of injecting a stuck-at-one flip fault on 'random' fault type")
    cyclesPermamentFaultCheck = Param.Int(1, "Number of cycles between each periodic check for permanent faults.")
    rngSeed = Param.UInt64(0, "Seed for the injection RNG (std::mt19937). 0 = seed from std::random_device (original, NON-reproducible behavior). Nonzero = fixed seed for reproducible block/byte/mask selection.")
    maxFaults = Param.UInt64(0, "G5: maximum number of faults to inject; 0 = unlimited (original). Use 1 for single-fault campaigns.")
    targetBlockAddr = Param.Addr(0, "Directed: pin the fault to the cache block "
        "containing this address (block-aligned lookup among VALID blocks). "
        "0 = random block (original). Use to land a fault on a live-data "
        "byte (L1D) or an executed instruction byte (L1I) — report §六.3 "
        "'fixed-to' runs. If the block is not valid/resident at injection "
        "time, falls back to random with a log warning.")
    targetByteOffset = Param.Int(-1, "Directed: pin the fault to this byte "
        "offset within the target block (0..blockSize-1). -1 = random "
        "byte (original).")
    writeLog = Param.Bool(True, "Write a log file")