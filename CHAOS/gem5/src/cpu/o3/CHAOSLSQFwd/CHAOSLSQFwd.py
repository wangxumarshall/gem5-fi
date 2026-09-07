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
        "§2.4: 64-bit (was UInt32 — truncated bit>=32). Per-byte bitmask "
        "applied to the forwarded data (0 = random, bitsToChange bits). "
        "Applied to ONE byte selected by byteOffset (-1 = random byte).")
    bitsToChange = Param.Int(1, "Bits to change when faultMask=0")
    byteOffset = Param.Int(-1,
        "Which byte of the forwarded buffer to corrupt (-1 = random within "
        "[0, size-1]). method2's mantissa concentration comes from corrupting "
        "the low bytes of IEEE754 data.")
    # §2.4 structured fault mode (from fi-h6-h7 branch, H5 closed):
    structMode = Param.String("byte_flip",
        "byte_flip (default, orig) | byte_lane_skew (rol_k rotate the whole "
        "forwarded buffer by laneSkewK bytes — core179 D1 byte-lane phase "
        "signature) | all_zero (zero the whole 8-byte buffer) | "
        "fwd_source_sub (F5 Phase 4.2: forward from the WRONG older SQ "
        "entry — method1 wrong-source store->load forwarding)")
    laneSkewK = Param.Int(1, "§2.4 byte_lane_skew: rotate by k bytes (default 1)")

    firstClock = Param.UInt64(0, "First clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "Last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "Max faults to inject; 0 = unlimited")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    # v1.1 Phase 8.2 uniform sampling (design doc §1.7 rule 4): FIXED skip
    # from the driver's chaosPickSkip(seed, N_eligible) overrides the
    # legacy geometric(p=0.1) draw. UINT64_MAX sentinel = legacy behavior.
    eventsToSkip = Param.UInt64(0xFFFFFFFFFFFFFFFF,
        "FIXED number of eligible events to skip before the first "
        "injection (uniform-sampling mode). Default UINT64_MAX = legacy "
        "geometric(0.1) draw from rngSeed.")
    countOnly = Param.Bool(False,
        "v1.1 Phase 8.2 countOnlyMode: consume eligible events and print "
        "CHAOS_ELIGIBLE_COUNT=<n> at teardown, never corrupt.")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
