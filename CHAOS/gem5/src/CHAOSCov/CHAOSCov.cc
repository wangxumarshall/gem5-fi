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

// Global notification hooks (called from sim/pseudo_inst.cc workbegin/end).
// No instance mounted -> no-ops (zero overhead for non-harp runs).
void harp_cov_notify_work_begin() { if (CHAOSCov::instance) CHAOSCov::instance->onWorkBegin(); }
void harp_cov_notify_work_end()   { if (CHAOSCov::instance) CHAOSCov::instance->onWorkEnd(); }

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

    if (roi_mode == RoiMode::All)
        roi_active = true;
}

CHAOSCov::~CHAOSCov()
{
    if (instance == this)
        instance = nullptr;
}

void
CHAOSCov::startup()
{
    if (write_detail) {
        detail_stream = simout.create("harp_cov_detail.log", false, true);
        if (!detail_stream || !detail_stream->stream())
            panic("CHAOSCov: could not open harp_cov_detail.log");
    }
    DPRINTF(CHAOSCov, "CHAOSCov started, roiMode=%d\n", (int)roi_mode);
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
    harpStats.roiEndTick = curTick();
    harpStats.roiCycles = roi_cycles;
    DPRINTF(CHAOSCov, "ROI end @ tick %llu (roi_cycles=%llu)\n",
            (unsigned long long)curTick(), (unsigned long long)roi_cycles);
    if (detail_stream && detail_stream->stream())
        *(detail_stream->stream())
            << "# workend @ tick " << curTick()
            << " roi_cycles " << roi_cycles << "\n";
}

CHAOSCov::HarpStats::HarpStats(statistics::Group *parent)
    : statistics::Group(parent, "harp"),
      ADD_STAT(roiCycles, statistics::units::Cycle::get(),
               "Cycles inside the ROI window"),
      ADD_STAT(roiBeginTick, statistics::units::Tick::get(),
               "Tick of the first workbegin marker (m5ops ROI mode)"),
      ADD_STAT(roiEndTick, statistics::units::Tick::get(),
               "Tick of the workend marker (m5ops ROI mode)")
{
}

} // namespace gem5
