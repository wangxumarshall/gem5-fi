#ifndef __CPU_O3_CHAOS_FPU_HH__
#define __CPU_O3_CHAOS_FPU_HH__

#include <random>
#include <memory>
#include <string>
#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "cpu/reg_class.hh"  // PhysRegIdPtr, RegClassType (v2 writeback hook)
#include "params/CHAOSFPU.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"

namespace gem5
{
namespace o3 { class CPU; }
class PhysRegId;

// CHAOSFPU — FSU writeback-path injector (plan §5.6, S8-2).
// Primary hook (v2): maybeCorruptWriteback — called from
// DynInst::setRegOperand BEFORE the value reaches the PhysReg + result
// queue (the true FSU result corruption point). The injector self-attaches
// via cpu->setChaosFPUHook in its constructor. Filters FP-class dests
// (FloatRegClass scalar FP / VecRegClass SIMD FP).
// Legacy hook (v1, kept for compat): the ROB-head attackEvent sampling
// (corruptResultRegVal) — reaches the head DynInst via cpu->robAccess();
// on gemm_double this hit "result already popped" 5089/5089 times, so the
// writeback hook is the reliable path.
class CHAOSFPU : public SimObject
{
  public:
    CHAOSFPU(const CHAOSFPUParams &p);
    ~CHAOSFPU();
    void startup() override;

    // §5.6 writeback-path hook (v2): called from DynInst::setRegOperand
    // with the dest physReg and the ABOUT-TO-BE-WRITTEN value. Applies the
    // fault IN PLACE (val ^= mask) when: dest is FP-class (Float/Vec),
    // inside [firstClock, lastClock], under maxFaults, and the per-write
    // Bernoulli draw fires. Hot path: one pointer check at the call site.
    void maybeCorruptWriteback(const PhysRegIdPtr &reg, RegVal &val);

    // Blob overload (const void* setRegOperand — vector/FP results written
    // as byte blobs). XORs the mask into the first 8 bytes in place.
    void maybeCorruptWritebackBlob(const PhysRegIdPtr &reg, const void *val);

    // §5.6 source-read hooks: an FP SOURCE operand is corrupted at the
    // moment the consumer reads it. This is the reliable corruption point
    // for back-to-back dependency chains (fmadd d0 -> fmadd d0): the value
    // flows through the bypass network and the PRF cell is never re-read,
    // so cell injection (CHAOSPhysReg) is defeated by forwarding — but the
    // read hook sees EVERY consumption. Same gates as the writeback hook.
    void maybeCorruptRead(const PhysRegIdPtr &reg, RegVal &val);
    void maybeCorruptReadBlob(const PhysRegIdPtr &reg, void *val);

    // shared corruption logger for the v2/v3 hooks
    void logCorruption(const char *site, const PhysRegIdPtr &reg,
                       RegClassType cls, uint64_t old, uint64_t neu,
                       uint64_t mask);

  private:
    enum class BitSeg { All, Low, Mid, High, Sign, Exp, Mantissa };
    static BitSeg stringToBitSeg(const std::string &s);

    o3::CPU *cpu;
    float probability;
    uint64_t fault_mask;
    int num_bits_to_change;
    BitSeg bit_seg;
    Cycles first_clock, last_clock;
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;
    std::string semantic_role;
    std::mt19937 rng;
    std::random_device rd;
    std::geometric_distribution<unsigned> inter_fault_cycles_dist;
    OutputStream *log_stream;
    EventFunctionWrapper attackEvent;
    void scheduleAttackEvent(Cycles delay);
    void attackCheck();
    void processFault(ThreadID tid);
    uint64_t genMask();
    void writeLog(ThreadID tid, uint64_t mask, int bit_seg_lo, int bit_seg_hi);
    struct Stats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numFpResultCorrupted;
        statistics::Scalar numSkippedNonFp;
        statistics::Scalar numResultPopped;  // FP head but instResult already popped (writeback done)
        Stats(statistics::Group *parent);
    };
    std::unique_ptr<Stats> stats;
};
} // namespace gem5
#endif
