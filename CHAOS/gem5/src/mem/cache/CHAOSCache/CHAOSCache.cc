#include "mem/cache/CHAOSCache/CHAOSCache.hh"

#include <random>
#include <vector>

#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"  // [LSU][OBS-L3] L3 registration
#include "debug/CHAOSCache.hh"
#include "mem/cache/base.hh"
#include "mem/cache/cache_blk.hh"
#include "mem/cache/tags/base.hh"

namespace gem5
{
    CHAOSCache::CHAOSCache(const CHAOSCacheParams& p) :
        SimObject(p),
        targetCache(p.target_cache),
        probability(p.probability),
        bits_to_change(p.bitsToChange),
        corruption_size(p.corruptionSize),
        first_clock(p.firstClock),
        last_clock(p.lastClock),
        fault_type_enum(stringToFaultType(p.faultType)),
        fault_mask(static_cast<unsigned char>(std::stoi(p.faultMask, nullptr, 2))),
        tick_to_clock_ratio(p.tickToClockRatio),
        bit_flip_prob(p.bitFlipProb),
        stuck_at_zero_prob(p.stuckAtZeroProb),
        stuck_at_one_prob(p.stuckAtOneProb),
        cycles_permament_fault_check(p.cyclesPermamentFaultCheck),
        write_log(p.writeLog),
        target_block_addr(p.targetBlockAddr),
        target_byte_offset(p.targetByteOffset),
        paired_sector(p.pairedSector),
        target_field(p.targetField),
        victim_fault(p.victimFault),
        l1i_semantic_field(p.l1iSemanticField),
        protection_model(p.protectionModel),
        rng_seed(p.rngSeed),
        max_faults(p.maxFaults),
        faults_injected_count(0),
        attackEvent([this] { this->injectFault(); }, name()),
        periodicCheck([this] { this->checkPermanent(); }, name() + ".periodicCheck"),
        fillResumeEvent([this] { this->resumeDeferredFill(); },
                        name() + ".fillResume"),
        stats(nullptr)
    {
        // v1.2 Phase 14: register the victim hook with BaseCache so
        // writebackBlk can consult us (victim-path faults).
        if (victim_fault) {
            BaseCache::chaosVictimHook = this;
        }
        // [MDSPEC][R4-5.1] C11 MSHR merge corruption mode + [MDSPEC][R4-5.2]
        // C12 fill-timing offset mode: event-normalized trigger (LSU track,
        // chaos_lsu_trigger.hh) on the model's own event stream + the
        // corresponding static hook. The legacy periodic block attack is
        // DISABLED in these modes (it would inject an unrelated data fault
        // on a random block — a different model's fault polluting the
        // sample). A tier is REQUIRED: "off" is rejected loudly (a hook
        // mode without a trigger has no fire semantics; probability checks
        // are never hand-rolled, CLAUDE.md trigger discipline).
        const bool merge_mode = (target_field == "mshr_merge");
        // [MDSPEC][R4-5.2] C12: defer a fill response by lsuFillDelayCycles
        // cache cycles (see maybeDeferFillTiming).
        const bool fill_timing_mode = (target_field == "mshr_fill_timing");
        // [MDSPEC][R4-5.5] C14-a: MSHR busy/occupied stuck-at-1 (a resource
        // leak — the released entry never returns to the free list).
        const bool mshr_busy_mode = (target_field == "mshr_busy_leak");
        // [MDSPEC][R4-5.6] C15-b: MSHR capacity-arbitration fake-free.
        const bool mshr_occ_mode = (target_field == "mshr_occupancy");
        // [MDSPEC][R4-9-FSMC] O04/O05/O09: the three LSE atomic-RMW modes
        // share the SwapReq commit hook (BaseCache::satisfyRequest); the
        // sub-model is picked by lsuRmwRule (validated below).
        const bool rmw_mux_mode   = (target_field == "rmw_mux");
        const bool rmw_latch_mode = (target_field == "rmw_latch");
        const bool rmw_order_mode = (target_field == "rmw_order");
        const bool rmw_mode = rmw_mux_mode || rmw_latch_mode || rmw_order_mode;
        const bool lsu_hook_mode = merge_mode || fill_timing_mode ||
                                   mshr_busy_mode || mshr_occ_mode ||
                                   rmw_mode;
        // [MDSPEC][R4-9-FSMC] the RMW sub-rule (kept as a member; assigned
        // here rather than in the init list to avoid a -Wreorder hazard).
        rmw_rule = p.lsuRmwRule;
        if (lsu_hook_mode) {
            if (p.lsuTier == "off") {
                panic("CHAOSCache: targetField=%s requires a tier "
                      "(--l1d_lsu_tier F0..F6, LSU event-normalized trigger; "
                      "'off' has no fire semantics for the %s hook)\n",
                      target_field.c_str(),
                      merge_mode ? "merge"
                                 : (fill_timing_mode ? "fill-timing"
                                   : (mshr_busy_mode ? "mshr-busy"
                                     : (mshr_occ_mode ? "mshr-occupancy"
                                                      : "rmw"))));
            }
            // [MDSPEC][R4-9-FSMC] mode/rule consistency: a rmw_* mode whose
            // lsuRmwRule names another model's sub-model (or a non-rmw mode
            // carrying a non-default rule) is a half-specified model —
            // rejected loudly, never silently run with an unintended rule.
            const bool rule_ok =
                (rmw_mux_mode   && rmw_rule == "swap_oldnew") ||
                (rmw_latch_mode && rmw_rule == "result_old") ||
                (rmw_order_mode && (rmw_rule == "lost" || rmw_rule == "dup")) ||
                (!rmw_mode      && rmw_rule == "swap_oldnew");
            if (!rule_ok) {
                panic("CHAOSCache: targetField=%s is inconsistent with "
                      "lsuRmwRule=%s (rmw_mux needs swap_oldnew; rmw_latch "
                      "needs result_old; rmw_order needs lost|dup; every "
                      "other targetField needs the default swap_oldnew)\n",
                      target_field.c_str(), rmw_rule.c_str());
            }
            if (fill_timing_mode && p.lsuFillDelayCycles == 0) {
                panic("CHAOSCache: targetField=mshr_fill_timing requires "
                      "lsuFillDelayCycles >= 1 (--l1d_fill_delay_cycles; a "
                      "zero-cycle offset is a no-op, not a timing fault)\n");
            }
            fill_delay_cycles = p.lsuFillDelayCycles;
            lsuTrigger = new ChaOSLsuTrigger(
                tierFromString(p.lsuTier), rng_seed ? rng_seed : 1,
                p.lsuWarmupEvents, p.lsuSpanEvents);
            if (merge_mode)
                BaseCache::chaosMergeHook = this;
            else if (fill_timing_mode)
                BaseCache::chaosFillTimingHook = this;
            else if (mshr_busy_mode)
                BaseCache::chaosMshrBusyHook = this;   // C14-a
            else if (mshr_occ_mode)
                BaseCache::chaosMshrOccHook = this;    // C15-b
            else
                BaseCache::chaosRmwHook = this;        // R4-9-FSMC O04/O05/O09
        }
        // [LSU][OBS-L3] final funnel row (final counts; runs only on normal
        // exit — aborts keep the last per-attack injection-time node, which
        // is exactly why the per-attack rows exist). In a trigger-hook mode
        // (merge / fill-timing) the trigger's teardown summary (stdout
        // CHAOS_LSU_TRIGGER line, the campaign L0 funnel source) prints
        // first; the funnel row itself reads the TRIGGER counters there
        // (see noteFunnelAtInjection).
        registerExitCallback([this]() {
            if (lsuTrigger)
                lsuTrigger->summary("CHAOSCache");
            // [MDSPEC][R4-5.5] C14-a teardown read-back: the leak count and
            // whether the stuck slot is still held at end of run. Runs only
            // on normal exit (an abort keeps the last injection-log node).
            if (target_field == "mshr_busy_leak")
                printf("CHAOS_MSHR_BUSY: injector=CHAOSCache mode=c14a_busy_stuck "
                       "leaks=%lu slot_held=%d released_normally=%d "
                       "(C14-a MSHR occupied stuck-at-1; the leaked entry "
                       "never returned to the free list)\n",
                       (unsigned long)mshr_busy_leaks,
                       mshr_busy_victim ? 1 : 0,
                       mshr_busy_leaks ? 0 : 1);
            // [MDSPEC][R4-5.6] C15-b teardown read-back: fires = fabricated
            // free slots (trigger-consented, = the injection-log count and
            // the C-family activated PROXY), activated = over-capacity
            // allocations actually allowed (the REAL arbitration
            // read-back). fires > activated = Inject-not-activated.
            if (target_field == "mshr_occupancy")
                printf("CHAOS_MSHR_OCC: injector=CHAOSCache mode=c15b_fake_free "
                       "fires=%lu activated=%lu occ_at_fire=%lu "
                       "(C15-b capacity-arbitration fake-free; activated = "
                       "allocations genuinely allowed beyond capacity)\n",
                       (unsigned long)mshr_fake_free_fires,
                       (unsigned long)mshr_over_commit,
                       (unsigned long)mshr_occ_at_fire);
            // [MDSPEC][R4-9-FSMC] O04/O05/O09 teardown read-back: how many
            // atomic RMW commits were corrupted under the mode's rule (the
            // L0 injected count; activated stays the L3 chain's verdict).
            if (target_field == "rmw_mux" || target_field == "rmw_latch" ||
                target_field == "rmw_order")
                printf("CHAOS_RMW: injector=CHAOSCache field=%s rule=%s "
                       "rmw_injections=%lu (R4-9-FSMC O04/O05/O09 LSE "
                       "atomic-RMW hook at the SwapReq commit site)\n",
                       target_field.c_str(), rmw_rule.c_str(),
                       (unsigned long)rmw_injections);
            noteFunnelAtInjection();
        });
        if (probability != 0.0 || lsu_hook_mode) {
            log_stream = simout.create("cache_injections.log", false, true);
            if (!log_stream || !log_stream->stream()) {
                panic("CHAOSCache: Could not open log file");
            }

            if (bits_to_change == -1){
                std::uniform_int_distribution<int> dist(1, 8);
                bits_to_change = dist(rng);
            }

            stats = std::make_unique<CHAOSCacheStats>(this);

            first_tick = first_clock * tick_to_clock_ratio;
            last_tick = last_clock * tick_to_clock_ratio;
            ticks_permament_fault_check = cycles_permament_fault_check * tick_to_clock_ratio;

            rng.seed(rng_seed != 0 ? rng_seed : rd());
            if (probability != 0.0) {
                // (a trigger-hook mode with probability==0 skips this — a
                // geometric distribution requires p in (0,1]; the legacy
                // attack that consumes it never runs in those modes.)
                inter_fault_cycles_dist =
                    std::geometric_distribution<unsigned>(probability);
            }

            if (!lsu_hook_mode) {
                scheduleAttack(first_tick + inter_fault_cycles_dist(rng) * tick_to_clock_ratio);
            }

            if ((bit_flip_prob + stuck_at_zero_prob + stuck_at_one_prob) != 1.0){
                warn("Sum of probabilities is not 1, assuming 0.9 for bitFlipProb, 0.05 for stuckAtZeroProb and 0.05 for stuckAtOneProb.\n");
                bit_flip_prob = 0.9;
                stuck_at_zero_prob = 0.05;
                stuck_at_one_prob = 0.05;
            }

            std::vector<double> weights = {bit_flip_prob, stuck_at_zero_prob, stuck_at_one_prob};
            random_fault_distribution = std::discrete_distribution<int>(weights.begin(), weights.end());

            if (!lsu_hook_mode)
                scheduleCheckPermanentFault(first_tick + ticks_permament_fault_check);
        }
    }

    CHAOSCache::CHAOSCacheStats::CHAOSCacheStats(statistics::Group *parent)
    : statistics::Group(parent),
      ADD_STAT(numFaultsInjected, statistics::units::Count::get(),
               "Total number of faults injected"),
      ADD_STAT(numBitFlips, statistics::units::Count::get(),
               "Number of bit flip faults injected"),
      ADD_STAT(numStuckAtZero, statistics::units::Count::get(),
               "Number of stuck-at-0 faults injected"),
      ADD_STAT(numStuckAtOne, statistics::units::Count::get(),
               "Number of stuck-at-1 faults injected"),
      ADD_STAT(numPermanentFaults, statistics::units::Count::get(),
               "Total number of permanent faults injected")
    {
    }

    CHAOSCache::FaultType 
    CHAOSCache::stringToFaultType(const std::string &s) {
        if (s == "bit_flip") return FaultType::BitFlip;
        else if (s == "stuck_at_zero") return FaultType::StuckAtZero;
        else if (s == "stuck_at_one") return FaultType::StuckAtOne;
        return FaultType::Random;
    }

    const char*
    CHAOSCache::faultTypeToString(CHAOSCache::FaultType f) {
        switch (f) {
            case FaultType::BitFlip: return "bit_flip";
            case FaultType::StuckAtZero: return "stuck_at_zero";
            case FaultType::StuckAtOne: return "stuck_at_one";
            case FaultType::Random: return "random";  // G7: handle enum to clear -Wswitch
        }
        return "random";
    }

    // [MDSPEC][R4-5.1] C11: lsuTier param -> enum (CHAOSAddrPath precedent;
    // "off" is rejected in the ctor before we get here).
    ChaOSLsuTier
    CHAOSCache::tierFromString(const std::string &s) {
        if (s == "F0") return ChaOSLsuTier::F0;
        if (s == "F1") return ChaOSLsuTier::F1;
        if (s == "F2") return ChaOSLsuTier::F2;
        if (s == "F3") return ChaOSLsuTier::F3;
        if (s == "F4") return ChaOSLsuTier::F4;
        if (s == "F5") return ChaOSLsuTier::F5;
        if (s == "F6") return ChaOSLsuTier::F6;
        panic("CHAOSCache: unknown lsuTier '%s'\n", s.c_str());
    }

    // §1.2 protection-aware modeling (N1 TRM Table 9-1 PROXY). Map the
    // protectionModel string to an outcome-ladder enum. "none" (default) =
    // raw upper bound = leave the corruption (escape), zero regression.
    CHAOSCache::ProtectionOutcome
    CHAOSCache::stringToProtectionModelPub(const std::string &s) {
        if (s == "sed") return ProtectionOutcome::DetectedContained;  // placeholder; real ladder is in applyProtection by popcount
        if (s == "secded_poison") return ProtectionOutcome::Latent;
        if (s == "secded") return ProtectionOutcome::DetectedContained;
        return ProtectionOutcome::Raw;  // "none" / unknown -> raw
    }

    const char*
    CHAOSCache::protectionOutcomeToString(CHAOSCache::ProtectionOutcome o) {
        switch (o) {
            case ProtectionOutcome::Raw: return "Raw";
            case ProtectionOutcome::Corrected: return "Corrected";
            case ProtectionOutcome::DetectedContained: return "DetectedContained";
            case ProtectionOutcome::Latent: return "Latent";
            case ProtectionOutcome::SilentEscape: return "SilentEscape";
        }
        return "Raw";
    }

    // §1.2 post-injection protection handling. Decides the observable outcome
    // from popcount(mask) (bits this fault flips) + protectionModel, then acts:
    //   none           -> Raw (leave = escape). Default, zero regression.
    //   sed            -> 1-bit: invalidate block (Corrected); >=2: SilentEscape.
    //   secded_poison  -> 1-bit: undo (Corrected); 2-bit: poison-log + leave
    //                       (Latent; classic cache has no poison bit, E3);
    //                       >=3: SilentEscape.
    //   secded         -> 1-bit: undo (Corrected); 2-bit: invalidate block
    //                       (DetectedContained); >=3: SilentEscape (false-hit).
    // `blk` may be null for the paired-sector partner path (no invalidate
    // there — honest: the partner's containment is logged, not enforced).
    CHAOSCache::ProtectionOutcome
    CHAOSCache::applyProtection(CacheBlk *blk, int byteOffset,
                                uint8_t mask, uint8_t orig_byte,
                                FaultType ft, bool is_paired)
    {
        // popcount(mask) = bits this injection flips (§1.2 "1-bit/2-bit/≥3-bit").
        int bits = __builtin_popcount(mask);

        ProtectionOutcome outcome = ProtectionOutcome::Raw;
        uint8_t *data = blk ? blk->data : nullptr;
        // For the paired path we operate on the partner's data (caller sets blk).
        (void)is_paired;

        if (protection_model == "none") {
            outcome = ProtectionOutcome::Raw;  // leave = escape (default)
        } else if (protection_model == "sed") {
            if (bits == 1) {
                // 1-bit: invalidate block -> re-fetch clean on next access.
                if (blk) blk->invalidate();
                outcome = ProtectionOutcome::Corrected;
            } else {
                outcome = ProtectionOutcome::SilentEscape;  // >=2-bit silent
            }
        } else if (protection_model == "secded_poison") {
            if (bits == 1) {
                // 1-bit: undo the injection (re-apply the mutation = restore).
                if (data) {
                    switch (ft) {
                        case FaultType::BitFlip:  data[byteOffset] ^= mask; break;
                        case FaultType::StuckAtZero: data[byteOffset] |= mask; break;
                        case FaultType::StuckAtOne:  data[byteOffset] &= ~mask; break;
                        default: break;
                    }
                }
                outcome = ProtectionOutcome::Corrected;
            } else if (bits == 2) {
                // 2-bit: poison-log + leave (Latent). Classic cache has no
                // poison bit -> E3 proxy; the corruption propagates if read
                // (SDC), but we LOG what real-hw SECDED would contain here.
                outcome = ProtectionOutcome::Latent;
            } else {
                outcome = ProtectionOutcome::SilentEscape;  // >=3-bit silent
            }
        } else if (protection_model == "secded") {
            if (bits == 1) {
                if (data) {  // undo (Corrected)
                    switch (ft) {
                        case FaultType::BitFlip:  data[byteOffset] ^= mask; break;
                        case FaultType::StuckAtZero: data[byteOffset] |= mask; break;
                        case FaultType::StuckAtOne:  data[byteOffset] &= ~mask; break;
                        default: break;
                    }
                }
                outcome = ProtectionOutcome::Corrected;
            } else if (bits == 2) {
                if (blk) blk->invalidate();  // DetectedContained (recovery)
                outcome = ProtectionOutcome::DetectedContained;
            } else {
                outcome = ProtectionOutcome::SilentEscape;  // false-hit
            }
        } else {
            outcome = ProtectionOutcome::Raw;  // unknown model -> raw
        }

        if (write_log) {
            *(log_stream->stream()) << "    protection: model=" << protection_model
                << " bits=" << bits << " -> " << protectionOutcomeToString(outcome)
                << std::endl;
        }
        return outcome;
    }

    void 
    CHAOSCache::scheduleAttack(Tick time) {
        if (!attackEvent.scheduled()) {
            schedule(attackEvent, time);
        }
    }

    void 
    CHAOSCache::scheduleCheckPermanentFault(Tick time) {
        if (!periodicCheck.scheduled()) {
            schedule(periodicCheck, time);
        }
    }

    BaseTags*
    CHAOSCache::getTags() const
    {
        // G3 (plan §4): use the supported Cache::getTags() accessor instead
        // of the unsafe `static_cast<CacheAccessor*>` downcast that poked
        // the protected BaseCache::tags member via a reinterpret helper
        // (undefined behavior if targetCache is not exactly a Cache, and
        // it broke C++ object-layout assumptions). targetCache is a Cache*
        // per the param, so this is the supported path.
        return targetCache->getTags();
    }

    uint8_t 
    CHAOSCache::generateRandomMask(std::mt19937 &rng, int bits_to_change, unsigned size) {
        // v1.1 Phase 8.3 (design doc §1.2 multi-bit ECC ladder): when
        // faultMask==0 (caller wants a generated mask), bits_to_change bits
        // are now ADJACENT (a contiguous n-bit burst starting at a random
        // position), not independent random positions. Independent random
        // picks made popcount(mask)==bits_to_change improbable (overlapping
        // picks collapse the burst), so applyProtection()'s 2-bit (poison/
        // Latent) and >=3-bit (SilentEscape) branches never fired
        // deterministically — the L1D secded_poison formal only exercised
        // 1-bit Corrected. A contiguous burst matches the physical MBU
        // model (adjacent-cell upset, e.g. a single particle strike) and
        // popcount == bits_to_change exactly.
        if (bits_to_change <= 0) return 0;
        if ((unsigned)bits_to_change >= size) return (uint8_t)((1ULL << size) - 1);
        std::uniform_int_distribution<int> start_dist(0, size - bits_to_change);
        int start = start_dist(rng);
        return (uint8_t)(((1ULL << bits_to_change) - 1) << start);
    }

    void
    CHAOSCache::noteFunnelAtInjection()
    {
        // [LSU][OBS-L3] funnel row with the counts as of NOW. Legacy attack
        // funnel: attempted = attack-event firings, eligible = firings that
        // found >=1 valid block, injected = faults_injected_count.
        // [MDSPEC][R4-5.1] merge mode / [MDSPEC][R4-5.2] fill-timing mode
        // (lsuTrigger != nullptr): the counters are the TRIGGER's —
        // merge: attempted = merge-hook invocations on this cache, eligible
        // = demand-read merges with a corruptible offset bit, injected =
        // trigger-consented corruptions; fill-timing: attempted = fill-hook
        // invocations (response arrivals at the mounted cache), eligible =
        // non-error read fills on a non-forward MSHR, injected =
        // trigger-consented deferrals — the legacy attack never fires in
        // those modes. stdout stays untouched (W2.1 discipline) — the
        // FUNNEL line goes to the injection log only; the abort-survivable
        // copy is the prop-trace node (per-node gzflush).
        const bool merge_mode = (lsuTrigger != nullptr);
        const uint64_t att = merge_mode ? lsuTrigger->attempted
                                        : attack_attempts;
        const uint64_t eli = merge_mode ? lsuTrigger->eligible
                                        : attack_eligible;
        const uint64_t inj = merge_mode ? lsuTrigger->injected
                                        : faults_injected_count;
        if (CHAOSPropagation::instance())
            CHAOSPropagation::instance()->noteFunnel("CHAOSCache", att,
                                                     eli, inj);
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "FUNNEL: attempted=" << att
                << " eligible=" << eli
                << " injected=" << inj << std::endl;
        }
    }

    void
    CHAOSCache::injectFault()
    {
        // [LSU][OBS-L3] legacy attack funnel: this firing attempted an
        // injection (attempted); eligible is counted below when a valid
        // block was found.
        ++attack_attempts;
        BaseTags* tags = getTags();
        unsigned blockSize = targetCache->getBlockSize();

        std::vector<CacheBlk*> validBlocks;

        tags->forEachBlk([&validBlocks](CacheBlk &blk) {
            if (blk.isValid()) {
                validBlocks.push_back(&blk);
            }
        });

        if (validBlocks.empty()) {
            warn("No valid block found\n");
        } else{
            // [LSU][OBS-L3] this firing found >=1 valid block (eligible).
            ++attack_eligible;
            // Directed target (report §六.3 'fixed-to'): if target_block_addr
            // is set, find the VALID block whose regenerated address matches
            // the block-aligned target. If not resident at injection time,
            // fall back to random with a log warning (honest: the fault did
            // not land on the directed block because it wasn't valid).
            CacheBlk* targetBlk = nullptr;
            bool directed_block = (target_block_addr != 0);
            if (directed_block) {
                Addr blkMask = ~(static_cast<Addr>(blockSize) - 1);
                Addr wantBlockAddr = target_block_addr & blkMask;
                for (CacheBlk* blk : validBlocks) {
                    if (tags->regenerateBlkAddr(blk) == wantBlockAddr) {
                        targetBlk = blk;
                        break;
                    }
                }
                if (!targetBlk && write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Directed target_block_addr=0x" << std::hex
                        << target_block_addr << std::dec
                        << " NOT resident (no valid block at that address) — "
                        << "falling back to random block." << std::endl;
                }
            }
            if (!targetBlk) {
                std::uniform_int_distribution<int> blockDist(0, validBlocks.size() - 1);
                int randomIdx = blockDist(rng);
                targetBlk = validBlocks[randomIdx];
            }

            Addr blockAddr = tags->regenerateBlkAddr(targetBlk);

            uint8_t* data = targetBlk->data;

            // §7.7 paired-sector 128B fault-domain proxy: find the 128B-aligned
            // paired partner block (blockAddr XOR 64B). The fault is applied to
            // BOTH sectors at the SAME byte offset. The partner must be VALID+
            // resident (else only the primary is faulted — logged honestly).
            // This models a 128B L3 fault domain spanning two 64B sectors. It is
            // a PROXY, not a cycle-exact Kunpeng L3 model (per plan §7.7/§3.1).
            CacheBlk* partnerBlk = nullptr;
            uint8_t* partnerData = nullptr;
            Addr partnerAddr = 0;
            if (paired_sector) {
                // The partner is the other 64B sector in the same 128B superline.
                Addr partnerBlockAddr = blockAddr ^ blockSize;  // toggle bit (log2(64)=6)
                for (CacheBlk* blk : validBlocks) {
                    if (tags->regenerateBlkAddr(blk) == partnerBlockAddr) {
                        partnerBlk = blk;
                        partnerData = blk->data;
                        partnerAddr = partnerBlockAddr;
                        break;
                    }
                }
                if (write_log && !partnerBlk) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", PAIRED-SECTOR WARN: partner block 0x" << std::hex
                        << partnerBlockAddr << std::dec << " NOT resident — "
                        << "only primary sector faulted (128B domain incomplete)."
                        << std::endl;
                }
            }

            // Directed byte offset (report §六.3 'fixed-to'): if set, pin the
            // fault to this byte within the block; else random.
            bool directed_byte = (target_byte_offset >= 0
                                  && target_byte_offset < (int)blockSize);

            FaultType chosen_fault_type_enum = fault_type_enum;
            if (fault_type_enum == FaultType::Random) {
                int faultIdx = random_fault_distribution(rng);
                chosen_fault_type_enum = static_cast<FaultType>(faultIdx);
            }

            for (int i = 0; i < corruption_size; i++) {
                unsigned char mask = (fault_mask != 0) ? fault_mask : generateRandomMask(rng, bits_to_change, 8);
                int byteOffset;
                if (directed_byte) {
                    byteOffset = target_byte_offset;
                } else {
                    std::uniform_int_distribution<int> byteDist(0, blockSize - 1);
                    byteOffset = byteDist(rng);
                }

                if (mask == 0) {
                    warn("Mask is 0.");
                    continue;
                }

                // §2.7/§2.11 field-level fault: when target_field != "data",
                // corrupt the CacheBlk field (valid/dirty/coh) instead of the
                // data byte. tag(F5) + repl deferred.
                // v1.2 Phase 14 (plan 14 item 1): L2 tag F5 — replace the
                // block's tag with ANOTHER VALID BLOCK's tag from the same
                // cache (a legal, aligned, in-cache alias — modeling a tag
                // SRAM soft error that hits a legal value, NOT a random bit
                // flip). The block now aliases: a lookup for the OTHER
                // address hits THIS block's data -> silent wrong-data
                // (method2-style).
                if (target_field == "tag") {
                    if (validBlocks.size() < 2) {
                        if (write_log) {
                            *(log_stream->stream()) << "Tick: " << curTick()
                                << ", Cache Block Addr: " << blockAddr
                                << ", Field: tag — NO partner block (need >=2 valid)"
                                << std::endl;
                        }
                        faults_injected_count++;
                        continue;
                    }
                    // pick a partner != targetBlk
                    CacheBlk *partner = nullptr;
                    for (auto *b : validBlocks) {
                        if (b != targetBlk) { partner = b; break; }
                    }
                    if (!partner) continue;
                    auto old_tag = targetBlk->getTag();
                    // re-tag via invalidate + insert (TaggedEntry::insert
                    // asserts !isValid() — setValid on a valid block aborts;
                    // found on the real machine as a gem5 assertion failure
                    // at the injection tick). The block now answers to the
                    // partner's address.
                    bool was_secure = targetBlk->isSecure();
                    targetBlk->invalidate();
                    targetBlk->insert({partner->getTag(), was_secure});
                    stats->numFaultsInjected++;
                    faults_injected_count++;
                    // [LSU][OBS-L3] tag fault: inj node only (alias target
                    // unknowable from the CPU side — chain honestly stops).
                    if (CHAOSPropagation::instance())
                        CHAOSPropagation::instance()->registerCacheFault(
                            blockAddr, -2, blockSize, "tag");
                    if (write_log) {
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", Cache Block Addr: " << blockAddr
                            << ", Field: tag (F5 alias), old_tag=0x" << std::hex
                            << old_tag << " -> new_tag=0x" << partner->getTag()
                            << std::dec << std::endl;
                    }
                    continue;
                }
                if (target_field == "valid") {
                    targetBlk->invalidate();
                    stats->numFaultsInjected++;
                    // [LSU][OBS-L3] metadata fault: inj node only.
                    if (CHAOSPropagation::instance())
                        CHAOSPropagation::instance()->registerCacheFault(
                            blockAddr, -2, blockSize, "valid");
                    if (write_log) {
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", Cache Block Addr: " << blockAddr
                            << ", Field: valid (invalidate)" << std::endl;
                    }
                    faults_injected_count++;
                    continue;  // skip byte mutation
                } else if (target_field == "data_shift") {
                    // LSU W6 C09: way-select MUX / alignment corruption —
                    // rotate the block's data by 1 byte (misaligned readout
                    // from the wrong way/offset in the data array).
                    int blkSize = targetCache->getBlockSize();
                    uint8_t *data = targetBlk->data;
                    if (data && blkSize > 1) {
                        uint8_t tmp = data[0];
                        for (int i = 0; i < blkSize - 1; ++i)
                            data[i] = data[i + 1];
                        data[blkSize - 1] = tmp;
                    }
                    stats->numFaultsInjected++;
                    faults_injected_count++;
                    // [LSU][OBS-L3] whole-block fault: every byte corrupt —
                    // register the full block range (delivery tracking ON).
                    if (CHAOSPropagation::instance())
                        CHAOSPropagation::instance()->registerCacheFault(
                            blockAddr, -1, blockSize, "data_shift");
                    if (write_log) {
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", Cache Block Addr: " << blockAddr
                            << ", Field: data_shift (C09 rotate by 1 byte)"
                            << std::endl;
                    }
                    continue;
                } else if (target_field == "dirty" || target_field == "coh") {
                    // Force-set a coherence bit (dirty is a coherence bit in
                    // gem5). honest: a true toggle needs a getter (none public);
                    // set-the-bit is a valid fault (e.g. spurious dirty ->
                    // spurious writeback). Use the public setCoherenceBits.
                    unsigned bit = (target_field == "dirty") ? 0x4 : 0x1;
                    targetBlk->setCoherenceBits(bit);
                    stats->numFaultsInjected++;
                    // [LSU][OBS-L3] metadata fault: inj node only.
                    if (CHAOSPropagation::instance())
                        CHAOSPropagation::instance()->registerCacheFault(
                            blockAddr, -2, blockSize, target_field.c_str());
                    if (write_log) {
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", Cache Block Addr: " << blockAddr
                            << ", Field: " << target_field << " (toggle bit "
                            << bit << ")" << std::endl;
                    }
                    faults_injected_count++;
                    continue;
                }

                // §2.11 L1I semantic-field stratification
                if (!l1i_semantic_field.empty() && l1i_semantic_field != "none") {
                    int lo=-1, hi=-1;
                    if (l1i_semantic_field == "opcode") { lo=25; hi=31; }
                    else if (l1i_semantic_field == "rn") { lo=5; hi=9; }
                    else if (l1i_semantic_field == "rm") { lo=16; hi=20; }
                    else if (l1i_semantic_field == "rd") { lo=0; hi=4; }
                    else if (l1i_semantic_field == "imm12") { lo=10; hi=21; }
                    else if (l1i_semantic_field == "cond") { lo=0; hi=3; }
                    if (lo >= 0) {
                        int bit = lo + (int)(rng() % (unsigned)(hi - lo + 1));
                        byteOffset = (bit / 8);
                        mask = (1 << (bit % 8));
                        if (write_log) {
                            *(log_stream->stream()) << "    §2.11 l1i_field=" << l1i_semantic_field
                                << " bit=" << bit << " byteOffset=" << byteOffset
                                << " mask=0x" << std::hex << (int)mask << std::dec << std::endl;
                        }
                    }
                }

                uint8_t orig_byte = data[byteOffset];  // §1.2: for undo (Corrected)

                switch (chosen_fault_type_enum) {
                    case FaultType::StuckAtZero:
                        data[byteOffset] &= ~mask;
                        stats->numStuckAtZero++;
                        stats->numPermanentFaults++;
                        permanent_faults[std::make_pair(blockAddr, byteOffset)] = {chosen_fault_type_enum, mask, true};
                        break;
                    case FaultType::StuckAtOne:
                        data[byteOffset] |= mask;
                        stats->numStuckAtOne++;
                        stats->numPermanentFaults++;
                        permanent_faults[std::make_pair(blockAddr, byteOffset)] = {chosen_fault_type_enum, mask, true};
                        break;
                    case FaultType::BitFlip:
                        data[byteOffset] ^= mask;
                        stats->numBitFlips++;
                        break;
                    default:
                        break;
                }

                // uint8_t newValue = data[byteOffset];
                stats->numFaultsInjected++;

                // [LSU][OBS-L3] data fault on one byte: register the faulted
                // byte with the propagation tracer (inj node + faulted-byte
                // registry — delivery tracking ON; a later load/store whose
                // range covers this byte gets mem_req/resp nodes).
                if (CHAOSPropagation::instance())
                    CHAOSPropagation::instance()->registerCacheFault(
                        blockAddr, byteOffset, blockSize, "data");

                if (write_log){
                    *(log_stream->stream())  << "Tick: " << curTick()
                        << ", Cache Block Addr: " << blockAddr
                        << ", Byte Offset: " << byteOffset
                        << ", FaultType: " << faultTypeToString(chosen_fault_type_enum)
                        << ", Mask: " << std::bitset<8>(mask)
                        << std::endl;
                }

                // §1.2 post-injection protection handling (N1 TRM Table 9-1
                // PROXY). Acts on the faulted block; may undo the mutation
                // (Corrected) or invalidate the block (DetectedContained).
                // Default protection_model="none" = Raw (no-op, zero regression).
                applyProtection(targetBlk, byteOffset, mask, orig_byte,
                                 chosen_fault_type_enum, /*is_paired=*/false);

                // §7.7 paired-sector: apply the SAME fault to the 128B-aligned
                // partner block's same byte offset (128B fault-domain proxy).
                if (paired_sector && partnerBlk) {
                    uint8_t orig_partner = partnerData[byteOffset];  // §1.2 undo
                    switch (chosen_fault_type_enum) {
                        case FaultType::StuckAtZero:
                            partnerData[byteOffset] &= ~mask;
                            permanent_faults[std::make_pair(partnerAddr, byteOffset)] = {chosen_fault_type_enum, mask, true};
                            break;
                        case FaultType::StuckAtOne:
                            partnerData[byteOffset] |= mask;
                            permanent_faults[std::make_pair(partnerAddr, byteOffset)] = {chosen_fault_type_enum, mask, true};
                            break;
                        case FaultType::BitFlip:
                            partnerData[byteOffset] ^= mask;
                            break;
                        default: break;
                    }
                    stats->numFaultsInjected++;  // count the paired fault too
                    // [LSU][OBS-L3] paired-sector partner byte (own chain).
                    if (CHAOSPropagation::instance())
                        CHAOSPropagation::instance()->registerCacheFault(
                            partnerAddr, byteOffset, blockSize, "data_paired");
                    if (write_log) {
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", PAIRED Cache Block Addr: " << partnerAddr
                            << ", Byte Offset: " << byteOffset
                            << ", FaultType: " << faultTypeToString(chosen_fault_type_enum)
                            << ", Mask: " << std::bitset<8>(mask)
                            << ", superline: 0x" << std::hex
                            << (blockAddr & ~((Addr)2*blockSize - 1))
                            << std::dec << std::endl;
                    }
                    // §1.2 protection handling on the paired partner too.
                    applyProtection(partnerBlk, byteOffset, mask, orig_partner,
                                     chosen_fault_type_enum, /*is_paired=*/true);
                }
            }

            // [LSU][OBS-L3] one funnel row per attack that ran (log line is
            // best-effort — lost on abort; the prop-trace node is durable).
            noteFunnelAtInjection();

            // targetBlk->setCoherenceBits(CacheBlk::DirtyBit);
        }

        // G5: single-fault enforcement. Count the valid injections that
        // happened this attack (one per corruption_size byte). If we've
        // reached max_faults, STOP rescheduling. max_faults==0 = unlimited.
        faults_injected_count += corruption_size;
        if (max_faults != 0 && faults_injected_count >= max_faults) {
            return;  // do not reschedule
        }

        // G6: next-event interval must be >= 1 clock cycle. Clamp the
        // geometric-sampled distance to >= 1 (it can be 0 at high p, which
        // made the event re-fire in the same tick infinitely).
        unsigned dist_cycles = inter_fault_cycles_dist(rng);
        if (dist_cycles < 1) dist_cycles = 1;
        Tick next_injection = curTick() + dist_cycles * tick_to_clock_ratio;
        if (next_injection <= last_tick || last_tick == 0) {
            scheduleAttack(next_injection);
        }
    }

    void
    CHAOSCache::checkPermanent()
    {
        BaseTags* tags = getTags();

        for (auto& entry : permanent_faults) {
            if(entry.second.update){
                const std::pair<Addr, int>& key = entry.first;
                const PermanentFault& fault = entry.second;

                Addr blockAddr = key.first;
                int byteOffset = key.second;
                FaultType faultType = fault.fault_type;
                uint64_t mask = fault.mask;

                CacheBlk* blk = nullptr;
                tags->forEachBlk([&](CacheBlk &b) {
                    Addr blkAddr = tags->regenerateBlkAddr(&b);
                    if (blkAddr == blockAddr && b.isValid()) {
                        blk = &b;
                    }
                });
                if (!blk) {
                    continue;
                }

                uint8_t* data = blk->data;
                // uint8_t oldValue = data[byteOffset];

                switch (faultType) {
                    case FaultType::StuckAtZero:
                        data[byteOffset] &= ~((uint8_t)mask);
                        break;
                    case FaultType::StuckAtOne:
                        data[byteOffset] |= ((uint8_t)mask);
                        break;
                    default:
                        break;
                }
            }
        }
    }
    // v1.2 Phase 14 (plan item 2): victim/writeback-path fault. Called by
    // BaseCache::writebackBlk after setDataFromBlock — the corruption lives
    // only in the in-flight writeback payload (the cache array stays
    // clean, so a re-read of the block gets the GOOD data: the fault
    // surfaces only if the next level's copy is later read back).
    bool
    CHAOSCache::maybeCorruptVictim(PacketPtr pkt)
    {
        if (!victim_fault) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults) return false;
        if (!pkt || !pkt->hasData()) return false;
        uint8_t *data = pkt->getPtr<uint8_t>();
        unsigned sz = pkt->getSize();
        if (sz == 0) return false;
        // adjacent multi-bit mask (the Phase 8.3 generator) on a random byte
        std::uniform_int_distribution<int> byteDist(0, sz - 1);
        int off = byteDist(rng);
        uint8_t mask = generateRandomMask(rng, bits_to_change, 8);
        if (mask == 0) mask = 0x80;
        data[off] ^= mask;
        faults_injected_count++;
        // [LSU][OBS-L3] victim-path fault: inj node only — the corruption
        // lives in the in-flight writeback payload (block_addr recorded for
        // the chain bookkeeping; no delivery tracking, the chain honestly
        // stops at inj). Attempted/eligible are not attack-event counters
        // on this path — the funnel row uses the real legacy counters.
        if (CHAOSPropagation::instance())
            CHAOSPropagation::instance()->registerCacheFault(
                pkt->getAddr(), -2, 0, "victim");
        if (write_log) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Site: writebackBlk (victim path), pkt_addr=0x" << std::hex
                << pkt->getAddr() << std::dec << ", byte_off=" << off
                << ", Mask: " << std::bitset<8>(mask)
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

    // [MDSPEC][R4-5.1] C11 MSHR merge corruption. BaseCache::
    // handleTimingReqMiss calls this in its coalescing branch (MSHR hit),
    // BEFORE mshr->allocateTarget. With the trigger's consent, ONE bit of
    // the merging target's address is flipped inside the block-offset
    // domain at/above log2(size): the merged target stays same-line (the
    // merge remains a legal same-line merge — the activation criterion
    // "at least 1 outstanding miss; merge needs same-line requests" holds),
    // the access stays size-aligned, and offset+size <= blkSize always
    // (BaseCache::satisfyRequest asserts it; bits below log2(size) could
    // push an unaligned offset past the bound — the [P4-FIX-GEOM] class).
    // Downstream: the fill's readout (satisfyRequest -> setDataFromBlock
    // at getOffset(blkSize)) serves the block at the WRONG offset and the
    // response returns on the corrupted address, so the fault is consumed
    // (activated) by the load that owns the merged target.
    bool
    CHAOSCache::maybeCorruptMergeTarget(BaseCache *cache, PacketPtr pkt)
    {
        if (target_field != "mshr_merge") return false;  // mode off
        if (cache != targetCache) return false;          // only the mounted cache
        if (!pkt || !lsuTrigger) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;                                // G5 single-fault cap

        lsuTrigger->onAttempt();

        // Eligibility: a demand READ merging into the outstanding MSHR,
        // with at least one flippable offset bit (log2(size) <= bit <
        // log2(blkSize); a whole-line access has none — honest skip).
        const unsigned blk_sz = targetCache->getBlockSize();
        const unsigned size = pkt->getSize();
        if (!pkt->isRead() || !pkt->isDemand() || size == 0 || size > blk_sz)
            return false;
        int lo = 0;  while ((1u << lo) < size)   ++lo;   // ceil(log2(size))
        int hi = 0;  while ((1u << hi) < blk_sz) ++hi;   // log2(blkSize)
        if (lo >= hi)
            return false;

        bool go;
        if (lsuTrigger->tier == ChaOSLsuTier::F6) {
            // C11's F6 "specified event" IS the MSHR merge (this model's
            // event source — the 09 §2.1 four-event list is the W1 map,
            // not an exhaustive enumeration; the matrix F6 row reads "如
            // TLB hit、SQ forward、..."; recorded as the fifth F6 source
            // in chaos_lsu_trigger.hh). TRUE firing condition: F6 fires
            // at the FIRST merge that passes the eligibility gate above —
            // a demand READ merging into the mounted cache's outstanding
            // MSHR with >=1 flippable offset bit ([log2(size),
            // log2(blkSize))). Non-demand merges (writes, prefetches) and
            // whole-line accesses (no flippable bit) return BEFORE this
            // point: attempted, but never the F6 event. Once-ever =
            // early_stress (first occurrence), the only formal-track F6
            // semantics (A5 ruling).
            //
            // Funnel accounting ([MDSPEC][R4-5.1-review-I1]): onAttempt()
            // above already booked attempted for THIS hook invocation
            // exactly once — the merge hook is the attempt stream — so the
            // event gate must not re-book it: onF6Event(false). It books
            // eligible+injected at the firing merge (the W1 thunk sites
            // keep the onF6Event() default — their event notification has
            // no onAttempt, see chaos_lsu_trigger.hh). With the campaign
            // cap maxFaults=1 the hook stops at the cap check above right
            // after the fire, so attempted/eligible freeze at fire time
            // (exact); with maxFaults=0 post-fire merges keep counting
            // attempted only — the single-shot trigger stops sampling.
            go = lsuTrigger->onF6Event(false);
        } else {
            go = lsuTrigger->onEligible();
        }
        if (!go)
            return false;

        // Bit choice: uniform over the alignment-preserving domain, driven
        // by the seeded mt19937 (reproducible with --l1d_rng_seed).
        const int bit = lo + (int)(rng() % (unsigned)(hi - lo));
        const Addr old_addr = pkt->getAddr();
        const Addr new_addr = old_addr ^ ((Addr)1 << bit);
        pkt->setAddr(new_addr);
        ++faults_injected_count;
        if (stats)
            stats->numFaultsInjected++;
        const Addr line = old_addr & ~((Addr)blk_sz - 1);

        // Propagation registration: inj node (corr=origin; the writeNode
        // dual-emit lifts old_addr/new_addr -> before/after and block_addr
        // -> cache_line) + the CORRUPTED target range in the faulted-byte
        // registry, so (a) the H4 mshr_merge event right after this (it
        // correlates on the corrupted address, same line) joins the chain,
        // (b) mshr_fill/cache_fill/mshr_free on the line join by overlap,
        // and (c) noteMemResponse's cache arm (pkt->getAddr() = the
        // corrupted address the response returns on) fires resp +
        // lq_complete + taint_reg. All address-only joins — corr=
        // addr_fallback, the labeled C-family arm (no seq primary at this
        // site).
        if (CHAOSPropagation::instance())
            CHAOSPropagation::instance()->registerMshrMergeFault(
                line, old_addr, new_addr, size);

        // Injection-log detail line (L0 parses the "Cache Block Addr/Field"
        // contract — tools/lsu_obs_core._CACHE_FIELD_INJ_RE; the mshr_id of
        // the merged-into MSHR is on the H4 mshr_merge event that follows
        // this on the prop stream).
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Cache Block Addr: " << line
                << ", Field: mshr_merge (C11 target addr bit_flip bit " << bit
                << "), old_addr=0x" << std::hex << old_addr
                << ", new_addr=0x" << new_addr << std::dec
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        // One funnel row per successful injection (abort-survivable: the
        // prop-trace node is gzflushed per node; the log line is
        // best-effort) — merge-mode counters via noteFunnelAtInjection.
        noteFunnelAtInjection();
        return true;
    }

    // [MDSPEC][R4-9-FSMC] O04/O05/O09 LSE atomic-RMW hook (declared in
    // CHAOSCache.hh). BaseCache::satisfyRequest's SwapReq branch calls this
    // right after the atomic op functor ran, so at entry:
    //   ret  = pkt->getPtr()  -> the OLD value (the result/old-value latch)
    //   blk_data              -> the NEW memory value (the write-side latch)
    // The three modes are pure data-path edits of those two windows; the
    // trigger is the LSU event-normalized one on the RMW-commit stream (F6
    // fires at the first eligible RMW — the same CasSuccess event the F6
    // census already counts in base.cc).
    bool
    CHAOSCache::maybeCorruptRmw(BaseCache *cache, PacketPtr pkt,
                                uint8_t *blk_data)
    {
        const bool rmw_on = (target_field == "rmw_mux" ||
                             target_field == "rmw_latch" ||
                             target_field == "rmw_order");
        if (!rmw_on) return false;                       // mode off
        if (cache != targetCache) return false;          // only the mounted cache
        if (!pkt || !blk_data || !lsuTrigger) return false;
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;                                // G5 single-fault cap

        lsuTrigger->onAttempt();

        // Eligibility: a real atomic RMW with a non-zero access size that
        // carries a return-value buffer. An ATOMIC_NO_RETURN_OP form has no
        // result latch to deliver and a whole-line access has no bounded
        // window — both honest skips (attempted, never eligible).
        const unsigned blk_sz = targetCache->getBlockSize();
        const unsigned size = pkt->getSize();
        if (size == 0 || size > blk_sz)
            return false;
        // The returned OLD value lives in the packet's data buffer (set by
        // BaseCache::satisfyRequest's pkt->setData(blk_data) before the
        // atomic op functor ran). getPtr is a template (no default arg).
        if (!pkt->isAtomicOp())
            return false;
        uint8_t *ret = pkt->getPtr<uint8_t>();

        bool go;
        if (lsuTrigger->tier == ChaOSLsuTier::F6) {
            // R4-9-FSMC: the RMW commit IS the F6 event source for these
            // modes (the atomic's specified event). onAttempt() already
            // booked this hook invocation, so book_attempt=false
            // ([R4-5.1-review-I1] accounting).
            go = lsuTrigger->onF6Event(false);
        } else {
            go = lsuTrigger->onEligible();
        }
        if (!go)
            return false;

        int log_byte = -1;      // -1 = whole-access range (multi-byte rules)

        if (rmw_rule == "swap_oldnew") {
            // O04-a "交换 old/new 值": the data-select MUX delivered the
            // wrong source — software receives the NEW value and memory keeps
            // the OLD one. Both fragments are legal bit strings, so the
            // encoding/crash profile is unchanged (the spec's 位模式合法且
            // 可能不崩溃，预期高 SDC).
            for (unsigned i = 0; i < size; ++i) {
                const uint8_t t = ret[i];
                ret[i] = blk_data[i];
                blk_data[i] = t;
            }
        } else if (rmw_rule == "result_old") {
            // O09-a: ONE bit of the result/old-value latch (the returned
            // value). Address, opcode, success status and transaction timing
            // are untouched — the injected fault is purely the value
            // software observes.
            const unsigned bit = (unsigned)(rng() % (8u * size));
            ret[bit >> 3] ^= (uint8_t)(1u << (bit & 7u));
            log_byte = (int)(bit >> 3);
        } else if (rmw_rule == "lost") {
            // O05-a: the RMW's completion is lost — the memory update is
            // dropped (the RMW took effect zero times) while the returned
            // OLD value stays correct (the spec's "数据载荷保持正确").
            for (unsigned i = 0; i < size; ++i)
                blk_data[i] = ret[i];
        } else {   // "dup"
            // O05-b: the RMW is executed twice — the atomic op functor is
            // re-applied to the block. The returned OLD value stays correct.
            AtomicOpFunctor *op = pkt->getAtomicOp();
            if (op)
                (*op)(blk_data);
        }

        ++faults_injected_count;
        ++rmw_injections;
        if (stats)
            stats->numFaultsInjected++;

        // [MDSPEC][R4-9-FSMC] Propagation registration: a
        // result/old-value-face fault. The registerable correlate surface at
        // this site is the RMW's LINE (+ the exact byte for the one-bit
        // latch rule); registering it lets the downstream events on that
        // line join the chain address-only (the labeled addr_fallback arm —
        // the C-family has no seq primary at the cache site).
        const Addr acc_addr = pkt->getAddr();
        const Addr line = acc_addr & ~((Addr)blk_sz - 1);
        const int blk_off = (int)(acc_addr & ((Addr)blk_sz - 1));
        if (CHAOSPropagation::instance())
            CHAOSPropagation::instance()->registerCacheFault(
                line, log_byte < 0 ? -1 : (blk_off + log_byte), blk_sz,
                target_field.c_str());

        // Injection-log detail line (L0 parses the "Cache Block Addr/Field"
        // contract — tools/lsu_obs_core._CACHE_FIELD_INJ_RE).
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Cache Block Addr: " << line
                << ", Field: " << target_field << " (rule " << rmw_rule
                << ", size " << size << ")"
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        noteFunnelAtInjection();
        return true;
    }

    // [MDSPEC][R4-5.2] C12 fill-timing resume (fillResumeEvent thunk, fired
    // at the shifted tick). fillPendingPkt stays SET during the re-entry:
    // the re-entered recvTimingResp -> maybeDeferFillTiming sees
    // pkt == fillPendingPkt and processes the packet instead of deferring
    // again — independent of tier/maxFaults (an F5+unlimited config cannot
    // loop). The packet is deleted inside recvTimingResp, so afterwards the
    // stale pointer is only nulled, never dereferenced. If the simulation
    // ends before the resume fires, the deferred fill is simply LOST (the
    // honest C12-a "fill lost" semantics) — with a finite delay this needs
    // an exit within the offset window, which no campaign cell does.
    void
    CHAOSCache::resumeDeferredFill()
    {
        PacketPtr pkt = fillPendingPkt;
        if (!pkt)
            return;
        targetCache->chaosResumeDeferredResp(pkt);
        fillPendingPkt = nullptr;
    }

    // [MDSPEC][R4-5.2] C12 fill-timing offset. BaseCache::recvTimingResp
    // calls this at the TOP, BEFORE popSenderState — the packet still owns
    // its MSHR sender state, so deferring it keeps the MSHR outstanding
    // (later same-line requests keep merging; the targets keep waiting).
    // With the trigger's consent, the fill's processing is shifted to
    // curTick() + lsuFillDelayCycles cache clock edges: the miss-latency
    // stat, handleFill (with the H4 mshr_fill/cache_fill/mshr_free
    // events), serviceMSHRTargets and the MSHR deallocation all run at the
    // shifted tick — the consumer gets the SAME data at a SHIFTED time
    // (the timing fault the C12 model specifies; the drop/duplicate/
    // early-valid/stale-tag submodels C12-a..d are NOT this mode — only
    // the bounded offset is).
    bool
    CHAOSCache::maybeDeferFillTiming(BaseCache *cache, PacketPtr pkt)
    {
        if (target_field != "mshr_fill_timing") return false;  // mode off
        if (cache != targetCache) return false;   // only the mounted cache
        if (!pkt || !lsuTrigger) return false;
        if (pkt == fillPendingPkt) return false;  // resume re-entry: process
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;                         // G5 single-fault cap
        if (fillPendingPkt) return false;         // single slot occupied

        lsuTrigger->onAttempt();

        // Eligibility: a response that will FILL this cache — a non-error
        // READ whose sender state is a non-forward MSHR (mirrors
        // recvTimingResp's is_fill for the read arm). Write-class
        // responses (UpgradeResp / whole-line-write / LockedRMWWriteResp)
        // and error responses count as attempted but never defer. A
        // HardPFResp prefetch fill on the mounted cache would be an
        // eligible READ; on B0 the L2 owns the prefetcher, so the L1D
        // stream the campaign measures is demand-only (honest note).
        MSHR *mshr = dynamic_cast<MSHR *>(pkt->senderState);
        if (!pkt->isRead() || pkt->isError() || !mshr || mshr->isForward)
            return false;

        bool go;
        if (lsuTrigger->tier == ChaOSLsuTier::F6) {
            // C12's F6 "specified event" IS the miss fill (a read fill
            // response arriving at the mounted L1D — this model's event
            // source, the SIXTH registered in chaos_lsu_trigger.hh; the
            // 09 §2.1 four-event list is the W1 map, not exhaustive).
            // TRUE firing condition: the FIRST fill response that passes
            // the eligibility gate above (early_stress first-occurrence,
            // A5 ruling). onF6Event(false): attempted was already booked
            // exactly once by onAttempt() above — the fill hook is the
            // attempt stream, so the event gate must not re-book it
            // ([MDSPEC][R4-5.1-review-I1], the C11 fix; the W1 thunk
            // sites keep the default true).
            go = lsuTrigger->onF6Event(false);
        } else {
            go = lsuTrigger->onEligible();
        }
        if (!go)
            return false;

        // The offset: shift the fill's processing to a later clock edge of
        // the MOUNTED cache's domain. lsuFillDelayCycles >= 1 is ctor-
        // panicked, so clockEdge is strictly in the future.
        const Tick when = targetCache->clockEdge(Cycles(fill_delay_cycles));
        if (when <= curTick())
            return false;   // defensive: never schedule in the past

        fillPendingPkt = pkt;
        schedule(fillResumeEvent, when);
        ++faults_injected_count;
        if (stats)
            stats->numFaultsInjected++;
        const unsigned blk_sz = targetCache->getBlockSize();
        const Addr line = pkt->getAddr() & ~((Addr)blk_sz - 1);

        // Propagation registration: inj node (corr=origin; addr column =
        // the fill line; the timing pair arrival_tick/deferred_tick rides
        // the UNIFIED before/after fields — registerFillTimingFault writes
        // before=<arrival_tick>;after=<deferred_tick> into the detail,
        // before/after are registered PROP_EVT_FIELDS, so parseDetail
        // lifts the pair onto the stream. They carry this model's faulted
        // VALUE, the fill's delivery tick before/after the offset —
        // tick-valued here, address-valued for the C11 merge model, so
        // consumers must read them together with `field`. delay_cycles
        // stays detail-only (v1 CSV node; derivable as after-before) and
        // the shift is also witnessed on the trace as
        // mshr_fill.tick - inj.tick) + the WHOLE fill line in the
        // faulted-byte registry, so (a) the delayed H4 mshr_fill/
        // cache_fill/mshr_free events (correlateBlock on the line) join
        // the chain at the shifted tick, (b) cache_access on any later
        // lookup of the line joins (L1), and (c) noteMemResponse's cache
        // arm (the response is delivered on this very line) fires resp +
        // lq_complete + taint_reg at the shifted tick. All address-only
        // joins — corr=addr_fallback, the labeled C-family arm (no seq
        // primary at this site).
        if (CHAOSPropagation::instance())
            CHAOSPropagation::instance()->registerFillTimingFault(
                line, blk_sz, curTick(), when, fill_delay_cycles);

        // Injection-log detail line (L0 parses the "Cache Block Addr/
        // Field" contract — tools/lsu_obs_core._CACHE_FIELD_INJ_RE; the
        // mshr_id/fill_id of the deferred fill are on the DELAYED H4
        // mshr_fill/cache_fill events).
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Cache Block Addr: " << line
                << ", Field: mshr_fill_timing (C12 fill deferred "
                << fill_delay_cycles << " cycles), arrival_tick=" << curTick()
                << ", deferred_tick=" << when
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        // One funnel row per successful injection (abort-survivable: the
        // prop-trace node is gzflushed per node; the log line is
        // best-effort) — trigger-mode counters via noteFunnelAtInjection.
        noteFunnelAtInjection();
        return true;
    }

    // [MDSPEC][R4-5.5] C14-a MSHR busy/occupied stuck-at-1 (resource leak).
    // BaseCache::recvTimingResp calls this IMMEDIATELY BEFORE
    // mshrQueue.deallocate(mshr). Consent => the caller SKIPS the
    // deallocation: the serviced entry stays in the queue's allocated list
    // and never returns to the free list (the "busy/occupied stuck-at-1"
    // of the model). The corresponding miss completed normally — the fill
    // was already delivered by serviceMSHRTargets before this point, so
    // the consumer got its data; only the SLOT is lost. Once the leaked
    // slot is the last free-demand entry isFull() stays true, the CPU side
    // stays blocked (Blocked_NoMSHRs) and prefetch is starved: the 03
    // sheet's "容量退化和Timeout". See the .hh contract for the call
    // site, the single-slot rule and the honest consequences.
    bool
    CHAOSCache::maybeStickMshrBusy(BaseCache *cache, MSHR *mshr, Addr line,
                                   uint64_t in_service, bool was_full)
    {
        if (target_field != "mshr_busy_leak") return false;  // mode off
        if (cache != targetCache) return false;   // only the mounted cache
        if (!mshr || !lsuTrigger) return false;
        if (mshr_busy_victim) return false;  // single slot: one entry per run
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;                     // G5 single-fault cap

        lsuTrigger->onAttempt();

        // Eligibility: THIS call site is the MSHR release point — the fill
        // has completed (the 03 sheet's "对应 miss 正常完成") and the entry
        // is about to return to the free list. The faulted VALUE is the
        // entry's occupied/busy state: correct = released, faulty = stuck
        // busy. No further filter (every release is an eligible event; the
        // one-entry rule comes from the single slot + maxFaults=1).
        bool go;
        if (lsuTrigger->tier == ChaOSLsuTier::F6) {
            // C14's F6 "specified event" IS the MSHR completing-and-
            // should-release (this model's event source — the 09 §2.1
            // four-event list is the W1 map, not an exhaustive
            // enumeration; recorded as the NINTH F6 source in
            // chaos_lsu_trigger.hh). onF6Event(false): attempted was
            // already booked exactly once by onAttempt() above — the
            // release hook IS the attempt stream, so the event gate must
            // not re-book it ([MDSPEC][R4-5.1-review-I1], the C11 fix
            // shape; the W1 thunk sites keep the default true).
            go = lsuTrigger->onF6Event(false);
        } else {
            go = lsuTrigger->onEligible();
        }
        if (!go)
            return false;

        mshr_busy_victim = mshr;
        ++mshr_busy_leaks;
        ++faults_injected_count;
        if (stats)
            stats->numFaultsInjected++;

        // Occupancy pair (this model's faulted value — the 4th per-model
        // value type after C12's tick pair, L04's seq pair and P06's
        // classification pair). in_service was sampled by the caller
        // BEFORE the deallocation, so it still counts this entry: the
        // correct release would leave in_service-1, the skipped release
        // leaves in_service.
        const uint64_t occ_after = in_service;
        const uint64_t occ_before = in_service ? in_service - 1 : 0;

        // Propagation registration: inj node (corr=origin; addr column =
        // the leaked entry's line; before/after = the occupancy pair) +
        // the model-specific mshr_busy node (the stuck state itself) + the
        // line in the faulted-byte registry so later events on that line
        // join address-only (the labeled addr_fallback arm — the C-family
        // site has no seq primary). HONEST NOTE: the H4 mshr_free event
        // for this line fires EARLIER, inside handleFill — it reports the
        // INTENDED release, while this mshr_busy node reports that the
        // release was actually SKIPPED; the two together are the read-out
        // of the leak.
        if (CHAOSPropagation::instance())
            CHAOSPropagation::instance()->registerMshrBusyFault(
                line, targetCache->getBlockSize(), occ_before, occ_after,
                was_full);

        // Injection-log detail line (L0 parses the "Cache Block Addr/
        // Field" contract — tools/lsu_obs_core._CACHE_FIELD_INJ_RE).
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Cache Block Addr: " << line
                << ", Field: mshr_busy_leak (C14-a occupied-stuck-at-1 "
                << "release-skipped), in_service_before=" << occ_before
                << ", in_service_after=" << occ_after
                << ", was_full=" << (was_full ? 1 : 0)
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        // One funnel row per successful injection (abort-survivable via the
        // prop-trace node; the log line is best-effort) — trigger-mode
        // counters via noteFunnelAtInjection.
        noteFunnelAtInjection();
        return true;
    }

    // [MDSPEC][R4-5.6] C15-b capacity-arbitration "fake free" (sub-model
    // C15-b: "在容量已满时伪造空位"). BaseCache::chaosMshrOccArbitrate
    // calls this from the TAIL of allocateMissBuffer, right after a new
    // miss allocation ran the queue's capacity arbitration. When the queue
    // is FULL (`isFull()` — the public capacity predicate; the private
    // `allocated` counter is unreachable, honest approximation of the 03
    // sheet's "接近或达到容量上限") and the trigger consents, the injector
    // FABRICATES A FREE SLOT: the caller clears the Blocked_NoMSHRs block,
    // the CPU side retries, and exactly ONE further miss allocation
    // consumes a reserve entry BEYOND the arbitration's capacity — the
    // arbitration's allow/deny decision is genuinely wrong, which is the
    // 03 sheet's "仅在仲裁结果真正允许…一次 miss 分配时计为 activated".
    // The fabricated slot is a single-slot state (the flag doubles as the
    // guard); the materialization is read back by noteMshrAllocAttempt.
    bool
    CHAOSCache::maybeFakeFreeSlot(BaseCache *cache, PacketPtr pkt, MSHR *mshr,
                                  uint64_t in_service)
    {
        if (target_field != "mshr_occupancy") return false;  // mode off
        if (cache != targetCache) return false;   // only the mounted cache
        if (!lsuTrigger) return false;
        if (mshr_fake_free_armed) return false;   // single fabricated slot
        if (max_faults != 0 && faults_injected_count >= max_faults)
            return false;                         // G5 single-fault cap

        lsuTrigger->onAttempt();

        // Eligibility: THIS call site is a new miss allocation that left
        // the queue FULL — i.e. the allocation reached the capacity limit
        // (the 03 sheet's trigger condition). No further filter: the
        // arbitration decision this allocation ran is about to be
        // overridden by the fabricated free slot.
        bool go;
        if (lsuTrigger->tier == ChaOSLsuTier::F6) {
            // C15's F6 "specified event" IS a new miss allocation at the
            // MSHR capacity limit (this model's event source — the 09 §2.1
            // four-event list is the W1 map, not exhaustive; recorded as
            // the TENTH F6 source in chaos_lsu_trigger.hh). onF6Event(false):
            // attempted was already booked exactly once by onAttempt()
            // above — the arbitration hook IS the attempt stream, so the
            // event gate must not re-book it ([MDSPEC][R4-5.1-review-I1]).
            go = lsuTrigger->onF6Event(false);
        } else {
            go = lsuTrigger->onEligible();
        }
        if (!go)
            return false;

        mshr_fake_free_armed = true;
        ++mshr_fake_free_fires;
        mshr_occ_at_fire = in_service;
        ++faults_injected_count;
        if (stats)
            stats->numFaultsInjected++;

        // Injection-log detail line (L0 parses the "Cache Block Addr/
        // Field" contract — tools/lsu_obs_core._CACHE_FIELD_INJ_RE). The
        // log records the FABRICATION (the C-family fire-side record, like
        // C11/C12); the real arbitration read-back is the prop-stream
        // mshr_arb node emitted at materialization + the CHAOS_MSHR_OCC
        // teardown line.
        const unsigned blk_sz = targetCache->getBlockSize();
        const Addr line = pkt ? pkt->getBlockAddr(blk_sz) : 0;
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Cache Block Addr: " << line
                << ", Field: mshr_occupancy (C15-b fake-free at capacity), "
                << "in_service=" << in_service
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        // One funnel row per successful injection (abort-survivable via the
        // prop-trace node; the log line is best-effort).
        noteFunnelAtInjection();
        return true;   // caller clears Blocked_NoMSHRs (the fabricated slot)
    }

    // [MDSPEC][R4-5.6] C15-b materialization read-back. Called at the TOP
    // of every allocateMissBuffer on the mounted cache. A pending
    // fabricated free slot is CONSUMED here iff this allocation still runs
    // while the queue is full — that allocation is the over-capacity
    // (reserve) one the faulty arbitration allowed. The fault is then
    // REGISTERED (inj + the mshr_arb observation node + the request's line
    // in the faulted-byte registry) and `activated` is bumped. If the
    // queue drained in between (is_full false) the fabricated slot was
    // never used: the flag is dropped and nothing is recorded — an honest
    // Inject-not-activated sample (the fire stays visible in the injection
    // log and the trigger funnel).
    bool
    CHAOSCache::noteMshrAllocAttempt(BaseCache *cache, PacketPtr pkt,
                                     MSHR *mshr, bool is_full,
                                     uint64_t in_service)
    {
        if (target_field != "mshr_occupancy") return false;  // mode off
        if (cache != targetCache) return false;   // only the mounted cache
        if (!mshr_fake_free_armed) return false;  // nothing pending
        if (!is_full) {
            // The queue drained before the fabricated slot was used: the
            // arbitration was never actually widened. Honest no-op.
            mshr_fake_free_armed = false;
            return false;
        }

        mshr_fake_free_armed = false;
        ++mshr_over_commit;

        const unsigned blk_sz = targetCache->getBlockSize();
        const Addr line = pkt ? pkt->getBlockAddr(blk_sz) : 0;

        // Propagation registration: inj node (corr=origin; addr column =
        // the over-committed request's line; before/after = the occupancy
        // pair — the model's faulted value is the occupancy bookkeeping)
        // + the model-specific mshr_arb node + the line in the
        // faulted-byte registry so later events on that line join
        // address-only (corr=addr_fallback — the C-family site has no seq
        // primary).
        if (CHAOSPropagation::instance())
            CHAOSPropagation::instance()->registerMshrArbFault(
                line, blk_sz, mshr_occ_at_fire, in_service, mshr != nullptr);

        // Injection-log detail line: the MATERIALIZATION of the fabricated
        // slot (the arbitration genuinely allowed an over-capacity
        // allocation). Written in addition to the fire line so the log
        // itself carries the fire/materialization distinction.
        if (write_log && log_stream && log_stream->stream()) {
            *(log_stream->stream()) << "Tick: " << curTick()
                << ", Cache Block Addr: " << line
                << ", Field: mshr_occupancy_materialized (C15-b over-capacity "
                << "allocation allowed), occupancy=" << in_service
                << ", faults_injected: " << faults_injected_count
                << std::endl;
        }
        return true;
    }

} // namespace gem5
