from m5.params import *
from m5.SimObject import SimObject

class CHAOSL1DForward(SimObject):
    type = 'CHAOSL1DForward'
    cxx_class = 'gem5::CHAOSL1DForward'
    cxx_header = "cpu/o3/CHAOSL1DForward/CHAOSL1DForward.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.7 post-check escape injector. Hooks LSQUnit::completeDataAccess at
    # load completion — AFTER the data has come back from L1D (model: ECC
    # checked and passed) and BEFORE writeback to the register. The mask is
    # applied to the response packet data -> models the "post-check escape"
    # path (ECC can't catch it; the corruption is on the datapath between
    # cache and PRF). §2.7 H.③ asserts P_SDC >= raw cache injection (upper bound).
    probability = Param.Float(1.0, "per-load-complete injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    faultMask = Param.UInt64(0, "bitmask for the load data XOR (0 = random single bit)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
