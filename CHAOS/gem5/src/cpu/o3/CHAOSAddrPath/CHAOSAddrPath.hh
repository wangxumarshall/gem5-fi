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
#include "cpu/o3/CHAOSAddrPath/a01_coords.hh"  // [LSU][V3.2.12][A01] golden/actual EA records
#include "cpu/o3/CHAOSAddrPath/a03_stream.hh"  // [LSU][V3.2.12][A03] F5 eligibility stream
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

    // LSU W4 PRE hook (W1 ⑦ ruling): called at LSQ::pushRequest entry —
    // the AGU's raw output, BEFORE split decision / Request construction.
    // Mutates the by-value addr/size copies so every downstream consumer
    // (split, Request, translation) sees the fault. Returns the (possibly
    // substituted) access size; the call site rebuilds byte_enable when it
    // changed (A06). pre_mode selects the
    // A-series family: a04_subst (same-4KiB-page legal substitution —
    // "same object" needs the W9 oracle table, documented proxy), a05_shift
    // (shift-amount submodel: low-byte rotate; the base/index/extend-swap
    // submodels are NOT expressible from the final addr — deferred, R5),
    // a06_size (access-size substitution; byte_enable is const at this
    // hook — size only), a08_subst (same-page, no object constraint).
    // [LSU][V3.2.12][A01] pc (defaulted, 0 = not observable at the call
    // site yet): the faulting PC for the staged a01_ea record; the lsq.cc
    // call site passes inst->pcState().instAddr() (one-line shared-side
    // patch, task-7-report.md §4B) — until then it stays kPcUnknown.
    unsigned int maybeCorruptPre(Addr& addr, unsigned int size, bool isLoad,
                               Request::Flags& flags, uint64_t dyn_seq = 0,
                               uint64_t pc = 0);

    // [LSU][OBS-L3] true iff the PREVIOUS maybeCorruptPre call on this
    // injector performed an injection. The lsq.cc pushRequest call site
    // needs this to register the injection with CHAOSPropagation: the
    // flag-only PRE modes (S06 STRICT_ORDER / L02 STRICTLY_ORDERED) leave
    // addr/size untouched, so a before/after compare at the call site
    // cannot see them.
    bool lastPreHookInjected() const { return obs_pre_hook_injected; }

    // [LSU][V3.2.12][A01] staged golden/actual EA record (a01_ea, plan
    // Task 7): computed at EA formation by the A01 injection branches
    // (pre_mode a01_bit3_load at the pushRequest PRE hook; Mode::A01Bit at
    // the sendFragmentToTranslation post hook). READ-ONLY trace evidence —
    // no data-path change, no fault-semantics change. CHAOSPropagation
    // stays the SINGLE prop-trace writer: the sink-side emitter reads the
    // staged record through these accessors at the lsq.cc call sites and
    // writes the trace node (see task-7-report.md for the contract). The
    // durable in-process copy at formation time is the A01_EA line in the
    // existing addrpath_injections.log (same stream, same writer).
    bool a01EAStaged() const { return a01_ea_staged; }
    const chaos_a01::EACoords &stagedA01EA() const { return staged_a01_ea; }
    void clearStagedA01EA() { a01_ea_staged = false; }

    // [LSU][V3.2.12][A03] staged F5 eligibility-stream record (a03_stream,
    // plan Task 8): one record per trigger-fired eligible load after
    // activation, staged at the a03 application branch for the sink side.
    // READ-ONLY trace evidence — no data-path change, no fault-semantics
    // change; CHAOSPropagation stays the SINGLE prop-trace writer (the
    // a01_ea contract, task-7-report.md). The sink-side emitter reads the
    // latest record through these accessors at the lsq.cc call sites and
    // may clear the flag after emitting. Durable in-process copies: the
    // A03_ACTIVATION / A03_STREAM lines in the existing
    // addrpath_injections.log (same stream, same writer).
    bool a03StreamStaged() const { return a03_stream_staged; }
    const chaos_a03::StreamEvent &stagedA03Stream() const
        { return staged_a03_stream; }
    void clearStagedA03Stream() { a03_stream_staged = false; }
    bool a03Activated() const { return a03_stream_rec.activated(); }
    const chaos_a03::Activation &a03ActivationRecord() const
        { return a03_stream_rec.activation(); }

    // [A01 v3.3 proposal] matched no-fault control: register the
    // ordinal-selected load's golden EA read-only (no addr mutation, no
    // injection) so the propagation tracer can emit mem_req/resp/DataDelta.
    void probeA01Control(Addr addr, unsigned size, bool isLoad,
                         uint64_t dyn_seq, uint64_t pc);

  private:
    // LSU W4 A-series (03-design-matrix A01-A03, bit-level family on the
    // sendFragmentToTranslation hook = DTLB-input semantics, W1 ⑦ ruling):
    //   A01Bit     single-bit flip, low/mid/high band sampling (A01)
    //   A02Double  two-bit flip, 50% adjacent / 50% non-adjacent (A02)
    //   A03Stuck0/1 one EA bit stuck-at, applied on every event (A03, F5)
    enum class Mode { Byte7Zero, LowBitFlip, A01Bit, A02DoubleBit,
                      A03Stuck0, A03Stuck1 };
    static Mode stringToMode(const std::string &s);
    // [LSU][V3.2.12][A01] the mode's true config name for the injection-log
    // line — the legacy ternary printed "low_bit_flip" for every non-byte7
    // mode, mislabeling the A-series post-hook injections in the very log the
    // A01/A03 evidence reads (byte7_zero/low_bit_flip stay byte-identical).
    static const char *modeName(Mode m);
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
    uint64_t f5_bit = 64;   // pinned bit index (F5 low-bit / A03 stuck), 64 = not yet chosen

    // [LSU][OBS-L3] resolved O3 CPU (cached at startup, dynamic_cast once —
    // the inWindow() per-call dynamic_cast is the cost counter-precedent);
    // nullptr = not O3. Used by the injection-time funnel notify below.
    o3::CPU *o3cpu_resolved = nullptr;
    // [LSU][OBS-L3] last PRE-hook injection verdict (see lastPreHookInjected).
    bool obs_pre_hook_injected = false;
    // [LSU][OBS-L3] funnel notify at injection time AND at exit (final
    // counts): one prop-trace funnel node (abort-survivable — per-node
    // gzflush) + one best-effort FUNNEL line in the injection log (the
    // log is a simout stream and is LOST on abort; the prop-trace node is
    // the durable copy). Central requirement: abort samples must carry
    // attempted/eligible.
    void notifyFunnelAtInjection();

    // [LSU][OBS-2] post-trigger decline counters (F-049 D-class diagnosis):
    // count trigger-fired-but-no-fault-write outcomes per reason. Observation
    // only — every increment sits on a path that already returned without
    // writing, so injection semantics are unchanged.
    uint64_t obs_pre_fired = 0;      // PRE hook: trigger said "inject now"
    uint64_t obs_pre_opclass = 0;    // PRE: op-class filter declined (phantom)
    uint64_t obs_pre_invalid = 0;    // PRE: invalid target / unknown pre_mode
    uint64_t obs_pre_nochange = 0;   // PRE: condition applied, value already stuck (A03)
    uint64_t obs_post_fired = 0;     // POST hook: trigger said "inject now"
    uint64_t obs_post_nochange = 0;  // POST: corruption produced identical vaddr

    // [LSU][V3.2.12][A01] staged a01_ea record (see the public accessor
    // block above). Overwritten per A01 injection; the sink-side emitter
    // (CHAOSPropagation — the single prop-trace writer) reads it at the
    // lsq.cc call sites and may clear the flag after emitting.
    chaos_a01::EACoords staged_a01_ea;
    bool a01_ea_staged = false;
    void stageA01EA(const chaos_a01::EACoords &c);

    // [LSU][V3.2.12][A03] F5 eligibility-stream state (plan Task 8): the
    // recorder owns the exactly-once discipline (one activation per run,
    // one record per fired eligible load, strictly advancing ordinals —
    // rejections counted, never silent); the staged record + flag feed the
    // sink-side emitter (the a01_ea pattern). Observation only — no
    // fault-semantics change, no data-path change.
    chaos_a03::StreamRecorder a03_stream_rec;
    chaos_a03::StreamEvent staged_a03_stream;
    bool a03_stream_staged = false;
    void a03NoteEligibleLoad(uint64_t dyn_seq, Addr golden_ea,
                             Addr actual_ea, int bit);
    void writeA03LogLine(const char *tag, const std::string &detail);

    // W3 L0: funnel (attempted/eligible/injected mirrored from the trigger;
    // activated = the read-back verdict — for THIS hook the corrupted vaddr
    // is consumed by the very next pipeline step (translateTiming consumes
    // the request we just corrupted), so activated counts the request as
    // consumed unless squashed — an honest near-tautological approximation
    // documented per-injector; hooks with real slack (W4 pushRequest) need
    // a genuine read-back judgement).
    ChaOSL0Funnel l0_funnel;
    ChaOSL0State l0_item;
    std::string pre_mode = "off";   // off | a04_subst | a05_shift | a06_size | a08_subst | s13_store_addr | l01_load_addr
    uint64_t agu_size_to = 0;       // a06_size: target size {1,2,4,8,16}
    static CHAOSAddrPath *f6Consumer;
    static void f6Thunk(ChaOSLsuEvent ev);

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_ADDR_PATH_HH__
