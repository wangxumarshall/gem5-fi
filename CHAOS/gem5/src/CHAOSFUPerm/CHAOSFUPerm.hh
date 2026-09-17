/*
 * CHAOSFUPerm — FU permanent fault injector, execution level (Task 5.2).
 * See CHAOSFUPerm.py for the fault-model contract. The active hook is
 * cpu/o3/dyn_inst.hh setRegOperand: every result of the target OpClass is
 * XOR-corrupted on the REAL writeback path (before cpu->setReg), i.e. the
 * execution-level permanent model — a stuck gate affecting every use.
 * (The iew.cc instResult queue turned out to be checker-only: 954649
 * corruptions there changed no output — measured, then moved here.)
 */
#ifndef __CHAOS_FU_PERM_CHAOSFUPERM_HH__
#define __CHAOS_FU_PERM_CHAOSFUPERM_HH__

#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"

#include <cstdint>

namespace gem5
{

class CHAOSFUPermParams;
namespace o3 { class CPU; }

class CHAOSFUPerm : public SimObject
{
  public:
    CHAOSFUPerm(const CHAOSFUPermParams &p);
    ~CHAOSFUPerm() override;

    // Single active instance (the mask oracle consults this).
    static CHAOSFUPerm *instance;

    // --- oracle state (public: the free-function oracle reads it on the
    // hot path; grouping as private would need a friend declaration) ---
    int target_opclass = -1;     // enums::OpClass value
    uint64_t fault_mask = 0;
    uint64_t first_clock = 0;    // fault active from this cycle (0 = start)
    uint64_t corrupt_count = 0;  // log-line throttle: log first 32 only

  public:
    // oracle-facing state (public: the free-function mask oracle reads
    // these on the writeback hot path)
    o3::CPU *cpu;
    bool write_log;
    OutputStream *log_stream = nullptr;

    // public: the free-function mask oracle increments these on the
    // writeback hot path
    struct Stats : public statistics::Group
    {
        Stats(statistics::Group *parent);
        statistics::Scalar numCorrupted;
        statistics::Scalar numMatchedOpClass;
    } stats;
};

// Guard + mask oracle used by cpu/o3/dyn_inst.hh setRegOperand.
// Returns the XOR mask to apply to this op's result, or 0 if none.
extern bool fu_perm_enabled;
uint64_t fu_perm_mask_for(int op_class);   // op_class = enums::OpClass
// Blob overload (FP/vector results are written as byte blobs through the
// const void* setRegOperand — measured: FloatMult matches stay 0 via the
// RegVal path). Returns the mask; the caller XORs the blob words.
uint64_t fu_perm_mask_for_blob(int op_class);

} // namespace gem5

#endif // __CHAOS_FU_PERM_CHAOSFUPERM_HH__
