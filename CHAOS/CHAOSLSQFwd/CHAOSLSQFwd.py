# CHAOSLSQFwd — store-to-load forwarding-path fault injector for O3CPU.
#
# Injects bit-flips / stuck-at faults into the data forwarded from the store
# queue to a load (the memcpy at lsq_unit.cc FullAddrRangeCoverage branch),
# modeling the store-buffer forwarding-path corruption that reproduce-method2
# v3 localized to core 179's load/store unit (the reload `ldr` of just-read
# input, multi-bit, mantissa-concentrated, sign-immune). This is the only
# injection point that directly exercises method2's mechanism — CHAOSPhysReg
# corrupts a register cell; CHAOSLSQFwd corrupts the forwarding datapath.
#
# O3-only: attaches via a cpu-side hook (cpu->lsqFwd accessor in cpu.hh,
# called from lsq_unit.cc after the forward memcpy).
from m5.params import *
from m5.SimObject import SimObject


class CHAOSLSQFwd(SimObject):
    type = "CHAOSLSQFwd"
    cxx_class = "gem5::CHAOSLSQFwd"
    cxx_header = "cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    probability = Param.Float(0.0,
        "Per-forwarding-event probability of corrupting the forwarded data. "
        "0 = no injection; use e.g. 0.001 to corrupt ~1/1000 forwards.")

    faultType = Param.String("bit_flip",
        "bit_flip | stuck_at_zero | stuck_at_one | random")

    # P-D1: structural (whole-word) fault axis. Mutually orthogonal to the
    # per-byte bit-fault `faultType`. When set != "none", the structural path
    # takes precedence (a structural byte-lane skew is NOT expressible as a bit
    # flip). Models core-179's D1 signature: load returned rol_k(stale
    # array-head content) and all-zero deliveries (MICROARCH_SUPPLEMENT §2.2).
    structuralFault = Param.String("none",
        "none | byte_lane_skew | all_zero  (P-D1 structural fault)")
    skewBytes = Param.Int(0,
        "For byte_lane_skew: rotation amount (1..7). 0 = random 1..7 per event. "
        "15:58 crash matched rol1; 0814 matched rol6 — bit-exact.")

    faultMask = Param.UInt32(0,
        "Per-byte bitmask applied to the forwarded data (0 = random, "
        "bitsToChange bits). The mask is applied to ONE byte of the "
        "forwarded buffer selected by byteOffset (-1 = random byte).")
    bitsToChange = Param.Int(1, "Bits to change when faultMask=0")
    byteOffset = Param.Int(-1,
        "Which byte of the forwarded buffer to corrupt (-1 = random within "
        "[0, size-1]). method2's mantissa concentration comes from corrupting "
        "the low bytes of IEEE754 data.")

    firstClock = Param.UInt64(0, "First clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults to inject; 0 = unlimited")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
