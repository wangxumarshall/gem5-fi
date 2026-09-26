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
//
// HONEST BOUNDARY — NOT in this injector:
//   P06 (prefetch marked demand / wrong permissions): no clean hook, deferred.
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

#include <random>
#include <string>
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
                      P05DropDup, P08StrideStuck };
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

    std::mt19937_64 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    void logInjection(const char *site, Addr a, const std::string &detail);
};

} // namespace gem5

#endif // __MEM_CACHE_PREFETCH_CHAOS_CHAOSPREFETCH_HH__
