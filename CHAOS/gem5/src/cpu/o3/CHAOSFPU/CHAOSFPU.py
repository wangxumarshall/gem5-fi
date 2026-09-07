from m5.params import *
from m5.SimObject import SimObject

class CHAOSFPU(SimObject):
    type = 'CHAOSFPU'
    cxx_class = 'gem5::CHAOSFPU'
    cxx_header = "cpu/o3/CHAOSFPU/CHAOSFPU.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.6 floating-point / vector execution-unit fault injector. Hooks
    # DynInst::execute() AFTER staticInst->execute(); filters by opClass
    # (FloatAdd/FloatMult/FloatMultAcc + SimdFloat*); corrupts the FP result
    # blob by a single-bit XOR (IEEE754 sign/exp/mantissa bit).
    probability = Param.Float(1.0, "per-execute injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    faultMask = Param.UInt64(0, "bitmask for the FP result XOR (0 = random single bit)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    # v1.1 Phase 8.2 uniform sampling (design doc §1.7 rule 4): the driver
    # dry-runs countOnly to learn N_eligible, then passes a FIXED uniform
    # skip here (chaosPickSkip(seed, N) from cpu/o3/chaos_event_sample.hh).
    # Default UINT64_MAX sentinel = legacy geometric(p=0.1) draw, so every
    # existing campaign replays byte-identically.
    eventsToSkip = Param.UInt64(0xFFFFFFFFFFFFFFFF,
        "FIXED number of eligible events to skip before the first "
        "injection (uniform-sampling mode). Default UINT64_MAX = legacy "
        "geometric(0.1) draw from rngSeed.")
    countOnly = Param.Bool(False,
        "v1.1 Phase 8.2 countOnlyMode: consume eligible events and print "
        "CHAOS_ELIGIBLE_COUNT=<n> at teardown, never corrupt.")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
