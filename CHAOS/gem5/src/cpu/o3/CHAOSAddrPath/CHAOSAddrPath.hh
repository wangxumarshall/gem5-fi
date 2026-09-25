#ifndef __CPU_O3_CHAOS_ADDR_PATH_HH__
#define __CPU_O3_CHAOS_ADDR_PATH_HH__

#include <random>
#include <string>

#include "params/CHAOSAddrPath.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/o3/chaos_l0.hh"           // LSU W3 L0 funnel + item lifecycle
#include "cpu/o3/chaos_lsu_trigger.hh"  // LSU W2 event-normalized tiers
#include "mem/request.hh"

namespace gem5 { namespace o3 { class CPU; } }

namespace gem5
{

class CHAOSAddrPath : public SimObject
{
  public:
    CHAOSAddrPath(const CHAOSAddrPathParams &p);
    ~CHAOSAddrPath();

    void startup() override;  // self-attach to CPU.chaosAddrPath

    // Called from LSQ::LSQRequest::sendFragmentToTranslation BEFORE
    // translateTiming. Corrupts the request vaddr (byte7 zero / low-bit flip).
    // HONEST: SE-inert (SE phys mem from 0; byte7 zero still in range).
    bool maybeCorrupt(RequestPtr &req);

  private:
    enum class Mode { Byte7Zero, LowBitFlip };
    static Mode stringToMode(const std::string &s);
    static ChaOSLsuTier tierFromString(const std::string &s);
    static ChaOSLsuEvent eventFromString(const std::string &s);

    BaseCPU *cpu;
    Mode fi_mode;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;

    // LSU W2 (05 r2-r8): when lsuTier != off, the injection decision routes
    // through the event-normalized trigger (warm-up/repetition semantics move
    // to the trigger layer; the legacy cycle-window path stays byte-identical
    // for the KP track). f6_pending: F6 fires at the first configured event,
    // the corruption itself happens at the next eligible hook call (the
    // event sites and this injector's hook are different code points —
    // per-unit F6 consumers in W5-W8 inject AT the event instead).
    ChaOSLsuTrigger *lsuTrigger = nullptr;
    bool f6_pending = false;
    uint64_t f5_bit = 64;   // F5: pinned low-bit index, 64 = not yet chosen

    // W3 L0: funnel (attempted/eligible/injected mirrored from the trigger;
    // activated = the read-back verdict — for THIS hook the corrupted vaddr
    // is consumed by the very next pipeline step (translateTiming consumes
    // the request we just corrupted), so activated counts the request as
    // consumed unless squashed — an honest near-tautological approximation
    // documented per-injector; hooks with real slack (W4 pushRequest) need
    // a genuine read-back judgement).
    ChaOSL0Funnel l0_funnel;
    ChaOSL0State l0_item;
    static CHAOSAddrPath *f6Consumer;
    static void f6Thunk(ChaOSLsuEvent ev);

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_ADDR_PATH_HH__
