#ifndef __ARCH_ARM_CHAOS_PTW_HH__
#define __ARCH_ARM_CHAOS_PTW_HH__

#include <random>
#include <string>

#include "params/CHAOSPTW.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"

namespace gem5
{

namespace ArmISA { class WalkUnit; }  // forward decl (full def in table_walker.hh)

class CHAOSPTW : public SimObject
{
  public:
    CHAOSPTW(const CHAOSPTWParams &p);
    ~CHAOSPTW();

    void startup() override;  // self-attach to WalkUnit.chaosPTW

    // Called from WalkUnit::doLongDescriptor — flips a bit of the just-fetched
    // PTE (longDesc.data) pre-eval. HONEST: FS-only (SE never calls
    // doLongDescriptor, doc §0.3). ptwEcc knob models H7.
    bool maybeCorrupt(uint64_t &pte_data, unsigned lookup_level, Addr vaddr);

  private:
    enum class Mode { SingleBitXor, ClearValid };
    static Mode stringToMode(const std::string &s);

    ArmISA::WalkUnit *walker;  // raw; set from p.walker
    Mode fi_mode;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t fault_mask;
    bool ptw_ecc;
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

#endif // __ARCH_ARM_CHAOS_PTW_HH__
