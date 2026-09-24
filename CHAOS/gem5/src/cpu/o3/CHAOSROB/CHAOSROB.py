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
    # W5.1-W5.3 (ooo 04-design-matrix D25-D31, Int Dispatch/ROB) — the
    # ROB-entry WRITE-path site (ROB::insertInst; the TC'23 site, the entry
    # is corrupted as it is written into the ROB):
    #   pc_bitflip/pc_bitflip2 (D25/D26): flip 1/2 random bits of the
    #                  entry's PC field (pcState pc address, ~48-bit space).
    #   pc_stuck (D27, F5): ONE entry's PC bit permanently forced 0/1
    #                  (write-path mask at the entry write + retire readback).
    #   destid_bitflip/destid_bitflip2 (D28/D29): flip 1/2 random bits of
    #                  the entry's int dest physReg identifier.
    #   destid_swap_active (D30): replace it with the dest physReg of
    #                  another ROB-resident in-flight instruction (legal
    #                  domain, designed to bypass the dependency check).
    #   destid_stuck (D31, F5): ONE entry's dest-id bit stuck-at 0/1.
    mode = Param.String("entry_bitflip",
        "entry_bitflip | exc_suppress | pc_bitflip | pc_bitflip2 | pc_stuck"
        " | destid_bitflip | destid_bitflip2 | destid_swap_active"
        " | destid_stuck (spec_leak deferred)")

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
