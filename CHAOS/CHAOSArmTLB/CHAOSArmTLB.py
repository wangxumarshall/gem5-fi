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
    faultType = Param.String("bit_flip",
        "bit_flip | stuck_at_zero | stuck_at_one | random")
    faultMask = Param.UInt64(0,
        "64-bit mask applied to the pfn (bit positions to flip/force). 0 = "
        "random (bitsToChange bits).")
    bitsToChange = Param.Int(1, "Bits to change when faultMask=0")
    # §5.7B: field-level injection (targetField) + F5 pfn offset.
    targetField = Param.String("pfn",
        "TLB entry field to corrupt: pfn (page frame, default) | ap (access "
        "permissions) | xn (execute-never) | attridx (memory attributes via "
        "innerAttrs) | ng (nG via ignoreAsn) | asid (ASN). Field-level "
        "quantification of the TLB protection boundary.")
    pfnOffset = Param.UInt64(0,
        "F5 directed pfn offset: when nonzero, pfn += pfnOffset (a "
        "legal-domain substitute to ANOTHER page frame — proxy for "
        "'another live page'; hit mapped -> SDC, unmapped -> DUE). "
        "0 = legacy random-bit flip on pfn.")
    pfnSelectMode = Param.String("bit_flip",
        "pfn fault-selection mode (§5.7B): bit_flip = legacy random mask; "
        "mapped_page = pfn_to_mapped_page — substitute the hit entry's pfn "
        "with the pfn of ANOTHER valid entry in the same TLB (a live "
        "mapped page; the most dangerous silent-SDC path: no DUE guard can "
        "fire). Takes precedence over pfnOffset.")
    maxFaults = Param.UInt64(0, "Max faults to inject; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    # §2.3 N1 TRM proxy: L1 TLB has NO parity; L2 TLB has interleaved parity
    # (1-bit -> entry invalidated + rewalk; same-parity >=2-bit -> silent
    # escape). Modeled POST-injection: a 1-bit pfn fault under
    # parity_interleaved is DETECTED -> the entry is invalidated (the next
    # access rewalks — a benign refetch, behavior visible in refills),
    # NOT an SDC. >=2-bit (even parity delta) escapes silently.
    protectionModel = Param.String("none",
        "TLB protection model (§2.3): none = raw (L1, no parity — every "
        "fault escapes); parity_interleaved = L2-style parity: 1-bit "
        "pfn faults are detected, the entry is invalidated (refetch), "
        ">=2-bit same-parity faults escape silently.")
    logName = Param.String("armtlb_injections.log",
        "Injection log file name (distinguishes dTLB vs iTLB instances "
        "writing into the same outdir).")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
