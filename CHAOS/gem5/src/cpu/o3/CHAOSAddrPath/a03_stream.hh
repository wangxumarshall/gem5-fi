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
// pc is kPcUnknown when the observing hook cannot see the PC (the PRE hook
// receives dyn_inst_seq only) — never fabricated.

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

  public:
    bool activated() const { return activated_; }
    const Activation &activation() const { return activation_; }
    uint64_t recorded() const { return recorded_; }
    uint64_t appliedCount() const { return applied_; }
    uint64_t alreadyStuckCount() const { return already_stuck_; }
    uint64_t rejected() const { return rejected_; }

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
        if (e.reason == StreamReason::AlreadyStuck)
            ++already_stuck_;
        else
            ++applied_;
        return true;
    }
};

} // namespace chaos_a03
} // namespace gem5

#endif // __CPU_O3_CHAOS_ADDR_PATH_A03_STREAM_HH__
