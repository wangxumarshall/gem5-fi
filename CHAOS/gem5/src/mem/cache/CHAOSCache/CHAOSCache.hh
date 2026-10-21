#ifndef __MEM_CACHE_CHAOSCACHE_CHAOSCACHE_HH__
#define __MEM_CACHE_CHAOSCACHE_CHAOSCACHE_HH__

#include <random>

#include "mem/cache/cache.hh"
#include "cpu/o3/chaos_l0.hh"           // LSU W3 L0
#include "cpu/o3/chaos_lsu_trigger.hh"  // LSU W2 trigger
#include "params/CHAOSCache.hh"
#include "sim/sim_object.hh"

#include "mem/cache/cache.hh"
#include "cpu/o3/chaos_l0.hh"           // LSU W3 L0
#include "cpu/o3/chaos_lsu_trigger.hh"  // LSU W2 trigger
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

    /** v1.2 Phase 14 (plan item 2): victim/writeback-path fault. Called by
     *  BaseCache::writebackBlk AFTER the packet data is set — XORs a byte
     * of the IN-FLIGHT writeback payload (the cache array stays clean).
     *  Returns true if corrupted. Nullptr-safe. */
    bool maybeCorruptVictim(PacketPtr pkt);

    /** [MDSPEC][R4-5.1] C11 MSHR merge corruption. Called by
     *  BaseCache::handleTimingReqMiss in the coalescing branch, BEFORE
     *  mshr->allocateTarget: with the trigger's consent (LSU-track
     *  ChaOSLsuTrigger, event-normalized on the merge-event stream) flip
     *  ONE bit of the MERGING TARGET's address. The flip is confined to
     *  the block-offset domain at/above log2(pkt size) — the target stays
     *  same-line (the merge remains legal) and alignment/bounds-safe.
     *  Only fires when `cache == targetCache` (the mounted L1D), the mode
     *  is targetField=="mshr_merge", and maxFaults is not exhausted.
     *  Registers the fault with CHAOSPropagation (inj node + the corrupted
     *  target range in the faulted-byte registry, so the later response on
     *  the corrupted address joins the chain). Returns true if corrupted. */
    bool maybeCorruptMergeTarget(BaseCache *cache, PacketPtr pkt);

    /** [MDSPEC][R4-5.2] C12 fill-timing offset. Called by
     *  BaseCache::recvTimingResp at the TOP, BEFORE popSenderState: with
     *  the trigger's consent (LSU-track ChaOSLsuTrigger, event-normalized
     *  on the fill-response stream), DEFER the fill response to a later
     *  tick — the packet is stashed (MSHR sender state intact, so the
     *  MSHR stays outstanding and later same-line requests keep merging)
     *  and a resume event at curTick() + lsuFillDelayCycles cache cycles
     *  re-enters recvTimingResp via BaseCache::chaosResumeDeferredResp.
     *  The whole fill path then runs at the shifted tick: the consumer
     *  gets the same data at a shifted time. Only fires when
     *  `cache == targetCache` (the mounted L1D), the mode is
     *  targetField=="mshr_fill_timing", and maxFaults is not exhausted.
     *  Registers the fault with CHAOSPropagation (inj node + the whole
     *  fill line in the faulted-byte registry, so the DELAYED
     *  mshr_fill/cache_fill/mshr_free events and the response delivery
     *  join the chain). Returns true if deferred (caller must NOT
     *  process the packet). */
    bool maybeDeferFillTiming(BaseCache *cache, PacketPtr pkt);

    /** [MDSPEC][R4-5.5] C14 MSHR busy/occupied stuck-at-1 (resource leak,
     *  sub-model C14-a). Called by BaseCache::recvTimingResp IMMEDIATELY
     *  BEFORE mshrQueue.deallocate(mshr) — the MSHR release point (the
     *  spec's "目标MSHR首次完成并应释放" event). With the trigger's
     *  consent the deallocation is SKIPPED: the entry stays in the MSHR
     *  queue's allocated list and never returns to the free list, i.e.
     *  its busy/occupied state is stuck-at-1. The corresponding miss DID
     *  complete normally (serviceMSHRTargets already delivered the fill
     *  before we get here) — only the slot is lost. Once the leaked slot
     *  is the last free-demand entry the queue reports full and BaseCache
     *  keeps the CPU side blocked (capacity degradation; the spec's
     *  "容量退化和Timeout"). Only fires when `cache == targetCache` (the
     *  mounted L1D), the mode is targetField=="mshr_busy_leak", no leak is
     *  already pending (single slot — the 03 sheet's "每次运行只固定一个
     *  表项"), and maxFaults is not exhausted. Returns true if the caller
     *  must SKIP the deallocation (and its clearBlocked bookkeeping).
     *
     *  `line`   = the fill's block address (the leaked entry's line).
     *  `in_service` = mshrQueue.numInService() read BEFORE the release
     *                 (a public proxy for the private allocated counter).
     *  `was_full`   = mshrQueue.isFull() read before the release. */
    bool maybeStickMshrBusy(BaseCache *cache, MSHR *mshr, Addr line,
                            uint64_t in_service, bool was_full);

    /** [MDSPEC][R4-5.6] C15-b MSHR capacity-arbitration "fake free"
     *  (sub-model C15-b: "在容量已满时伪造空位"). Called by
     *  BaseCache::chaosMshrOccArbitrate, which itself is called from the
     *  TAIL of BaseCache::allocateMissBuffer — i.e. right after a new miss
     *  allocation ran the queue's capacity arbitration. When the queue is
     *  FULL (`isFull()` true after the allocation — the 03 sheet's "MSHR
     *  接近或达到容量上限时发生新 miss 分配"; the private `allocated`
     *  counter is unreachable, so isFull() IS the only public capacity
     *  predicate, honest approximation) and the trigger consents, the
     *  injector fabricates a free slot: the caller CLEARS the
     *  Blocked_NoMSHRs block, so the CPU side retries and exactly ONE
     *  further miss allocation consumes a reserve entry BEYOND the
     *  arbitration's capacity — the arbitration's allow/deny decision is
     *  genuinely wrong (the 03 sheet's "仅在仲裁结果真正允许…一次 miss
     *  分配时计为 activated"). Returns true if the caller must clear the
     *  block. Only fires when `cache == targetCache` (the mounted L1D),
     *  the mode is targetField=="mshr_occupancy", no fabricated slot is
     *  already pending (single slot), and maxFaults is not exhausted. */
    bool maybeFakeFreeSlot(BaseCache *cache, PacketPtr pkt, MSHR *mshr,
                           uint64_t in_service);

    /** [MDSPEC][R4-5.6] C15-b materialization read-back. Called (from the
     *  same BaseCache helper) at the TOP of every subsequent
     *  allocateMissBuffer on the mounted cache. A pending fabricated free
     *  slot is CONSUMED here iff this allocation still runs while the
     *  queue is full — that allocation is the over-capacity (reserve) one
     *  the faulty arbitration allowed: the fault is then REGISTERED (inj +
     *  the mshr_arb observation node + the request's line in the
     *  faulted-byte registry) and `activated` is bumped. If the queue
     *  drained in between (isFull() false) the fabricated slot was simply
     *  never used — the pending flag is dropped and nothing is recorded
     *  (an honest Inject-not-activated sample; the fire is still visible
     *  in the injection log and the trigger funnel). Returns true if this
     *  allocation was the over-commit one (the caller must then NOT also
     *  fire a new fault on the same allocation). */
    bool noteMshrAllocAttempt(BaseCache *cache, PacketPtr pkt, MSHR *mshr,
                              bool is_full, uint64_t in_service);

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

    // Directed-injection target (report §六.3 'fixed-to' runs): when
    // non-default, the injector pins the fault to a SPECIFIC cache block
    // (by its address) and/or byte offset, instead of random sampling.
    // Used to land a fault on a live-data byte (L1D) or an executed
    // instruction byte (L1I) — the random sampler mostly misses them.
    // target_block_addr == 0 (MaxAddr sentinel) = random block (orig).
    // target_byte_offset < 0 = random byte (orig).
    Addr target_block_addr;
    int target_byte_offset;
    bool paired_sector;  // §7.7 128B fault-domain proxy (fault both 64B sectors)
    // §2.7/§2.11 field-level fault: data (default) / valid / dirty / coh.
    std::string target_field;
    std::string l1i_semantic_field;

    // §1.2 protection-aware modeling layer (N1 TRM Table 9-1 PROXY).
    // Post-injection, applyProtection() decides the observable outcome keyed
    // on popcount(mask): Corrected (undo), DetectedContained (invalidate),
    // Latent (poison-log, classic cache has no poison bit), SilentEscape
    // (leave, >=3-bit / sed >=2-bit), Raw (none default = leave). Default
    // "none" = zero regression vs prior behavior.
    std::string protection_model;
    enum class ProtectionOutcome { Raw, Corrected, DetectedContained, Latent, SilentEscape };
    static ProtectionOutcome stringToProtectionModel(const std::string &s);

    EventFunctionWrapper attackEvent, periodicCheck;
    Tick first_tick, last_tick, ticks_permament_fault_check;
    std::map<std::pair<Addr, int>, PermanentFault> permanent_faults;
    std::geometric_distribution<unsigned> inter_fault_cycles_dist;
    std::discrete_distribution<int> random_fault_distribution;
    
    std::mt19937 rng;
    std::random_device rd;
    uint64_t rng_seed;  // 0 = random_device (orig, non-reproducible); else fixed
    uint64_t max_faults;            // G6: 0 = unlimited; else cap
    uint64_t faults_injected_count; // G5: running count

    // LSU W6/W10: event-normalized trigger + L0 funnel
    ChaOSLsuTrigger *lsuTrigger = nullptr;
    ChaOSL0Funnel l0_funnel;

    // [MDSPEC][R4-5.2] C12 fill-timing offset: the single deferred-fill
    // slot + the scheduled resume event + the configured offset (cache
    // cycles). fillPendingPkt doubles as the re-entry guard: during the
    // resume event the stashed pointer is still set, so the re-entered
    // recvTimingResp->maybeDeferFillTiming sees pkt == fillPendingPkt and
    // processes the packet instead of deferring again (independent of
    // tier/maxFaults). A SECOND deferral while one is pending is
    // structurally refused (single slot — the campaign runs maxFaults=1;
    // an unlimited multi-defer needs a queue, out of scope, honest).
    PacketPtr fillPendingPkt = nullptr;
    EventFunctionWrapper fillResumeEvent;
    uint64_t fill_delay_cycles = 100;
    // C12 resume body (fillResumeEvent thunk): deliver the stashed fill
    // response at the shifted tick via the public BaseCache trampoline.
    void resumeDeferredFill();
    // [MDSPEC][R4-5.5] C14 MSHR busy-stuck leak: the single leaked slot.
    // nullptr until the (one) leak has happened; the slot is never freed
    // by construction, so there is nothing to reset — the pointer doubles
    // as the "one entry per run" guard the 03 sheet mandates.
    MSHR *mshr_busy_victim = nullptr;
    uint64_t mshr_busy_leaks = 0;      // successful leak injections (funnel)
    // [MDSPEC][R4-5.6] C15-b fake-free state. mshr_fake_free_armed = a
    // fabricated free slot has been handed to the caller (the full block
    // was cleared) and is waiting for its over-capacity allocation; the
    // flag doubles as the "one fabricated slot at a time" guard. fires =
    // trigger-consented fabrications (the L0 log + trigger funnel count);
    // over_commit = materializations (the real arbitration read-back —
    // `activated` in the teardown line). mshr_occ_at_fire = the occupancy
    // sampled at the fire (for the observation pair).
    bool mshr_fake_free_armed = false;
    uint64_t mshr_fake_free_fires = 0;
    uint64_t mshr_over_commit = 0;
    uint64_t mshr_occ_at_fire = 0;
    // [LSU][OBS-L3] nullptr default: the ctor only assigns log_stream when
    // probability != 0, and the [OBS-L3] funnel helper reads it on every
    // injection — the default-init makes that read defined (defensive; the
    // write_log uses inside injectFault keep their existing guards).
    OutputStream *log_stream = nullptr;
    // v1.2 Phase 14 (plan item 2): victim/writeback-path fault mode.
    bool victim_fault = false;

    // [LSU][OBS-L3] real funnel counters for the legacy attack path
    // (attempted = attack-event firings, eligible = firings that found
    // >=1 valid block, injected = the existing faults_injected_count) +
    // the funnel-row helper: one prop-trace funnel node (abort-survivable,
    // per-node gzflush) + one best-effort FUNNEL line in the injection log
    // (the log is a simout stream and is LOST on abort; the prop-trace node
    // is the durable copy — central requirement: abort samples must carry
    // attempted/eligible).
    uint64_t attack_attempts = 0;
    uint64_t attack_eligible = 0;
    void noteFunnelAtInjection();
    
    static FaultType stringToFaultType(const std::string &s);
    const char* faultTypeToString(CHAOSCache::FaultType f);
    // [MDSPEC][R4-5.1] C11: parse the lsuTier param string ("off" is
    // rejected loudly — merge mode without a tier has no trigger).
    static ChaOSLsuTier tierFromString(const std::string &s);
    static ProtectionOutcome stringToProtectionModelPub(const std::string &s);
    const char* protectionOutcomeToString(CHAOSCache::ProtectionOutcome o);
    // §1.2 post-injection protection handling. Called right after the byte
    // mutation (data[byteOffset] ^= mask etc.). `blk` is the faulted block
    // (for invalidate on sed/secded 2-bit); `byteOffset`+`mask` define the
    // injection (popcount(mask) = bits flipped). `orig_byte` is the pre-fault
    // byte (for undo = Corrected). Returns the outcome; logs to fault log.
    ProtectionOutcome applyProtection(CacheBlk *blk, int byteOffset,
                                      uint8_t mask, uint8_t orig_byte,
                                      FaultType ft, bool is_paired = false);
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
      
      CHAOSCacheStats(statistics::Group *parent);
    };

    std::unique_ptr<CHAOSCacheStats> stats;
};

} // namespace gem5

#endif // __MEM_CACHE_CHAOSCACHE_CHAOSCACHE_HH__