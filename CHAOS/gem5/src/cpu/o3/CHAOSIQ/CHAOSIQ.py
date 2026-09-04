from m5.params import *
from m5.SimObject import SimObject

class CHAOSIQ(SimObject):
    type = 'CHAOSIQ'
    cxx_class = 'gem5::CHAOSIQ'
    cxx_header = "cpu/o3/CHAOSIQ/CHAOSIQ.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.5 IQ modes:
    #   wake_omit (F6): on wakeDependents, DROP one wakeup broadcast — the
    #                   completed instruction's dependents stay not-ready (one
    #                   missed wake). Models method3 timing-race phase shift.
    #   src_ready_bitflip / tag_sub (F5): mark a not-ready µop's source ready
    #                   (or swap src tag to another in-flight µop's legal tag)
    #                   — needs dependency-graph traversal; DEFERRED (§2.5
    #                   patch 2).
    mode = Param.String("wake_omit", "wake_omit (src_ready_bitflip/tag_sub deferred)")
    phaseOffset = Param.Int(0, "F6 wake_phase: cycles to advance(-)/delay(+) — proxy")
    probability = Param.Float(1.0, "per-wakeDependents injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
