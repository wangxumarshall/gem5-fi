#ifndef __CPU_O3_CHAOS_PROPAGATION_CONSUMER_SUMMARY_HH__
#define __CPU_O3_CHAOS_PROPAGATION_CONSUMER_SUMMARY_HH__

// [MDSPEC][R6-FIXCPP] T04 `consumer_summary` aggregation — the C++ half of the
// R6-FIXTOOLS contract (tools/lsu_prop_fields.py SUMMARY_* / lsu_chain_check.py
// GATE_VIOLATIONS, commit 4c74e3ac).
//
// User ruling (2026-10-24): **semantic state changes are preserved in full;
// repeated consumers are aggregated with accounted bookkeeping; a plain
// truncation is forbidden.** One fault chain can feed the SAME polluted value
// to a huge number of consumers (the same taint source consumed over and over
// — "同一 dyn_inst_seq 反复命中，或同一状态的重复消费"), and writing each one
// out floods the stream with no information gain. So the emitter folds the
// REPEATED consumptions of one taint source into one CONSUMER-SUMMARY record,
// while every semantic state change still goes out as its own PROP-EVT:
// a NEW taint source (`inj` / `taint_reg` / a first consumer of another
// source), a Cache/MSHR state change, a `request_fork` bridge, the
// `errant_commit` detection, an explicit containment, and the `chain_end`
// terminus — none of which are ever aggregated. The group's FIRST member is
// emitted (the representative the chain checker anchors its L4 witness on);
// every LATER member of the same (fault_id, source_id) is a repeated
// consumption of the same polluted state and is folded, its dyn_inst_seq
// still counted in distinct_dyn_seq_count (that field's whole point: how many
// distinct instructions consumed this source).
//
// The emitted record (field order frozen by the tools lane):
//   CONSUMER-SUMMARY: schema=1 version=1 run_id=… sample_run_id=… fault_id=…
//     source_id=… suppressed_consumer_count=… distinct_dyn_seq_count=…
//     emitted_consumer_count=… first_tick=… last_tick=… min_dyn_seq=…
//     max_dyn_seq=… by_kind=<k:n,…> by_outcome=<k:n,…> total_before=…
//     total_after=…
// Conservation (validated LOUDLY by validate_consumer_summary):
//   total_before == total_after == emitted_consumer_count + suppressed_consumer_count
//   sum(by_kind) == sum(by_outcome) == total_before
//   total_before > 0  =>  emitted_consumer_count >= 1  (never "suppress all")
//
// The record is NOT a PROP-EVT: it carries no kind/event_id, maps to no L0-L5
// layer, and never becomes a chain/containment/terminal node — the checker keeps
// the identical path/terminal/admitted verdict whether or not a summary is
// present (rule ⑤).
//
// This header is dependency-free on purpose (same pattern as
// chaos_lsu_trigger.hh / chaos_tlb_chain.hh / chaos_lsu_tier_cap.hh):
// CHAOSPropagation.cc (inside the gem5 build) and the standalone unit test
// (tests/chaos_consumer_summary_test.cc, plain g++) share THIS ONE definition,
// so the aggregation under test is the aggregation that runs.

#include <cstdint>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace gem5
{
namespace chaos_consumer
{

// The ONE kind that may be aggregated. Everything else — inj, addr_form,
// mem_req, resp, taint_reg, errant_commit, chain_end, request_fork bridges,
// squash/containment markers, and every TLB / Cache / MSHR state event — is a
// semantic state change, a hierarchical-unique witness, or a detection /
// terminal / lifecycle event, and MUST always be emitted individually.
inline bool
aggregatableKind(const std::string &kind)
{
    return kind == "consumer";
}

// The taint-source identity a consumer group is keyed on. Matches the tools'
// fixture vocabulary (`source_id=phys_reg:31`).
inline std::string
sourceIdOf(uint32_t phys_index)
{
    return "phys_reg:" + std::to_string(phys_index);
}

// The outcome label carried by a consumer-summary's by_outcome map (a consumer
// that consumed a fault-delivered value = silent-data propagation observed).
static constexpr const char *CONSUMER_OUTCOME = "sd_observed";

struct Group
{
    uint64_t ptag = 0;
    std::string source_id;
    uint64_t emitted = 0;        // members emitted as their own PROP-EVT
    uint64_t suppressed = 0;     // repeated members folded into the summary
    std::set<uint64_t> dyn_seqs;         // every distinct dyn_inst_seq seen
    uint64_t first_tick = 0, last_tick = 0;
    uint64_t min_dyn = 0, max_dyn = 0;
    bool have_dyn = false;
    uint64_t representative_event = 0;   // event_id of the first emitted member
};

class Aggregator
{
  public:
    // A GENEROUS bound on the number of tracked groups. It exists only to keep
    // memory finite; it is NOT a silent evidence cap. When it is hit the
    // aggregator sets resourceAborted() and STOPS suppressing — every further
    // consumer is emitted, so nothing is dropped — and the emitter records the
    // abort LOUDLY (never a silent truncation read as complete evidence).
    static constexpr uint64_t MAX_GROUPS = 1ull << 20;   // 1,048,576

    // Observe one freshly committed consumer.
    // Returns true  => the caller MUST emit it as its own PROP-EVT (the group's
    //                  FIRST member = the representative).
    // Returns false => the caller must NOT emit it; it is a repeated
    //                  consumption of an already-accounted source and is folded
    //                  into the group's summary accounting.
    // A non-aggregatable kind ALWAYS returns true (never aggregated): this is
    // the L5 / containment / terminal guarantee.
    bool
    observe(const std::string &kind, uint64_t ptag,
            const std::string &source_id, uint64_t dyn_seq, uint64_t tick)
    {
        if (!aggregatableKind(kind))
            return true;                 // never aggregate a non-consumer
        auto it = groups_.find({ptag, source_id});
        if (it == groups_.end()) {
            if (groups_.size() >= MAX_GROUPS) {
                // Resource limit hit: refuse to grow, refuse to suppress.
                aborted_ = true;
                return true;             // emit — never silently drop
            }
            it = groups_.emplace(std::make_pair(ptag, source_id), Group())
                     .first;
            it->second.ptag = ptag;
            it->second.source_id = source_id;
        }
        Group &g = it->second;
        noteDyn(g, dyn_seq, tick);       // counts EVERY member (incl. folded)
        if (g.emitted == 0) {
            ++g.emitted;                 // the representative goes out as-is
            return true;
        }
        ++g.suppressed;                  // repeated consumption: fold in
        return false;
    }

    // Tell the aggregator the event_id of the member just emitted for this
    // group (so a suppressed member can name the group's representative as its
    // taint parent — the DAG stays connected).
    void
    noteEmitted(const std::string &kind, uint64_t ptag,
                const std::string &source_id, uint64_t event_id)
    {
        if (!aggregatableKind(kind))
            return;
        auto it = groups_.find({ptag, source_id});
        if (it == groups_.end())
            return;
        if (it->second.representative_event == 0)
            it->second.representative_event = event_id;
    }

    // The group's representative event id (0 when nothing was emitted yet).
    uint64_t
    representativeEvent(const std::string &kind, uint64_t ptag,
                        const std::string &source_id) const
    {
        if (!aggregatableKind(kind))
            return 0;
        auto it = groups_.find({ptag, source_id});
        return it == groups_.end() ? 0 : it->second.representative_event;
    }

    bool resourceAborted() const { return aborted_; }

    uint64_t emittedTotal() const
    {
        uint64_t n = 0;
        for (const auto &kv : groups_) n += kv.second.emitted;
        return n;
    }
    uint64_t suppressedTotal() const
    {
        uint64_t n = 0;
        for (const auto &kv : groups_) n += kv.second.suppressed;
        return n;
    }
    uint64_t groupCount() const { return groups_.size(); }
    // Groups that actually aggregated something (emitted a summary).
    uint64_t summaryCount() const
    {
        uint64_t n = 0;
        for (const auto &kv : groups_)
            if (kv.second.suppressed > 0) ++n;
        return n;
    }

    // Serialize every group that suppressed at least one duplicate into one
    // CONSUMER-SUMMARY line (field order frozen by the tools lane). Groups with
    // no duplicates produce nothing (the honest "no aggregation" case).
    std::vector<std::string>
    flush(const std::string &run_id, const std::string &sample_run_id) const
    {
        std::vector<std::string> out;
        for (const auto &kv : groups_) {
            if (kv.second.suppressed == 0)
                continue;
            out.push_back(summaryLine(kv.second, run_id, sample_run_id));
        }
        return out;
    }

    static std::string
    summaryLine(const Group &g, const std::string &run_id,
                const std::string &sample_run_id)
    {
        const uint64_t total = g.emitted + g.suppressed;
        // Conservation is enforced where the record is BUILT: a group with
        // members always has an emitted representative, so emitted >= 1.
        std::string s = "CONSUMER-SUMMARY:";
        s += " schema=1";
        s += " version=1";
        s += " run_id=" + run_id;
        s += " sample_run_id=" + sample_run_id;
        s += " fault_id=" + std::to_string(g.ptag);
        s += " source_id=" + g.source_id;
        s += " suppressed_consumer_count=" + std::to_string(g.suppressed);
        s += " distinct_dyn_seq_count=" + std::to_string(g.dyn_seqs.size());
        s += " emitted_consumer_count=" + std::to_string(g.emitted);
        s += " first_tick=" + std::to_string(g.first_tick);
        s += " last_tick=" + std::to_string(g.last_tick);
        s += " min_dyn_seq=" + std::to_string(g.min_dyn);
        s += " max_dyn_seq=" + std::to_string(g.max_dyn);
        s += " by_kind=consumer:" + std::to_string(total);
        s += " by_outcome=" + std::string(CONSUMER_OUTCOME) + ":"
             + std::to_string(total);
        s += " total_before=" + std::to_string(total);
        s += " total_after=" + std::to_string(total);
        return s;
    }

    // The LOUD marker written when the resource bound is hit. It is NOT a
    // CONSUMER-SUMMARY (a different prefix) so it never masquerades as
    // accounting; the emitter prints it to stdout and into the stream so the
    // abort is visible, never silent.
    static std::string
    resourceAbortLine(uint64_t groups)
    {
        return "CONSUMER-SUMMARY-ABORT: reason=resource_limit groups="
             + std::to_string(groups) + " max_groups="
             + std::to_string(MAX_GROUPS)
             + " suppressed=0 (every consumer emitted; admission must be "
               "refused, evidence is NOT silently truncated)";
    }

  private:
    static void
    noteDyn(Group &g, uint64_t dyn_seq, uint64_t tick)
    {
        g.dyn_seqs.insert(dyn_seq);
        if (!g.have_dyn) {
            g.have_dyn = true;
            g.min_dyn = g.max_dyn = dyn_seq;
            g.first_tick = g.last_tick = tick;
        } else {
            if (dyn_seq < g.min_dyn) g.min_dyn = dyn_seq;
            if (dyn_seq > g.max_dyn) g.max_dyn = dyn_seq;
            if (tick < g.first_tick) g.first_tick = tick;
            if (tick > g.last_tick) g.last_tick = tick;
        }
    }

    std::map<std::pair<uint64_t, std::string>, Group> groups_;
    bool aborted_ = false;
};

}  // namespace chaos_consumer
}  // namespace gem5

#endif // __CPU_O3_CHAOS_PROPAGATION_CONSUMER_SUMMARY_HH__
