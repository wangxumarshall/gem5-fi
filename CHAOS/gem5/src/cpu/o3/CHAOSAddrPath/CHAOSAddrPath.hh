#ifndef __CPU_O3_CHAOS_ADDR_PATH_HH__
#define __CPU_O3_CHAOS_ADDR_PATH_HH__

#include <random>
#include <string>

#include "params/CHAOSAddrPath.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "mem/request.hh"

namespace gem5 { namespace o3 { class CPU; } }

namespace gem5
{

class CHAOSAddrPath : public SimObject
{
  public:
    CHAOSAddrPath(const CHAOSAddrPathParams &p);
    ~CHAOSAddrPath();

    void startup() override;  // self-attach to CPU.chaosAddrPath

    // Called from LSQ::LSQRequest::sendFragmentToTranslation BEFORE
    // translateTiming. Corrupts the request vaddr (byte7 zero / low-bit flip).
    // HONEST: SE-inert (SE phys mem from 0; byte7 zero still in range).
    bool maybeCorrupt(RequestPtr &req);

  private:
    enum class Mode { Byte7Zero, LowBitFlip };
    static Mode stringToMode(const std::string &s);

    BaseCPU *cpu;
    Mode fi_mode;
    double probability;
    uint64_t first_clock, last_clock;
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

#endif // __CPU_O3_CHAOS_ADDR_PATH_HH__
