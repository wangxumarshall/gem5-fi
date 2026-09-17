/*
 * CHAOSCov — single-run hardware coverage instrumentation for the
 * Harpocrates reproduction (harp plan Task 1.2; metrics per ISCA'24 §II-D).
 *
 * Two coverage families (definitions mirror the paper exactly):
 *   ACE lifetime (bit arrays: IRF, L1D, LSQ): ACE cycles / total ROI cycles
 *     summed over all bits, i.e. AVF. Upper bound of transient-fault
 *     detection capability.
 *   IBR (functional units): effective input bits delivered to the unit /
 *     theoretical max (full-width inputs at every ROI cycle). Correlates
 *     with (does not bound) permanent gate-level fault detection.
 *
 * ROI gating: m5ops workbegin/workend markers (inserted by tools/harp_wrap.py)
 * flip roi_active. Collection hooks short-circuit when !roi_active.
 * The pseudo_inst.cc side calls harp_cov_notify_work_begin/end() (weak
 * default no-op in CHAOSCov.cc; CHAOSCov registers itself there).
 *
 * This skeleton registers stats + detail dump; per-structure collectors
 * arrive in plan Tasks 2.x/3.x/4.1.
 */
#ifndef __CHAOS_COV_CHAOSCOV_HH__
#define __CHAOS_COV_CHAOSCOV_HH__

#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"

#include <cstdint>
#include <string>

namespace gem5
{

class CHAOSCovParams;
namespace o3 { class CPU; }

// Global ROI notification hooks called from sim/pseudo_inst.cc.
// Defined in CHAOSCov.cc; when no CHAOSCov instance exists they are no-ops.
void harp_cov_notify_work_begin();
void harp_cov_notify_work_end();

class CHAOSCov : public SimObject
{
  public:
    CHAOSCov(const CHAOSCovParams &p);
    ~CHAOSCov() override;
    void startup() override;

    // ROI state (also read by collector hooks in later tasks)
    static bool roiActive() { return roi_active; }

    // Single-instance pointer (read by the global notify hooks below).
    static CHAOSCov *instance;

    // Notification from the global hooks (pseudo_inst workbegin/workend).
    void onWorkBegin();
    void onWorkEnd();

    // Per-cycle poll from collectors (cycle-granular ROI bookkeeping).
    void tickROICycles() { if (roi_active) roi_cycles++; }

    uint64_t roiCycles() const { return roi_cycles; }

  private:
    o3::CPU *cpu;
    enum class RoiMode { M5Ops, Cycles, All };
    RoiMode roi_mode;
    uint64_t roi_begin_cycle, roi_end_cycle;
    bool write_detail;

    static bool roi_active;         // set/cleared by hooks (or cycle mode)
    uint64_t roi_cycles = 0;

    OutputStream *detail_stream = nullptr;

  protected:
    struct HarpStats : public statistics::Group
    {
        HarpStats(statistics::Group *parent);
        // --- ROI bookkeeping ---
        statistics::Scalar roiCycles;
        statistics::Scalar roiBeginTick;
        statistics::Scalar roiEndTick;
        // --- structure coverage stats (filled by Tasks 2-4 collectors) ---
    } harpStats;
};

} // namespace gem5

#endif // __CHAOS_COV_CHAOSCOV_HH__
