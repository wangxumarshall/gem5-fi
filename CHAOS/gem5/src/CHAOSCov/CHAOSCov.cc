/*
 * CHAOSCov — Harpocrates coverage analyzer, skeleton (Task 1.2).
 * See CHAOSCov.hh for the metric definitions and ROI contract.
 */
#include "CHAOSCov/CHAOSCov.hh"
#include "params/CHAOSCov.hh"
#include "cpu/o3/cpu.hh"
#include "base/trace.hh"
#include "debug/CHAOSCov.hh"

#include <fstream>
#include <iomanip>

namespace gem5
{

// --- static ROI state shared with collector hooks (Tasks 2-4) ---
bool CHAOSCov::roi_active = false;
CHAOSCov *CHAOSCov::instance = nullptr;

// Hot-path guard for the inline hooks in cpu/o3/regfile.hh/free_list.hh.
bool harp_enabled = false;

// Global notification hooks (called from sim/pseudo_inst.cc workbegin/end).
// No instance mounted -> no-ops (zero overhead for non-harp runs).
void harp_cov_notify_work_begin() { if (CHAOSCov::instance) CHAOSCov::instance->onWorkBegin(); }
void harp_cov_notify_work_end()   { if (CHAOSCov::instance) CHAOSCov::instance->onWorkEnd(); }

// --- IRF ACE collector hooks (Task 2.1) — see CHAOSCov.hh for semantics ---
bool harp_cov_prf_enabled() { return CHAOSCov::instance != nullptr; }

void harp_cov_on_prf_write(int class_type, int idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->irfOnWrite(class_type, idx); }

void harp_cov_on_prf_read(int class_type, int idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->irfOnRead(class_type, idx); }

void harp_cov_on_prf_alloc(int class_type, int idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->irfOnAlloc(class_type, idx); }

void harp_cov_on_prf_free(int class_type, int idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->irfOnFree(class_type, idx); }

// Per-cycle tick from Commit::tick — drives the ROI cycle counter and the
// IRF occupancy sampling (advice-engine evidence).
void harp_cov_on_cycle()
{
    if (!CHAOSCov::instance) return;
    CHAOSCov::instance->tickROICycles();
    if (CHAOSCov::roiActive())
        CHAOSCov::instance->irfSampleOccupancy();
}

CHAOSCov::CHAOSCov(const CHAOSCovParams &p)
    : SimObject(p),
      cpu(dynamic_cast<o3::CPU *>(p.cpu)),
      roi_begin_cycle(p.roiBeginCycle),
      roi_end_cycle(p.roiEndCycle),
      write_detail(p.writeDetail),
      harpStats(this)
{
    if (!cpu)
        throw std::runtime_error(
            "CHAOSCov: cpu is not an O3CPU — O3-only (IRF/LSQ/IQ hooks)");
    if (p.roiMode == "m5ops")       roi_mode = RoiMode::M5Ops;
    else if (p.roiMode == "cycles") roi_mode = RoiMode::Cycles;
    else                            roi_mode = RoiMode::All;

    if (instance)
        warn("CHAOSCov: multiple instances mounted; the last one wins "
             "(ROI hooks are global)\n");
    instance = this;
    // NOTE: irf_state must be sized BEFORE harp_enabled goes true — the
    // regfile/free_list hooks fire during CPU init (before startup()),
    // and an empty vector would segfault on [idx] (measured).
    // Spaces: [0]=int (64b), [1]=float (legacy 32b-ARM FP; AArch64 FP
    // aliases into [2] vector), [2]=vector/NEON (128b — where AArch64
    // fadd/fmul d-registers actually live, per arch/arm/isa/operands.isa
    // FpDest = VectorElem).
    const unsigned n_int = cpu->physRegFile().numIntPhysRegs();
    const unsigned n_flt = cpu->physRegFile().numFloatPhysRegs();
    const unsigned n_vec = cpu->physRegFile().numVecPhysRegs();
    irf_state[0].assign(n_int, PrfRegState{});
    irf_state[1].assign(n_flt, PrfRegState{});
    irf_state[2].assign(n_vec, PrfRegState{});
    irf_occ_hist.assign(OCC_BUCKETS, 0);
    harp_enabled = true;

    if (roi_mode == RoiMode::All)
        roi_active = true;
}

CHAOSCov::~CHAOSCov()
{
    if (instance == this) {
        instance = nullptr;
        harp_enabled = false;
    }
}

void
CHAOSCov::onWorkBegin()
{
    if (roi_mode != RoiMode::M5Ops)
        return;
    assert(!roi_active);
    roi_active = true;
    harpStats.roiBeginTick = curTick();
    DPRINTF(CHAOSCov, "ROI begin @ tick %llu\n", (unsigned long long)curTick());
}

void
CHAOSCov::onWorkEnd()
{
    if (roi_mode != RoiMode::M5Ops)
        return;
    // Marker pair seen; close the window. (Re-open supported: harp_wrap
    // emits exactly one pair, but keep it robust for multi-ROI workloads.)
    roi_active = false;
    irfFinish();
    harpStats.roiEndTick = curTick();
    harpStats.roiCycles = roi_cycles;
    harpStats.irfIntAceCycles = irf_ace_cycles[0];
    harpStats.irfFloatAceCycles = irf_ace_cycles[1];
    harpStats.irfVecAceCycles = irf_ace_cycles[2];
    // AVF per the paper's definition: ACE cycles summed over all bits of
    // the structure / (total bits * exposure window). Computed per-reg
    // with widths: int/float 64b, vector 128b (NEON) — the weighted form
    // is the literal paper formula; the unweighted per-slot variant is
    // dominated by the same numerator/denominator scaling, so we report
    // the width-weighted AVF as the primary metric.
    const double w[3] = {64.0, 64.0, 128.0};
    double bits_total = 0, bits_ace = 0;
    for (int c = 0; c < 3; c++) {
        bits_total += (double)irf_state[c].size() * w[c] * roi_cycles;
        bits_ace += (double)irf_ace_cycles[c] * w[c];
    }
    if (roi_cycles > 0 && bits_total > 0) {
        harpStats.irfAvf = bits_ace / bits_total;
        harpStats.irfAvfInt =
            (double)irf_ace_cycles[0] * w[0]
            / ((double)irf_state[0].size() * w[0] * roi_cycles);
        harpStats.irfAvfFloat =
            irf_state[1].size()
                ? (double)irf_ace_cycles[1] * w[1]
                      / ((double)irf_state[1].size() * w[1] * roi_cycles)
                : 0.0;
        harpStats.irfAvfVec =
            irf_state[2].size()
                ? (double)irf_ace_cycles[2] * w[2]
                      / ((double)irf_state[2].size() * w[2] * roi_cycles)
                : 0.0;
    }
    DPRINTF(CHAOSCov, "ROI end @ tick %llu (roi_cycles=%llu)\n",
            (unsigned long long)curTick(), (unsigned long long)roi_cycles);
    if (detail_stream && detail_stream->stream()) {
        auto &os = *(detail_stream->stream());
        os << "# workend @ tick " << curTick()
           << " roi_cycles " << roi_cycles << "\n";
        // IRF detail block (advice-engine evidence)
        os << "irf int_regs " << irf_state[0].size()
           << " float_regs " << irf_state[1].size()
           << " vec_regs " << irf_state[2].size() << "\n";
        os << "irf int_ace_cycles " << irf_ace_cycles[0]
           << " float_ace_cycles " << irf_ace_cycles[1]
           << " vec_ace_cycles " << irf_ace_cycles[2] << "\n";
        os << "irf live_at_end int " << irf_live_regs[0]
           << " float " << irf_live_regs[1]
           << " vec " << irf_live_regs[2] << "\n";
        os << "irf occupancy_hist (bucket=live/8)";
        for (auto b : irf_occ_hist) os << " " << b;
        os << "\n";
    }
}

// ---------------------------------------------------------------------------
// IRF ACE collector (Task 2.1, optimistic mode)
// ---------------------------------------------------------------------------
// Cycle-granularity: all events use cpu->curCycle() (== roi_cycles clock).
// The interval accounting is exactly the paper's Fig.3 semantics adapted to
// a rename-based PRF: a phys slot's value is ACE from write until its last
// read; idle time after the last read (until free/overwrite) is un-ACE.

void
CHAOSCov::irfOnWrite(int class_type, int idx)
{
    if (!roi_active) return;
    auto &st = irf_state[class_type][idx];
    const uint64_t now = roi_cycles;
    // Close the previous value's interval: if it was read at least once,
    // its ACE contribution [birth, last_read] has already been accumulated
    // incrementally at each read (see irfOnRead); if never read, it
    // contributes nothing (write→write overwrite = un-ACE).
    // Start the new value's interval.
    st.birth = now;
    st.last_read = now;
    st.has_value = true;
    st.ever_read = false;
}

void
CHAOSCov::irfOnRead(int class_type, int idx)
{
    if (!roi_active) return;
    auto &st = irf_state[class_type][idx];
    if (!st.has_value) return;    // read of a slot with no ROI value (e.g.
                                  // value written before ROI): treat the
                                  // readable residency as ACE from ROI start
    const uint64_t now = roi_cycles;
    if (!st.ever_read) {
        // First read: accumulate [birth, now] (write→read interval).
        irf_ace_cycles[class_type] += now - st.birth;
        st.ever_read = true;
    } else {
        // read→read: extend to now.
        irf_ace_cycles[class_type] += now - st.last_read;
    }
    st.last_read = now;
}

void
CHAOSCov::irfOnAlloc(int class_type, int idx)
{
    // Allocation itself is un-ACE (free-list residency). Nothing to do:
    // the interval only starts at write. Reset stale state defensively.
    auto &st = irf_state[class_type][idx];
    st.has_value = false;
    st.ever_read = false;
}

void
CHAOSCov::irfOnFree(int class_type, int idx)
{
    // Freeing closes any open interval; unread tail (last_read..free) is
    // un-ACE and was never accumulated. has_value=false stops future reads.
    auto &st = irf_state[class_type][idx];
    st.has_value = false;
}

void
CHAOSCov::irfFinish()
{
    // ROI end: values still open with reads (read→ROI-end tail is un-ACE —
    // the paper's analysis stops at the last confirmed use). Nothing to
    // add; just count how many intervals were live for the detail dump.
    for (int c = 0; c < 3; c++) {
        irf_live_regs[c] = 0;
        for (auto &st : irf_state[c])
            if (st.has_value) irf_live_regs[c]++;
    }
}

void
CHAOSCov::irfSampleOccupancy()
{
    // Advice-engine evidence: histogram of live-value registers per cycle.
    unsigned live = 0;
    for (int c = 0; c < 3; c++)
        for (auto &st : irf_state[c])
            if (st.has_value) live++;
    unsigned bucket = std::min<unsigned>(live / 8, OCC_BUCKETS - 1);
    irf_occ_hist[bucket]++;
    irf_occ_samples++;
}

CHAOSCov::HarpStats::HarpStats(statistics::Group *parent)
    : statistics::Group(parent, "harp"),
      ADD_STAT(roiCycles, statistics::units::Cycle::get(),
               "Cycles inside the ROI window"),
      ADD_STAT(roiBeginTick, statistics::units::Tick::get(),
               "Tick of the first workbegin marker (m5ops ROI mode)"),
      ADD_STAT(roiEndTick, statistics::units::Tick::get(),
               "Tick of the workend marker (m5ops ROI mode)"),
      ADD_STAT(irfIntAceCycles, statistics::units::Cycle::get(),
               "IRF ACE cycles accumulated over int phys regs (optimistic)"),
      ADD_STAT(irfFloatAceCycles, statistics::units::Cycle::get(),
               "IRF ACE cycles accumulated over float phys regs (optimistic)"),
      ADD_STAT(irfVecAceCycles, statistics::units::Cycle::get(),
               "IRF ACE cycles accumulated over vector phys regs (optimistic) —"
               " AArch64 FP/SIMD regs live here"),
      ADD_STAT(irfAvf, statistics::units::Ratio::get(),
               "IRF AVF = (int+float ACE cycles) / ((int+float regs) * ROI "
               "cycles). Paper: ACE lifetime analysis (upper bound of "
               "transient-fault detection)"),
      ADD_STAT(irfAvfInt, statistics::units::Ratio::get(),
               "IRF AVF, int space"),
      ADD_STAT(irfAvfFloat, statistics::units::Ratio::get(),
               "IRF AVF, float space"),
      ADD_STAT(irfAvfVec, statistics::units::Ratio::get(),
               "IRF AVF, vector space (AArch64 FP/SIMD)")
{
}

void
CHAOSCov::startup()
{
    if (write_detail) {
        detail_stream = simout.create("harp_cov_detail.log", false, true);
        if (!detail_stream || !detail_stream->stream())
            panic("CHAOSCov: could not open harp_cov_detail.log");
    }
    DPRINTF(CHAOSCov, "CHAOSCov started, roiMode=%d, intRegs=%zu fltRegs=%zu\n",
            (int)roi_mode, irf_state[0].size(), irf_state[1].size());
}

} // namespace gem5
