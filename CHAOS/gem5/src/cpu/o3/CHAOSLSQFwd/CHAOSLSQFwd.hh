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

    // §2.4 fwd_source_sub (F5, Phase 4.2 — method1 wrong-source forwarding):
    // called from lsq_unit.cc at the forwarding DECISION point, after a
    // store entry is selected as the forward source (FullAddrRangeCoverage)
    // and BEFORE the memcpy. If the RNG fires, the load's data is copied
    // from a DIFFERENT (older) SQ entry instead — the load receives the
    // wrong store's data (wrong-source forward, 张冠李戴). Parameters are
    // raw pointers/sizes so lsq_unit.cc doesn't need CHAOS types. Returns
    // true if the substitution happened (the caller skips its own memcpy).
    bool maybeSubstituteSource(uint8_t *load_data,
                               const uint8_t *true_src, unsigned copy_size,
                               const uint8_t *alt_src, unsigned alt_size,
                               Addr vaddr);

  private:
    enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random };
    static FaultType stringToFaultType(const std::string &s);
    const char *faultTypeToString(FaultType f);

    // §2.4 structured fault mode (from fi-h6-h7 branch, H5 closed):
    //   byte_flip       (default): single/multi-byte XOR/OR/AND on one byte (orig)
    //   byte_lane_skew  : rotate the whole forwarded data by k bytes (rol_k) —
    //                     reproduces core179 D1 byte-lane phase signature (method2)
    //   all_zero        : zero the whole forwarded buffer (8 bytes)
    //   stale_line_replay: (deferred — needs older-line replay plumbing)
    //   fwd_source_sub (F5): DONE (Phase 4.2) — wrong-source forward from an
    //                     older SQ entry (maybeSubstituteSource hook in
    //                     lsq_unit.cc's forward-decision point)
    //   phase_offset (F6): (deferred — needs timing shift in lsq_unit.cc)
    enum class StructMode { ByteFlip, ByteLaneSkew, AllZero, FwdSourceSub };
    static StructMode stringToStructMode(const std::string &s);

    o3::CPU *cpu;
    float probability;
    FaultType fault_type_enum;
    StructMode struct_mode;
    std::bitset<64> fault_mask;   // §2.4: 64-bit (was 32 — truncated bit>=32)
    int num_bits_to_change;
    int byte_offset;       // -1 = random byte within [0,size-1]
    int lane_skew_k;       // §2.4 byte_lane_skew: rotate by k bytes (default 1)
    Cycles first_clock, last_clock;
    uint64_t max_faults, faults_injected_count;
    uint64_t rng_seed;
    bool write_log;
    // Sampling-bias fix (same as CHAOSL1DForward, findings.md Phase 2.2):
    // number of eligible forwarding events to skip before the first
    // injection — geometric(p=0.1) from the seed, so maxFaults=1 lands on a
    // seed-dependent forwarding event instead of always the first eligible
    // one (which is the same dynamic store->load pair every rep on a
    // deterministic stream).
    uint64_t events_to_skip = 0;

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
