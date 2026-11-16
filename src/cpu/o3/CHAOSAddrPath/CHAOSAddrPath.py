from m5.params import *
from m5.SimObject import SimObject

class CHAOSAddrPath(SimObject):
    type = 'CHAOSAddrPath'
    cxx_class = 'gem5::CHAOSAddrPath'
    cxx_header = "cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh"

    cpu = Param.BaseCPU(NULL, "Target CPU (must be an O3CPU)")

    # §2.4 AGU address-path fault injector. Hooks LSQ::LSQRequest::
    # sendFragmentToTranslation BEFORE translateTiming — corrupts the
    # request vaddr (byte7 zero = canonical->non-canonical kernel address,
    # or low-bit flip). HONEST: SE-inert (SE physical memory from 0, 512MiB
    # — byte7 zero still lands in range, no fault). FS-only effective.
    mode = Param.String("byte7_zero",
        "byte7_zero: clear vaddr byte7 (canonical->non-canonical) | "
        "low_bit_flip: XOR a low bit of vaddr | "
        "a01_bit: A01 single-bit flip, low/mid/high band (LSU 03) | "
        "a02_2bit: A02 two-bit flip, 50% adjacent/50% dispersed (LSU 03) | "
        "a03_stuck0/a03_stuck1: A03 one EA bit stuck-at (LSU 03, F5)")
    probability = Param.Float(1.0, "per-sendFragment injection probability")
    firstClock = Param.UInt64(0, "first clock cycle eligible for injection")
    lastClock = Param.UInt64(0, "last cycle (0 = unrestricted)")
    maxFaults = Param.UInt64(0, "max faults; 0 = unlimited. Use 1.")
    rngSeed = Param.UInt64(0, "RNG seed (0 = random_device)")
    writeLog = Param.Bool(True, "Write a fault_injections.log file")

    # LSU W2 (docs/gem5-fi/lsu/05 r2-r8): event-normalized trigger tier.
    # "off" = legacy cycle-window path (byte-identical, KP track). F0-F6
    # route the injection decision through ChaOSLsuTrigger
    # (cpu/o3/chaos_lsu_trigger.hh): warm-up/repetition/max-faults semantics
    # move to the trigger layer (eligible-event denominator).
    lsuTier = Param.String("off",
        "off | F0 | F1 | F2 | F3 | F4 | F5 | F6 (LSU event-normalized tier)")
    lsuWarmupEvents = Param.UInt64(0,
        "eligible events skipped before arming (LSU tiers)")
    lsuSpanEvents = Param.UInt64(1000,
        "F0 uniform window size in eligible events")
    lsuEventOrdinal = Param.UInt64(0,
        "R01-R05: 1-based target eligible-event ordinal (0 = legacy)")
    lsuF6Event = Param.String("sq_forward",
        "F6 event: tlb_hit (FS-only) | sq_forward | dirty_eviction | "
        "cas_success")

    # LSU W4 PRE-hook family (03-design-matrix A04/A05/A06/A08; hook =
    # LSQ::pushRequest entry, W1 ⑦ ruling). Exactly one hook per run: a
    # non-off preMode registers on the pushRequest pointer INSTEAD of the
    # sendFragment pointer.
    preMode = Param.String("off",
        "off | a04_subst | a05_shift | a06_size | a08_subst | "
        "s13_store_addr | s04_store_subst (SQ addr same-page, stores) | "
        "l01_load_addr (LQ addr single-bit, loads only) | "
        "a01_bit3_load (LSU v3.2 A01: load bit3 XOR at pushRequest, F0) | "
        "a03_bit3_stuck0_load (LSU v3.2 A03: load bit3 stuck-at-0, F5)")
    aguSizeTo = Param.UInt64(0,
        "a06_size target size: 1|2|4|8|16 (0 = invalid, no-op)")

    # [LSU][V3.3.3][A03] in-simulator watchdog (ledger L-A02). A03's
    # persistent stuck-at fault can corrupt the guest exit path after the
    # final checksum; an external kill then truncates the trace and skips
    # the exit callbacks. Armed once at activation for this many CPU cycles,
    # then gem5 exits cleanly via exitSimLoop and emits
    # A03_WATCHDOG_EXPIRED. 0 = disabled (default; every other model is
    # byte-identical).
    watchdogCycles = Param.UInt64(0,
        "A03: in-simulator watchdog clock cycles after activation "
        "(0 = disabled)")
    # v3.3.3 A01 re-census (ledger L-A12): log every eligible 8-byte load as
    # CHAOS_ELIGIBLE and never inject. The A01 size==8 filter makes this the
    # exact eligible stream used for the percentile ROI.
    countOnly = Param.Bool(False,
        "A01: count-only eligible-stream log; never injects")
