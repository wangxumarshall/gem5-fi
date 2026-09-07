from m5.params import *
from m5.SimObject import SimObject

class CHAOSFPU(SimObject):
    type = 'CHAOSFPU'
    cxx_class = 'gem5::CHAOSFPU'
    cxx_header = "cpu/o3/CHAOSFPU/CHAOSFPU.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.6 floating-point / vector execution-unit fault injector. Hooks
    # DynInst::execute() AFTER staticInst->execute(); filters by opClass
    # (FloatAdd/FloatMult/FloatMultAcc + SimdFloat*); corrupts the FP result
    # blob by a single-bit XOR (IEEE754 sign/exp/mantissa bit).
    probability = Param.Float(1.0, "per-execute injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    faultMask = Param.UInt64(0, "bitmask for the FP result XOR (0 = random single bit)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    # v1.1 Phase 8.2 uniform sampling (design doc §1.7 rule 4): the driver
    # dry-runs countOnly to learn N_eligible, then passes a FIXED uniform
    # skip here (chaosPickSkip(seed, N) from cpu/o3/chaos_event_sample.hh).
    # Default UINT64_MAX sentinel = legacy geometric(p=0.1) draw, so every
    # existing campaign replays byte-identically.
    eventsToSkip = Param.UInt64(0xFFFFFFFFFFFFFFFF,
        "FIXED number of eligible events to skip before the first "
        "injection (uniform-sampling mode). Default UINT64_MAX = legacy "
        "geometric(0.1) draw from rngSeed.")
    countOnly = Param.Bool(False,
        "v1.1 Phase 8.2 countOnlyMode: consume eligible events and print "
        "CHAOS_ELIGIBLE_COUNT=<n> at teardown, never corrupt.")
    # v1.1 Phase 9 patch 1a mode 1 — bitseg: flip bits ONLY within the
    # chosen IEEE754 field of the FP result (instead of a uniform whole-
    # register bit). Matches method3's mantissa-concentrated signature.
    # '' (default) = legacy uniform whole-register pick.
    bitseg = Param.String("", "FP bit segment: sign | exp_hi | exp_lo | "
                              "mant_hi | mant_mid | mant_lo ('' = uniform)")
    # v1.1 Phase 9 patch 1a mode 2 — fma_intermediate (E3 BEHAVIORAL
    # PROXY, not a microarchitectural replay): gem5's ARM FP is a pure
    # functional model (arch/arm/fplib.cc fplibMulAdd) with no real
    # alignment-shift/partial-product/normalization hardware, so the
    # pre-rounding FMA intermediate cannot be reached. Plan fallback (b):
    # draw the flip bit from a method3-matched weighted field
    # distribution on the FINAL result — mant 85% / exp 10% / sign 5%,
    # with the mantissa draw uniform over its 52 bits. The doc records
    # this as an E3 behavioral proxy.
    fmaWeighted = Param.Bool(False, "fma_intermediate mode: weighted "
                                    "field draw (mant 85% / exp 10% / "
                                    "sign 5%) on the final result")
    # v1.1 Phase 9 patch 1a mode 3 — recurring_result_stuck: the SAME
    # fixed mask is applied to EVERY opClass-eligible FSU result (modeling
    # a stuck multiplier partial-product bit — the literature's dominant
    # execution-unit SDC source). The mask is drawn once (first eligible
    # event) and reused. Runs with maxFaults=0 (unlimited; the Phase 8.4
    # runner contract enforces the pairing). Skip consumption is disabled
    # in this mode (every event is hit).
    recurringStuck = Param.Bool(False, "recurring_result_stuck mode: same "
                                       "fixed mask on every eligible result")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
