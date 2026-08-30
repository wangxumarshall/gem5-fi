# CHAOSPTW — page-table-walker readout fault injector (P-D3) for ARM (plan §5.7, S2-5c).
#
# Core 179's D3 signature (MICROARCH_SUPPLEMENT §2.4): 73 transient translation-
# fault warnings on VALID static mappings (ESR 0x96000044 / 0x96000004) — the
# hardware page-table walker transiently mis-read a page-table entry, the
# immediate AT-retry succeeded. This is the PTW readout data-path, sibling to
# D1 (load data path) and D2 (address path).
#
# Hooks the ARM table walker's doLongDescriptor to bit-flip a freshly-fetched
# descriptor (PTE) before evaluation. If the flip clears the valid bits, the
# entry becomes invalid -> translation fault, reproducing the spurious symptom.
# `ptwEcc` models whether the PTW array has ECC (H7: ECC-on corrects single-bit).
#
# FS MODE REQUIRED (FI_DESIGN_SUPPLEMENT §3): gem5 SE uses translateMmuOff
# (mmu.cc:1213, SCTLR.M=0) -> setPaddr(vaddr) identity mapping, NEVER calls the
# table walker, so numFaultsInjected=0. Only FS (SCTLR.M=1 after Linux boots)
# routes through the real TLB->PTW->doLongDescriptor, where the hook fires.

from m5.params import *
from m5.SimObject import SimObject


class CHAOSPTW(SimObject):
    type = "CHAOSPTW"
    cxx_class = "gem5::CHAOSPTW"
    cxx_header = "arch/arm/CHAOSPTW/CHAOSPTW.hh"

    mmu = Param.BaseMMU(NULL, "Target MMU (whose table-walker to hook)")
    probability = Param.Float(0.0,
        "Per-descriptor-fetch probability of bit-flipping the PTE. 0 = no "
        "injection; FS required (SE never walks the table).")
    bitsToChange = Param.Int(1, "Bits to flip when faultMask=0")
    faultMask = Param.UInt64(0,
        "64-bit mask applied to the descriptor (0=random bitsToChange bits). "
        "Bit positions in the PTE byte at byteOffset.")
    byteOffset = Param.Int(-1,
        "Byte in the descriptor to flip (-1=random 0..7).")
    clearValidBit = Param.Bool(False,
        "If true, force-clear the descriptor valid bits[1:0] (AND ~0x3) — "
        "reliably manufactures spurious translation faults (2-bit, bypasses "
        "ECC). Reproduces core179's 73 spurious ESR=0x96000044 warnings.")
    ptwEcc = Param.Bool(False,
        "Model PTW array ECC (H7 self-variable: ECC-on corrects single-bit "
        "flips -> numFaultsInjected=0; ECC-off lets the flip through).")
    firstClock = Param.UInt64(0,
        "First sim TICK eligible (curTick domain, NOT CPU cycles — the walker "
        "isn't a ClockedObject; consistent with CHAOSArmTLB D1 fix). FS: set "
        "after MMU-on (Linux boot) to avoid boot-path noise.")
    lastClock = Param.UInt64(0, "Last tick (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0 = unlimited). Use 1 for single-fault.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device). Nonzero = reproducible.")
    writeLog = Param.Bool(True, "Write ptw_injections.log")
