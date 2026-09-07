#include "mem/cache/CHAOSCache/CHAOSCache.hh"

#include <random>
#include <vector>

#include "debug/CHAOSCache.hh"
#include "mem/cache/base.hh"
#include "mem/cache/cache_blk.hh"
#include "mem/cache/replacement_policies/base.hh"
#include "mem/cache/tags/base.hh"
#include "mem/cache/tags/indexing_policies/base.hh"

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
        protection_model(stringToProtectionModel(p.protectionModel)),
        rng_seed(p.rngSeed),
        max_faults(p.maxFaults),
        attackEvent([this] { this->injectFault(); }, name()),
        periodicCheck([this] { this->checkPermanent(); }, name() + ".periodicCheck"),
        faults_injected_count(0),
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

            // §5.8B tag false-hit: register self with the target cache's
            // tag store so BaseTags::findBlock() can consult the alias
            // diversion (same self-attach pattern as cpu->lsqFwd /
            // tlb->chaosTLB). The cache Param is guaranteed constructed
            // first; findBlock only reads chaosCache long after
            // construction. Only needed for tag/tag_to_legal, but
            // registering unconditionally is harmless (hot path checks
            // one bool).
            if (target_field == "tag" || target_field == "tag_to_legal") {
                getTags()->setChaosCache(this);
            }
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
               "Total number of permanent faults injected"),
      ADD_STAT(numEccCorrected, statistics::units::Count::get(),
               "S0-3: 1-bit faults corrected by ECC (ProtectionModel reverted)"),
      ADD_STAT(numDetectedContained, statistics::units::Count::get(),
               "S0-3: 2-bit faults detected+contained (poison, SECDED)"),
      ADD_STAT(numLatent, statistics::units::Count::get(),
               "S0-3: >=2-bit/3-bit beyond SECDED (latent escape)"),
      ADD_STAT(numRawEscaped, statistics::units::Count::get(),
               "S0-3: raw escape (protectionModel=none)"),
      ADD_STAT(numTagFaults, statistics::units::Count::get(),
               "§5.8B: tag bit_flip faults (false-hit/aliasing)"),
      ADD_STAT(numTagToLegalFaults, statistics::units::Count::get(),
               "§5.8B: tag F5 same-set legal substitutions"),
      ADD_STAT(numValidFaults, statistics::units::Count::get(),
               "§5.8B: valid-bit clear faults (refetch)"),
      ADD_STAT(numDirtyFaults, statistics::units::Count::get(),
               "§5.8B: dirty-bit flip faults (silent loss / spurious wb)"),
      ADD_STAT(numReplFaults, statistics::units::Count::get(),
               "§5.8B: replacement-data poisoning faults"),
      ADD_STAT(numCohFaults, statistics::units::Count::get(),
               "§5.8B: coherence permission flip faults")
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

    CHAOSCache::ProtectionModel
    CHAOSCache::stringToProtectionModel(const std::string &s) {
        if (s == "sed")                 return ProtectionModel::SED;
        if (s == "secded")              return ProtectionModel::SECDED;
        if (s == "secded_poison")       return ProtectionModel::SECDEDPoison;
        if (s == "parity_interleaved")  return ProtectionModel::ParityInterleaved;
        return ProtectionModel::None;
    }

    const char*
    CHAOSCache::protectionModelToString(ProtectionModel m) {
        switch (m) {
            case ProtectionModel::None:              return "none";
            case ProtectionModel::SED:               return "sed";
            case ProtectionModel::SECDED:             return "secded";
            case ProtectionModel::SECDEDPoison:       return "secded_poison";
            case ProtectionModel::ParityInterleaved:  return "parity_interleaved";  // G7
        }
        return "none";
    }

    // S0-3 (plan §4.2, §2.3 N1 TRM proxy): apply the ECC model to the just-
    // corrupted byte and report the outcome. Called AFTER the fault mask was
    // applied to *byte (data is now dirty). Decides the observable outcome:
    //   1-bit (popcount==1):
    //     SED            -> line invalidate+refetch (corrected) -> REVERT *byte
    //     SECDED         -> corrected -> REVERT *byte
    //     secded_poison  -> corrected -> REVERT *byte
    //     parity_interleaved -> parity detects 1-bit -> REVERT (re-fetch)
    //   2-bit (popcount==2):
    //     SED            -> >=2-bit silent (cannot detect) -> escape (Latent)
    //     SECDED         -> detected+contained (poison) -> leave dirty, mark poison
    //     secded_poison   -> poison+propagate -> leave dirty, mark poison
    //     parity_interleaved -> same-parity 2-bit silent -> escape (Latent)
    //   >=3-bit: all models beyond SECDED -> escape (Latent/SDC)
    //   None: raw escape.
    // Returns true if the corruption SURVIVED (data left dirty -> may escape
    // as SDC/Latent); false if corrected/reverted (data restored -> Masked/
    // Corrected).
    bool
    CHAOSCache::applyProtectionModel(uint8_t *byte, uint8_t orig, uint8_t mask,
                                     int byteOffset, Addr blockAddr)
    {
        if (protection_model == ProtectionModel::None) {
            stats->numRawEscaped++;
            if (write_log) {
                *(log_stream->stream()) << "  ProtectionModel=none: raw escape "
                    "(mask=" << std::bitset<8>(mask) << ")\n";
            }
            return true;  // data left dirty
        }
        int bits = __builtin_popcount(mask);
        bool survived = false;
        const char *outcome = "";
        if (bits == 1) {
            // All ECC models correct a single-bit flip -> REVERT the byte.
            *byte = orig;
            stats->numEccCorrected++;
            outcome = "EccCorrected";
            survived = false;
        } else if (bits == 2) {
            // SED/parity: cannot detect a same-parity 2-bit -> escape.
            // SECDED/secded_poison: detect+contain (poison) -> leave dirty.
            if (protection_model == ProtectionModel::SED ||
                protection_model == ProtectionModel::ParityInterleaved) {
                stats->numLatent++;
                outcome = "Latent";  // >=2-bit silent
                survived = true;
            } else {  // SECDED, SECDEDPoison
                stats->numDetectedContained++;
                outcome = "Poisoned: DetectedContained";  // contained DUE
                survived = true;  // dirty but contained (poisoned)
            }
        } else {  // >=3 bits: beyond SECDED
            stats->numLatent++;
            outcome = "Latent";  // >=3-bit, undetected escape
            survived = true;
        }
        if (write_log) {
            *(log_stream->stream()) << "  ProtectionModel=" << protectionModelToString(protection_model)
                << " bits=" << bits << " -> " << outcome
                << " (mask=" << std::bitset<8>(mask) << ")\n";
        }
        return survived;
    }

    // §5.8B tag false-hit alias selection: pick the WAY of another VALID
    // block in the SAME set as blk (its data will be served to lookups
    // that match the victim block). Returns -1 if no other valid block
    // exists in the set (caller skips honestly — not an error).
    int
    CHAOSCache::pickSameSetAliasWay(CacheBlk *blk)
    {
        std::vector<int> candidates;
        BaseTags* tags = getTags();
        tags->forEachBlk([&](CacheBlk &b) {
            if (b.isValid() && b.getSet() == blk->getSet()
                && b.getWay() != blk->getWay()) {
                candidates.push_back((int)b.getWay());
            }
        });
        if (candidates.empty()) {
            return -1;
        }
        std::uniform_int_distribution<size_t> dist(0, candidates.size() - 1);
        return candidates[dist(rng)];
    }

    // §5.8B tag false-hit diversion, called from BaseTags::findBlock():
    // `blk` is the block a lookup just matched. If blk is the registered
    // VICTIM way of the alias, return the ALIAS way's block from the
    // same set instead (the lookup gets the WRONG block's data — the
    // false-hit semantics). Otherwise return nullptr (serve the match
    // as-is). Hot path when no alias is registered: one predictable
    // branch on a bool.
    CacheBlk*
    CHAOSCache::chaosDivertFindBlock(CacheBlk *blk,
        const std::vector<ReplaceableEntry*> &entries,
        const CacheBlk::KeyType &key) const
    {
        if (!tag_alias_valid || blk->getSet() != tag_alias_set ||
            blk->getWay() != victim_way) {
            return nullptr;
        }
        // Only divert while the victim still holds the tag it had at
        // injection time — if the victim was replaced meanwhile, the
        // alias no longer models the same fault (skip; the replacement
        // line is innocent).
        for (const auto* location : entries) {
            const CacheBlk* b = static_cast<const CacheBlk*>(location);
            if (b->getWay() == (int)alias_way && b->isValid()) {
                return const_cast<CacheBlk*>(b);
            }
        }
        return nullptr;
    }

    // §5.8B metadata-field injection (plan §5.8B targetField extension):
    // apply the fault to the target block's METADATA instead of its data
    // bytes. Fields:
    //   tag           — XOR the tag with a 1-bit (or bitsToChange-bit) mask
    //                   -> false-hit / aliasing (block answers the WRONG
    //                   address; silent SDC or benign depending on use).
    //   tag_to_legal  — F5: rewrite the tag to another valid same-set
    //                   block's tag (see pickSameSetLegalTag).
    //   valid         — clear the valid bit -> the line no longer answers;
    //                   refetched from below (models tag-SED 1-bit outcome).
    //   dirty         — flip the dirty bit. On a modified line: the
    //                   writeback goes out CLEAN -> the store is silently
    //                   LOST (SDC). On a clean line: marked dirty -> a
    //                   spurious (stale-data) writeback.
    //   repl          — poison the block's replacement data via
    //                   BaseReplacementPolicy::invalidate(), making the RP
    //                   consider it the next probable victim (premature
    //                   eviction of live data).
    //   coh           — flip one coherence permission bit (Writable or
    //                   Readable). Clearing Readable turns hits into misses
    //                   (refetch, likely Masked); clearing Writable on a
    //                   written line forces an upgrade miss (loud); setting
    //                   bits can trip gem5 coherence asserts — the observed
    //                   outcome is honestly whatever gem5 does (Crash is a
    //                   valid DUE-class outcome, but SimulatorError-class
    //                   panics are NOT — the classifier separates them).
    // Returns true if a metadata fault was applied (caller skips the
    // legacy byte path).
    bool
    CHAOSCache::injectMetadataFault(CacheBlk *blk, BaseTags *tags,
                                    Addr blockAddr)
    {
        if (target_field == "tag") {
            // §5.8B tag bit_flip, FALSE-HIT formulation (v2; see header
            // comment for why the stored tag is NOT rewritten): pick an
            // alias block (another VALID block in the same set) and
            // register the false-hit diversion victim->alias. Lookups
            // that match the victim block are served the ALIAS block's
            // data (wrong-data false hit); the tag store/eviction state
            // remain untouched.
            int alias = pickSameSetAliasWay(blk);
            if (alias < 0) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Field: tag, SKIPPED (no other valid block in "
                        << "set " << blk->getSet() << " to alias onto)"
                        << std::endl;
                }
                return false;
            }
            Addr victimTag = blk->getTag();
            tag_alias_set = blk->getSet();
            victim_way = blk->getWay();
            alias_way = (unsigned)alias;
            tag_alias_valid = true;
            stats->numTagFaults++;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Cache Block Addr: " << blockAddr
                    << ", Field: tag (false-hit), VictimTag: 0x" << std::hex
                    << victimTag << ", VictimWay: " << blk->getWay()
                    << " -> AliasWay: " << alias
                    << ", Set: " << blk->getSet() << std::dec << std::endl;
            }
            return true;
        } else if (target_field == "tag_to_legal") {
            // §5.8B F5 tag substitution, false-hit formulation: same
            // diversion as `tag`, but the semantic is "the tag was
            // substituted to another LEGAL tag of the same set" (legal-
            // domain F5): lookups for the victim's address are answered
            // by the alias block (a REAL live line of the same set).
            int alias = pickSameSetAliasWay(blk);
            if (alias < 0) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Field: tag_to_legal, SKIPPED (no other valid "
                        << "block in set " << blk->getSet() << ")"
                        << std::endl;
                }
                return false;  // no legal candidate — skip (not an error)
            }
            Addr victimTag = blk->getTag();
            tag_alias_set = blk->getSet();
            victim_way = blk->getWay();
            alias_way = (unsigned)alias;
            tag_alias_valid = true;
            stats->numTagToLegalFaults++;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Cache Block Addr: " << blockAddr
                    << ", Field: tag_to_legal (F5 false-hit), VictimTag: 0x"
                    << std::hex << victimTag << ", VictimWay: "
                    << blk->getWay() << " -> AliasWay: " << alias
                    << ", Set: " << blk->getSet() << std::dec << std::endl;
            }
            return true;
        } else if (target_field == "valid") {
            // Clear the valid bit. Use the supported CacheBlk::invalidate()
            // (not the raw TaggedEntry path) so all derived state (prefetch,
            // task id, locks) is cleared consistently.
            blk->invalidate();
            stats->numValidFaults++;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Cache Block Addr: " << blockAddr
                    << ", Field: valid, Action: cleared (line refetched)"
                    << std::endl;
            }
            return true;
        } else if (target_field == "dirty") {
            if (blk->isSet(CacheBlk::DirtyBit)) {
                // Modified line marked clean: its eventual writeback will
                // go out CLEAN -> the store is silently lost.
                blk->clearCoherenceBits(CacheBlk::DirtyBit);
            } else {
                // Clean line marked dirty: spurious stale writeback later.
                blk->setCoherenceBits(CacheBlk::DirtyBit);
            }
            stats->numDirtyFaults++;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Cache Block Addr: " << blockAddr
                    << ", Field: dirty, Action: flipped, NowDirty: "
                    << (blk->isSet(CacheBlk::DirtyBit) ? 1 : 0)
                    << std::endl;
            }
            return true;
        } else if (target_field == "repl") {
            // Poison the block's replacement data so the RP sees it as the
            // next probable victim (premature eviction of live data).
            // BaseTags keeps the RP protected (BaseSetAssoc/SectorTags),
            // so we add a supported narrow accessor there (same G3
            // pattern as Cache::getTags). If the tags type does not
            // expose one, we skip honestly (no silent no-op).
            replacement_policy::Base *rp = tags->getReplacementPolicy();
            if (!rp) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Field: repl, SKIPPED (tags type exposes no "
                        << "replacement policy)" << std::endl;
                }
                return false;
            }
            rp->invalidate(blk->replacementData);
            stats->numReplFaults++;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Cache Block Addr: " << blockAddr
                    << ", Field: repl, Action: replacement-data poisoned "
                    "(next probable victim)" << std::endl;
            }
            return true;
        } else if (target_field == "coh") {
            // Flip ONE coherence permission bit. Prefer clearing Readable
            // (hit->miss->refetch, silent-ish) 50/50 with clearing
            // Writable (write hit->upgrade miss, louder). Never SET bits
            // — setting Writable on a shared line trips gem5 coherence
            // asserts (SimulatorError, not a valid DUE outcome).
            std::uniform_int_distribution<int> coin(0, 1);
            unsigned bit = coin(rng) ? CacheBlk::WritableBit
                                     : CacheBlk::ReadableBit;
            // Only CLEAR a bit that is actually set (clearing a clear bit
            // is a no-op, not a fault).
            if (!blk->isSet(bit)) {
                bit = (bit == CacheBlk::WritableBit) ? CacheBlk::ReadableBit
                                                     : CacheBlk::WritableBit;
            }
            if (!blk->isSet(bit)) {
                if (write_log) {
                    *(log_stream->stream()) << "Tick: " << curTick()
                        << ", Field: coh, SKIPPED (neither perm bit set)"
                        << std::endl;
                }
                return false;
            }
            blk->clearCoherenceBits(bit);
            stats->numCohFaults++;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            const char *bitName =
                (bit == CacheBlk::WritableBit) ? "Writable" : "Readable";
            if (write_log) {
                *(log_stream->stream()) << "Tick: " << curTick()
                    << ", Cache Block Addr: " << blockAddr
                    << ", Field: coh, Action: cleared " << bitName
                    << " permission" << std::endl;
            }
            return true;
        }
        return false;  // not a metadata field
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

            // §5.8B metadata-field injection (tag/tag_to_legal/valid/
            // dirty/repl/coh): apply the fault to the block's METADATA
            // and skip the legacy byte path entirely. A metadata fault is
            // one fault (not corruption_size bytes).
            if (target_field == "tag" || target_field == "tag_to_legal" ||
                target_field == "valid" || target_field == "dirty" ||
                target_field == "repl" || target_field == "coh") {
                injectMetadataFault(targetBlk, tags, blockAddr);
            } else

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

                // §5.8C L1I semantic-field remap: when targetField is an
                // A64 encoding field, move the selected bit(s) into the
                // field's position within the 32-bit instruction word.
                // The cache stores little-endian bytes; the instruction
                // word is data[off..off+3]. Field positions (in-word):
                //   rd=[4:0], rn=[9:5], rm=[20:16], opcode=[28:23]
                if (target_field != "data") {
                    byteOffset &= ~3;  // 4B-align to the instruction word
                    int fsh, fw;
                    if      (target_field == "rd")     { fsh = 0;  fw = 5; }
                    else if (target_field == "rn")     { fsh = 5;  fw = 5; }
                    else if (target_field == "rm")     { fsh = 16; fw = 5; }
                    else /* opcode */                  { fsh = 23; fw = 6; }
                    unsigned long long inword = 0;
                    for (int k = 0; k < fw; ++k)
                        if (mask & (1u << k)) inword |= (1ULL << (fsh + k));
                    unsigned char fm[4] = {0,0,0,0};
                    fm[0] = inword & 0xff; fm[1] = (inword>>8)&0xff;
                    fm[2] = (inword>>16)&0xff; fm[3] = (inword>>24)&0xff;
                    for (int b = 0; b < 4; ++b)
                        if (fm[b]) data[byteOffset + b] ^= fm[b];
                    stats->numFaultsInjected++;
                    ++faults_injected_count;
                    if (write_log) {
                        *(log_stream->stream())
                            << "Tick: " << curTick()
                            << ", Cache Block Addr: " << blockAddr
                            << ", Field: " << target_field
                            << ", InwordMask: 0x" << std::hex << inword
                            << std::dec << std::endl;
                    }
                    continue;  // field path done; skip the legacy byte path
                }

                // S0-3: save the pre-corruption byte so applyProtectionModel
                // can REVERT it when ECC corrects (1-bit).
                uint8_t origByte = data[byteOffset];

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

                // S0-3: apply the ECC model AFTER the mask. This may REVERT
                // the byte (ECC corrected) or leave it dirty (escape). The
                // PA marker (EccCorrected/Poisoned:DetectedContained/Latent)
                // is written to the log for classify_run_pa nine-class split.
                applyProtectionModel(&data[byteOffset], origByte, mask,
                                     byteOffset, blockAddr);

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

                // §7.7 paired-sector: apply the SAME fault to the 128B-aligned
                // partner block's same byte offset (128B fault-domain proxy).
                if (paired_sector && partnerBlk) {
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
