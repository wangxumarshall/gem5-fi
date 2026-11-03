#ifndef __CPU_O3_CHAOS_FPU_HH__
#define __CPU_O3_CHAOS_FPU_HH__

#include <deque>
#include <map>
#include <ostream>
#include <random>
#include <string>
#include <utility>
#include <vector>

#include "params/CHAOSFPU.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/o3/dyn_inst_ptr.hh"
#include "cpu/o3/CHAOSFPU/chaos_fsu_fields.hh"
#include "cpu/o3/CHAOSFPU/decoded_fp.hh"

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class DynInst; } }

namespace gem5
{

class CHAOSFPU : public SimObject
{
  public:
    CHAOSFPU(const CHAOSFPUParams &p);
    ~CHAOSFPU();

    void startup() override;  // self-attach to CPU.chaosFPU

    // Called from DynInst::execute() AFTER staticInst->execute(). Filters by
    // opClass (FloatAdd/FloatMult/FloatMultAcc + SimdFloat*); XORs the FP
    // result blob. Returns true if an injection happened.
    bool maybeCorrupt(o3::DynInst *dyn_inst);

    // [FSU] Read-only propagation observers. Called from DynInst::execute()
    // (same anchor as maybeCorrupt) and Commit::commitHead(); they never
    // change architectural or microarchitectural state.
    void noteConsumerExecute(o3::DynInst *inst);
    void noteCommit(ThreadID tid, o3::DynInst *inst);

  private:
    BaseCPU *cpu;
    double probability;
    uint64_t first_clock, last_clock;
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
    // v1.1 Phase 8.2 uniform sampling (design doc §1.7 rule 4): the
    // geometric(p=0.1) skip has mean 10 / P(skip<=30)~=96% — the single
    // fault lands in the FIRST ~30 eligible events for nearly every rep.
    // The driver (campaign.py) dry-runs countOnlyMode to learn N_eligible,
    // then passes a FIXED uniform skip (chaosPickSkip(seed, N_eligible),
    // chaos_event_sample.hh) via eventsToSkip. Sentinel
    // UINT64_MAX (= param default -1) keeps the legacy geometric draw.
    bool fixed_skip_mode = false;
    bool count_only = false;         // consume + count, never corrupt
    uint64_t eligible_count = 0;     // CHAOS_ELIGIBLE_COUNT=<n> at teardown

    // v1.1 Phase 9 patch 1a mode 1 — bitseg field (empty = uniform).
    std::string bitseg;
    // [FSU][D3] Precision + lane geometry. Validated in the constructor;
    // an unknown precision, field or lane configuration panics (fail closed).
    std::string precision;
    int precision_bits = 64;
    int lane_width = 64;
    int lane_offset = 0;
    // [FSU][D3] Reject dynamic candidates whose real decoded precision /
    // element width / lane does not match the manifest. Default false keeps
    // legacy campaigns byte-identical; formal D3 runs enable it.
    bool decode_guard = false;
    uint64_t decode_reject_count = 0;
    std::map<std::string, uint64_t> decode_reject_reasons;
    std::map<std::string, uint64_t> decode_kind_counts;
    // [FSU][FP06] Explicit eligible-stream filters. `opClasses` is a
    // comma-separated allowlist of gem5 OpClass names (empty = every FP
    // opClass this injector already accepted). `regClass` restricts the
    // TARGET destination register class (empty/any = legacy behavior).
    // Unknown names panic in the constructor (fail closed). Both the
    // countOnly census and the injection path use the SAME predicate.
    std::vector<int> op_class_allow;      // empty = no opClass filter
    int required_reg_class = -1;          // -1 = any FP register class
    // Census evidence: eligible events per opClass / regClass. Emitted only
    // in countOnly mode so a gate can prove the filter really narrowed the
    // stream instead of only relabeling it.
    std::map<std::string, uint64_t> eligible_opclass_counts;
    std::map<std::string, uint64_t> eligible_regclass_counts;
    // mode 2 — fma_intermediate weighted proxy (E3).
    bool fma_weighted = false;
    // mode 3 — recurring_result_stuck: same fixed mask every event.
    bool recurring_stuck = false;
    uint64_t recurring_mask = 0;      // drawn once on the first event
    bool recurring_mask_drawn = false;
    // mode 4 — rounding_sub: one-ULP opposite-neighbor nudge.
    bool rounding_sub = false;
    // mode 5 — f3_data_dependent: exponent-window gate.
    bool f3_dependent = false;
    int exp_lo = -1, exp_hi = -1;
    // mode 6 — fpsr_suppress: logged count of cleared-flag events.
    bool fpsr_suppress = false;
    uint64_t suppressed_count = 0;
    // mode 7 — permanent_stuck (F5): install ONE fixed stuck-at fault
    // (one fault_id / fixed mask / fixed SA0-or-SA1 polarity) on the first
    // eligible event after the warm-up, then apply the SAME forced polarity
    // to every later eligible result until the run ends. This is not XOR
    // and not a per-event new fault: the exposure stream shares one
    // fault_id and one L0 install root.
    bool permanent_stuck = false;
    int stuck_polarity = -1;          // -1 = draw once, then fixed; 0/1 = explicit
    uint64_t f5_warmup = 0;           // eligible events before installation
    uint64_t f5_sample_limit = 0;     // ordinary exposure samples (mandatory extra)
    uint64_t f5_keep_first_last_n = 0; // bounded "first N + last N" sample policy
    uint64_t f5_keep_first = 0;       // resolved sample budget: first N
    uint64_t f5_keep_last = 0;        // resolved sample budget: last N

    // [FSU][F5] Installed permanent fault state. Exactly one fault is ever
    // installed per run; every later eligible event is an exposure of it.
    bool f5_armed = false;
    uint64_t f5_fault_id = 0;
    uint64_t f5_install_event = 0;
    uint64_t f5_carrier_event = 0;
    uint64_t f5_fixed_mask = 0;
    int f5_polarity = -1;
    uint64_t f5_first_eligible_sn = 0;
    uint64_t f5_exposures_total = 0;
    uint64_t f5_activated_total = 0;
    uint64_t f5_exposures_sampled = 0;
    uint64_t f5_exposures_dropped = 0;
    uint64_t f5_first_activated_sn = 0;
    Tick f5_first_activated_tick = 0;
    uint64_t f5_last_exposure_sn = 0;
    uint64_t f5_first_impact_sn = 0;
    Tick f5_first_impact_tick = 0;
    uint64_t f5_first_impact_latency = 0;
    bool f5_first_activated_done = false;
    bool f5_taint_registered = false;
    bool f5_commit_seen = false;
    // The terminal chain_end must be written by the tracer's exit callback
    // (before it closes the stream); register the flush hook once at install.
    bool f5_flush_registered = false;
    uint64_t f5_ordinary_emitted = 0;
    uint64_t f5_last_event_id = 0;
    // Identity of the single installation (chain_end is emitted outside any
    // dynamic instruction, so it cannot re-derive these from a DynInst).
    std::string f5_op_class;
    std::string f5_reg_class;
    // Direct parent for the terminal chain_end: the real commit when one
    // happened, else the first activated exposure, else the L1 carrier.
    // Sample-branch events never become the terminal's parent.
    uint64_t f5_terminal_parent = 0;
    // Bounded tail buffer; only the LAST f5_keep_last samples are retained.
    // Flushed by the exit callback, so EVENT_CAP is never silently exceeded.
    std::deque<std::vector<std::pair<std::string, std::string>>>
        f5_last_samples;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    // [FSU] Pilot identity (set from ooo_proxy CLI; empty = not reported).
    std::string fsu_model, fsu_freq, fsu_load, fsu_submodel;
    uint64_t fsu_eligible_total = 0;

    // [FSU][D2] F1/F2/F3 deterministic rate semantics. The driver supplies
    // exact eligible ordinals; the injector matches them 1:1 and never draws
    // a probability/geometric substitute. Empty vector = F0 mode.
    bool rate_mode = false;
    std::vector<uint64_t> rate_ordinals;
    uint64_t rate_warmup = 0;
    uint64_t rate_divisor = 0;
    uint64_t jitter_pct = 0;
    uint64_t eligible_ordinal = 0;   // 1-based count of eligible events
    size_t next_rate_index = 0;
    uint64_t injected_eligible_ordinal = 0;
    uint64_t current_interval = 0;
    uint64_t current_ordinal_index = 0;

    // [FSU] Faulted-result taint. A fault is "activated" only when a real
    // consumer instruction reads the faulted physical register; the root
    // fault_applied event therefore leaves activated empty, and the L2
    // operand_read event carries activated=1.
    struct FaultedReg {
        uint64_t fault_id = 0;
        uint64_t l0_id = 0, l1_id = 0;
        uint64_t producer_sn = 0;
        Tick tick = 0;
        int tid = 0, reg_class = 0, reg_index = 0;
        uint64_t before = 0, after = 0, mask = 0;
        std::string field;
        int precision_bits = 64;
        int lane_width = 64, lane_offset = 0;
        int bit_in_lane = 0, abs_bit = 0;
        int field_lo = -1, field_hi = -1;
        uint64_t abs_lo = 0, abs_hi = 0;
        uint64_t full_before_lo = 0, full_before_hi = 0;
        uint64_t full_after_lo = 0, full_after_hi = 0;
        uint32_t instruction_bits = 0;
        std::string decoded_kind;
        int decoded_precision_bits = 0;
        int decoded_element_width = 0;
        int decoded_lanes = 0;
        bool decoded_reliable = false;
        bool precision_match = false;
        bool lane_match = false;
        bool is_vec = false;
        bool consumed = false;
        std::string op_class;   // gem5 OpClass name of the producer
        // [FSU][F5] The taint belongs to a permanent fault: its terminal is
        // reported by the F5 chain_end (with exposure accounting), never by
        // a generic not_activated event (which would contradict
        // activated_exposure_count > 0).
        bool f5 = false;
    };
    struct TaintedConsumer {
        uint64_t fault_id = 0;
        uint64_t l2_id = 0, l3_id = 0, l4_id = 0;
        uint64_t consumer_sn = 0;
        std::string field;
        int precision_bits = 64;
        int lane_width = 64, lane_offset = 0;
        int bit_in_lane = 0, abs_bit = 0;
        int field_lo = -1, field_hi = -1;
        uint64_t abs_lo = 0, abs_hi = 0;
        uint32_t instruction_bits = 0;
        std::string decoded_kind;
        int decoded_precision_bits = 0;
        int decoded_element_width = 0;
        int decoded_lanes = 0;
        bool decoded_reliable = false;
        bool precision_match = false;
        bool lane_match = false;
        bool is_store = false;
        bool has_l3 = false, has_l4 = false, committed = false;
        std::string op_class;   // gem5 OpClass name of the producer
        std::string reg_class;  // vec | float | vec_elem
    };

    // Everything an injection site needs to describe itself to the chain
    // events. Built once per injected fault so L0-L5 carry identical
    // field/lane provenance.
    struct FaultInfo {
        int reg_class = -1, reg_index = -1;
        uint64_t before = 0, after = 0, mask = 0;
        int precision_bits = 64;
        int lane_width = 64, lane_offset = 0;
        int bit_in_lane = 0, abs_bit = 0;
        int field_lo = -1, field_hi = -1;
        uint64_t abs_lo = 0, abs_hi = 0;
        uint64_t full_before_lo = 0, full_before_hi = 0;
        uint64_t full_after_lo = 0, full_after_hi = 0;
        uint32_t instruction_bits = 0;
        std::string decoded_kind;
        int decoded_precision_bits = 0;
        int decoded_element_width = 0;
        int decoded_lanes = 0;
        bool decoded_reliable = false;
        bool precision_match = false;
        bool lane_match = false;
        bool is_vec = false;
        std::string field;
        std::string op_class;   // gem5 OpClass name of this instruction
    };
    std::vector<FaultedReg> faulted_regs;
    std::map<uint64_t, TaintedConsumer> tainted_consumers;
    uint64_t next_fault_id = 1;

    void noteFaultApplied(o3::DynInst *inst, const FaultInfo &info);
    uint64_t emitFsu(const char *kind, uint64_t fault_id, uint64_t parent,
                     std::vector<std::pair<std::string, std::string>> kv);
    void noteNotActivated();
    void dumpCensus(std::ostream &os) const;
    bool regClassMatches(int cls) const
    {
        return required_reg_class < 0 || cls == required_reg_class;
    }

    // [FSU][F5] Permanent stuck-at path. One install (L0 root + L1 carrier),
    // then one exposure event per eligible event (bounded samples) while the
    // SAME mask/polarity is applied. The first ACTIVATED exposure supplies
    // the L1 parent for the existing L2-L5 taint/consumer/commit machinery,
    // so the real impact chain stays direct and auditable.
    std::vector<std::pair<std::string, std::string>>
    buildF5Kv(o3::DynInst *inst, const FaultInfo &info) const;
    void notePermanentExposure(o3::DynInst *inst, const FaultInfo &info);
    void registerF5Taint(o3::DynInst *inst, const FaultInfo &info,
                         uint64_t parent_event);
    uint64_t emitF5Exposure(
        const std::vector<std::pair<std::string, std::string>> &kv,
        uint64_t parent);
    std::string f5PolicyString() const;
    void flushF5Samples();
    void emitF5ChainEnd();
    static std::string hex64(uint64_t v);
    static std::string hexWidth(uint64_t v, int bits);
    static std::string hex128(uint64_t lo, uint64_t hi);
    static std::string hash64(uint64_t v);

    bool inWindow();
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_FPU_HH__
