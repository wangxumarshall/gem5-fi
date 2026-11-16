#ifndef __CPU_O3_CHAOS_ADDR_PATH_A03_STREAM_HH__
#define __CPU_O3_CHAOS_ADDR_PATH_A03_STREAM_HH__

// [LSU][V3.2.12][A03] pure record shapes + the exactly-once discipline for
// the F5 stuck-at eligibility stream (plan Task 8,
// LSU_Propagation_Acceptance_Standard_v3.2.12.md).
//
// PURE HEADER: no gem5 types (only <cstdint>/<string>/<sstream> plus the
// equally pure a01_coords.hh), so the host unit test
// tests/test_addrpath_a03_stream.cc compiles it with plain
// g++ -O2 -std=c++17 -I CHAOS/gem5/src (the a01_coords precedent).
//
// WHAT THIS CLOSES: the v3.2.11 A03 audit could not separate "the stuck-at
// condition fired on a load whose EA bit was already at the stuck level"
// (the ALREADY_STUCK masking path) from "the stream went missing", and the
// five contexts R01-R05 could not be shown to be five ACTIVATION START
// positions of one persistent fault rather than five one-shot injections.
// The a03_stream record gives every post-activation eligible load its own
// row — golden_ea vs actual_ea on the same dyn_inst_seq — so a control
// run's response at golden_ea can be compared with the fault run's
// response at actual_ea (standard section 3 data rule), and the
// event_ordinal column shows the activation start position directly
// (R05's first stream row is ordinal 5, not 1).
//
// ADDITIVE ONLY: A03's F5 persistent fault semantics are UNCHANGED
// (task-8-brief.md "Consumes: the same hook as Task 7; A03's F5 persistent
// semantics are unchanged"). This header observes the (golden, actual)
// pair the injector already computes; it never derives the applied address
// for the data path. The coordinate math and the frozen detail dialect are
// REUSED from a01_coords.hh (xorDelta/affectedBits/toHexField, kNoBit,
// kPcUnknown) — one classifier, no drift; this file defines NO second
// format and NO second hash.
//
// WRITER DISCIPLINE: CHAOSPropagation stays the SINGLE prop-trace writer
// (per-node Z_SYNC_FLUSH CSV nodes, the only abort-survivable copy). This
// header only computes + FORMATS the records; CHAOSAddrPath stages them at
// the fired-eligible-load site and the sink side emits them (the a01_ea
// contract recorded in task-7-report.md). The durable in-process copy is
// the A03_ACTIVATION / A03_STREAM lines in the existing
// addrpath_injections.log (same stream, same writer, frozen detail format
// so the log line and the future prop-trace node can never drift).
//
// IDENTITY (standard section 2): dyn_inst_seq is the faulting DynInst's
// seqNum — the identity the commit-side chain join uses. event_ordinal is
// this load's 1-based ordinal in the trigger's eligible-event stream, the
// SAME space the R01-R05 activation positions index into
// (chaos_lsu_trigger.hh F5 case: start = warmup_events + event_ordinal).
// pc is the faulting DynInst's PC, threaded from the lsq.cc pushRequest
// call site (inst->pcState().instAddr() via the maybeCorruptPre pc param);
// kPcUnknown only when the observing path genuinely cannot see a PC (the
// legacy non-lsq hook) — never fabricated.
//
// LIFECYCLE (v3.3.2 P0-5): the F5 stuck-at fault is ONE persistent fault
// observed at every eligible load, not a stream of independent injections.
// StreamRecorder therefore also keeps the lifecycle split — applications
// (affected=1) vs already_stuck (affected=0) — plus the identity of the
// first activation row and of the first AFFECTED row. An ALREADY_STUCK
// activation is a no-op APPLICATION (nothing to propagate at that load),
// but the fault remains active for every later eligible load; the lifecycle
// record keeps the two readings distinct instead of letting the ordinal
// stream hide them.

#include <cstdint>
#include <sstream>
#include <string>

#include "cpu/o3/CHAOSAddrPath/a01_coords.hh"

namespace gem5
{
namespace chaos_a03
{

// Reason value set (frozen): exactly the two outcomes of applying one
// stuck-at condition to one eligible load.
//   STUCK_APPLIED  the golden EA bit differed from the stuck level — the
//                  application changed the EA (affected=1).
//   ALREADY_STUCK  the golden EA bit already equalled the stuck level —
//                  the condition was applied but changed nothing
//                  (affected=0). This is the MASKING path: the event IS
//                  recorded (exactly once, like every eligible event),
//                  never silently dropped — a missing event and a
//                  no-change event are different facts.
enum class StreamReason : int {
    StuckApplied = 0,
    AlreadyStuck = 1
};

inline const char *
streamReasonName(StreamReason r)
{
    return (r == StreamReason::AlreadyStuck) ? "ALREADY_STUCK"
                                             : "STUCK_APPLIED";
}

// a03_activation: the F5 activation record — {tick, bit, mode}, one per
// run. The activation start position is the first trigger-fired eligible
// load (the F5 case arms there and fires on every later eligible event);
// on the rng-selected path the pinned bit is chosen at that same moment,
// on the v3.2 pilot path (a03_bit3_stuck0_load) the bit is fixed at 3.
struct Activation {
    uint64_t tick = 0;                    // curTick() at the activation load
    int bit = chaos_a01::kNoBit;           // pinned stuck bit
    std::string mode;                      // injector mode string
    // v3.3.2 P0-5 lifecycle identity of the activation row (defaults keep
    // the frozen {tick, bit, mode} activationDetail byte-identical):
    uint64_t event_ordinal = 0;            // activation load's ordinal
    uint64_t dyn_inst_seq = 0;             // activation load's DynInst seq
    uint64_t pc = chaos_a01::kPcUnknown;   // activation load's PC
    uint64_t golden_ea = 0;                // activation load's pre-apply EA
};

// a03_stream: one eligible load after activation. Exactly the nine
// contracted fields (plan Task 8 Interfaces), nothing else.
struct StreamEvent {
    uint64_t event_ordinal = 0;   // 1-based eligible-event ordinal (the
                                   // space R01-R05 activation positions
                                   // index)
    uint64_t dyn_inst_seq = 0;     // faulting DynInst::seqNum
    uint64_t pc = chaos_a01::kPcUnknown;   // kPcUnknown = not observable
    int eligible = 1;              // this record exists ONLY for eligible
                                   // loads — the stream's contract; frozen
                                   // by the record shape, never 0 here
    int affected = 0;              // 1 iff the application changed the EA
    uint64_t golden_ea = 0;        // pre-application EA
    uint64_t actual_ea = 0;        // post-application EA
    int bit = chaos_a01::kNoBit;   // the stuck bit index
    StreamReason reason = StreamReason::StuckApplied;
};

// ---- pure stuck-at math ----------------------------------------------------
// The pure mirror of the injector's mask application, for derivation and
// the host test ONLY — the data path keeps its own (unchanged) mask line.
// level 0 = stuck-at-0 (addr & ~mask), level 1 = stuck-at-1 (addr | mask).
inline uint64_t
applyStuckAt(uint64_t ea, int bit, int level)
{
    const uint64_t mask = 1ULL << bit;
    return level ? (ea | mask) : (ea & ~mask);
}

// Stream record builder: derives affected/reason from the observed pair —
// affected=1 iff the application changed the EA (xor_delta != 0). The
// property is enforced by construction; callers never hand-set it.
inline StreamEvent
streamEvent(uint64_t event_ordinal, uint64_t dyn_inst_seq, uint64_t pc,
            uint64_t golden_ea, uint64_t actual_ea, int bit)
{
    StreamEvent e;
    e.event_ordinal = event_ordinal;
    e.dyn_inst_seq = dyn_inst_seq;
    e.pc = pc;
    e.eligible = 1;
    e.golden_ea = golden_ea;
    e.actual_ea = actual_ea;
    e.bit = bit;
    const uint64_t delta = chaos_a01::xorDelta(golden_ea, actual_ea);
    e.affected = (delta != 0) ? 1 : 0;
    e.reason = (delta != 0) ? StreamReason::StuckApplied
                            : StreamReason::AlreadyStuck;
    return e;
}

// ---- frozen detail formatting (single format, no drift) -------------------

// a03_activation detail: exactly {tick, bit, mode}. Tick is decimal; bit is
// decimal or the literal NOT_APPLICABLE (kNoBit); mode is the injector's
// mode string. k=v;k=v fields, NO commas (the CSV detail column is last).
inline std::string
activationDetail(const Activation &a)
{
    std::ostringstream d;
    d << "tick=" << a.tick
      << ";bit=" << (a.bit == chaos_a01::kNoBit
                        ? "NOT_APPLICABLE" : std::to_string(a.bit))
      << ";mode=" << a.mode;
    return d.str();
}

// a03_stream detail: exactly the nine contracted fields, in the contracted
// order — event_ordinal, dyn_inst_seq, pc, eligible, affected, golden_ea,
// actual_ea, bit, reason. Addresses bare lowercase hex; ordinals/seq/
// eligible/affected decimal; bit decimal or NOT_APPLICABLE; reason is the
// frozen reason name. NO commas.
inline std::string
streamDetail(const StreamEvent &e)
{
    std::ostringstream d;
    d << "event_ordinal=" << e.event_ordinal
      << ";dyn_inst_seq=" << e.dyn_inst_seq
      << ";pc=" << chaos_a01::toHexField(e.pc)
      << ";eligible=" << e.eligible
      << ";affected=" << e.affected
      << ";golden_ea=" << chaos_a01::toHexField(e.golden_ea)
      << ";actual_ea=" << chaos_a01::toHexField(e.actual_ea)
      << ";bit=" << (e.bit == chaos_a01::kNoBit
                        ? "NOT_APPLICABLE" : std::to_string(e.bit))
      << ";reason=" << streamReasonName(e.reason);
    return d.str();
}

// ---- persistent stuck-at lifecycle (v3.3.2 P0-5) --------------------------
//
// The F5 fault is ONE persistent fault with five observation points, not
// five independent transient injections. The lifecycle record makes that
// reading explicit: every recorded eligible load is an APPLICATION of the
// same stuck bit; affected=1 means the application changed the EA (the
// fault propagated at that load), affected=0 (ALREADY_STUCK) means the
// application changed nothing at that load but the fault remains ACTIVE
// for every later eligible load. first_activation is the activation-start
// row (which may itself be ALREADY_STUCK — a no-op application), and
// first_affected is the first row where the fault actually changed the EA
// — the earliest load at which the persistent fault can have propagated.
struct StuckLifecycle {
    uint64_t fault_id = 0;                 // injector fault ordinal (1-based)
    int bit = chaos_a01::kNoBit;           // pinned stuck bit
    std::string mode;                      // injector mode string
    uint64_t eligible_events = 0;          // recorded applications (all)
    uint64_t applications = 0;             // affected=1 applications
    uint64_t already_stuck = 0;            // affected=0 no-op applications
    bool has_activation = false;           // an activation row exists
    uint64_t activation_ordinal = 0;       // activation row identity
    uint64_t activation_dyn_inst_seq = 0;
    uint64_t activation_pc = chaos_a01::kPcUnknown;
    uint64_t activation_golden_ea = 0;
    bool has_first_affected = false;       // some application changed the EA
    uint64_t first_affected_ordinal = 0;   // first affected row identity
    uint64_t first_affected_dyn_inst_seq = 0;
    uint64_t first_affected_pc = chaos_a01::kPcUnknown;
};

// a03_stuck_lifecycle detail: fault identity {fault_id, bit, mode}, the
// application split {eligible_events, applications, already_stuck}, the
// activation identity {ordinal, dyn seq, pc, golden EA} and the first
// AFFECTED identity {ordinal, dyn seq, pc}. k=v;k=v, NO commas; addresses
// bare lowercase hex, counts decimal, absent identities NOT_APPLICABLE.
inline std::string
lifecycleDetail(const StuckLifecycle &l)
{
    std::ostringstream d;
    d << "fault_id=" << l.fault_id
      << ";bit=" << (l.bit == chaos_a01::kNoBit
                        ? "NOT_APPLICABLE" : std::to_string(l.bit))
      << ";mode=" << l.mode
      << ";eligible_events=" << l.eligible_events
      << ";applications=" << l.applications
      << ";already_stuck=" << l.already_stuck
      << ";activation_ordinal="
      << (l.has_activation ? std::to_string(l.activation_ordinal)
                           : "NOT_APPLICABLE")
      << ";activation_dyn_inst_seq="
      << (l.has_activation ? std::to_string(l.activation_dyn_inst_seq)
                           : "NOT_APPLICABLE")
      << ";activation_pc="
      << (l.has_activation ? chaos_a01::toHexField(l.activation_pc)
                           : "NOT_APPLICABLE")
      << ";activation_golden_ea="
      << (l.has_activation ? chaos_a01::toHexField(l.activation_golden_ea)
                           : "NOT_APPLICABLE")
      << ";first_affected_ordinal="
      << (l.has_first_affected ? std::to_string(l.first_affected_ordinal)
                               : "NOT_APPLICABLE")
      << ";first_affected_dyn_inst_seq="
      << (l.has_first_affected ? std::to_string(l.first_affected_dyn_inst_seq)
                               : "NOT_APPLICABLE")
      << ";first_affected_pc="
      << (l.has_first_affected
              ? chaos_a01::toHexField(l.first_affected_pc)
              : "NOT_APPLICABLE");
    return d.str();
}

// ---- the exactly-once discipline (host-testable) ---------------------------
//
// StreamRecorder: one per injector instance. The injector routes EVERY
// trigger-fired eligible load through record() — on the F5 tier that is
// exactly "every eligible load after activation" (the trigger returns false
// for every pre-activation eligible event, so the application branch never
// runs before the activation start position). Rejections are counted,
// never silent:
//   - activate() after the first activation  → one activation per run;
//   - record() before activation             → the stream starts at
//                                              activation, never before;
//   - record() with a non-advancing ordinal  → a double-record or an
//                                              ordinal regression (the
//                                              trigger's eligible count is
//                                              monotonic; this guard makes
//                                              a double-record
//                                              structurally impossible).
struct StreamRecorder {
  private:
    bool activated_ = false;
    Activation activation_;
    uint64_t last_ordinal_ = 0;
    uint64_t recorded_ = 0;
    uint64_t applied_ = 0;
    uint64_t already_stuck_ = 0;
    uint64_t rejected_ = 0;
    bool has_first_affected_ = false;
    StreamEvent first_affected_;

  public:
    bool activated() const { return activated_; }
    const Activation &activation() const { return activation_; }
    uint64_t recorded() const { return recorded_; }
    uint64_t appliedCount() const { return applied_; }
    uint64_t alreadyStuckCount() const { return already_stuck_; }
    uint64_t rejected() const { return rejected_; }
    // v3.3.2 P0-5 lifecycle accessors: eligible_events is the recorded
    // stream size (the recorder only sees post-activation fired events =
    // the applications of this ONE persistent fault).
    uint64_t eligibleEvents() const { return recorded_; }
    bool hasFirstAffected() const { return has_first_affected_; }
    const StreamEvent &firstAffected() const { return first_affected_; }

    // Lifecycle record built from the counters this recorder owns. fault_id
    // and mode come from the injector (the record shape cannot derive the
    // run-level fault ordinal).
    StuckLifecycle
    lifecycle(uint64_t fault_id, const std::string &mode) const
    {
        StuckLifecycle l;
        l.fault_id = fault_id;
        l.bit = activation_.bit;
        l.mode = mode;
        l.eligible_events = recorded_;
        l.applications = applied_;
        l.already_stuck = already_stuck_;
        l.has_activation = activated_;
        l.activation_ordinal = activation_.event_ordinal;
        l.activation_dyn_inst_seq = activation_.dyn_inst_seq;
        l.activation_pc = activation_.pc;
        l.activation_golden_ea = activation_.golden_ea;
        l.has_first_affected = has_first_affected_;
        l.first_affected_ordinal = first_affected_.event_ordinal;
        l.first_affected_dyn_inst_seq = first_affected_.dyn_inst_seq;
        l.first_affected_pc = first_affected_.pc;
        return l;
    }

    // One activation per run: the first call wins and is returned; every
    // later call is rejected (counted).
    bool activate(const Activation &a)
    {
        if (activated_) {
            ++rejected_;
            return false;
        }
        activated_ = true;
        activation_ = a;
        return true;
    }

    // One record per fired eligible load: accepts only post-activation
    // records with a strictly advancing event_ordinal.
    bool record(const StreamEvent &e)
    {
        if (!activated_ || e.event_ordinal <= last_ordinal_) {
            ++rejected_;
            return false;
        }
        last_ordinal_ = e.event_ordinal;
        ++recorded_;
        if (e.reason == StreamReason::AlreadyStuck) {
            ++already_stuck_;
        } else {
            ++applied_;
            // first_affected = the FIRST row that changed the EA, not the
            // first recorded row (an ALREADY_STUCK activation is ordinal 1
            // and must not be reported as the first affected row).
            if (!has_first_affected_) {
                has_first_affected_ = true;
                first_affected_ = e;
            }
        }
        return true;
    }
};

} // namespace chaos_a03
} // namespace gem5

#endif // __CPU_O3_CHAOS_ADDR_PATH_A03_STREAM_HH__
