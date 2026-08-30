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
    // bits in `data`. D2 fix: the faultMask is now a full 64-bit value applied
    // across `maskWidth` consecutive bytes (little-endian) starting at
    // byteOffset, so high bytes (bit 32..63) are reachable — previously the
    // mask was UInt32 truncated to one byte (&0xff). maskWidth=1 preserves
    // the legacy single-byte behavior. Hot-path: when probability==0 or
    // outside the [firstClock,lastClock] window, returns immediately.
    void corrupt(uint8_t *data, unsigned size, Addr vaddr);

  private:
    enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random };
    static FaultType stringToFaultType(const std::string &s);
    const char *faultTypeToString(FaultType f);

    o3::CPU *cpu;
    float probability;
    FaultType fault_type_enum;
    std::bitset<64> fault_mask;   // D2: was bitset<32>; now full 64-bit
    int mask_width;               // D2: bytes the mask covers (1..8)
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

    // D2: returns a 64-bit mask (was 8-bit). For maskWidth=1 only the low
    // 8 bits are used (legacy); for maskWidth>1 the mask spans the window.
    uint64_t generateRandomMask(int bits_to_change);
    void writeLog(const char *type, unsigned size, Addr vaddr, int byte_off,
                  uint64_t mask, int width);

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
