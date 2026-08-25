#ifndef __CPU_O3_CHAOS_LSQ_FWD_HH__
#define __CPU_O3_CHAOS_LSQ_FWD_HH__

#include <random>
#include <bitset>
#include <memory>

#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSLSQFwd.hh"
#include "sim/sim_object.hh"

namespace gem5
{

namespace o3 { class CPU; }

// CHAOSLSQFwd — store-to-load forwarding-path fault injector for O3CPU.
//
// A load that hits a younger-pending store in the store queue gets its data
// via a memcpy (lsq_unit.cc FullAddrRangeCoverage branch). This injector
// corrupts that forwarded data with probability `probability` per forwarding
// event, modeling the store-buffer forwarding-path corruption localized by
// reproduce-method2 v3 (core 179's reload `ldr` of just-read input — multi-bit,
// mantissa-concentrated, sign-immune). Distinct from CHAOSPhysReg (which
// corrupts a physical register cell): this corrupts the *datapath* between
// store queue and load, which is invisible to a register-only injector.
class CHAOSLSQFwd : public SimObject
{
  public:
    CHAOSLSQFwd(const CHAOSLSQFwdParams &p);
    ~CHAOSLSQFwd();

    // Called from lsq_unit.cc after the forward memcpy, BEFORE the data is
    // packetized and written back to the load. If the RNG fires, this flips
    // bits in `data` (one byte selected by byteOffset). Hot-path: when
    // probability==0 or outside the [firstClock,lastClock] window, returns
    // immediately with no work.
    void corrupt(uint8_t *data, unsigned size, Addr vaddr);

  private:
    enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random };
    static FaultType stringToFaultType(const std::string &s);
    const char *faultTypeToString(FaultType f);

    o3::CPU *cpu;
    float probability;
    FaultType fault_type_enum;
    std::bitset<32> fault_mask;
    int num_bits_to_change;
    int byte_offset;       // -1 = random byte within [0,size-1]
    Cycles first_clock, last_clock;
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;

    std::mt19937 rng;
    std::random_device rd;
    std::discrete_distribution<int> random_fault_distribution;
    OutputStream *log_stream;

    int generateRandomMask(int bits_to_change);  // 8-bit mask (per byte)
    void writeLog(const char *type, unsigned size, Addr vaddr, int byte_off,
                  int mask);

    struct CHAOSLSQFwdStats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numBitFlips;
        statistics::Scalar numStuckAtZero;
        statistics::Scalar numStuckAtOne;
        CHAOSLSQFwdStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSLSQFwdStats> stats;
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_LSQ_FWD_HH__
