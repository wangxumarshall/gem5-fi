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
    lsuF6Event = Param.String("sq_forward",
        "F6 event: tlb_hit (FS-only) | sq_forward | dirty_eviction | "
        "cas_success")
    f6Mode = Param.String("early_stress",
        "[LSU][P4-F6] F6 dual-track (2026-10-15): early_stress = inject at "
        "the FIRST occurrence of the event (legacy semantics, stress test); "
        "steady_state = skip lsuWarmupEvents occurrences (golden-profiling "
        "warm-up), then fire at a pre-drawn random occurrence in "
        "[warmup+1, warmup+span] — if the event stream ends first, NO "
        "injection (never falls back to early semantics)")

    # LSU W4 PRE-hook family (03-design-matrix A04/A05/A06/A08; hook =
    # LSQ::pushRequest entry, W1 ⑦ ruling). Exactly one hook per run: a
    # non-off preMode registers on the pushRequest pointer INSTEAD of the
    # sendFragment pointer.
    preMode = Param.String("off",
        "off | a04_subst | a05_shift | a06_size (A06-a: store = any legal "
        "target; load = contract-safe WIDEN only, see aguSizeToLoad) | "
        "a08_subst | s13_store_addr | s04_store_subst (SQ addr same-page, "
        "stores) | l01_load_addr (LQ addr single-bit, loads only). "
        "'a06s_store_size' is a REJECTED alias (never use — no silent "
        "model-ID rewrite; it is refused at config time and is a no-op in "
        "the .cc, counted as obs_pre_invalid)")
    aguSizeTo = Param.UInt64(0,
        "a06_size STORE leg target size: 1|2|4|8|16 "
        "(anything else = invalid, no-op + counted)")
    aguObjectSpec = Param.String("",
        "[R6-A2/A04-a] Explicit oracle-object registry, ';'-separated. Each "
        "item is 'id:symbol:size:elem_width' or 'id:@addr:size:elem_width'. "
        "A04-a is eligible only when the source EA lies inside a registered "
        "object; no registry => loud refusal (never falls back to same-page).")
    # [MDSPEC][R4-6-A06 / R4-8-A06] A06-a LOAD leg: ANOTHER legal size,
    # widen OR shrink. The AArch64 load completion is fixed-width per static
    # instruction (LoadCompleteAcc getMemLE(pkt, Mem, ..) reads sizeof(Mem)
    # bytes), while the destination buffer is sized by the request size
    # (lsq_unit.cc read()). A shrink is therefore only safe because
    # LSQ::pushRequest hands the pre-fault static width to the LSQUnit
    # (DynInst::chaosA06BufBytes), which floors + zero-fills that buffer —
    # turning the shrink into a faithful zero-extended truncation.
    aguSizeToLoad = Param.UInt64(0,
        "a06_size LOAD leg target size: 1|2|4|8|16 (another legal value; "
        "widen or shrink, must differ from the original access size and keep "
        "(addr&63)+target <= 64). "
        "0 = load leg disabled (loads are declined + counted, never a "
        "silent no-op)")
    # [MDSPEC][R4-6-A06] A06-b byte-enable. Every AArch64 load/store path in
    # this tree passes std::vector<bool>(size, true) (mem.isa, neon64.isa,
    # sve_mem.isa, sme.isa), so the ISA-side mask domain is {all-ones} and
    # the only functional lever is the inactive-TAIL trim in
    # LSQRequest::addReq (== an access-size change). shift_mid clears an
    # INTERIOR byte => no tail run => the request size is unchanged.
    beMode = Param.String("off",
        "off | observe (census the faulted request's mask: be_len/be_ones/"
        "be_all_true into the injection log + the CHAOS_L0_A06 summary line) "
        "| shift_mid (A06-b injection: substitute an interior-cleared mask; "
        "STORES only — a load's mask has no architectural consumer on this "
        "path; requires preMode=a06_size) "
        "| rotate1_clear_msb (A06 RULING 2026-10-28: rotate the original "
        "mask by one byte; if it is all-true (the ISA's normal mask) clear "
        "the most-significant byte. Same width, non-zero, != original; "
        "STORES only, size>=2)")

    # [MDSPEC][R4-5.8] A07 AGU clean-ready/handshake family (03 sheet A07:
    # "AGU 结果的 address-ready 握手信号与 EA 流水锁存器"; hook =
    # IEW::executeInsts' isMemRef branch — the ready point, BEFORE the EA
    # exists, which is why neither the pushRequest PRE hook (AGU raw
    # OUTPUT) nor the sendFragment POST hook (DTLB input) could express
    # the ready-timing model). Landed sub-model: a07b_ready_delay = A07-b
    # bounded ready delay (delay_cycles CPU clock edges; spec "延后1
    # 周期"; data payload stays correct — only the timing shifts).
    # A07-a (ready early + stale latched EA) and A07-c (ready lost) are
    # pending — see tools/lsu_runid_map.py SPEC_IMPL_LANDED. LSU-trigger-
    # native: a non-off mode REQUIRES lsuTier != off and is mutually
    # exclusive with preMode (one hook per run, W1-⑦).
    aguReadyMode = Param.String("off",
        "off | a07b_ready_delay (A07-b bounded AGU-ready delay at the IEW "
        "memRef ready/handshake point)")
    aguWatchdogCycles = Param.UInt64(4096,
        "[R6-A2/A07-c] ready-loss watchdog delay in CPU cycles (>=1).")
    aguWatchdogMax = Param.UInt64(1 << 20,
        "[R6-A2/A07-c] hard upper bound; exceeding it exits with code 124 "
        "instead of hanging forever.")
    aguReadyDelayCycles = Param.UInt64(1,
        "A07-b: the ready handshake is delayed by this many CPU clock "
        "edges (bounded, >=1; spec default 1 = '延后1周期')")
