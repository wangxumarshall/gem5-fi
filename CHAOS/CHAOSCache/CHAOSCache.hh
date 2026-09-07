#ifndef __MEM_CACHE_CHAOSCACHE_CHAOSCACHE_HH__
#define __MEM_CACHE_CHAOSCACHE_CHAOSCACHE_HH__

#include <random>

#include "mem/cache/cache.hh"
#include "params/CHAOSCache.hh"
#include "sim/sim_object.hh"

#include "mem/cache/cache.hh"
#include "params/CHAOSCache.hh"
#include <bitset>
#include <string>
#include <iostream>
#include <random>
#include <stdexcept>
#include "base/output.hh"
#include <map>

namespace gem5
{

class CHAOSCache : public SimObject
{
  public:
    CHAOSCache(const CHAOSCacheParams& params);
    virtual ~CHAOSCache() {}

    // §5.8B tag-array fault, FALSE-HIT formulation (v2, learned from the
    // first verification round): directly rewriting the stored tag via
    // setTag made the block evict under an address the snoop filter never
    // tracked (WritebackDirty/CleanEvict of an untracked line panics in
    // snoop_filter.cc:144 — a SimulatorError, not a valid DUE outcome).
    // The FAULT MODEL the plan §2.3 actually specifies is "tag >=3-bit:
    // silent false-hit": a lookup for address A is answered by the block
    // of ANOTHER address B of the same set. We therefore model the fault
    // AT LOOKUP TIME: the injector registers a false-hit alias (victim
    // way -> alias way, one set), and BaseTags::findBlock() diverts a
    // lookup that matched the victim block to the alias block instead.
    // The tag STORE stays untouched, so evictions/writebacks remain
    // protocol-consistent (the line evicts under its REAL address); only
    // the data SUPPLY is wrong — exactly the SDC-relevant semantics.
    //
    // Called from BaseTags::findBlock() when a lookup matched a block.
    // blk is the block that matched; entries are the set's possible
    // entries (for locating the alias way). Returns the block to SERVE
    // instead (the alias block), or nullptr to keep the original match.
    // Hot path: no alias registered -> nullptr (one predictable branch).
    CacheBlk* chaosDivertFindBlock(CacheBlk *blk,
        const std::vector<ReplaceableEntry*> &entries,
        const CacheBlk::KeyType &key) const;

  private:
    // False-hit alias state: {set, victim way, alias way}. A single alias
    // is registered per injection (single-fault discipline, G5). The
    // victim is the block whose tag is considered corrupted; the alias is
    // the block whose DATA gets served to lookups that match the victim.
    unsigned tag_alias_set = 0;
    unsigned victim_way = 0;
    unsigned alias_way = 0;
    bool tag_alias_valid = false;

  private:
    enum class FaultType {
      BitFlip,
      StuckAtZero,
      StuckAtOne,
      Random
    };

    struct PermanentFault {
      FaultType fault_type;
      uint64_t mask;
      bool update;
    };

    Cache* targetCache;
    double probability;
    int bits_to_change;
    int corruption_size;
    uint64_t first_clock, last_clock;
    FaultType fault_type_enum;
    unsigned char fault_mask;
    int tick_to_clock_ratio;
    float bit_flip_prob, stuck_at_zero_prob, stuck_at_one_prob;
    int cycles_permament_fault_check;
    bool write_log;

    // S0-3: protection-aware ECC model (plan §4.2, §2.3 N1 TRM Table 9-1
    // proxy). none = raw (escape); sed/secded/secded_poison/parity_interleaved
    // = model the ECC outcome post-injection and report a PA marker
    // (EccCorrected/Poisoned/Latent) for classify_run_pa nine-class split.
    enum class ProtectionModel { None, SED, SECDED, SECDEDPoison, ParityInterleaved };
    static ProtectionModel stringToProtectionModel(const std::string &s);
    const char *protectionModelToString(ProtectionModel m);
    ProtectionModel protection_model;
    // Apply the ECC model post-injection: may REVERT the corruption (ECC
    // corrected) or leave it (escaped). Reports the outcome label + bumps the
    // matching stat. Returns true if the corruption survived (data left dirty).
    bool applyProtectionModel(uint8_t *byte, uint8_t orig, uint8_t mask,
                              int byteOffset, Addr blockAddr);

    // Directed-injection target (report §六.3 'fixed-to' runs): when
    // non-default, the injector pins the fault to a SPECIFIC cache block
    // (by its address) and/or byte offset, instead of random sampling.
    // Used to land a fault on a live-data byte (L1D) or an executed
    // instruction byte (L1I) — the random sampler mostly misses them.
    // target_block_addr == 0 (MaxAddr sentinel) = random block (orig).
    // target_byte_offset < 0 = random byte (orig).
    Addr target_block_addr;
    int target_byte_offset;
    bool paired_sector;
    // §5.8C: data(legacy)/rd/rn/rm/opcode (L1I semantic fields);
    // §5.8B: tag/tag_to_legal/valid/dirty/repl/coh (metadata fields).
    // §7.7 128B fault-domain proxy (fault both 64B sectors)
    std::string target_field;

    // §5.8B metadata-field injection: apply the fault to the target
    // block's METADATA (tag/valid/dirty/repl/coh) instead of its data
    // bytes. Returns true if a metadata fault was applied (the caller
    // then skips the legacy byte path entirely).
    bool injectMetadataFault(CacheBlk *blk, BaseTags *tags, Addr blockAddr);
    // §5.8B tag false-hit: pick the WAY of another VALID block in the
    // SAME set as blk (the alias whose data gets served). Returns the
    // way index, or -1 if no other valid block exists in the set.
    int pickSameSetAliasWay(CacheBlk *blk);

    EventFunctionWrapper attackEvent, periodicCheck;
    Tick first_tick, last_tick, ticks_permament_fault_check;
    std::map<std::pair<Addr, int>, PermanentFault> permanent_faults;
    std::geometric_distribution<unsigned> inter_fault_cycles_dist;
    std::discrete_distribution<int> random_fault_distribution;
    
    std::mt19937 rng;
    std::random_device rd;
    uint64_t rng_seed;  // 0 = random_device (orig, non-reproducible); else fixed
    uint64_t max_faults;            // G5: 0 = unlimited; else cap
    uint64_t faults_injected_count; // G5: running count
    OutputStream *log_stream;
    
    static FaultType stringToFaultType(const std::string &s);
    const char* faultTypeToString(CHAOSCache::FaultType f);
    void scheduleAttack(Tick tick);
    void scheduleCheckPermanentFault(Tick time);
    BaseTags* getTags() const;
    uint8_t generateRandomMask(std::mt19937 &rng, int bits_to_change, unsigned size);
    void injectFault();
    void checkPermanent();

    struct CHAOSCacheStats : public statistics::Group
    {
      statistics::Scalar numFaultsInjected;
      statistics::Scalar numBitFlips;
      statistics::Scalar numStuckAtZero;
      statistics::Scalar numStuckAtOne;
      statistics::Scalar numPermanentFaults;
      // S0-3: protection-aware ECC outcome stats (plan §6.5).
      statistics::Scalar numEccCorrected;          // 1-bit, ECC corrected (reverted)
      statistics::Scalar numDetectedContained;    // 2-bit, ECC detected+contained (poison)
      statistics::Scalar numLatent;                // >=3-bit, beyond SECDED (escaped)
      statistics::Scalar numRawEscaped;            // protectionModel=none, raw escape
      // §5.8B metadata-field stats (per-field counters; a metadata fault
      // is counted BOTH in numFaultsInjected and its per-field counter).
      statistics::Scalar numTagFaults;             // tag bit_flip (false-hit)
      statistics::Scalar numTagToLegalFaults;      // tag F5 same-set substitution
      statistics::Scalar numValidFaults;           // valid-bit clear (refetch)
      statistics::Scalar numDirtyFaults;           // dirty-bit flip (silent loss)
      statistics::Scalar numReplFaults;            // replacement-data poisoning
      statistics::Scalar numCohFaults;             // coherence permission flip

      CHAOSCacheStats(statistics::Group *parent);
    };

    std::unique_ptr<CHAOSCacheStats> stats;
};

} // namespace gem5

#endif // __MEM_CACHE_CHAOSCACHE_CHAOSCACHE_HH__