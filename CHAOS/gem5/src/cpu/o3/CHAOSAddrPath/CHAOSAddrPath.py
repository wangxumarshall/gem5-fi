# CHAOSAddrPath — address-path fault injector (P-D2) for O3CPU.
#
# Core 179's D2 signature (MICROARCH_SUPPLEMENT §2.3): the MSB byte of the
# address presented to the MMU was forced to 0 (0814: d9->00; 0824: 55->00),
# while the architectural register held the true computed value. This is an
# address-PATH corruption distinct from the data-path D1.
#
# This injector zeroes one byte of a load's virtual address in
# LSQ::LSQRequest::sendFragmentToTranslation, BEFORE the MMU translates it.
# The corrupted vaddr is what the PTW/MMU actually walks — reproducing
# core 179's D2 (arch MSB d9 -> MMU saw 00).
#
# FS MODE REQUIRED (FI_DESIGN_SUPPLEMENT §3): gem5 SE uses translateMmuOff
# (mmu.cc:1213, SCTLR.M=0) -> setPaddr(vaddr) identity mapping, so a byte7-zeroed
# vaddr still lands in physical memory and does NOT fault. Only FS mode
# (SCTLR.M=1 after Linux boots) routes through the real TLB->PTW->doLongDescriptor,
# where a non-canonical address (byte7 zeroed) raises a translation fault
# (ESR 0x96000004 / 0x96000044, matching core 179).
#
# O3-only: attaches via the CPU's `addrPath` accessor (cpu.hh, set in its
# constructor — self-attach, same pattern as CHAOSLSQFwd/CHAOSArmTLB).

from m5.params import *
from m5.SimObject import SimObject


class CHAOSAddrPath(SimObject):
    type = "CHAOSAddrPath"
    cxx_class = "gem5::CHAOSAddrPath"
    cxx_header = "cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")
    probability = Param.Float(0.0,
        "Per-load probability of zeroing a byte of the effAddr. 0 = no "
        "injection; use 1.0 with maxFaults=1 for a single directed fault.")
    byteOffset = Param.Int(7,
        "Which byte of effAddr to zero (7=MSB bits 56..63; -1=random 0..7). "
        "Default 7 reproduces core 179 D2 (MSB forced to 0).")
    firstClock = Param.UInt64(0,
        "First sim TICK eligible for injection (curTick domain, NOT CPU "
        "cycles — the LSQ is not a ClockedObject; consistent with CHAOSArmTLB "
        "D1 fix). FS: set after MMU-on (Linux boot) to avoid boot-path noise.")
    lastClock = Param.UInt64(0, "Last tick (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults (0 = unlimited). Use 1 for single-fault.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device). Nonzero = reproducible.")
    writeLog = Param.Bool(True, "Write addr_path_injections.log")
