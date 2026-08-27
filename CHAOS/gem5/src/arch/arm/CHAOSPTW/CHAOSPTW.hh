#ifndef __ARCH_ARM_CHAOS_PTW_HH__
#define __ARCH_ARM_CHAOS_PTW_HH__

#include <random>
#include <memory>
#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSPTW.hh"
#include "sim/sim_object.hh"

namespace gem5
{

namespace ArmISA { class MMU; }

// CHAOSPTW — page-table-walker readout fault injector (D3).
//
// Core 179's D3 signature (MICROARCH_SUPPLEMENT §2.4): 73 transient
// translation-fault warnings on VALID static mappings (ESR 0x96000044 /
// 0x96000004) — the hardware page-table walker transiently mis-read a
// page-table entry, the immediate AT-retry succeeded. This is the PTW
// readout data-path, sibling to D1 (load data path) and D2 (address path).
//
// Hooks the ARM table walker's doLongDescriptor to bit-flip a freshly-fetched
// descriptor (PTE) before evaluation. If the flip clears the valid bits, the
// entry becomes invalid -> translation fault, reproducing the spurious symptom.
// `ptwEcc` models whether the PTW array has ECC (H7: ECC-on suppresses spurious).
//
// FAITHFULNESS (FI_DESIGN_SUPPLEMENT §5): gem5's ARM walker is a simplified
// model of TSV110's PTW; the corruption lands on the in-memory PTE read,
// matching where D3 sits physically. Declared as a modeling limitation.
class CHAOSPTW : public SimObject
{
  public:
    CHAOSPTW(const CHAOSPTWParams &p);
    ~CHAOSPTW();
    void corruptDescriptor(uint8_t *data, unsigned size, Addr desc_addr);
  private:
    ArmISA::MMU *mmu;
    float probability;
    int num_bits;
    unsigned fault_mask;
    int byte_offset;
    bool ptw_ecc;
    Cycles first_clock, last_clock;
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;
    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream;
    struct Stats : public statistics::Group {
        statistics::Scalar numHooksCalled;
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numSpuriousFaults;
        statistics::Scalar numBenignFlips;
        Stats(statistics::Group *parent);
    };
    std::unique_ptr<Stats> stats;
    int generateRandomMask(int bits_to_change);
    void writeLog(Addr desc_addr, uint64_t orig, uint64_t corr, bool became_invalid);
};

} // namespace gem5
#endif
