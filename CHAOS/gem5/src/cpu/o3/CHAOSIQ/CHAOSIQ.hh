#ifndef __CPU_O3_CHAOS_IQ_HH__
#define __CPU_O3_CHAOS_IQ_HH__

#include <deque>
#include <random>
#include <string>
#include <vector>

#include "params/CHAOSIQ.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/o3/dyn_inst_ptr.hh"
#include "cpu/op_class.hh"          // OpClass (W5.12 D55 fu-class misroute)

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class InstructionQueue; } }

namespace gem5
{

class CHAOSIQ : public SimObject
{
  public:
    CHAOSIQ(const CHAOSIQParams &p);
    ~CHAOSIQ();

    void startup() override;  // self-attach to InstructionQueue.chaosIQ

    // Called from InstructionQueue::wakeDependents at the START. If
    // wake_omit and the RNG fires, returns true (the caller SKIPS the
    // wakeup broadcast — one dropped wake). Otherwise false (normal wake).
    bool shouldOmitWake(ThreadID tid, const o3::DynInstPtr &completed_inst);

    // §2.5 F5 src_ready_bitflip (Phase 4.3, method3 wrong-source wakeup):
    // GATE only — the dependency-graph surgery (pop a not-ready dependent
    // from a different reg's chain, markSrcRegReady, addIfReady) lives in
    // InstructionQueue::wakeDependents, which owns dependGraph/addIfReady/
    // scoreboard (no internals exposed). Returns true = inject this event.
    bool shouldWrongSourceWake(ThreadID tid,
                               const o3::DynInstPtr &completed_inst);

    // §2.5 F6 wake_phase (Phase 4.3, method3 phase collapse): GATE only —
    // the caller skips this broadcast now and re-issues it after
    // |phase_offset| cycles via its own scheduled event. Delay only
    // (advance = wake in the past = no-op; documented E3 proxy limit).
    bool shouldDelayWake(ThreadID tid, const o3::DynInstPtr &completed_inst);

    // F6: the configured delay in cycles (InstructionQueue reads it when
    // scheduling the DelayedWakeEvent).
    int phaseOffset() const { return phase_offset; }

    // ------------------------------------------------------------------
    // W5.10-W5.11 (ooo 04-design-matrix D47-D54, Int Dispatch/ROB — the
    // Int-IQ entry's ready bit / source-tag field). Hooks live in
    // InstructionQueue (insert / wakeDependents / the issue loop); the
    // surgery below is DynInst-level so CHAOSIQ owns it directly.

    // Called from InstructionQueue::insert AFTER the entry is linked and
    // BEFORE addToDependents: corrupt ONE int-class source TAG of the
    // entry being written (tag_swap D50 / tag_bitflip D51 / tag_bitflip2
    // D52 / tag_stuck D53 / tag_stale_read D54). The surgery is
    // renameSrcReg(slot, otherPhysRegId) — the dependency graph, the
    // scoreboard check and the ISSUE-TIME OPERAND READ
    // (DynInst::getRegOperand reads renamedSrcIdx, dyn_inst.hh) all
    // follow the corrupted tag: the entry waits for / reads the WRONG
    // physreg, the faithful CAM-tag-mismatch realization.
    // Returns true if this insert was corrupted.
    bool maybeCorruptTag(ThreadID tid, const o3::DynInstPtr &inst);

    // Called from InstructionQueue::insert BEFORE addToDependents:
    // D47 ready_early — force ONE not-yet-ready int-class source slot's
    // ready bit (markSrcRegReady(idx): per-slot bit + counter). The
    // per-slot bit keeps the entry OFF that slot's dependency chain (no
    // later wake can re-mark it — the double-issue assert is
    // impossible); if the counter completes the entry, the normal
    // addIfReady path queues it this very insert and it issues reading a
    // not-yet-written physreg (stale value, the "状态位撒谎" silent-SDC
    // family).
    void maybeReadyEarly(ThreadID tid, const o3::DynInstPtr &inst);

    // Called from the wakeDependents dependent loop for EACH popped
    // dependent: D48/D49 ready_never(_event) — return true to SUPPRESS
    // this markSrcRegReady + addIfReady (the operand value IS ready but
    // the ready bit never sets; the pop consumed the only wake, so the
    // entry is permanently never-ready -> the ROB head blocks -> the ROB
    // fills -> Timeout). D49 additionally requires IQ occupancy > 80%
    // (iq_used*5 > iq_cap*4, the "约 51/64 项" gate — occupancy computed
    // by the caller, which owns the IQUnit counts).
    bool shouldSuppressReadyMark(const o3::DynInstPtr &dep_inst,
                                 RegIndex producer_flat,
                                 unsigned iq_used, unsigned iq_cap);

    // Called from the wakeDependents dependent loop for each popped
    // dependent: D53 tag_stuck consumption evidence — log when the ARMED
    // entry is woken through a chain (the wrong tag actually matched a
    // producer broadcast).
    void noteTagWake(const o3::DynInstPtr &dep_inst, RegIndex chain_flat);

    // Called from the issue loop at the non-mem clearInIQ site: record
    // the departed entry (its src tags) into the bounded D54 ring — the
    // "previous occupant" pool for tag_stale_read.
    void noteIqDeparture(const o3::DynInstPtr &inst);

    // ------------------------------------------------------------------
    // W5.12 (D55, R56): dispatch-port FU-class misroute at the issue
    // site. Called from InstructionQueue::scheduleReadyInsts right
    // before fu_pool->getUnit(); if it fires it rewrites fu_class
    // (IntAlu <-> IntMult, the design's binary ALU-vs-MDU judgment) and
    // the caller uses the MISROUTED class for getUnit/getOpLatency/
    // isPipelined. HONEST SCOPE (spike C, findings.md): gem5's FU index
    // only drives latency/port accounting — the executed VALUE comes
    // from inst->execute() (StaticInst vtable) — so the misroute is a
    // timing/port-occupancy effect with a CORRECT value, never a value
    // corruption; every log line says so.
    void maybeMisrouteFU(const o3::DynInstPtr &issuing_inst,
                         OpClass &fu_class);

  private:
    enum class Mode {
        WakeOmit, SrcReadyBitflip, WakePhase,
        // W5.10 (D47-D49): the entry's ready bit.
        ReadyEarly, ReadyNever, ReadyNeverEvent,
        // W5.11 (D50-D54): the entry's source-tag field.
        TagSwap, TagBitflip, TagBitflip2, TagStuck, TagStaleRead,
        // W5.12 (D55): FU-class misroute at issue.
        DispatchMisroute
    };
    static Mode stringToMode(const std::string &s);
    Mode fi_mode;
    BaseCPU *cpu;
    double probability;
    uint64_t first_clock, last_clock;
    int phase_offset;
    uint64_t fault_mask;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;
    // Sampling-bias fix (findings.md Phase 2.2/3.0, same as CHAOSL1DForward
    // 7387649): skip a geometric(p=0.1) number of eligible events before
    // the first injection, so maxFaults=1 lands on a seed-dependent event
    // instead of always the first eligible one (same dynamic instruction
    // every rep on a deterministic stream).
    uint64_t events_to_skip = 0;
    // v1.1 Phase 8.2 uniform sampling (chaos_event_sample.hh): FIXED skip
    // from the driver overrides the legacy geometric(0.1) draw.
    bool count_only = false;         // consume + count, never corrupt
    uint64_t eligible_count = 0;     // CHAOS_ELIGIBLE_COUNT=<n> at teardown

    // W5.11 D53 tag_stuck state (F5): ONE armed entry (by seqNum) + ONE
    // int src slot + ONE bit + polarity. The write-path mask applies at
    // the armed entry's IQ insert (the single write of the tag field —
    // gem5 never rewrites renamedSrcIdx while the entry is IQ-resident,
    // so persistence = value permanence; noteTagWake logs the wrong-chain
    // consumption).
    bool tag_stuck_armed = false;
    uint64_t tag_stuck_sn = 0;
    int tag_stuck_slot = -1;
    int tag_stuck_bit = -1;
    int tag_stuck_polarity = 0;
    uint64_t tag_stuck_wakes = 0;    // wrong-chain wake count (evidence)

    // W5.11 D54 tag_stale_read: bounded ring of recently DEPARTED
    // (issued) entries — the "previous occupant" pool (the D40
    // stale_departed pattern; the DynInstPtr keeps the record readable).
    std::deque<o3::DynInstPtr> tag_departed;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
    // shared gates for the insert/wake/issue-site hooks: window +
    // max_faults + probability + the events_to_skip discipline. Returns
    // true when the injection may fire.
    bool gateEligible();
    // int-class source slots of inst (the Int-IQ tag-field scope).
    int collectIntSrcSlots(const o3::DynInstPtr &inst,
                           std::vector<int> &slots);
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_IQ_HH__
