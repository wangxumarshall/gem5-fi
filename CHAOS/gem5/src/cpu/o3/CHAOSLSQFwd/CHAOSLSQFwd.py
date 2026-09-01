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
    faultMask = Param.UInt64(0,
        "64-bit bitmask applied to the forwarded data (0 = random, "
        "bitsToChange bits). D2 fix (was UInt32 + &0xff single-byte): the "
        "mask now spans maskWidth consecutive bytes (little-endian) starting "
        "at byteOffset, so high bytes (e.g. 1<<32) are reachable to reproduce "
        "method2's high-byte/multi-byte signatures. Default maskWidth=1 "
        "preserves the legacy single-byte behavior.")
    maskWidth = Param.Int(1,
        "Number of consecutive bytes the 64-bit faultMask covers (little-"
        "endian), within [1,8]. 1 = legacy single-byte (mask truncated to "
        "8 bits); 2/4/8 = multi-byte corruption for method2's cross-byte "
        "spectra. Clamped to min(maskWidth, fwdSize, 8).")
    # S1-5: structural (whole-word) faults (P-D1, core 179 D1 signature).
    # These re-route the entire delivered word — cannot be expressed as a bit
    # flip (verified bit-exact against crash values), so they are a separate
    # axis that takes precedence over the per-byte faultType path when set.
    structuralFault = Param.String("none",
        "none | byte_lane_skew | all_zero (P-D1 structural fault). "
        "byte_lane_skew: right-rotate the delivered byte array by skewBytes "
        "(core 179 D1: 15:58 rol1, 0814 rol6 — bit-exact). "
        "all_zero: deliver an all-zero word (15:42 empty-slot signature). "
        "When != none, takes precedence over faultType/faultMask.")
    skewBytes = Param.Int(0,
        "For byte_lane_skew: right-rotation amount (1..7). 0 = random 1..7 "
        "per event. 15:58 crash matched rol1; 0814 matched rol6 — bit-exact.")
    # S6-1/S6-2: source-substitution faults (forward-source F5 + stale line).
    # Substitutes the memcpy source with a STALE historical buffer (a
    # previously-seen store's data) BEFORE the forward memcpy.
    sourceFault = Param.String("none",
        "none | fwd_source_sub | stale_line_replay | phase_offset. "
        "fwd_source_sub: stale buffer as forward source (wrong-store F5). "
        "stale_line_replay: stale fill-buffer line. "
        "phase_offset: F6 — return the history entry N steps back (phaseOffset "
        "param), modeling a timing-phase race (method3 100%->10-20% signature). "
        "When != none, takes precedence at the memcpy-source step.")
    phaseOffset = Param.Int(1,
        "F6 phase offset N (history depth, 1..HIST_CAP). Used with "
        "sourceFault=phase_offset: return the history entry N steps back. "
        "Reproduces method3 timing-phase race (no-op ALU -> 100%->10-20%).")
    bitsToChange = Param.Int(1, "Bits to change when faultMask=0")
    byteOffset = Param.Int(-1,
        "Which byte of the forwarded buffer to corrupt (-1 = random within "
        "[0, size-1]). method2's mantissa concentration comes from corrupting "
        "the low bytes of IEEE754 data. With maskWidth>1, this is the LOW "
        "byte of the masked window.")

    firstClock = Param.UInt64(0, "First clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults to inject; 0 = unlimited")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
