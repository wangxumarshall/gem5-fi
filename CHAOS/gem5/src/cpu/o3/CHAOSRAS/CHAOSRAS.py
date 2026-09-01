from m5.params import *
from m5.SimObject import SimObject

class CHAOSRAS(SimObject):
    type = 'CHAOSRAS'
    cxx_class = 'gem5::CHAOSRAS'
    cxx_header = "cpu/o3/CHAOSRAS/CHAOSRAS.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.18 RAS-escape injector. Hooks Commit::commitHead at the fault-check
    # (commit.cc:1161). Modes:
    #   exc_suppress: clear the head's fault (NoFault) -> a pending SError/DUE
    #     is silently swallowed at commit (models 'ROB exception bit → DUE-to-
    #     SDC conversion' at the commit level; §2.18 says 'exc_suppress (与 §7
    #     ROB 共用逻辑)' — same effect at commit instead of ROB-retire).
    #   errrec_bitflip: (deferred — needs ERR* miscReg write path hook)
    #   poison_lose: (deferred — needs poison bit in store buffer/PRF)
    mode = Param.String("exc_suppress",
        "exc_suppress: clear the commit-time fault (DUE swallowed)")
    probability = Param.Float(1.0, "per-commitHead injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
