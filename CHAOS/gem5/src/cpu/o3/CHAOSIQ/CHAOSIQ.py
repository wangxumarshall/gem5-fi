from m5.params import *
from m5.SimObject import SimObject

class CHAOSIQ(SimObject):
    type = 'CHAOSIQ'
    cxx_class = 'gem5::CHAOSIQ'
    cxx_header = "cpu/o3/CHAOSIQ/CHAOSIQ.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.5 IQ modes:
    #   wake_omit (F6): on wakeDependents, DROP one wakeup broadcast — the
    #                   completed instruction's dependents stay not-ready (one
    #                   missed wake). Models method3 timing-race phase shift.
    #   src_ready_bitflip (F5, Phase 4.3): on one wakeDependents event, ALSO
    #                   wake one not-ready dependent from a DIFFERENT chain —
    #                   it issues immediately and reads a stale physreg
    #                   (wrong-source wakeup, method3).
    #   wake_phase (F6, Phase 4.3): delay one wakeup broadcast by
    #                   phaseOffset cycles (DelayedWakeEvent; advance not
    #                   modeled — E3 proxy limit).
    mode = Param.String("wake_omit",
        "wake_omit | src_ready_bitflip | wake_phase | ready_early | "
        "ready_never | ready_never_event | tag_swap | tag_bitflip | "
        "tag_bitflip2 | tag_stuck | tag_stale_read | dispatch_misroute")
    phaseOffset = Param.Int(0, "F6 wake_phase: cycles to advance(-)/delay(+) — proxy")
    probability = Param.Float(1.0, "per-event injection probability")
    # W5.11 (D51-D53): directed bit control for the int-tag index field
    # (lowest set bit = the bit; two lowest = the bit pair), the
    # CHAOSROB faultMask convention. 0 = random.
    faultMask = Param.UInt64(0,
        "directed bit mask for tag_bitflip/tag_bitflip2/tag_stuck")
    # W7.4 (ooo 04-design-matrix D86-D91, FP/SIMD Dispatch/ROB): the
    # register-class scope of the ready-bit (ready_early) and source-tag
    # (tag_*) populations. "int" = the W5 Int-IQ scope (default,
    # byte-identical behavior); "vec" = the FP/SIMD queue — scalar FP,
    # FP SIMD and integer SIMD sources ALL rename onto VecRegClass on
    # AArch64 (the W1 platform finding: S/D are the low bits of V,
    # FloatRegClass is never renamed), so ONE vec class covers the whole
    # FP/SIMD IQ; the tag domain becomes [0, numVecPhysRegs).
    targetClass = Param.String("int", "int | vec (register class scope)")
    # W7.4 D86 optional opClass filter for the three §2.5 wake modes
    # (wake_omit / src_ready_bitflip / wake_phase): restrict eligibility
    # to FP/SIMD completed instructions (isFpOpClass = Float* ∪ SimdFloat*,
    # the CHAOSFPU §2.6 convention) — the D86 "FP/SIMD 队列版" scoping.
    # Default False = legacy class-agnostic behavior (zero regression).
    fpOnly = Param.Bool(False,
        "§2.5 wake modes: only fire on FP/SIMD (Float* ∪ SimdFloat*)"
        " completed instructions")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
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
