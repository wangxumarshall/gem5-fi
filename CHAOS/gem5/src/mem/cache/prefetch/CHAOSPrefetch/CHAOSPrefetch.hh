// CHAOSPrefetch.hh — LSU W8 P-series prefetcher injector (09 §3 W8;
// 03-design-matrix P rows). Hooks the TAIL of Stride::calculatePrefetch
// via the single-consumer registry Stride::chaosPrefetchHook (same pattern
// as BaseCache::chaosVictimHook). One injector per run by grid
// construction (chaos_lsu_trigger.hh single-consumer scope note).
//
// Mode semantics (03 P-rows verbatim; approximations marked):
//   P01StrideBitflip     training-entry stride 1-bit XOR (P01)
//   P02ConfidenceCorrupt confidence clear (reset) / fake-set (saturate),
//                        50/50 per injection (P02; gem5 models confidence
//                        as a SatCounter8 — version/granule sub-fields of
//                        the xlsx row do not exist here, documented)
//   P03AddrSubst         generated address -> another legal aligned line
//                        in the SAME 4KiB page (P03 negative control: an
//                        SDC means the injector polluted the fill path)
//   P05DropDup           drop / duplicate one generated prefetch, 50/50
//                        (P05; also the P04 queue-family approximation —
//                        a missing/extra generation IS the observable
//                        queue-content effect)
//   P08StrideStuck       stride stuck-at-0, re-applied on every eligible
//                        event (P08, F5 nature; the tier decides)
//   P06AsDemand          [MDSPEC][R4-5.4] P06-a prefetch-as-demand fill
//                        classification marking (p06_as_demand). NOT a
//                        generation-site mode: maybeCorrupt is INERT here
//                        (P06's event source is the FILL site). The hook
//                        is maybeMarkFillAsDemand, consulted by Cache::
//                        serviceMSHRTargets at the setPrefetched gate —
//                        the site where a fill's demand/prefetch
//                        classification becomes the durable line state.
//                        With the trigger's consent ONE prefetch-owned
//                        fill is classified DEMAND: CacheBlk::Prefetched
//                        is not set, so the line enters the cache exactly
//                        as a demand fill (replacement data hwPrefetched,
//                        wasPrefetched useful/unused accounting, and
//                        hasBeenPrefetched probes all read the demand
//                        value — the classification's downstream
//                        consumers). The packet's own plumbing (HardPFReq
//                        cmd, FromPrefetcher MSHR target, silent target
//                        delete, downstream ReadSharedReq) is untouched:
//                        rewriting the cmd would push an unrequested
//                        response up the CPU side (mshr.cc:320 derives
//                        the target source from it) — a structural crash,
//                        not a legal-value substitution. The REVERSE
//                        direction (demand marked prefetch) and the
//                        permission attributes (P06-b dirty / P06-c
//                        ownership / P06-d allocate) are NOT implemented
//                        (see SPEC_IMPL_LANDED pending list).
//
// HONEST BOUNDARY — NOT in this injector:
//   P06-b/c/d (wrong dirty/ownership/allocate fill permissions): the
//                        fill-permission attributes are coherence-side
//                        state, not a prefetcher marking — deferred.
//   P06-a reverse arm (demand marked prefetch): would need a hook on the
//                        demand path's classification — deferred.
//   P07 (fill way/tag mismatch): cache-side, CHAOSCache tag approximation.
//   P09 (prefetch-caused dirty-eviction writeback loss): cache-side,
//        CHAOSCache dirty/victim approximation.
//
// L0 funnel: this injector is LSU-track-native — the W2 event-normalized
// trigger (ChaOSLsuTrigger) is MANDATORY (no legacy cycle-window path).
// activated (04 L0 read-back): for generation-point corruptions the
// corrupted stride/address enters the very next training/prefetch-queue
// step — an honest near-tautological activation, same class of
// approximation as CHAOSAddrPath's sendFragment hook (documented there).
#ifndef __MEM_CACHE_PREFETCH_CHAOS_CHAOSPREFETCH_HH__
#define __MEM_CACHE_PREFETCH_CHAOS_CHAOSPREFETCH_HH__

#include <map>
#include <random>
#include <string>
#include <utility>
#include <vector>

#include "base/output.hh"
#include "base/types.hh"
#include "cpu/o3/chaos_lsu_trigger.hh"   // LSU W2 event-normalized tiers
#include "mem/cache/prefetch/stride.hh"   // Stride::StrideEntry, AddrPriority
#include "params/CHAOSPrefetch.hh"
#include "sim/sim_object.hh"

namespace gem5
{

class CHAOSPrefetch : public SimObject
{
  public:
    enum class Mode { P01StrideBitflip, P02ConfidenceCorrupt, P03AddrSubst,
                      P05DropDup, P08StrideStuck, P06AsDemand };
    static Mode stringToMode(const std::string &s);

    CHAOSPrefetch(const CHAOSPrefetchParams &p);
    ~CHAOSPrefetch() override;

    void startup() override;   // SELF-ATTACH: Stride::chaosPrefetchHook = this

    // Stride::calculatePrefetch tail hook. entry: the LIVE table entry in
    // BOTH branches (confident hit / miss-just-inserted — stride.cc de-
    // shadows the miss branch so the outer pointer stays live). addresses:
    // the generated prefetch vector (non-empty only on the confident-hit
    // path; AddrPriority is Queued's public std::pair<Addr, int32_t>
    // alias). pf_addr: this demand access's block address.
    void maybeCorrupt(prefetch::Stride::StrideEntry *entry,
                      std::vector<prefetch::Queued::AddrPriority> &addresses,
                      Addr pf_addr);

    // [MDSPEC][R4-5.4] P06-a prefetch-as-demand fill-classification hook.
    // Cache::serviceMSHRTargets calls this (through fillMarkHook below) at
    // the setPrefetched gate, for EVERY prefetch-involving fill (from_pref
    // — including demand-merged ones, which book attempted but are not
    // eligible: a demand target already classifies the fill demand, a mark
    // there would be a void value, not a legal substitution). With the
    // trigger's consent ONE eligible prefetch-owned fill is classified
    // DEMAND — the caller then SKIPS blk->setPrefetched(). Params mirror
    // the gate's own inputs: line = mshr->blkAddr; blk_size = the host
    // cache's block size; demand_merged = the gate's from_core; blk_valid
    // = (blk != nullptr). Returns true iff this fill was marked (the
    // caller must then treat the fill as demand-classified).
    bool maybeMarkFillAsDemand(Addr line, unsigned blk_size,
                               bool demand_merged, bool blk_valid);

    // Single-consumer registry (CHAOSCache chaosVictimHook/chaosMergeHook
    // precedent): set only by a P06-mode injector (one per run by grid
    // construction), consulted by Cache::serviceMSHRTargets. Null for
    // every other run — the gate is then byte-identical to the original.
    // Single-target by construction: only the cache that OWNS the mounted
    // prefetcher allocates FromPrefetcher MSHR targets (HardPFReq packets
    // originate from Queued::DeferredPacket::createPkt and never leave
    // the owning cache — createMissPacket rewrites them to ReadSharedReq/
    // ReadCleanReq downstream, cache.cc:1305 comment), so prefetch-owned
    // fills occur only at that cache (the L2 in the B0 profile; the S4
    // variant moves the single prefetcher to the L1D and the hook follows
    // it — still one cache).
    static CHAOSPrefetch *fillMarkHook;

  private:
    static ChaOSLsuTier tierFromString(const std::string &s);
    static ChaOSLsuEvent eventFromString(const std::string &s);

    Mode fi_mode;
    ChaOSLsuTrigger trigger;      // W2 event-normalized (mandatory here)
    uint64_t max_faults;
    uint64_t faults_injected = 0;
    uint64_t rng_seed;
    Addr line_size;
    bool write_log;

    // F6 fires at the first configured event; the corruption happens at
    // the next eligible hook call (event sites and this hook are different
    // code points — same f6_pending pattern as CHAOSAddrPath).
    bool f6_pending = false;
    static CHAOSPrefetch *f6Consumer;
    static void f6Thunk(ChaOSLsuEvent ev);

    // [MDSPEC][H5] training-entry PC → (ptag, pf_request_id) of its active
    // fault chain. Needed because the hook sits at calculatePrefetch's TAIL:
    // a stride-affecting fault changes what the NEXT call for the same PC
    // generates, so those later candidates must join the already-open
    // request chain (see maybeCorrupt).
    std::map<Addr, std::pair<uint64_t, uint64_t>> corrupted_entries;

    std::mt19937_64 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    void logInjection(const char *site, Addr a, const std::string &detail);
};

} // namespace gem5

#endif // __MEM_CACHE_PREFETCH_CHAOS_CHAOSPREFETCH_HH__
