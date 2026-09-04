from m5.params import *
from m5.SimObject import SimObject

class CHAOSRenameMap(SimObject):
    type = 'CHAOSRenameMap'
    cxx_class = 'gem5::CHAOSRenameMap'
    cxx_header = "cpu/o3/CHAOSRenameMap/CHAOSRenameMap.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.2 injection mode:
    #   map_bitflip  : after setEntry, remap arch_reg's entry to a DIFFERENT
    #                  valid physReg (XOR a bit of the physReg index — realized
    #                  as a 1-bit remap to another legal physReg, the method1
    #                  "张冠李戴" semantics; §2.2 map_bitflip).
    #   f5_substitute: point arch_reg's entry at ANOTHER CURRENTLY-ALLOCATED
    #                  (= not in the free list) physReg of the same class —
    #                  legal-domain substitution (§2.2 F5).
    #   f4_field_stuck: pin ONE map entry to a wrong physReg permanently
    #                  (every setEntry on that arch_reg re-applies the wrong
    #                  target) — §2.2 f4_field_stuck.
    mode = Param.String("map_bitflip",
        "map_bitflip | f5_substitute | f4_field_stuck")

    targetArchReg = Param.Int(-1,
        "which architectural reg's map entry to corrupt (-1 = random within "
        "the integer class, 0-30 on aarch64 X0-X30). The method1 'long-lived "
        "accumulator' is X3/X19-X28 — target the cross-inner-loop accumulator.")

    probability = Param.Float(1.0,
        "per-setEntry injection probability (use 1.0 with maxFaults=1 so the "
        "single injection lands at firstClock on the next eligible setEntry)")

    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")

    faultMask = Param.UInt64(0,
        "bitmask for map_bitflip: which physReg-index bit to flip (0 = random "
        "bit in [0, log2(numPhysRegs)))")

    maxFaults = Param.UInt64(0,
        "max faults to inject; 0 = unlimited. Use 1 for single-fault campaigns.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")

    writeLog = Param.Bool(True, "Write a fault_injections.log file")
