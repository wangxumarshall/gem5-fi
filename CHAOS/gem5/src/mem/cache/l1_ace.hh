#ifndef __MEM_CACHE_L1_ACE_HH__
#define __MEM_CACHE_L1_ACE_HH__

#include <cstdint>
#include <unordered_map>

#include "base/statistics.hh"

namespace gem5
{

class BaseCache;
class CacheBlk;
class System;

class L1AceTracker
{
  public:
    L1AceTracker(BaseCache *cache, System *system, bool enable,
                 bool use_work_items, int64_t work_item_id,
                 uint64_t start_cycle, uint64_t end_cycle,
                 uint64_t cache_size_bytes, unsigned block_size_bytes);
    ~L1AceTracker();

    void recordFill(CacheBlk *blk);
    void recordRead(CacheBlk *blk);
    void recordWrite(CacheBlk *blk);
    void recordInvalidation(CacheBlk *blk);
    void resetTracking();

    static void notifyWorkItemBegin(System *system, uint64_t work_id);
    static void notifyWorkItemEnd(System *system, uint64_t work_id);

  private:
    struct LineState
    {
        bool hasRead = false;
        uint64_t writeCycle = 0;
        uint64_t lastReadCycle = 0;
    };

    bool selectedWorkItem(uint64_t work_id) const;
    bool windowActive(uint64_t cycle) const;
    uint64_t currentWindowStart() const;
    uint64_t currentCycle() const;
    void workItemBegin(uint64_t work_id);
    void workItemEnd(uint64_t work_id);
    void startLifetime(CacheBlk *blk, bool fill);
    void endLifetime(CacheBlk *blk);
    uint64_t liveLineCycles() const;
    uint64_t aceLineCycles() const;
    uint64_t aceBitCycles() const;
    uint64_t measuredCycles() const;
    double aceRatio() const;

    BaseCache *cache;
    System *system;
    const bool trackingEnabled;
    const bool useWorkItems;
    const int64_t targetWorkItemId;
    const uint64_t configuredStartCycle;
    const uint64_t configuredEndCycle;
    const uint64_t cacheSizeBytes;
    const unsigned blockSizeBytes;

    uint64_t resetCycle = 0;
    bool workWindowStarted = false;
    bool workWindowActive = false;
    bool workWindowComplete = false;
    uint64_t activeWorkItemId = 0;
    uint64_t workWindowStart = 0;
    uint64_t workWindowEnd = 0;

    std::unordered_map<CacheBlk *, LineState> lineStates;
    uint64_t finalizedAceLineCycles = 0;
    uint64_t trackedFills = 0;
    uint64_t trackedReads = 0;
    uint64_t trackedWrites = 0;
    uint64_t lifetimeEnds = 0;
    uint64_t windowBegins = 0;
    uint64_t windowEnds = 0;

    struct Stats : public statistics::Group
    {
        Stats(L1AceTracker &tracker, BaseCache *cache);
        void resetStats() override;

        L1AceTracker &tracker;
        statistics::Value aceLineCycles;
        statistics::Value aceBitCycles;
        statistics::Value aceRatio;
        statistics::Value trackedFills;
        statistics::Value trackedDemandReads;
        statistics::Value trackedDemandWrites;
        statistics::Value lifetimeEnds;
        statistics::Value measuredCycles;
        statistics::Value windowBegins;
        statistics::Value windowEnds;
    } stats;
};

} // namespace gem5

#endif // __MEM_CACHE_L1_ACE_HH__
