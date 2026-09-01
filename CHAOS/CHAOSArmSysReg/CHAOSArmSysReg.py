from m5.params import *
from m5.SimObject import SimObject

# CHAOSArmSysReg — ARM system-register fault injector (Phase 3 §六.4 item 3).
#
# Hooks ISA::readMiscRegNoEffect (arch/arm/isa.cc): when a system register in
# the `targetRegs` whitelist is read, with probability `probability` per read
# (capped by maxFaults), corrupts the returned value by a bit-flip mask. The
# reading instruction (MRS) thus gets a WRONG system-register value -> models
# a defective system-register cell or a read-path fault. FS mode (system
# registers are architectural state touched by MRS/MSR in full-system).
#
# Whitelist model: only target a handful of high-value control registers
# (TTBR0/1_EL1, TCR_EL1, SCTLR_EL1, MAIR_EL1, VBAR_EL1, NZCV/FPSR) by MiscReg
# enum NAME. This is the §六 item-3 'system register whitelist' intent
# (TTBR/TCR/MAIR/SCTLR/VBAR/NZCV). An empty whitelist = no injection.
class CHAOSArmSysReg(SimObject):
    type = 'CHAOSArmSysReg'
    cxx_class = 'gem5::CHAOSArmSysReg'
    cxx_header = "arch/arm/CHAOSArmSysReg/CHAOSArmSysReg.hh"

    isa = Param.ArmISA(NULL, "Target ArmISA (the ISA holding the miscRegs)")
    probability = Param.Float(0.0,
        "Per-read probability of corrupting a whitelisted sys-reg read (0..1).")
    firstClock = Param.UInt64(0, "First clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    faultType = Param.String("bit_flip",
        # (updated doc; the m5 Param system takes the second positional as
        # the doc string — keep one string, note value_to_legal in help)
        "bit_flip | stuck_at_zero | stuck_at_one | random")
    faultMask = Param.UInt64(0,
        "64-bit mask applied to the sys-reg value (bit positions). 0=random.")
    bitsToChange = Param.Int(1, "Bits to change when faultMask=0")
    targetRegs = Param.String("",
        "Comma-separated ARM miscRegName strings (the whitelist). These are "
        "the LOWERCASE names in ArmISA::miscRegName[] (misc.hh), NOT the "
        "MISCREG_ enum names — e.g. 'sctlr_el1,ttbr0_el1,ttbr1_el1,"
        "tcr_el1,mair_el1,vbar_el1'. Use grep on misc.hh:1359 for the full "
        "list. Unknown names are skipped with a warning. Empty = none.")
    maxFaults = Param.UInt64(0, "Max faults to inject; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
