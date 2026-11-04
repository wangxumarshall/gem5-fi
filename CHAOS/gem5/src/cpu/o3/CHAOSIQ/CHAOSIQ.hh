#ifndef __CPU_O3_CHAOS_IQ_HH__
#define __CPU_O3_CHAOS_IQ_HH__

#include <deque>
#include <random>
#include <string>
#include <vector>

#include "params/CHAOSIQ.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"            // Event (FQ08-c delayed wake)
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/o3/dyn_inst_ptr.hh"
#include "cpu/o3/CHAOSIQ/chaos_iq_lifecycle.hh"  // FQ08-b/c pure model
#include "cpu/op_class.hh"          // OpClass (W5.12 D55 fu-class misroute)
#include "cpu/reg_class.hh"         // RegClassType (W7.4 targetClass)

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

    // Called from InstructionQueue::wakeDependents at the START.
    //
    //  - wake_omit: if the RNG fires, returns true (the caller SKIPS the
    //    wakeup broadcast — one dropped wake).
    //  - wake_phase (FQ08-c): also handled HERE, not via shouldDelayWake().
    //    On a gate hit CHAOSIQ schedules its OWN DelayedWake event (identity +
    //    physical-register generation checked at fire time) and returns true
    //    so the caller skips the broadcast now. The caller's
    //    o3::DelayedWakeEvent path is therefore never taken (shouldDelayWake
    //    is permanently closed) — that event re-enters wakeDependents with no
    //    squash/generation check (FQ08-c risk).
    bool shouldOmitWake(ThreadID tid, const o3::DynInstPtr &completed_inst);

    // §2.5 F5 src_ready_bitflip (FQ08-b): ATTEMPT gate only.
    //
    // On a gate hit this records an attempt and returns FALSE: the actual
    // wrong-source ready write is applied later by noteTagWake(), on a live
    // dependent the caller is really waking. Returning false also disables
    // the caller's legacy "pop a random other chain" surgery, which could not
    // report whether a victim existed (the FQ08-b over-count). applied /
    // activated (and the max_faults budget) move only when a real victim is
    // modified.
    bool shouldWrongSourceWake(ThreadID tid,
                               const o3::DynInstPtr &completed_inst);

    // §2.5 F6 wake_phase: permanently closed legacy gate.
    //
    // FQ08-c: returning true here would make InstructionQueue schedule its
    // o3::DelayedWakeEvent, which stores a bare DynInstPtr and calls
    // wakeDependents() with no squash/generation validation. CHAOSIQ owns the
    // delayed wake instead (see shouldOmitWake). Kept for call-site ABI.
    bool shouldDelayWake(ThreadID tid, const o3::DynInstPtr &completed_inst);

    // F6: the configured delay in cycles (read by CHAOSIQ when scheduling its
    // own DelayedWake event; the caller's DelayedWakeEvent is not used).
    int phaseOffset() const { return phase_offset; }

    // FQ08-c: the delayed-wake event CHAOSIQ schedules itself. It holds a
    // refcounted DynInstPtr (the producer object cannot be freed while the
    // event holds it) plus a VALUE snapshot of the producer identity and of
    // every destination physical register's allocation generation. process()
    // compares the snapshot against the live state and only then re-enters
    // InstructionQueue::wakeDependents(); squash / free+realloc / identity
    // mismatch is a logged no-op.
    class DelayedWake : public Event
    {
      public:
        DelayedWake(CHAOSIQ *_injector, const o3::DynInstPtr &_inst,
                    const chaos_iq_lifecycle::WakeStamp &_stamp);
        void process() override;
        const char *description() const override
        {
            return "CHAOSIQ safe delayed wake";
        }

      private:
        CHAOSIQ *injector;
        o3::DynInstPtr inst;
        chaos_iq_lifecycle::WakeStamp stamp;
    };

    // ------------------------------------------------------------------
    // W5.10-W5.11 (ooo 04-design-matrix D47-D54, Int Dispatch/ROB — the
    // Int-IQ entry's ready bit / source-tag field) and the W7.4 FP/SIMD
    // twins (D86-D91 — same fields, targetClass=vec: VecRegClass slots,
    // [0, numVecPhysRegs) tag domain; scalar FP + FP SIMD + integer SIMD
    // all rename onto VecRegClass on AArch64). Hooks live in
    // InstructionQueue (insert / wakeDependents / the issue loop); the
    // surgery below is DynInst-level so CHAOSIQ owns it directly.

    // Called from InstructionQueue::insert AFTER the entry is linked and
    // BEFORE addToDependents: corrupt ONE target-class source TAG of the
    // entry being written (tag_swap D50/D87 / tag_bitflip D51/D88 /
    // tag_bitflip2 D52/D89 / tag_stuck D53/D90 / tag_stale_read D54/D91).
    // The surgery is renameSrcReg(slot, otherPhysRegId) — the dependency
    // graph, the scoreboard check and the ISSUE-TIME OPERAND READ
    // (DynInst::getRegOperand reads renamedSrcIdx, dyn_inst.hh) all
    // follow the corrupted tag: the entry waits for / reads the WRONG
    // physreg, the faithful CAM-tag-mismatch realization.
    // Returns true if this insert was corrupted.
    bool maybeCorruptTag(ThreadID tid, const o3::DynInstPtr &inst);

    // Called from InstructionQueue::insert BEFORE addToDependents:
    // D47/D86 ready_early — force ONE not-yet-ready target-class source
    // slot's ready bit (markSrcRegReady(idx): per-slot bit + counter).
    // The per-slot bit keeps the entry OFF that slot's dependency chain
    // (no later wake can re-mark it — the double-issue assert is
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
    // producer broadcast). FQ08-b: in src_ready_bitflip mode this is also
    // the victim hook — the dependent being woken is a real, live
    // instruction, so the wrong-source ready write is applied here or not at
    // all (an attempt with no live victim never counts as applied).
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
    // W7.4 (D86-D91): register-class scope of the ready-bit / tag-field
    // population. IntRegClass = the W5 Int-IQ scope (default); VecRegClass
    // = the FP/SIMD queue (scalar FP + FP SIMD + integer SIMD all rename
    // onto VecRegClass on AArch64 — S/D are the low bits of V, the W1
    // platform finding; FloatRegClass is never renamed).
    RegClassType target_reg_class = IntRegClass;
    // W7.4 D86: optional FP/SIMD opClass filter for the §2.5 wake modes.
    bool fp_only = false;
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

    // FQ08-b: separate observable counters (eligible / attempted / applied /
    // activated) and the pending-attempt state. `faults_injected_count` (the
    // max_faults budget) is incremented ONLY on apply, for every FQ08 mode.
    chaos_iq_lifecycle::Counters iq_counts;
    chaos_iq_lifecycle::Attempt ws_attempt;
    // One-shot suppression of the GENUINE wake of the source slot the
    // injection already marked ready (the victim stays in that dependency
    // chain because CHAOSIQ cannot pop it; see the pure header).
    chaos_iq_lifecycle::DuplicateWake ws_duplicate;
    // FQ08-c: counters for the CHAOSIQ-owned delayed wake.
    chaos_iq_lifecycle::DelayedWakeCounters dw_counts;
    // Set while a delayed wake is being re-issued: the nested
    // wakeDependents() call must not fire a NEW injection (otherwise an
    // unlimited-fault wake_phase run would keep delaying its own replay).
    bool replaying_delayed_wake = false;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
    // FQ08-b: build the VictimView of one woken dependent and apply the
    // wrong-source ready write if it is a live, eligible victim.
    void maybeApplyWrongSourceWake(const o3::DynInstPtr &dep_inst,
                                   RegIndex chain_flat);
    // FQ08-c: log a delayed wake that was safely ignored (squash / generation
    // / identity). Every line carries "faults_injected: <n>" so the existing
    // injection-log parsers keep counting real injections only.
    void noteDelayedWakeIgnored(chaos_iq_lifecycle::WakeDecision decision,
                                const o3::DynInstPtr &inst);
    // Exit summary: CHAOS_IQ_COUNTS ... , faults_injected: <n>
    void dumpIqCounts();
    const char *modeName();
    // FQ08-c: value snapshot of the producer identity + destination physreg
    // allocation generations at schedule time.
    chaos_iq_lifecycle::WakeStamp
    snapshotWakeStamp(o3::CPU *o3cpu, const o3::DynInstPtr &inst);
    // shared gates for the insert/wake/issue-site hooks: window +
    // max_faults + probability + the events_to_skip discipline. Returns
    // true when the injection may fire.
    bool gateEligible();
    // W7.4: source slots of inst in the TARGET register class (the
    // tag-field scope — IntRegClass for the W5 Int-IQ modes, VecRegClass
    // for the W7.4 FP/SIMD twins D86-D91).
    int collectSrcSlots(const o3::DynInstPtr &inst,
                        std::vector<int> &slots);
    // W7.4 class helpers: the tag index domain and the PhysRegId factory
    // of the target class (intPhysRegId / vecPhysRegId, regfile.hh).
    int numTargetPhysRegs(o3::CPU *o3cpu);
    PhysRegIdPtr targetPhysRegId(o3::CPU *o3cpu, int idx);
    const char *targetClassName();
    // W7.4 D86: the FP/SIMD opClass filter (Float* ∪ SimdFloat*, the
    // CHAOSFPU §2.6 isFpOpClass convention) for the §2.5 wake modes.
    static bool isFpOpClass(OpClass oc);
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_IQ_HH__
