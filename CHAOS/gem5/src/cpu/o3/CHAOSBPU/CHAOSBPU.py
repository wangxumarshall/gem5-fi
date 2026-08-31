from m5.params import *
from m5.SimObject import SimObject

class CHAOSBPU(SimObject):
    type = 'CHAOSBPU'
    cxx_class = 'gem5::CHAOSBPU'
    cxx_header = "cpu/o3/CHAOSBPU/CHAOSBPU.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.13 branch-prediction fault injector. Hooks BAC::predict AFTER
    # bpu->predict(); F5 substitutes the predicted direction (flip `taken`)
    # or target (mutate pc). Per doc §2.13: 'BPU itself producing SDC is not
    # the point — whether the wrong-path speculative flow it feeds leaks is'.
    mode = Param.String("dir_flip",
        "dir_flip: reverse the taken/not-taken prediction (F5 direction) | "
        "target_flip: flip a bit of the predicted PC target (F5 target)")
    probability = Param.Float(1.0, "per-predict injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    faultMask = Param.UInt64(0, "bitmask for target_flip (0 = random bit)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
