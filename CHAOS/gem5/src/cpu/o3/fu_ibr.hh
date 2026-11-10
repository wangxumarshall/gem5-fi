#ifndef __CPU_O3_FU_IBR_HH__
#define __CPU_O3_FU_IBR_HH__

#include <array>
#include <cstdint>

#include "base/statistics.hh"
#include "cpu/static_inst.hh"

namespace gem5 {
struct BaseO3CPUParams;
namespace o3 {
class CPU;
class FUPool;

/** Input-port activity at FU allocation, including speculative activity.
 * Two integer input ports for ALU/divide; three for multiply-add; two for each
 * scalar FP add/multiply/divide class.
 *
 * The six classes are: intAlu, intMult, intDiv, fpAdd, fpMult, fpDiv. FP
 * covers AArch64 scalar S/D/H encodings; SIMD/SVE and FP fused-multiply-add
 * remain outside this phase and increase excludedOps.
 */
class FUIbrTracker
{
  public:
    FUIbrTracker(CPU *cpu, const BaseO3CPUParams &params);
    void recordIssue(const StaticInstPtr &inst);
    void workItemBegin(uint64_t id);
    void workItemEnd(uint64_t id);
    void resetTracking();

  private:
    static constexpr unsigned numClasses = 6;
    uint64_t currentCycle() const;
    uint64_t measuredCycles() const;
    bool selected(uint64_t id) const;
    CPU *cpu;
    const bool enabled, useWorkItems;
    const int64_t workId;
    const uint64_t startCycle, endCycle;
    uint64_t resetCycle = 0, windowStart = 0, windowEnd = 0;
    uint64_t activeWorkId = 0;
    bool started = false, active = false, complete = false;
    uint64_t begins = 0, ends = 0, excluded = 0;
    std::array<uint64_t, numClasses> inputBits{}, issuedOps{}, unitCounts{};
    // Retain the current cycle so an end marker later in that cycle can
    // enforce the exclusive upper boundary, independent of stage ordering.
    uint64_t sampleCycle = 0;
    std::array<uint64_t, numClasses> cycleInputBits{}, cycleIssuedOps{};
    uint64_t cycleExcluded = 0;
    static constexpr std::array<unsigned, numClasses> ports =
        {2, 3, 2, 2, 2, 2};
    struct Stats : statistics::Group
    {
        Stats(FUIbrTracker &tracker, CPU *cpu);
        void resetStats() override;
        void preDumpStats() override;
        FUIbrTracker &tracker;
        statistics::Vector inputBits, issuedOps, unitCount, maxInputBits;
        statistics::Vector ibrRatio;
        statistics::Value measuredCycles, windowBegins, windowEnds;
        statistics::Value excludedOps;
    } stats;
};
} } // namespace gem5::o3
#endif
