from m5.params import *
from m5.proxy import *
from m5.SimObject import SimObject

class CHAOSCache(SimObject):
    type = 'CHAOSCache'
    cxx_header = "mem/cache/CHAOSCache/CHAOSCache.hh"
    cxx_class = 'gem5::CHAOSCache'
    target_cache = Param.Cache("Cache da corrompere")
    probability = Param.Float(0.0, "Probability (between 0 and 1) of injecting faults")
    bitsToChange = Param.Int(-1, "Bit to modify per byte")
    faultMask = Param.String("0", "Bit mask to be applied to the target cache packet value")
    corruptionSize = Param.Int(1, "Bytes to modify")
    firstClock = Param.UInt64(0, "Clock cycle after which fault injection starts")
    lastClock = Param.UInt64(0, "Clock cycle after which fault injection stops")
    faultType = Param.String("random", "Fault type: bit_flip, stuck_at_zero, stuck_at_one")
    tickToClockRatio = Param.Int(1000, "Ratio between tick and clock cycle (tick/cycle)")
    bitFlipProb = Param.Float(0.9, "Probability (between 0 and 1) of injecting a bit flip fault on 'random' fault type")
    stuckAtZeroProb = Param.Float(0.05, "Probability (between 0 and 1) of injecting a stuck-at-zero fault on 'random' fault type")
    stuckAtOneProb = Param.Float(0.05, "Probability (between 0 and 1) of injecting a stuck-at-one flip fault on 'random' fault type")
    cyclesPermamentFaultCheck = Param.Int(1, "Number of cycles between each periodic check for permanent faults.")
    rngSeed = Param.UInt64(0, "Seed for the injection RNG (std::mt19937). 0 = seed from std::random_device (original, NON-reproducible behavior). Nonzero = fixed seed for reproducible block/byte/mask selection.")
    maxFaults = Param.UInt64(0, "G5: maximum number of faults to inject; 0 = unlimited (original). Use 1 for single-fault campaigns.")
    targetBlockAddr = Param.Addr(0, "Directed: pin the fault to the cache block "
        "containing this address (block-aligned lookup among VALID blocks). "
        "0 = random block (original). Use to land a fault on a live-data "
        "byte (L1D) or an executed instruction byte (L1I) — report §六.3 "
        "'fixed-to' runs. If the block is not valid/resident at injection "
        "time, falls back to random with a log warning.")
    targetByteOffset = Param.Int(-1, "Directed: pin the fault to this byte "
        "offset within the target block (0..blockSize-1). -1 = random "
        "byte (original).")
    # §2.7/§2.11 field-level fault: which CacheBlk field to corrupt.
    #   data  (default): corrupt the data byte (orig behavior; byteOffset/mask).
    #   valid : invalidate the block (§2.7 valid field; sed/secded also use this
    #           for the Corrected path). Models a 'valid bit flip' -> block
    #           re-fetched on next access.
    #   dirty : toggle the dirty bit (§2.7 dirty field; clean block written-
    #           back spuriously, or dirty block dropped).
    #   coh   : toggle a coherence bit (§2.7 coh field; shared<->modified flip).
    # tag(F5 same-set legal tag) + repl(replacement meta) DEFERRED (need
    # lookup of another legal tag / repl meta, more plumbing).
    # v1.2 Phase 14 (plan item 2): victim/writeback path fault — corrupt the
    # data AS IT LEAVES the cache in a writeback packet (the victim buffer
    # path; the cache array itself stays clean — the corruption only exists
    # in flight to the next level).
    victimFault = Param.Bool(False, "victim/writeback path fault mode")
    targetField = Param.String("data",
        "§2.7/§2.11 field-level fault: data (default, byteOffset/mask) | "
        "valid (invalidate block) | dirty (toggle dirty bit) | coh (toggle "
        "coherence bit) | data_shift (C09 rotate) | tag(F5) | mshr_merge "
        "(MDSPEC C11: merge-target address bit_flip at the MSHR coalescing "
        "hook — event-normalized ChaOSLsuTrigger via lsuTier; the legacy "
        "periodic block attack is DISABLED in this mode) | mshr_fill_timing "
        "(MDSPEC C12: fill-timing OFFSET — a fill response is deferred by "
        "lsuFillDelayCycles cache cycles (stash + scheduled resume into "
        "recvTimingResp); same trigger discipline via lsuTier, legacy "
        "periodic attack DISABLED) | mshr_busy_leak (MDSPEC C14-a: the "
        "serviced MSHR entry is NOT released at the fill release point — "
        "its busy/occupied state is stuck-at-1, the slot never returns to "
        "the free list; same trigger discipline via lsuTier, legacy "
        "periodic attack DISABLED) | mshr_occupancy (MDSPEC C15-b: at MSHR "
        "capacity the injector fabricates a free slot so one further "
        "allocation runs beyond the arbitration's capacity — the "
        "arbitration's allow/deny decision is genuinely wrong; same trigger "
        "discipline via lsuTier, legacy periodic attack DISABLED) | "
        "rmw_mux (MDSPEC R4-9-FSMC O04-a: LSE read-modify-write "
        "data-select MUX mis-route — the OLD (returned) and NEW (memory) "
        "latches of an atomic CAS/SWP/LDADD are EXCHANGED at the SwapReq "
        "commit site in BaseCache::satisfyRequest; same trigger discipline "
        "via lsuTier, legacy periodic attack DISABLED) | rmw_latch "
        "(MDSPEC R4-9-FSMC O09: ONE bit of the RMW result/old-value latch "
        "— the value returned to software — is flipped; address/opcode/"
        "success/timing untouched; same trigger discipline) | rmw_order "
        "(MDSPEC R4-9-FSMC O05: the RMW's completion is corrupted while the "
        "DATA stays correct — the memory update is DROPPED (rule=lost) or "
        "the atomic op is applied TWICE (rule=dup); same trigger discipline)")
    lsuRmwRule = Param.String("swap_oldnew",
        "MDSPEC R4-9-FSMC RMW sub-rule, consumed only by the rmw_* "
        "targetField modes (a mode/rule mismatch is rejected loudly in the "
        "CHAOSCache ctor — a half-specified model is never silently run). "
        "swap_oldnew = O04-a old/new exchange (targetField=rmw_mux); "
        "result_old = O09-a result/old-value latch bit flip "
        "(targetField=rmw_latch); lost = O05-a RMW dropped; dup = O05-b RMW "
        "applied twice (targetField=rmw_order). Inert in every other "
        "targetField mode.")
    lsuFillDelayCycles = Param.UInt64(100,
        "MDSPEC C12 mshr_fill_timing: the fill-timing offset in cache clock "
        "cycles — the deferred fill's processing (handleFill + target "
        "service + MSHR free) runs at curTick() + this many clock edges of "
        "the mounted cache. >= 1 required in mshr_fill_timing mode (0 is "
        "panicked loudly — a zero-cycle offset is a no-op, not a timing "
        "fault). Inert in every other targetField mode.")
    pairedSector = Param.Bool(False,
        "Phase 5 §7.7 paired-sector 128B fault-domain proxy: when set, the "
        "fault is applied to BOTH the target 64B block AND its 128B-aligned "
        "paired neighbor (blockAddr XOR 64B), at the SAME byte offset — "
        "modeling a 128B L3 fault domain that spans two 64B sectors. This is "
        "a PROXY (not a cycle-exact Kunpeng L3 model); the paired partner must "
        "be VALID+resident to be corrupted (else only the primary is faulted, "
        "logged honestly). Use on a 64B-line cache designated as 'L3'.")
    l1iSemanticField = Param.String("none",
        "§2.11 L1I A64 field stratification: none/opcode/rn/rm/rd/imm12/cond")
    protectionModel = Param.String("none",
        "§1.2 protection-aware modeling layer (N1 TRM Table 9-1 PROXY). "
        "Post-injection, the injector applies protection logic keyed on "
        "popcount(mask) (bits this fault flips) to decide the observable "
        "outcome. 'none' (default = raw upper bound, leave corruption = "
        "escape, zero regression vs prior behavior); 'sed' (L1I data proxy: "
        "1-bit -> invalidate block = Corrected, >=2-bit -> silent = escape); "
        "'secded_poison' (L1D/L2 data proxy: 1-bit -> undo injection = "
        "Corrected, 2-bit -> poison-log + leave = Latent (classic cache has "
        "no poison bit, E3 proxy), >=3-bit -> silent); 'secded' (L1D/L2 tag "
        "proxy: 1-bit -> undo = Corrected, 2-bit -> invalidate block = "
        "DetectedContained, >=3-bit -> silent false-hit). Each cell should "
        "run 'none' (raw sensitivity) vs the proxy value "
        "(protection-aware escape rate). Does NOT convert to product FIT.")
    # LSU W2/W6 (05 r2-r8): event-normalized trigger tier; "off" = legacy.
    lsuTier = Param.String("off", "off | F0 | F1 | F2 | F3 | F4 | F5 | F6")
    lsuWarmupEvents = Param.UInt64(0, "eligible events skipped before arming")
    lsuSpanEvents = Param.UInt64(1000, "F0 uniform window size")
    writeLog = Param.Bool(True, "Write a log file")