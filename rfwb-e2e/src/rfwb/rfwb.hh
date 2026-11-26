#ifndef __CPU_O3_RFWB_HH__
#define __CPU_O3_RFWB_HH__

#include <cstdint>
#include <fstream>
#include <string>
#include <unordered_set>
#include <unordered_map>
#include <vector>

#include "base/types.hh"
#include "cpu/reg_class.hh"

namespace gem5
{

class StaticInst;

namespace o3
{
class DynInst;
}

/**
 * Minimal RF/WB experiment injector.
 *
 * Configuration is read from the environment so the same gem5 binary can be
 * reused for count-only pre-scan, Control, and one-shot fault runs:
 *   RFWB_MODEL=M001..M005
 *   RFWB_MODE=off|count|fault
 *   RFWB_ORDINAL=<1-based eligible-event ordinal>
 *   RFWB_PRODUCER_PC=<hex>   RFWB_MARKER_PC=<hex>
 *   RFWB_CONSUMER_PC=<hex>   RFWB_SRC_IDX=<n>
 *   RFWB_BIT=<0..63>         RFWB_BYTE=<0..15>
 *   RFWB_TRACE=<csv path>    RFWB_SAMPLE=<id>
 *
 * Hooks are intentionally thin; all model state lives here.
 */
class RFWB
{
  public:
    static RFWB &instance();

    bool active() const { return enabled; }

    static RegVal onScalarRead(o3::DynInst *inst, int idx,
                               PhysRegIdPtr reg, RegVal val);
    static void onScalarWrite(o3::DynInst *inst, int idx,
                              PhysRegIdPtr reg, RegVal val);
    static void onScalarWriteAny(o3::DynInst *inst, int idx,
                                 PhysRegIdPtr reg, RegVal val);
    static void *onWritableVec(o3::DynInst *inst, int idx,
                               PhysRegIdPtr reg);
    static void onExecute(o3::DynInst *inst, bool noFault);
    static bool skipCommit(o3::DynInst *inst);
    static bool skipGlobalReady(o3::DynInst *inst, int destIdx,
                                bool globalBefore);
    static void onRenameSrc(o3::DynInst *inst, int srcIdx,
                            PhysRegIdPtr reg, bool globalReady);
    static void onIQRepair(o3::DynInst *inst, PhysRegIdPtr reg);
    static void onVectorRead(o3::DynInst *inst, int idx, PhysRegIdPtr reg,
                             const void *val);
    static void onCommitStall(o3::DynInst *inst);
    static void onCommit(o3::DynInst *inst);
    static void onSquash(o3::DynInst *inst);
    static void onPhysAlloc(int cls, PhysRegIdPtr reg);
    static void onPhysFree(int cls, PhysRegIdPtr reg);
    uint64_t generation(PhysRegIdPtr reg) const;

  private:
    RFWB();
    bool matchPC(o3::DynInst *inst, uint64_t pc) const;
    bool isVecTarget(o3::DynInst *inst) const;
    bool isEligibleModel(const char *m) const;
    void log(const char *event, o3::DynInst *inst, PhysRegIdPtr reg,
             int srcIdx, uint64_t value, const std::string &extra);
    void logRaw(const std::string &line);

    bool enabled = false;
    bool countMode = false;
    bool faultMode = false;
    bool injected = false;
    std::string model;
    std::string mode;
    std::string sample;
    std::string tracePath;
    uint64_t ordinal = 1;
    uint64_t eligible = 0;
    uint64_t producerPc = 0;
    uint64_t markerPc = 0;
    uint64_t consumerPc = 0;
    int srcIdx = 0;
    int bit = 0;
    int byteIdx = 0;
    uint64_t producerSeq = 0;
    uint64_t targetSeq = 0;
    uint64_t faultProducerSeq = 0;
    uint64_t faultProducerGen = 0;
    uint64_t faultTick = 0;
    RegVal producerVal = 0;
    PhysRegIdPtr producerReg = nullptr;
    PhysRegIdPtr faultProducerReg = nullptr;
    PhysRegIdPtr faultVecReg = nullptr;
    PhysRegIdPtr faultReadReg = nullptr;
    std::ofstream trace;
    std::unordered_set<uint64_t> seenVecEvents;
    std::unordered_map<int, uint64_t> physGen;
    std::unordered_map<int, uint64_t> physAllocTick;
};

} // namespace gem5

#endif // __CPU_O3_RFWB_HH__
