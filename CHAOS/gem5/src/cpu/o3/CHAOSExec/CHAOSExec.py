from m5.params import *
from m5.SimObject import SimObject

class CHAOSExec(SimObject):
    type = 'CHAOSExec'
    cxx_class = 'gem5::CHAOSExec'
    cxx_header = "cpu/o3/CHAOSExec/CHAOSExec.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.12 integer execution-unit fault injector. Hooks DynInst::execute()
    # AFTER staticInst->execute(); filters by opClass (IntAluOp/IntMultOp/
    # IntDivOp); corrupts the integer result by a single-bit XOR.
    probability = Param.Float(1.0, "per-execute injection probability (use 1.0 + maxFaults=1)")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    faultMask = Param.UInt64(0, "bitmask for the integer result XOR (0 = random single bit)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    # v1.1 Phase 8.2 uniform sampling (design doc §1.7 rule 4): FIXED skip
    # from the driver's chaosPickSkip(seed, N_eligible) overrides the
    # legacy geometric(p=0.1) draw. UINT64_MAX sentinel = legacy behavior.
    eventsToSkip = Param.UInt64(0xFFFFFFFFFFFFFFFF,
        "FIXED number of eligible events to skip before the first "
        "injection (uniform-sampling mode). Default UINT64_MAX = legacy "
        "geometric(0.1) draw from rngSeed.")
    countOnly = Param.Bool(False,
        "v1.1 Phase 8.2 countOnlyMode: consume eligible events and print "
        "CHAOS_ELIGIBLE_COUNT=<n> at teardown, never corrupt.")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
