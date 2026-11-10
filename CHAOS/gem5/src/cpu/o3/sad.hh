#ifndef __CPU_O3_SAD_HH__
#define __CPU_O3_SAD_HH__

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

#include "base/statistics.hh"
#include "cpu/static_inst.hh"

namespace gem5
{
struct BaseO3CPUParams;
namespace o3
{
class CPU;
class FUPool;

/**
 * Structure Activation Depth (SAD) for the O3 pipeline.
 *
 * SAD(s) = sum_over_sampled_cycles used_s(cycle) /
 *          (samples * capacity_s)
 *
 * The tile-level definition in the route document uses "pipeline resources x
 * occupancy time"; gem5 cannot see gates, so this implementation samples the
 * O3 resources it can actually observe at the end of every cycle: ROB slots,
 * instruction-queue slots, load/store queue slots, integer and vector physical
 * registers, busy execution units, and issue-width slots. Each ratio is in
 * [0, 1] for a sane single-threaded run.
 *
 * Sampling and reset follow the ACE/IBR work-item rules: a selected ROI is
 * preserved across the standard stats reset, the begin cycle is sampled, and
 * the end cycle is the exclusive boundary.
 */
class SADTracker
{
  public:
    SADTracker(CPU *cpu, const BaseO3CPUParams &params);

    void recordIssue();
    void tick();
    void workItemBegin(uint64_t id);
    void workItemEnd(uint64_t id);
    void resetTracking();

  private:
    enum Resource : unsigned
    {
        Rob = 0,
        Iq,
        LoadQueue,
        StoreQueue,
        IntPrf,
        VecPrf,
        Fu,
        NumResources
    };

    static constexpr std::array<const char *, NumResources> resourceNames = {
        "rob", "iq", "lq", "sq", "intPrf", "vecPrf", "fu"};

    uint64_t currentCycle() const;
    bool cycleWindowActive(uint64_t cycle) const;
    bool selected(uint64_t id) const;
    void sample();
    double ratio(Resource resource) const;
    double issueRatio() const;

    CPU *cpu;
    const bool enabled;
    const bool useWorkItems;
    const int64_t workId;
    const uint64_t startCycle;
    const uint64_t endCycle;
    const unsigned issueWidth;
    std::array<unsigned, NumResources> capacities{};
    std::vector<FUPool *> fuPools;
    std::size_t fuUnitCount = 0;

    uint64_t resetCycle = 0;
    uint64_t windowStart = 0;
    uint64_t windowEnd = 0;
    uint64_t activeWorkId = 0;
    bool started = false;
    bool active = false;
    bool complete = false;

    uint64_t windowBegins = 0;
    uint64_t windowEnds = 0;
    uint64_t samples = 0;
    uint64_t issuedOps = 0;
    uint64_t cycleIssuedOps = 0;
    std::array<uint64_t, NumResources> usedSum{};

    struct Stats : statistics::Group
    {
        Stats(SADTracker &tracker, CPU *cpu);
        void resetStats() override;
        void preDumpStats() override;

        SADTracker &tracker;
        statistics::Value samples;
        statistics::Value issueWidth;
        statistics::Value issuedOps;
        statistics::Value issueRatio;
        statistics::Value measuredCycles;
        statistics::Value windowBegins;
        statistics::Value windowEnds;
        statistics::Vector usedSum;
        statistics::Vector capacity;
        statistics::Vector ratio;
    } stats;
};

} // namespace o3
} // namespace gem5

#endif // __CPU_O3_SAD_HH__
