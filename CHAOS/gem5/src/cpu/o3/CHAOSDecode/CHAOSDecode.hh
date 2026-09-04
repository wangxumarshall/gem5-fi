#ifndef __CPU_O3_CHAOS_DECODE_HH__
#define __CPU_O3_CHAOS_DECODE_HH__

#include <random>
#include <string>

#include "params/CHAOSDecode.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/reg_class.hh"

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class DynInst; } }

namespace gem5
{

class CHAOSDecode : public SimObject
{
  public:
    CHAOSDecode(const CHAOSDecodeParams &p);
    ~CHAOSDecode();

    void startup() override;  // self-attach to CPU.chaosDecode

    // Called from rename.cc:1137 AFTER inst->flattenedDestIdx(dest_idx,
    // flat_dest_regid) is set. May MUTATE flat_dest_regid's index to another
    // legal 0-30 integer reg (dest_reg_sub F5). Per-inst (safe, _flatDestIdx
    // is per-DynInst, not shared staticInst). Returns true if injected.
    bool maybeCorrupt(int dest_idx, RegId &flat_dest_regid,
                      const o3::DynInst *inst);

  private:
    BaseCPU *cpu;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;
    // Sampling-bias fix (findings.md Phase 2.2/3.0, same as CHAOSL1DForward
    // 7387649): skip a geometric(p=0.1) number of eligible events before
    // the first injection, so maxFaults=1 lands on a seed-dependent event
    // instead of always the first eligible one (same dynamic instruction
    // every rep on a deterministic stream).
    uint64_t events_to_skip = 0;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_DECODE_HH__
