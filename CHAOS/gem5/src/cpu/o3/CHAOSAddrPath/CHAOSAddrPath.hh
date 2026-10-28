#ifndef __CPU_O3_CHAOS_ADDR_PATH_HH__
#define __CPU_O3_CHAOS_ADDR_PATH_HH__

#include <random>
#include <string>
#include <vector>

#include "params/CHAOSAddrPath.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/o3/chaos_l0.hh"           // LSU W3 L0 funnel + item lifecycle
#include "cpu/o3/chaos_lsu_trigger.hh"  // LSU W2 event-normalized tiers
#include "cpu/o3/dyn_inst_ptr.hh"       // [MDSPEC][R4-5.8] DynInstPtr (A07 ready hook)
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
    // a06_size (access-size substitution, plus the A06-b byte-enable mask
    // fault below), a08_subst (same-page, no object constraint).
    //
    // [MDSPEC][R4-6-A06] byte_enable is now an IN/OUT parameter (the
    // caller passes a mutable copy; lsq.cc builds LSQRequest::_byteEnable
    // from it). A06-b ("byte-enable 改为另一合法掩码") substitutes it in
    // place; every other mode leaves it untouched.
    unsigned int maybeCorruptPre(Addr& addr, unsigned int size, bool isLoad,
                               Request::Flags& flags, uint64_t dyn_inst_seq,
                               std::vector<bool>& byte_enable,
                               const o3::DynInstPtr &inst = nullptr);

    // [LSU][OBS-L3] true iff the PREVIOUS maybeCorruptPre call on this
    // injector performed an injection. The lsq.cc pushRequest call site
    // needs this to register the injection with CHAOSPropagation: the
    // flag-only PRE modes (S06 STRICT_ORDER / L02 STRICTLY_ORDERED) leave
    // addr/size untouched, so a before/after compare at the call site
    // cannot see them.
    bool lastPreHookInjected() const { return obs_pre_hook_injected; }

    // [MDSPEC][R4-5.8] A07 AGU clean-ready / handshake hook (03 sheet A07:
    // "AGU 结果的 address-ready 握手信号与 EA 流水锁存器"). Called from
    // IEW::executeInsts' isMemRef branch — THE ready/handshake point of
    // this microarchitecture: the scheduler (IQ) has just handed a READY
    // memory instruction to the LSQ to calculate its address (the AGU =
    // initiateAcc inside executeLoad/executeStore); the DPRINTF right
    // above the call site literally reads "Calculating address for memory
    // reference". This is the single per-memory-instruction point where a
    // real AGU's address-ready signal would fire, BEFORE the EA exists
    // (the AGU runs inside initiateAcc) — which is exactly why no earlier
    // hook (pushRequest PRE = the AGU's raw OUTPUT, sendFragment POST =
    // the DTLB input) could express a ready-timing fault.
    //
    // Landed sub-model = A07-b (ready delayed, bounded): with the
    // trigger's consent the ready handshake for ONE plain load/store is
    // delayed by agu_ready_delay_cycles CPU clock edges — the instruction
    // is NOT executed this cycle; this injector's aguResumeEvent re-enters
    // the execute path (IEW::chaosAguResumeInst) at the delayed tick, so
    // the AGU output, the LSQRequest and every downstream event carry the
    // SAME (correct) values, only shifted in time (spec 03: "不改变值
    // 本身…数据载荷保持正确"). Attempt stream = every memRef reaching the
    // ready point; eligibility = plain load/store (atomics are the O-family
    // RMW territory, prefetches the P-family's; op-class filter BEFORE the
    // trigger decision, F-049 discipline). F6 fires at the FIRST eligible
    // ready event (onF6Event(false) — the ready hook already booked this
    // invocation's attempt; the EIGHTH F6 event source, registered in
    // chaos_lsu_trigger.hh).
    //
    // A07-a (ready early + stale latched EA — the SDC-capable sub-model;
    // needs the EA-latch value at pushRequest + a value substitution, a
    // two-point implementation) and A07-c (ready lost — hang/Timeout
    // channel, needs timeout bookkeeping, L04-a same class) are NOT
    // landed; see tools/lsu_runid_map.py SPEC_IMPL_LANDED pending list.
    bool maybeDelayAguReady(const o3::DynInstPtr &inst);

  private:
    // [MDSPEC][R4-5.8] A07-b resume thunk (aguResumeEvent, fires at the
    // delayed tick = cpu clockEdge(delay)). Single slot (C12 single-slot
    // discipline): a second fire while one resume is pending is
    // structurally refused at the hook (obs_agu_slotbusy). agu_fault_seq
    // drives the EA late binding in maybeCorruptPre: at the DELAYED
    // instruction's pushRequest entry (the AGU raw output — the first
    // point the EA exists) the fault chain is bound to the real address
    // range [addr, addr+size), so the very same request's lsq_push /
    // mem_req / tlb_translate join by seq+overlap (seq_primary) and the
    // downstream chain carries REAL va values.
    void resumeDeferredAgu();

    // LSU W4 A-series (03-design-matrix A01-A03, bit-level family on the
    // sendFragmentToTranslation hook = DTLB-input semantics, W1 ⑦ ruling):
    //   A01Bit     single-bit flip, low/mid/high band sampling (A01)
    //   A02Double  two-bit flip, 50% adjacent / 50% non-adjacent (A02)
    //   A03Stuck0/1 one EA bit stuck-at, applied on every event (A03, F5)
    enum class Mode { Byte7Zero, LowBitFlip, A01Bit, A02DoubleBit,
                      A03Stuck0, A03Stuck1 };
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
    // [LSU][P4-F6] dual-track F6 (2026-10-15): early_stress (default, legacy
    // first-occurrence) vs steady_state (golden-profiling warm-up + a
    // pre-drawn random target occurrence within the span; event stream
    // ending before target = no injection, honest inj=0).
    bool f6_steady_state = false;
    uint64_t f6_events_matched = 0;      // steady_state: matching events seen
    uint64_t f6_target_occurrence = 0;   // steady_state: fire at this occurrence
    uint64_t f6_fired_occurrence = 0;    // occurrence index AT fire time (frozen;
                                         // matched keeps counting past it)
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
    uint64_t obs_post_fired = 0;     // POST hook: trigger said "inject now"
    uint64_t obs_post_nochange = 0;  // POST: corruption produced identical vaddr
    // [LSU][P4-FIX-GEOM] POST: 64B line geometry declined (fixed-bit modes
    // check once; random-bit modes exhausted 16 resamples). Phantom decline
    // (trigger fired, no fault written) — counted here, never as injected.
    uint64_t obs_post_geomreject = 0;

    // [MDSPEC][R4-6-A06] A06-a load leg + A06-b byte-enable counters.
    // Every decline is counted per REASON (checklist 激活口径: a trigger
    // fire the mode cannot write is not an injection) and, when the F6
    // once-ever shot is armed, logged as a REJECT line (the load-candidate
    // convention introduced by the 2026-10-19 ruling).
    uint64_t obs_pre_a06_load_widen = 0;   // load leg: widen injected
    uint64_t obs_pre_a06_load_notarget = 0; // load: agu_size_to_load unset
    uint64_t obs_pre_a06_load_illegal = 0;  // load: target not in {1,2,4,8,16}
    // [R4-10][A06] == 0 by construction. Its only increment site (the
    // `else` of the widen test in the a06_size branch) is unreachable: for a
    // load, a06LoadSize returns ShrinkUnsafe for every target < orig size
    // BEFORE any write, so the hook can never return a shrunk load size.
    // Kept for summary-line field stability; the LIVE shrink signal is
    // obs_pre_a06_load_shrink_unsafe below (never a silent zero).
    uint64_t obs_pre_a06_load_shrink = 0;   // load leg: shrink injected (DEAD: always 0)
    // [R4-10][A06] load shrink DECLINED (loudly, per-reason). The real,
    // reachable counter for a shrink candidate: both a06 switch sites count
    // ShrinkUnsafe here instead of falling into `default: break;` (the pre-
    // R4-10 bug: it was folded only into the aggregate obs_pre_opclass, so
    // every A06 summary printed a silent `load_shrink=0` with no visible
    // decline — the "never a silent zero" convention this fixes).
    uint64_t obs_pre_a06_load_shrink_unsafe = 0; // load: shrink DECLINED (structural)
    uint64_t obs_pre_a06_load_nochange = 0; // load: target == orig (no-op)
    uint64_t obs_pre_a06_load_geom = 0;     // load: target crosses the 64B line
    uint64_t obs_be_seen = 0;               // A06-b: faulted requests seen
    uint64_t obs_be_all_true = 0;           // ... of which the mask is all-true
    uint64_t obs_be_substituted = 0;        // A06-b shift_mid applied (store)
    uint64_t obs_be_declined = 0;           // A06-b shift_mid declined
    // [R6-A2/A04] object-registry eligibility (A04-a) observability.
    uint64_t obs_pre_a04_not_in_object = 0;
    uint64_t obs_pre_a04_unaligned_source = 0;
    uint64_t obs_pre_a04_no_candidate = 0;

    // [R6-A2/A04-a] One explicitly registered oracle object. A04-a may only
    // replace an EA inside the same object; no table => loud refusal.
    struct AguObject {
        std::string id;
        Addr base = 0;
        uint64_t size = 0;
        unsigned elem = 0;
    };
    std::vector<AguObject> agu_objects;
    const AguObject *findAguObject(Addr addr, unsigned size) const;
    // A06-a load-leg eligibility (F-049: a mode/target combination that
    // cannot write this request is NOT eligible — decided BEFORE the
    // trigger decision so an unwritable load can never consume the F6
    // once-ever shot). Returns the reason; target is set only on Success.
    // [MDSPEC][R4-8-A06] The load leg accepts the WIDEN direction of the
    // legal envelope {1,2,4,8,16}; the SHRINK direction is DECLINED (see
    // ShrinkUnsafe). [R4-10] Correction of the R4-8-A06 draft: that draft
    // claimed a shrink "is only safe because DynInst::chaosA06BufBytes
    // floors the load's destination buffer". That premise is WRONG — the
    // fixed-width completion aborts on the PACKET's size field, not the
    // destination buffer — so the buffer floor cannot make shrink safe. The
    // DynInst::chaosA06BufBytes floor and the two lsq_unit.cc allocations
    // that honour it are retained but STRUCTURALLY UNREACHABLE under
    // a06_size (dead code, kept only to avoid churning lsq.cc/lsq_unit.cc).
    enum class A06LoadVerdict
    // [R4-8-INT] ShrinkUnsafe: the SHRINK direction is DECLINED (loudly,
    // counted) because it cannot be made safe on this platform. The
    // fixed-width completion contract asserts sizeof(T) <= pkt->size in
    // Packet::getRaw<T> (src/mem/packet_access.hh:55) — it keys on the
    // PACKET's size field, NOT on the destination buffer. Flooring the
    // buffer (DynInst::chaosA06BufBytes) therefore cannot prevent the
    // abort: measured 2026-10-22, `--agu_size_to_load 1` on
    // workloads/directed/a06_size_be SIGABRTs with
    //   Assertion `sizeof(T) <= size' failed  (T = unsigned long)
    // on the integrated binary (sha256 prefix 78b8582966e83072).
    // A faithful shrink needs the packet size kept >= the static width with
    // the truncation done at COMMIT — a deeper LSQ/AGU redesign, not this
    // arm. Widen / store-size / byte-enable stay available and are
    // real-machine verified.
    { Success, NoTarget, Illegal, NoChange, Geometry, ShrinkUnsafe };
    A06LoadVerdict a06LoadSize(Addr addr, unsigned size,
                               unsigned &target) const;
    static const char *a06LoadVerdictReason(A06LoadVerdict v);
    static bool isLegalAguSize(uint64_t s);
    // One A06 evidence line (stdout, W2.1 discipline — a NEW line only).
    // Self-guarded: prints only for A06-shaped runs (pre_mode a06_size /
    // the rejected a06s alias / a non-off be_mode).
    void a06Summary();

    // W3 L0: funnel (attempted/eligible/injected mirrored from the trigger;
    // activated = the read-back verdict — for THIS hook the corrupted vaddr
    // is consumed by the very next pipeline step (translateTiming consumes
    // the request we just corrupted), so activated counts the request as
    // consumed unless squashed — an honest near-tautological approximation
    // documented per-injector; hooks with real slack (W4 pushRequest) need
    // a genuine read-back judgement).
    ChaOSL0Funnel l0_funnel;
    ChaOSL0State l0_item;
    // [LSU][P4-FIX-A06S] a06_size RETIRED 2026-10-15 (root cause C: the
    // fixed-width load completion path asserts on shrunken packets);
    // a06s_store_size = store-only v2. Loads are op-class filtered out
    // before the trigger decision (F-049 discipline) and never counted.
    std::string pre_mode = "off";   // off | a04_same_object|a04_same_page | a05_shift | a06_size | a08_subst | ...
    std::string agu_object_spec;    // [R6-A2/A04-a] explicit oracle registry
    uint64_t agu_size_to = 0;       // a06_size store leg: target size {1,2,4,8,16}
    // [MDSPEC][R4-6-A06] A06-a LOAD leg (planned 2026-10-22). The load's
    // completion is fixed-width per STATIC INSTRUCTION (ARM
    // LoadCompleteAcc, arch/arm/isa/templates/mem.isa:487-512, copies
    // sizeof(Mem) bytes out of the packet via getMemLE), while the packet
    // and the destination buffer are sized by THIS request size
    // (lsq_unit.cc:1915-1917 `new uint8_t[request->mainReq()->getSize()]`).
    // A load size strictly BELOW the original is therefore a heap
    // over-read — never injectable. The legal load target set is the
    // strict WIDENINGS {1,2,4,8,16} that also fit one 64B line:
    //     (addr & 63) + target <= 64
    // (BaseCache::satisfyRequest's packet-offset invariant, the same guard
    // the POST hook applies as P4-FIX-GEOM). 0 = load leg disabled: loads
    // are declined with a counted reason, never silently no-op'd.
    uint64_t agu_size_to_load = 0;  // 0 = disabled; else strict widen target
    // [MDSPEC][R4-6-A06] A06-b byte-enable mode. Carrier finding (grep
    // evidence, R4-6-A06 report): every AArch64 load/store path in this
    // tree passes std::vector<bool>(size, true) — mem.isa:424/477,
    // neon64.isa:328/355/411/443, sve_mem.isa, sme.isa — so the ISA-side
    // mask domain is the singleton {all-ones}; the only functional lever
    // of the mask is LSQRequest::addReq's inactive-TAIL trim
    // (lsq.cc:1186-1197), which is semantically an access-size change
    // (and hence forbidden for loads by the contract above).
    //   off       : no mask handling (legacy; byte-identical output)
    //   observe   : census the mask of every faulted request (be_len /
    //               be_ones / be_all_true) into the log + the summary line
    //   shift_mid : inject "another legal mask" = all-true with the MIDDLE
    //               byte cleared (index size/2, requires size >= 2 and
    //               index < size-1 so inactiveTailSize()==0 => the request
    //               size is unchanged => the load contract is untouched).
    //               Applied to STORES only: Request::isMasked() ->
    //               Packet::isMaskedWrite() -> Packet::writeData (packet.hh
    //               :1320-1336) / MSHR::TargetList::add / base.cc:1090 — a
    //               real partial write. For LOADS the mask has no
    //               architectural consumer on this path, so shift_mid
    //               declines loads (counted).
    std::string be_mode = "off";    // off | observe | shift_mid
    bool a06s_retired_warned = false;  // one-time warn for retired a06_size
    static CHAOSAddrPath *f6Consumer;
    static void f6Thunk(ChaOSLsuEvent ev);

    // [MDSPEC][R4-5.8] A07 AGU clean-ready/handshake mode state. Declared
    // AFTER pre_mode/agu_size_to so the ctor's mem-init order (params,
    // then the event wrapper) matches declaration order (-Wreorder).
    std::string agu_ready_mode = "off";   // off | a07b_ready_delay
    uint64_t agu_ready_delay_cycles = 1;  // A07-b bounded delay (spec: 1)
    // Pending delayed instruction (single slot). agu_fault_seq drives the
    // EA late binding at pushRequest (see resumeDeferredAgu note above);
    // agu_fault_ptag is the chain id returned by registerAguReadyFault.
    o3::DynInstPtr aguPendingInst;        // stashed until the resume event fires
    uint64_t agu_fault_seq = 0;
    uint64_t agu_fault_ptag = 0;
    bool agu_addr_bound = false;      // late binding done for this fault
    bool agu_activated = false;       // resume consumed (genuine read-back)
    // [MDSPEC][OBS-2 shape] post-trigger decline counters (observation
    // only — every increment sits on a path that already returned).
    uint64_t obs_agu_opclass = 0;     // ready hook: atomic/prefetch declined
    uint64_t obs_agu_slotbusy = 0;    // ready hook: single slot occupied
    // Resume event (C12 fillResumeEvent shape): scheduled at the CPU's
    // clockEdge(delay); fires IEW::chaosAguResumeInst for the stashed inst.
    EventFunctionWrapper aguResumeEvent;

    // [R6-A2/A07-a] stale EA captured at the ready point (effAddr from the
    // instruction's previous execution) and installed at pushRequest.
    bool agu_stale_valid = false;
    Addr agu_stale_ea = 0;
    Addr agu_stale_pa = 0;
    Tick agu_stale_ready_tick = 0;
    // Real saved EA of the PREVIOUS memory operation (updated at every
    // non-fault pushRequest). A07-a uses it as the stale EA.
    bool agu_prior_valid = false;
    Addr agu_prior_ea = 0;
    uint64_t agu_prior_seq = 0;
    // [R6-A2/A07-c] bounded ready-loss watchdog (never an unbounded hang).
    uint64_t agu_watchdog_cycles = 4096;
    uint64_t agu_watchdog_max = 1ULL << 20;
    o3::DynInstPtr aguWatchdogInst;
    EventFunctionWrapper aguWatchdogEvent;
    uint64_t obs_agu_no_stale = 0;        // A07-a: no previous EA
    uint64_t obs_agu_watchdog = 0;        // A07-c: forced resume
    uint64_t obs_agu_watchdog_squash = 0; // A07-c: squashed before ready
    void aguWatchdogFired();

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_ADDR_PATH_HH__
