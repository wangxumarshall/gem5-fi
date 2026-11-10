#ifndef __CPU_O3_RF_ACE_HH__
#define __CPU_O3_RF_ACE_HH__

#include <array>
#include <cstdint>
#include <map>
#include <utility>
#include <vector>

#include "base/statistics.hh"
#include "base/types.hh"
#include "cpu/inst_seq.hh"
#include "cpu/reg_class.hh"
#include "cpu/static_inst_fwd.hh"
#include "cpu/thread_context.hh"

namespace gem5
{

namespace o3
{

class CPU;

/**
 * ACE lifetime tracker for the O3 integer and vector/FP physical register
 * files.
 *
 * Reads and writes are captured when they occur, but are applied only when
 * their instruction commits. This preserves the physical access time while
 * preventing wrong-path producers and consumers from contributing to ACE.
 *
 * The vector/FP file is tracked at 64-bit lane granularity: scalar D-register
 * arithmetic (FADD/FMUL/FDIV, FMOV, LDR/STR D) is exact, while a 128-bit SIMD
 * operation only covers its low 64-bit lane. That boundary is explicit rather
 * than silently overstating SIMD coverage.
 */
class RFAceTracker
{
  public:
    RFAceTracker(CPU *cpu, bool enable, bool use_work_items,
                 int64_t work_item_id, uint64_t start_cycle,
                 uint64_t end_cycle, bool bit_granularity,
                 unsigned reg_width_bits,
                 unsigned num_int_phys_regs,
                 unsigned num_vec_phys_regs);

    bool enabled() const { return trackingEnabled; }

    void recordRead(PhysRegIdPtr reg, ThreadID tid, InstSeqNum seq_num,
                    const StaticInst *inst, int src_index = -1);
    void recordWrite(PhysRegIdPtr reg, ThreadID tid, InstSeqNum seq_num,
                     const StaticInst *inst);
    void commitInstruction(ThreadID tid, InstSeqNum seq_num);
    void squashInstruction(ThreadID tid, InstSeqNum seq_num);
    void squashYounger(ThreadID tid, InstSeqNum squash_seq_num);
    void freeRegister(PhysRegIdPtr reg);

    void workItemBegin(uint64_t work_id, ThreadID tid, InstSeqNum seq_num);
    void workItemEnd(uint64_t work_id, ThreadID tid, InstSeqNum seq_num);
    void resetTracking();

  private:
    enum class EventType : uint8_t
    {
        Read,
        Write
    };

    struct Event
    {
        EventType type;
        RegIndex regIndex;
        uint64_t cycle;
        uint64_t windowStart;
        uint64_t mask;
        bool vector;
    };

    struct PendingInstruction
    {
        std::vector<Event> events;
    };

    struct RegState
    {
        uint64_t liveMask = 0;
        uint64_t readMask = 0;
        std::array<uint64_t, 64> writeCycles{};
        std::array<uint64_t, 64> lastReadCycles{};
    };

    using InstKey = std::pair<ThreadID, InstSeqNum>;

    bool selectedWorkItem(uint64_t work_id) const;
    bool windowActive(uint64_t cycle) const;
    uint64_t currentWindowStart() const;
    uint64_t currentCycle() const;
    bool trackedRegister(PhysRegIdPtr reg, bool &vector,
                         unsigned &slot_index) const;
    unsigned widthFor(bool vector) const;
    uint64_t fullMaskFor(bool vector) const;
    void recordEvent(EventType type, PhysRegIdPtr reg, ThreadID tid,
                     InstSeqNum seq_num, const StaticInst *inst,
                     int src_index = -1);
    uint64_t accessMask(EventType type, const StaticInst *inst,
                        int src_index, bool vector) const;
    void applyEvent(const Event &event);
    void endLifetime(RegState &state, uint64_t mask, bool vector);
    uint64_t liveBitCycles(uint64_t mask, bool vector) const;

    uint64_t aceRegCycles() const;
    uint64_t aceBitCycles() const;
    uint64_t aceBitCyclesLow32() const;
    uint64_t aceBitCyclesHigh32() const;
    uint64_t vecAceRegCycles() const;
    uint64_t vecAceBitCycles() const;
    uint64_t measuredCycles() const;
    double aceRatio() const;
    double vecAceRatio() const;

    CPU *cpu;
    const bool trackingEnabled;
    const bool useWorkItems;
    const int64_t targetWorkItemId;
    const uint64_t configuredStartCycle;
    const uint64_t configuredEndCycle;
    const bool bitGranularity;
    const unsigned registerWidthBits;
    const unsigned numIntPhysRegs;
    const unsigned numVecPhysRegs;

    static constexpr unsigned vecWidthBits = 64;

    uint64_t resetCycle = 0;
    bool workWindowStarted = false;
    bool workWindowActive = false;
    bool workWindowComplete = false;
    uint64_t activeWorkItemId = 0;
    uint64_t workWindowStart = 0;
    uint64_t workWindowEnd = 0;
    ThreadID markerThread = 0;
    InstSeqNum beginSeqNum = 0;

    std::map<InstKey, PendingInstruction> pendingInstructions;
    std::vector<RegState> regStates;

    uint64_t finalizedAceBitCycles = 0;
    uint64_t finalizedAceBitCyclesLow32 = 0;
    uint64_t finalizedAceBitCyclesHigh32 = 0;
    uint64_t finalizedVecAceBitCycles = 0;
    uint64_t trackedReads = 0;
    uint64_t trackedWrites = 0;
    uint64_t vecTrackedReads = 0;
    uint64_t vecTrackedWrites = 0;
    uint64_t overwriteDrops = 0;
    uint64_t vecOverwriteDrops = 0;
    uint64_t squashDiscards = 0;
    uint64_t vecSquashDiscards = 0;
    uint64_t windowBegins = 0;
    uint64_t windowEnds = 0;

    struct Stats : public statistics::Group
    {
        Stats(RFAceTracker &tracker, CPU *cpu);
        void resetStats() override;

        RFAceTracker &tracker;
        statistics::Value intAceRegCycles;
        statistics::Value intAceBitCycles;
        statistics::Value intAceBitCyclesLow32;
        statistics::Value intAceBitCyclesHigh32;
        statistics::Value intAceRatio;
        statistics::Value bitGranularity;
        statistics::Value intTrackedWrites;
        statistics::Value intTrackedReads;
        statistics::Value intSquashDiscards;
        statistics::Value intOverwriteDrops;
        statistics::Value vecAceRegCycles;
        statistics::Value vecAceBitCycles;
        statistics::Value vecAceRatio;
        statistics::Value vecTrackedWrites;
        statistics::Value vecTrackedReads;
        statistics::Value vecSquashDiscards;
        statistics::Value vecOverwriteDrops;
        statistics::Value measuredCycles;
        statistics::Value windowBegins;
        statistics::Value windowEnds;
    } stats;
};

} // namespace o3
} // namespace gem5

#endif // __CPU_O3_RF_ACE_HH__
