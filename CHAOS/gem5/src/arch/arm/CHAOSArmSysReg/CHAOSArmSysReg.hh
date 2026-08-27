#ifndef __ARCH_ARM_CHAOS_ARM_SYS_REG_HH__
#define __ARCH_ARM_CHAOS_ARM_SYS_REG_HH__

#include <random>
#include <bitset>
#include <memory>
#include <set>
#include <string>

#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSArmSysReg.hh"
#include "sim/sim_object.hh"

namespace gem5
{

namespace ArmISA { class ISA; }

// CHAOSArmSysReg — ARM system-register fault injector (Phase 3 §六.4 item 3).
//
// Hooks ISA::readMiscRegNoEffect (arch/arm/isa.cc): when a system register in
// the `targetRegs` whitelist is read, with probability `probability` per read
// (capped by maxFaults, within [firstClock, lastClock]), corrupts the returned
// value by a bit-flip mask. The reading instruction (MRS) gets a WRONG
// system-register value -> models a defective system-register cell. FS mode.
//
// Whitelist model: only target a handful of high-value control registers
// (TTBR/TCR/MAIR/SCTLR/VBAR/NZCV per §六 item-3) by MiscReg enum NAME, parsed
// from the targetRegs string. Empty whitelist = no injection.
class CHAOSArmSysReg : public SimObject
{
  public:
    CHAOSArmSysReg(const CHAOSArmSysRegParams &p);
    ~CHAOSArmSysReg();

    // Called from ISA::readMiscRegNoEffect AFTER computing val + applying
    // raz/rao, BEFORE returning. If `idx` is in the whitelist AND the RNG
    // fires (under the clock window + maxFaults cap), corrupts *val in
    // place (bit_flip/stuck_at_zero/stuck_at_one). Hot-path: empty whitelist
    // or probability==0 -> returns immediately. Returns true if corrupted
    // (for the caller's DPRINTF/log).
    bool maybeCorrupt(uint32_t idx, const char *reg_name, RegVal &val);
    void startup() override;  // convert first/last Cycles -> Tick window

  private:
    enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random };
    static FaultType stringToFaultType(const std::string &s);
    const char *faultTypeToString(FaultType f);

    // Parse a comma-separated list of MiscReg enum names into the index set.
    // Names not found in the MiscRegIndex enum are skipped (with a warning).
    void parseWhitelist(const std::string &s);

    ArmISA::ISA *isa;
    float probability;
    FaultType fault_type_enum;
    uint64_t fault_mask;
    int num_bits_to_change;
    Cycles first_clock, last_clock;
    Tick first_tick = 0, last_tick = 0;  // advisory tick window (curTick-based)
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;

    std::set<uint32_t> whitelist;   // target MiscReg indices (the whitelist)
    std::string whitelist_str;      // raw string (for logging)

    std::mt19937 rng;
    std::random_device rd;
    std::discrete_distribution<int> random_fault_distribution;
    OutputStream *log_stream;

    uint64_t generateRandomMask(int bits_to_change);

    struct CHAOSArmSysRegStats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numBitFlips;
        statistics::Scalar numStuckAtZero;
        statistics::Scalar numStuckAtOne;
        CHAOSArmSysRegStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSArmSysRegStats> stats;
};

} // namespace gem5
#endif // __ARCH_ARM_CHAOS_ARM_SYS_REG_HH__
