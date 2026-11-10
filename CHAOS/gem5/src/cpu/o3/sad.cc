#include "cpu/o3/sad.hh"

#include <algorithm>
#include <set>

#include "base/logging.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/fu_pool.hh"
#include "cpu/o3/inst_queue.hh"
#include "params/BaseO3CPU.hh"

namespace gem5 { namespace o3 {

SADTracker::SADTracker(CPU *_cpu, const BaseO3CPUParams &params)
    : cpu(_cpu), enabled(params.sad),
      useWorkItems(params.sadUseWorkItems), workId(params.sadWorkItemId),
      startCycle(params.sadStartCycle), endCycle(params.sadEndCycle),
      issueWidth(params.issueWidth), stats(*this, _cpu)
{
    capacities[Rob] = params.numROBEntries;
    capacities[LoadQueue] = params.LQEntries;
    capacities[StoreQueue] = params.SQEntries;
    capacities[IntPrf] = params.numPhysIntRegs;
    capacities[VecPrf] = params.numPhysVecRegs;

    std::set<FUPool *> seen;
    for (auto *iq : params.instQueues) {
        capacities[Iq] += iq->numEntries();
        auto *pool = iq->fuPool();
        if (seen.insert(pool).second) {
            fuPools.push_back(pool);
            fuUnitCount += pool->numUnits();
        }
    }
    capacities[Fu] = fuUnitCount;

    fatal_if(enabled && !useWorkItems && endCycle && endCycle <= startCycle,
             "sadEndCycle must be greater than sadStartCycle");
    fatal_if(enabled && issueWidth == 0,
             "sad requires a non-zero issue width");
}

uint64_t
SADTracker::currentCycle() const
{
    return static_cast<uint64_t>(cpu->curCycle());
}

bool
SADTracker::selected(uint64_t id) const
{
    return workId < 0 || static_cast<uint64_t>(workId) == id;
}

bool
SADTracker::cycleWindowActive(uint64_t cycle) const
{
    return cycle >= std::max(startCycle, resetCycle) &&
           (endCycle == 0 || cycle < endCycle);
}

void
SADTracker::recordIssue()
{
    if (!enabled)
        return;
    const uint64_t cycle = currentCycle();
    if (useWorkItems ? !active : !cycleWindowActive(cycle))
        return;
    ++cycleIssuedOps;
}

void
SADTracker::tick()
{
    if (!enabled)
        return;
    const uint64_t cycle = currentCycle();
    if (useWorkItems ? !active : !cycleWindowActive(cycle))
        return;
    sample();
}

void
SADTracker::sample()
{
    const auto used_from_free = [](unsigned capacity, unsigned free) {
        return free < capacity ? capacity - free : 0U;
    };
    usedSum[Rob] += cpu->sadRobUsed();
    usedSum[Iq] += used_from_free(capacities[Iq], cpu->sadIqFreeEntries());
    usedSum[LoadQueue] += used_from_free(
        capacities[LoadQueue], cpu->sadLoadQueueFreeEntries());
    usedSum[StoreQueue] += used_from_free(
        capacities[StoreQueue], cpu->sadStoreQueueFreeEntries());
    usedSum[IntPrf] += used_from_free(
        capacities[IntPrf], cpu->sadIntPrfFreeEntries());
    usedSum[VecPrf] += used_from_free(
        capacities[VecPrf], cpu->sadVecPrfFreeEntries());
    usedSum[Fu] += cpu->sadFuBusy();
    issuedOps += cycleIssuedOps;
    cycleIssuedOps = 0;
    ++samples;
}

void
SADTracker::workItemBegin(uint64_t id)
{
    if (!enabled || !useWorkItems || started || !selected(id))
        return;
    started = active = true;
    activeWorkId = id;
    windowStart = currentCycle();
    ++windowBegins;
}

void
SADTracker::workItemEnd(uint64_t id)
{
    if (!enabled || !useWorkItems || !active || id != activeWorkId)
        return;
    active = false;
    complete = true;
    windowEnd = currentCycle();
    cycleIssuedOps = 0;
    ++windowEnds;
}

void
SADTracker::resetTracking()
{
    const bool preserve = useWorkItems && active;
    const uint64_t now = currentCycle();

    usedSum.fill(0);
    samples = 0;
    issuedOps = 0;
    cycleIssuedOps = 0;
    windowBegins = 0;
    windowEnds = 0;
    resetCycle = now;
    complete = false;
    if (!preserve) {
        started = false;
        active = false;
        activeWorkId = 0;
        windowStart = 0;
        windowEnd = 0;
    } else {
        windowStart = now;
        windowBegins = 1;
    }
}

double
SADTracker::ratio(Resource resource) const
{
    if (!enabled || samples == 0 || capacities[resource] == 0)
        return 0.0;
    const long double denominator = static_cast<long double>(samples) *
        capacities[resource];
    return static_cast<double>(usedSum[resource] / denominator);
}

double
SADTracker::issueRatio() const
{
    if (!enabled || samples == 0 || issueWidth == 0)
        return 0.0;
    const long double denominator =
        static_cast<long double>(samples) * issueWidth;
    return static_cast<double>(issuedOps / denominator);
}

SADTracker::Stats::Stats(SADTracker &t, CPU *cpu)
    : statistics::Group(cpu, "sad"), tracker(t),
      ADD_STAT(samples, statistics::units::Cycle::get(),
               "Cycles sampled inside the SAD ROI"),
      ADD_STAT(issueWidth, statistics::units::Count::get(),
               "Configured O3 issue width used as the issue-slot capacity"),
      ADD_STAT(issuedOps, statistics::units::Count::get(),
               "Instructions issued inside the SAD ROI"),
      ADD_STAT(issueRatio, statistics::units::Ratio::get(),
               "Issue-width slots used / (samples * issue width)"),
      ADD_STAT(measuredCycles, statistics::units::Cycle::get(),
               "Alias of samples, kept consistent with ACE/IBR reporting"),
      ADD_STAT(windowBegins, statistics::units::Count::get(),
               "Selected work-item windows started"),
      ADD_STAT(windowEnds, statistics::units::Count::get(),
               "Selected work-item windows completed"),
      ADD_STAT(usedSum, statistics::units::Count::get(),
               "Sum of used resource entries over sampled cycles"),
      ADD_STAT(capacity, statistics::units::Count::get(),
               "Resource capacity used as the SAD denominator"),
      ADD_STAT(ratio, statistics::units::Ratio::get(),
               "SAD(s) = usedSum / (samples * capacity)")
{
    for (auto *v : {&usedSum, &capacity, &ratio}) {
        v->init(NumResources);
        for (unsigned i = 0; i < NumResources; ++i)
            v->subname(i, resourceNames[i]);
    }
    ratio.precision(8);
    issueRatio.precision(8);
    samples.functor([this]() { return tracker.samples; });
    issueWidth.functor([this]() { return tracker.issueWidth; });
    issuedOps.functor([this]() { return tracker.issuedOps; });
    issueRatio.functor([this]() { return tracker.issueRatio(); });
    measuredCycles.functor([this]() { return tracker.samples; });
    windowBegins.functor([this]() { return tracker.windowBegins; });
    windowEnds.functor([this]() { return tracker.windowEnds; });
}

void
SADTracker::Stats::preDumpStats()
{
    statistics::Group::preDumpStats();
    for (unsigned i = 0; i < NumResources; ++i) {
        usedSum[i] = tracker.usedSum[i];
        capacity[i] = tracker.capacities[i];
        ratio[i] = tracker.ratio(static_cast<Resource>(i));
    }
}

void
SADTracker::Stats::resetStats()
{
    tracker.resetTracking();
    statistics::Group::resetStats();
}

} } // namespace gem5::o3
