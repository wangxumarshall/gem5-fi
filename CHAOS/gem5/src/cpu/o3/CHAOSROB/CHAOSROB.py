from m5.params import *
from m5.SimObject import SimObject

class CHAOSROB(SimObject):
    type = 'CHAOSROB'
    cxx_class = 'gem5::CHAOSROB'
    cxx_header = "cpu/o3/CHAOSROB/CHAOSROB.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.3 ROB modes:
    #   entry_bitflip: at retireHead, flip a bit of a ROB entry field (field=
    #                  result|done|exc_status|dest_phys|spec) at distance D
    #                  from the head. Stratifies 'time-to-commit'.
    #   exc_suppress:  clear the head's fault/exception-status bit before
    #                  retireHead -> a fault that should raise SError/DUE is
    #                  silently swallowed (quantifies 'DUE->SDC conversion').
    #   spec_leak:     on squash, RETAIN one wrong-path µop's phys-reg write
    #                  (speculative state leak, method1) — TODO (needs squash
    #                  path edit; deferred to a follow-up §2.3 patch).
    mode = Param.String("entry_bitflip",
        "entry_bitflip | exc_suppress (spec_leak deferred)")

    field = Param.String("exc_status",
        "result | done | exc_status | dest_phys | spec (entry_bitflip field)")
    distanceFromHead = Param.Int(0,
        "inject into the entry D slots from the ROB head; -1=random. "
        "Stratifies time-to-commit (D=0 = head).")

    probability = Param.Float(1.0, "per-retireHead injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    faultMask = Param.UInt64(0, "bitmask for entry_bitflip (0=random single bit)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
