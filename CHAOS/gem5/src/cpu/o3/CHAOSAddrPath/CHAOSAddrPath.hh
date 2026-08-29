#ifndef __CPU_O3_CHAOS_ADDR_PATH_HH__
#define __CPU_O3_CHAOS_ADDR_PATH_HH__

#include <random>
#include <memory>
#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSAddrPath.hh"
#include "sim/sim_object.hh"

namespace gem5
{

namespace o3 { class CPU; }
class CHAOSAddrPath;  // self (for MMU forward-decl symmetry)

namespace ArmISA { class MMU; }

// CHAOSAddrPath — address-path fault injector (D2) for O3CPU.
//
// Core 179's D2 signature (MICROARCH_SUPPLEMENT §2.3): the MSB byte of the
// address presented to the MMU was forced to 0 (0814: d9->00; 0824: 55->00),
// while the architectural register held the true computed value. This is an
// address-PATH corruption distinct from the data-path D1.
//
// This injector zeroes one byte of a load's effective address at executeLoad
// time. FAITHFULNESS CAVEAT (FI_DESIGN_SUPPLEMENT §5): gem5 O3 translation
// happens inside DynInst::initiateAcc, so the corruption lands on the
// post-translation effAddr (cache-access path) rather than strictly pre-MMU.
// The symptom class (wrong address -> fault) is preserved; the exact pipeline
// stage differs from silicon. Declared as a modeling limitation.
class CHAOSAddrPath : public SimObject
{
  public:
    CHAOSAddrPath(const CHAOSAddrPathParams &p);
    ~CHAOSAddrPath();
    // Called from lsq_unit.cc executeLoad for each load. If the RNG fires,
    // zeroes the configured byte of *addr. Returns true if corrupted.
    bool corruptAddr(Addr *addr, uint64_t seq);
  private:
    o3::CPU *cpu;
    ArmISA::MMU *mmu = nullptr;  // for the non-O3 translateTiming hook
    float probability;
    int byte_offset;        // which byte to zero (default 7 = MSB); -1 = random
    Cycles first_clock, last_clock;
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;
    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream;
    struct Stats : public statistics::Group {
        statistics::Scalar numHooksCalled;
        statistics::Scalar numAddrFaults;
        Stats(statistics::Group *parent);
    };
    std::unique_ptr<Stats> stats;
    void writeLog(uint64_t seq, Addr orig, Addr corrupted);
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_ADDR_PATH_HH__
