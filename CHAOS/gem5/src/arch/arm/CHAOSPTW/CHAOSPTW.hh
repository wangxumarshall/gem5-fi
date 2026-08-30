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

// CHAOSPTW — page-table-walker readout fault injector (P-D3).
//
// Core 179's D3 signature (MICROARCH_SUPPLEMENT §2.4): 73 transient translation-
// fault warnings on VALID static mappings (ESR 0x96000044 / 0x96000004) — the
// hardware page-table walker transiently mis-read a page-table entry, the
// immediate AT-retry succeeded. PTW readout data-path, sibling to D1/D2.
//
// Hooks the ARM table walker's doLongDescriptor to bit-flip a freshly-fetched
// descriptor (PTE) before evaluation. If the flip clears the valid bits, the
// entry becomes invalid -> translation fault, reproducing the spurious symptom.
// `ptwEcc` models whether the PTW array has ECC (H7: ECC-on corrects single-bit).
// `clearValidBit` force-clears bits[1:0] (2-bit, bypasses ECC) for reliable
// spurious manufacturing.
//
// FS MODE REQUIRED: SE uses translateMmuOff (identity map, never walks).
class CHAOSPTW : public SimObject
{
  public:
    CHAOSPTW(const CHAOSPTWParams &p);
    ~CHAOSPTW();

    void startup() override;  // snapshot first/last clock as ticks (D1-style)

    // Called from table_walker.cc doLongDescriptor AFTER the long descriptor
    // is fetched and byte-swapped, BEFORE it is evaluated. If the RNG fires
    // (and under the tick window + maxFaults cap + ECC check), bit-flips the
    // descriptor data. nullptr/prob==0 -> no-op (hot-path short-circuit).
    void corruptDescriptor(uint8_t *data, unsigned size, Addr desc_addr);

  private:
    ArmISA::MMU *mmu;
    float probability;
    int num_bits;
    uint64_t fault_mask;
    int byte_offset;
    bool clear_valid_bit;
    bool ptw_ecc;
    Cycles first_clock, last_clock;
    Tick first_tick = 0, last_tick = 0;  // advisory tick window (curTick)
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;

    // rng via lambda (not member order) — avoids rng_seed==0 -> rd() UB.
    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream;

    uint64_t generateRandomMask(int bits_to_change);
    void writeLog(Addr desc_addr, uint64_t orig, uint64_t corr,
                  bool became_invalid, bool ecc_corrected);

    struct Stats : public statistics::Group {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numSpuriousFaults;   // flip made the PTE invalid
        statistics::Scalar numBenignFlips;     // flip did not clear valid bits
        statistics::Scalar numEccCorrected;     // single-bit flip corrected by ECC
        Stats(statistics::Group *parent);
    };
    std::unique_ptr<Stats> stats;
};

} // namespace gem5
#endif // __ARCH_ARM_CHAOS_PTW_HH__
