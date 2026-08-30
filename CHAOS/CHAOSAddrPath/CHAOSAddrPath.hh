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

// CHAOSAddrPath — address-path fault injector (D2) for O3CPU.
//
// Core 179's D2 signature (MICROARCH_SUPPLEMENT §2.3): the MSB byte of the
// address presented to the MMU was forced to 0 (0814: d9->00; 0824: 55->00),
// while the architectural register held the true computed value. This is an
// address-PATH corruption distinct from the data-path D1.
//
// This injector zeroes one byte of a load's effective address in
// LSQ::LSQRequest::sendFragmentToTranslation, BEFORE the MMU translates it.
// The corrupted vaddr is what the PTW/MMU actually walks.
//
// FAITHFULNESS CAVEAT (FI_DESIGN_SUPPLEMENT §5): gem5 O3 translation happens
// inside sendFragmentToTranslation -> translateTiming, so the corruption lands
// at the vaddr->MMU boundary (the faithful pre-translation point). FS MODE
// REQUIRED: SE uses translateMmuOff (identity map, no fault on zeroed byte).
class CHAOSAddrPath : public SimObject
{
  public:
    CHAOSAddrPath(const CHAOSAddrPathParams &p);
    ~CHAOSAddrPath();

    // Called from lsq.cc sendFragmentToTranslation for each load fragment,
    // BEFORE translateTiming. If the RNG fires (and under the tick window +
    // maxFaults cap), zeroes the configured byte of *addr. Returns true if
    // corrupted (so the caller can r->setVaddr(va)). Hot-path: probability==0
    // or outside the window -> returns false immediately.
    bool corruptAddr(Addr *addr, uint64_t seq);

    void startup() override;  // snapshot first/last clock as ticks (D1-style)

  private:
    o3::CPU *cpu;
    float probability;
    int byte_offset;        // which byte to zero (default 7 = MSB); -1 = random
    Cycles first_clock, last_clock;
    Tick first_tick = 0, last_tick = 0;  // advisory tick window (curTick)
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;

    // rng initialized via lambda (not member order) — avoids the
    // rng_seed==0 -> rd() UB that crashed sibling injectors (FI_DESIGN_SUPPLEMENT
    // patch bc4feb4). rng_seed!=0 uses the seed without touching rd().
    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream;

    struct Stats : public statistics::Group {
        statistics::Scalar numAddrFaults;
        Stats(statistics::Group *parent);
    };
    std::unique_ptr<Stats> stats;

    void writeLog(uint64_t seq, Addr orig, Addr corrupted);
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_ADDR_PATH_HH__
