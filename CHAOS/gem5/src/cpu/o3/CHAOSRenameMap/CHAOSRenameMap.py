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
    #   map_bitflip2 : W4.1 D12 (04-design-matrix R13) — flip TWO distinct
    #                  random bits of the physReg index (faultMask with >=2
    #                  set bits = directed control: its two lowest set bits).
    #                  Out-of-range flip on non-power-of-2 numPhysRegs is an
    #                  honest skip (logged, never clamped — hamming distance
    #                  between old/new phys idx is exactly 2 by construction).
    #   swap_to_active: W4.2a D13 (04-design-matrix R14, 换值·固定间隔) —
    #                  re-point arch_reg's entry at the dest physReg of a
    #                  RANDOM in-flight (ROB-resident) instruction (≠ the
    #                  current mapping): a legal, allocated, in-use physReg,
    #                  designed to bypass the dependency-check luck of the
    #                  bit-flip models. ROB empty / no candidate = honest
    #                  skip (logged). Log line carries new_phys=Z(active,
    #                  rob_dist=D) + the full ROB-active dest pool as the
    #                  "new_phys ∈ ROB active set" evidence.
    #   f5_substitute: point arch_reg's entry at ANOTHER CURRENTLY-ALLOCATED
    #                  (= not in the free list) physReg of the same class —
    #                  legal-domain substitution (§2.2 F5).
    #   f4_field_stuck: pin ONE map entry to a wrong physReg permanently
    #                  (every setEntry on that arch_reg re-applies the wrong
    #                  target) — §2.2 f4_field_stuck.
    # spec_leak (§2.3 Phase 4.1, method1 speculative-state leak): suppress
    # ONE history-buffer rollback in Rename::doSquash — the wrong-path µop's
    # dest reg stays mapped, its wrong-path value leaks into the correct
    # path (the rollback-suppression, not a value flip).
    mode = Param.String("map_bitflip",
        "map_bitflip | map_bitflip2 | swap_to_active | f5_substitute | "
        "f4_field_stuck | spec_leak")

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
