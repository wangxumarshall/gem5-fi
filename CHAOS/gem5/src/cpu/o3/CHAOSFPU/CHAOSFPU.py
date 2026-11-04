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
    # [FSU][D3] Precision and lane geometry. The field table is selected by
    # precision; the selected bit must fit inside the storage lane. FP64
    # fields require laneWidth=64; FP32 fields require laneWidth >= 32.
    # [FSU][FR07-HOOK v2] Real PRF writeback-data boundary: arm before
    # execute, route the destination write through a shadow WB buffer /
    # pre-store mask, then commit the masked value to the PRF. Requires an
    # explicit faultMask and an F0-style single-fault mode. Default false
    # keeps every existing (post-execute rewrite) campaign byte-identical.
    prfWbHook = Param.Bool(False,
        "FR07 v2: inject at the PRF writeback-data boundary (pre-PRF-write "
        "shadow/pre-store mask) instead of rewriting the PRF cell after "
        "execute")
    precision = Param.String("fp64", "FP precision for field selection: "
                                     "fp64 | fp32")
    laneWidth = Param.UInt32(64, "Storage lane width in bits: 8 | 16 | 32 | 64")
    laneOffset = Param.UInt32(0, "Lane index inside the 128-bit register; "
                                 "valid range [0, 128/laneWidth)")
    # [FSU][D3] Dynamic decode guard: reject a candidate unless its real
    # AArch64 encoding proves the configured precision/element width/lane.
    # Default false keeps every legacy campaign byte-identical.
    decodeGuard = Param.Bool(False,
        "Reject candidates whose decoded precision/element width/lane does "
        "not match the manifest (fail closed). Formal D3 runs enable this.")
    # [FSU][FP06] Explicit eligible-stream filters. opClasses is a
    # comma-separated allowlist of gem5 OpClass names (FloatAdd,
    # FloatMultAcc, ..., SimdFloat*); '' = every FP opClass the injector
    # already accepted (legacy behavior). regClass restricts the TARGET
    # destination register class: '' / any | vec | float | vec_elem.
    # Unknown names panic in the constructor (fail closed). The countOnly
    # census and the injection path share the exact same predicate, and the
    # census emits CHAOS_ELIGIBLE_OPCLASS / CHAOS_ELIGIBLE_REGCLASS counts.
    opClasses = Param.String("",
        "Comma-separated OpClass allowlist (empty = all FP opClasses)")
    regClass = Param.String("",
        "Target destination register class: ''/any | vec | float | vec_elem")
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
    # [FSU][F5] permanent_stuck: install ONE fixed stuck-at fault (one
    # fault_id, one explicit faultMask, one SA0/SA1 polarity) on the first
    # eligible event after f5Warmup, then apply that SAME forced polarity to
    # every later eligible result until the run ends. This is NOT XOR and
    # NOT recurring_result_stuck: exposures share the single installation's
    # fault_id, and only an exposure whose correct value differs from the
    # forced polarity is an activated exposure. Requires fsuFreq=F5,
    # probability=1.0, an explicit faultMask, and maxFaults=0/1. Mutually
    # exclusive with rate modes / recurringStuck / roundingSub /
    # f3Dependent / fpsrSuppress / fmaWeighted.
    permanentStuck = Param.Bool(False,
        "F5 permanent stuck-at: one install, every later eligible result is "
        "an exposure of the same fixed mask/polarity")
    # -1 = draw the polarity ONCE at installation from rngSeed, then keep it
    # fixed for the whole run; 0 = SA0 (force mask bits to 0); 1 = SA1
    # (force mask bits to 1). Formal seeds should pin 0 or 1 explicitly.
    stuckPolarity = Param.Int(-1,
        "Permanent stuck polarity: -1 draw once at install, 0=SA0, 1=SA1")
    # Count of eligible events to skip before installation (warm-up). The
    # first eligible event with ordinal > f5Warmup installs the fault.
    f5Warmup = Param.UInt64(0,
        "F5 warm-up: eligible events before the single installation")
    # Bounded exposure evidence. Mandatory events (install, first exposure,
    # first activated exposure, first impact commit, chain_end) are ALWAYS
    # emitted; f5SampleLimit bounds the additional ordinary exposure
    # samples. 0 = mandatory events only. The resolved budget is capped well
    # below the 200000 PROP-EVT event cap so evidence is never silently
    # truncated.
    f5SampleLimit = Param.UInt64(0,
        "F5 ordinary exposure sample budget (mandatory events extra)")
    # 0 = prefix policy (first f5SampleLimit samples). N>0 = keep the first
    # N and the last N ordinary samples within the same budget, so a run
    # that spans millions of exposures still carries bounded early/late
    # evidence; totals/dropped are always exact on chain_end.
    f5KeepFirstLastN = Param.UInt64(0,
        "F5 bounded samples: keep the first N and last N (0 = prefix only)")
    # v1.1 Phase 9 patch 1a mode 4 — rounding_sub (F5, E3 proxy): re-round
    # the injected double one ULP toward the OPPOSITE of the current
    # rounding direction (nearest -> the value's other neighbor). Models a
    # flipped RMODE field in FPCR changing one rounding decision.
    roundingSub = Param.Bool(False, "rounding_sub mode: nudge the result "
                                    "one ULP to the opposite neighbor")
    # mode 5 — f3_data_dependent: corrupt ONLY when the result double's
    # biased exponent falls in [expLo, expHi] (the --fpu_operand_range
    # proxy; -1..-1 = unrestricted).
    f3Dependent = Param.Bool(False, "f3_data_dependent mode: corrupt only "
                                    "when the result exponent is in range")
    expLo = Param.Int(-1, "f3 operand-range lower bound (biased exp, incl.)")
    expHi = Param.Int(-1, "f3 operand-range upper bound (biased exp, incl.)")
    # mode 6 — fpsr_suppress (E3 placeholder): consume eligible events and
    # clear the accumulated exception-state model; the arch FPSR is only
    # observable via an MRS read, which SE kernels never take — logged
    # honestly as a count of suppressed-flag events.
    fpsrSuppress = Param.Bool(False, "fpsr_suppress mode: clear FP "
                                     "exception flags (logged count)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")
    # [FSU] Pilot identity written into FSU_PROP events. Empty = honestly
    # unset (the chain doc then shows N/A rather than a guessed RunID).
    fsuModel = Param.String("", "FSU model id (e.g. FP04) for FSU_PROP events")
    fsuFreq = Param.String("", "FSU frequency id (F0..F5) for FSU_PROP events")
    fsuLoad = Param.String("", "FSU workload id (W1..W9) for FSU_PROP events")
    fsuSubmodel = Param.String("", "FSU submodel (e.g. FP04-c) for FSU_PROP events")
    fsuEligibleTotal = Param.UInt64(0, "countOnly eligible-event total for "
                                       "this seed (0 = not measured)")
    # [FSU][D2] F1/F2/F3 deterministic rate semantics. The driver generates
    # the exact ordinals (tools/fsu_rate_ordinals.py, SplitMix64, interval in
    # [ceil(0.5*rate), floor(1.5*rate)]) from the countOnly eligible total and
    # passes them here. The injector matches the eligible-event ordinal
    # exactly — no probability/geometric approximation. Empty = F0 mode.
    rateOrdinals = Param.String("", "Comma-separated strict-increasing "
                                    "eligible ordinals for F1/F2/F3 "
                                    "(empty = F0 single-fault mode)")
    rateWarmup = Param.UInt64(0, "Eligible events before the first rate "
                                 "ordinal window")
    fsuRateDivisor = Param.UInt64(0, "F1=1000000, F2=100000, F3=10000 "
                                     "(0 = F0/not rate mode)")
    fsuJitterPct = Param.UInt64(0, "Interval jitter percentage (workbook=50)")
