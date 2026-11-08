from m5.params import *
from m5.SimObject import SimObject

class CHAOSMD04(SimObject):
    type = 'CHAOSMD04'
    cxx_class = 'gem5::CHAOSMD04'
    cxx_header = "cpu/o3/CHAOSMD04/CHAOSMD04.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(1.0, "per-eligible-alias injection probability")
    firstClock = Param.UInt64(0, "first cycle eligible")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(1, "max faults; 0 = unlimited")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    eventOrdinal = Param.UInt64(0,
        "1-based eligible alias ordinal to suppress (0 = first)")
    countOnly = Param.Bool(False, "count eligible aliases, never inject")
    writeLog = Param.Bool(True, "write md04_injections.log")
