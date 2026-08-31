#ifndef __CPU_O3_CHAOS_FPU_HH__
#define __CPU_O3_CHAOS_FPU_HH__

#include <random>
#include <string>

#include "params/CHAOSFPU.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/o3/dyn_inst_ptr.hh"

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class DynInst; } }

namespace gem5
{

class CHAOSFPU : public SimObject
{
  public:
    CHAOSFPU(const CHAOSFPUParams &p);
    ~CHAOSFPU();

    void startup() override;  // self-attach to CPU.chaosFPU

    // Called from DynInst::execute() AFTER staticInst->execute(). Filters by
    // opClass (FloatAdd/FloatMult/FloatMultAcc + SimdFloat*); XORs the FP
    // result blob. Returns true if an injection happened.
    bool maybeCorrupt(o3::DynInst *dyn_inst);

  private:
    BaseCPU *cpu;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t fault_mask;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_FPU_HH__
