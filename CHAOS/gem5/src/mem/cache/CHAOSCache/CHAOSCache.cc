#include "mem/cache/CHAOSCache/CHAOSCache.hh"

#include <random>
#include <vector>

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
        protection_model(p.protectionModel),
        rng_seed(p.rngSeed),
        max_faults(p.maxFaults),
        faults_injected_count(0),
        attackEvent([this] { this->injectFault(); }, name()),
        periodicCheck([this] { this->checkPermanent(); }, name() + ".periodicCheck"),
        stats(nullptr)
    {
        if (probability != 0.0) {
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
            inter_fault_cycles_dist = std::geometric_distribution<unsigned>(probability);

            scheduleAttack(first_tick + inter_fault_cycles_dist(rng) * tick_to_clock_ratio);

            if ((bit_flip_prob + stuck_at_zero_prob + stuck_at_one_prob) != 1.0){
                warn("Sum of probabilities is not 1, assuming 0.9 for bitFlipProb, 0.05 for stuckAtZeroProb and 0.05 for stuckAtOneProb.\n");
                bit_flip_prob = 0.9;
                stuck_at_zero_prob = 0.05;
                stuck_at_one_prob = 0.05;
            }

            std::vector<double> weights = {bit_flip_prob, stuck_at_zero_prob, stuck_at_one_prob};
            random_fault_distribution = std::discrete_distribution<int>(weights.begin(), weights.end());

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
        uint8_t mask = 0;
        std::uniform_int_distribution<int> bit_dist(0, size - 1);
        for (int i = 0; i < bits_to_change; i++) {
            mask |= (1ULL << bit_dist(rng));
        }
        return mask;
    }

    void
    CHAOSCache::injectFault()
    {   
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
                if (target_field == "valid") {
                    targetBlk->invalidate();
                    stats->numFaultsInjected++;
                    if (write_log) {
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", Cache Block Addr: " << blockAddr
                            << ", Field: valid (invalidate)" << std::endl;
                    }
                    faults_injected_count++;
                    continue;  // skip byte mutation
                } else if (target_field == "dirty" || target_field == "coh") {
                    // Force-set a coherence bit (dirty is a coherence bit in
                    // gem5). honest: a true toggle needs a getter (none public);
                    // set-the-bit is a valid fault (e.g. spurious dirty ->
                    // spurious writeback). Use the public setCoherenceBits.
                    unsigned bit = (target_field == "dirty") ? 0x4 : 0x1;
                    targetBlk->setCoherenceBits(bit);
                    stats->numFaultsInjected++;
                    if (write_log) {
                        *(log_stream->stream()) << "Tick: " << curTick()
                            << ", Cache Block Addr: " << blockAddr
                            << ", Field: " << target_field << " (toggle bit "
                            << bit << ")" << std::endl;
                    }
                    faults_injected_count++;
                    continue;
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
} // namespace gem5
