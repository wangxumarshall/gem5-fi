#include "mem/cache/l1_ace.hh"

#include <algorithm>
#include <limits>
#include <vector>

#include "base/logging.hh"
#include "mem/cache/base.hh"
#include "sim/system.hh"

namespace gem5
{

namespace
{

std::vector<L1AceTracker *> trackers;

uint64_t
saturatingMultiply(uint64_t lhs, uint64_t rhs)
{
    if (rhs != 0 && lhs > std::numeric_limits<uint64_t>::max() / rhs)
        return std::numeric_limits<uint64_t>::max();
    return lhs * rhs;
}

} // anonymous namespace

L1AceTracker::L1AceTracker(
        BaseCache *_cache, System *_system, bool enable, bool use_work_items,
        int64_t work_item_id, uint64_t start_cycle, uint64_t end_cycle,
        uint64_t cache_size_bytes, unsigned block_size_bytes)
    : cache(_cache), system(_system), trackingEnabled(enable),
      useWorkItems(use_work_items), targetWorkItemId(work_item_id),
      configuredStartCycle(start_cycle), configuredEndCycle(end_cycle),
      cacheSizeBytes(cache_size_bytes), blockSizeBytes(block_size_bytes),
      stats(*this, _cache)
{
    fatal_if(trackingEnabled && cacheSizeBytes == 0,
            "%s: l1Ace requires a non-zero cache size", cache->name());
    fatal_if(trackingEnabled && blockSizeBytes == 0,
            "%s: l1Ace requires a non-zero cache line size", cache->name());
    fatal_if(trackingEnabled && !useWorkItems && configuredEndCycle != 0 &&
             configuredEndCycle <= configuredStartCycle,
            "%s: l1AceEndCycle must be greater than l1AceStartCycle",
            cache->name());
    resetCycle = currentCycle();
    trackers.push_back(this);
}

L1AceTracker::~L1AceTracker()
{
    trackers.erase(std::remove(trackers.begin(), trackers.end(), this),
                   trackers.end());
}

uint64_t
L1AceTracker::currentCycle() const
{
    return static_cast<uint64_t>(cache->curCycle());
}

bool
L1AceTracker::selectedWorkItem(uint64_t work_id) const
{
    return targetWorkItemId < 0 ||
           static_cast<uint64_t>(targetWorkItemId) == work_id;
}

uint64_t
L1AceTracker::currentWindowStart() const
{
    if (useWorkItems)
        return workWindowStart;
    return std::max(configuredStartCycle, resetCycle);
}

bool
L1AceTracker::windowActive(uint64_t cycle) const
{
    if (!trackingEnabled)
        return false;
    if (useWorkItems)
        return workWindowActive;
    return cycle >= currentWindowStart() &&
           (configuredEndCycle == 0 || cycle < configuredEndCycle);
}

void
L1AceTracker::startLifetime(CacheBlk *blk, bool fill)
{
    const uint64_t cycle = currentCycle();
    if (!blk || !windowActive(cycle))
        return;

    endLifetime(blk);
    lineStates[blk] = {false, std::max(cycle, currentWindowStart()), 0};
    if (fill)
        ++trackedFills;
    else
        ++trackedWrites;
}

void
L1AceTracker::recordFill(CacheBlk *blk)
{
    startLifetime(blk, true);
}

void
L1AceTracker::recordWrite(CacheBlk *blk)
{
    startLifetime(blk, false);
}

void
L1AceTracker::recordRead(CacheBlk *blk)
{
    const uint64_t cycle = currentCycle();
    if (!blk || !windowActive(cycle))
        return;

    auto it = lineStates.try_emplace(
        blk, LineState{false, currentWindowStart(), 0}).first;
    LineState &state = it->second;
    state.hasRead = true;
    state.lastReadCycle = std::max(state.lastReadCycle, cycle);
    ++trackedReads;
}

void
L1AceTracker::endLifetime(CacheBlk *blk)
{
    auto it = lineStates.find(blk);
    if (it == lineStates.end())
        return;

    const LineState &state = it->second;
    if (state.hasRead && state.lastReadCycle >= state.writeCycle)
        finalizedAceLineCycles += state.lastReadCycle - state.writeCycle;
    lineStates.erase(it);
    ++lifetimeEnds;
}

void
L1AceTracker::recordInvalidation(CacheBlk *blk)
{
    if (trackingEnabled && blk)
        endLifetime(blk);
}

void
L1AceTracker::workItemBegin(uint64_t work_id)
{
    if (!trackingEnabled || !useWorkItems || workWindowStarted ||
        !selectedWorkItem(work_id)) {
        return;
    }

    workWindowStarted = true;
    workWindowActive = true;
    activeWorkItemId = work_id;
    workWindowStart = currentCycle();
    ++windowBegins;
}

void
L1AceTracker::workItemEnd(uint64_t work_id)
{
    if (!trackingEnabled || !useWorkItems || !workWindowActive ||
        work_id != activeWorkItemId) {
        return;
    }

    workWindowEnd = currentCycle();
    workWindowActive = false;
    workWindowComplete = true;
    ++windowEnds;
}

void
L1AceTracker::notifyWorkItemBegin(System *target_system, uint64_t work_id)
{
    for (auto *tracker : trackers) {
        if (tracker->system == target_system)
            tracker->workItemBegin(work_id);
    }
}

void
L1AceTracker::notifyWorkItemEnd(System *target_system, uint64_t work_id)
{
    for (auto *tracker : trackers) {
        if (tracker->system == target_system)
            tracker->workItemEnd(work_id);
    }
}

void
L1AceTracker::resetTracking()
{
    const bool preserve_work_window = useWorkItems && workWindowActive;
    const uint64_t new_start = currentCycle();

    lineStates.clear();
    finalizedAceLineCycles = 0;
    trackedFills = 0;
    trackedReads = 0;
    trackedWrites = 0;
    lifetimeEnds = 0;
    windowBegins = 0;
    windowEnds = 0;
    resetCycle = new_start;
    workWindowStarted = preserve_work_window;
    workWindowActive = preserve_work_window;
    workWindowComplete = false;
    if (!preserve_work_window)
        activeWorkItemId = 0;
    workWindowStart = preserve_work_window ? new_start : 0;
    workWindowEnd = 0;
    if (preserve_work_window)
        windowBegins = 1;
}

uint64_t
L1AceTracker::liveLineCycles() const
{
    uint64_t cycles = 0;
    for (const auto &entry : lineStates) {
        const LineState &state = entry.second;
        if (state.hasRead && state.lastReadCycle >= state.writeCycle)
            cycles += state.lastReadCycle - state.writeCycle;
    }
    return cycles;
}

uint64_t
L1AceTracker::aceLineCycles() const
{
    return finalizedAceLineCycles + liveLineCycles();
}

uint64_t
L1AceTracker::aceBitCycles() const
{
    return saturatingMultiply(
        aceLineCycles(), static_cast<uint64_t>(blockSizeBytes) * 8);
}

uint64_t
L1AceTracker::measuredCycles() const
{
    if (!trackingEnabled)
        return 0;

    const uint64_t now = currentCycle();
    if (useWorkItems) {
        if (!workWindowStarted)
            return 0;
        const uint64_t end = workWindowComplete ? workWindowEnd : now;
        return end >= workWindowStart ? end - workWindowStart : 0;
    }

    const uint64_t start = currentWindowStart();
    const uint64_t end = configuredEndCycle == 0 ?
        now : std::min(now, configuredEndCycle);
    return end >= start ? end - start : 0;
}

double
L1AceTracker::aceRatio() const
{
    const uint64_t cycles = measuredCycles();
    if (cycles == 0 || cacheSizeBytes == 0)
        return 0.0;

    const long double denominator =
        static_cast<long double>(cacheSizeBytes) * 8 * cycles;
    return static_cast<double>(aceBitCycles() / denominator);
}

L1AceTracker::Stats::Stats(L1AceTracker &_tracker, BaseCache *_cache)
    : statistics::Group(_cache, "l1Ace"), tracker(_tracker),
      ADD_STAT(aceLineCycles, statistics::units::Cycle::get(),
               "ACE cache-line cycles"),
      ADD_STAT(aceBitCycles, statistics::units::Count::get(),
               "ACE bit-cycles (line cycles times cache-line width)"),
      ADD_STAT(aceRatio, statistics::units::Ratio::get(),
               "L1 cache ACE coverage ratio"),
      ADD_STAT(trackedFills, statistics::units::Count::get(),
               "Cache-line fills tracked in the measurement window"),
      ADD_STAT(trackedDemandReads, statistics::units::Count::get(),
               "Demand reads tracked in the measurement window"),
      ADD_STAT(trackedDemandWrites, statistics::units::Count::get(),
               "Demand writes tracked in the measurement window"),
      ADD_STAT(lifetimeEnds, statistics::units::Count::get(),
               "Tracked lifetimes ended by overwrite or invalidation"),
      ADD_STAT(measuredCycles, statistics::units::Cycle::get(),
               "Cycles in the selected L1 ACE measurement window"),
      ADD_STAT(windowBegins, statistics::units::Count::get(),
               "Selected work-item windows started"),
      ADD_STAT(windowEnds, statistics::units::Count::get(),
               "Selected work-item windows completed")
{
    aceLineCycles.functor([this]() { return tracker.aceLineCycles(); });
    aceBitCycles.functor([this]() { return tracker.aceBitCycles(); });
    aceRatio.functor([this]() { return tracker.aceRatio(); }).precision(8);
    trackedFills.functor([this]() { return tracker.trackedFills; });
    trackedDemandReads.functor([this]() { return tracker.trackedReads; });
    trackedDemandWrites.functor([this]() { return tracker.trackedWrites; });
    lifetimeEnds.functor([this]() { return tracker.lifetimeEnds; });
    measuredCycles.functor([this]() { return tracker.measuredCycles(); });
    windowBegins.functor([this]() { return tracker.windowBegins; });
    windowEnds.functor([this]() { return tracker.windowEnds; });
}

void
L1AceTracker::Stats::resetStats()
{
    tracker.resetTracking();
    statistics::Group::resetStats();
}

} // namespace gem5
