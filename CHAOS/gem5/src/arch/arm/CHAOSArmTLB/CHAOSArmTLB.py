from m5.params import *
from m5.SimObject import SimObject

# CHAOSArmTLB — ARM TLB-entry fault injector (Phase 3 §六.4 item 3).
#
# Hooks TLB::lookup (arch/arm/tlb.cc): on a TLB HIT, with probability
# `probability` per lookup (capped by maxFaults), corrupts the hit entry's
# `pfn` (physical frame number) by a bit-flip mask. The next translation
# that reuses this entry resolves to a WRONG physical address -> potential
# SDC (read/write the wrong page) or Crash (wrong page unmapped/fault).
# Models a defective TLB cell / translation-structure fault — invisible to
# register-only or cache-only injectors (the address-translation path).
# FS mode only (TLB lookups happen under the MMU in full-system).
class CHAOSArmTLB(SimObject):
    type = 'CHAOSArmTLB'
    cxx_class = 'gem5::CHAOSArmTLB'
    cxx_header = "arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh"

    tlb = Param.ArmTLB(NULL, "Target ArmTLB to inject into (the I or D TLB)")
    probability = Param.Float(0.0,
        "Per-lookup probability of corrupting a TLB hit's pfn (0..1).")
    firstClock = Param.UInt64(0, "First clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    # pfn_to_mapped_page (F5, Phase 4.4, FS-only): instead of an XOR into
    # (likely unmapped) space, substitute the hit entry's pfn with the pfn
    # of ANOTHER MAPPED entry in the same TLB (legal-domain substitution ->
    # silent wrong-page access, the method2 silent-SDC pathway). The other
    # four modes are bit-level on the hit entry's pfn.
    faultType = Param.String("bit_flip",
        "bit_flip | stuck_at_zero | stuck_at_one | random | "
        "pfn_to_mapped_page")
    faultMask = Param.UInt64(0,
        "64-bit mask applied to the pfn (bit positions to flip/force). 0 = "
        "random (bitsToChange bits).")
    bitsToChange = Param.Int(1, "Bits to change when faultMask=0")
    maxFaults = Param.UInt64(0, "Max faults to inject; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    protectionModel = Param.String("none",
        "§1.2 protection-aware modeling layer (N1 TRM Table 9-1 PROXY). "
        "L1 iTLB/dTLB = 'none' (TRM flop, no protection = raw escape, "
        "default, zero regression); L2 TLB / walk cache = 'parity_interleaved' "
        "(1-bit even/odd-independent: detect -> entry restored (undo, "
        "Corrected/DetectedContained-equivalent; real HW invalidates+re-walks, "
        "this restores the pfn before MMU use to model the same observable "
        "outcome re-entrancy-safely, E3); same-parity 2-bit / >=3-bit -> "
        "SilentEscape. Keyed on popcount(mask) (64-bit pfn). Does NOT "
        "convert to product FIT.")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
