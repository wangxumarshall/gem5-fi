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

    // S6-1/S6-2: pick a (possibly substituted) forward source. Called from
    // lsq_unit.cc BEFORE the forward memcpy. `cur_data` is the current store's
    // data pointer (store_it->data() + shift_amt). Returns a pointer to use
    // as the memcpy source — by default returns cur_data (no substitution);
    // in fwd_source_sub / stale_line_replay mode returns a STALE/historical
    // buffer (a previously-seen store's data) to model the wrong-source /
    // stale-line-replay signature. Records cur_data into the history buffer.
    // Hot-path: probability==0 or no injector -> returns cur_data.
    uint8_t *pickSource(uint8_t *cur_data, unsigned size, Addr vaddr);

  private:
    enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random };
    static FaultType stringToFaultType(const std::string &s);
    const char *faultTypeToString(FaultType f);

    // S1-5: structural (whole-word) faults (P-D1, core 179 D1 signature).
    enum class StructuralFault { None, ByteLaneSkew, AllZero };
    static StructuralFault stringToStructuralFault(const std::string &s);
    const char *structuralFaultToString(StructuralFault f);
    void applyStructuralFault(uint8_t *data, unsigned size, Addr vaddr);

    // S6-1/S6-2: source-substitution faults (forward-source F5 + stale line).
    // fwd_source_sub : return a STALE buffer (a previously-seen store's data)
    //                  as the memcpy source — wrong-store forwarding (F5).
    // stale_line_replay: same mechanism, models a stale fill-buffer line
    //                  replayed to a newer load.
    // None           : return cur_data (no substitution).
    enum class SourceFault { None, FwdSourceSub, StaleLineReplay, PhaseOffset };
    static SourceFault stringToSourceFault(const std::string &s);
    const char *sourceFaultToString(SourceFault f);
    SourceFault source_fault_enum = SourceFault::None;
    int phase_offset = 0;  // S6-3: F6 phase offset (history depth N, -2..+2)
    // History ring buffer of recently-seen store data (for stale/sub source).
    // Capped at 8 entries of up to 64 bytes each (cache-line sized forwards).
    static constexpr int HIST_CAP = 8;
    static constexpr int HIST_BYTES = 64;
    struct HistEntry { uint8_t data[HIST_BYTES]; unsigned size; Addr vaddr; bool valid; };
    HistEntry hist[HIST_CAP];
    int hist_next = 0;  // ring buffer write cursor

    o3::CPU *cpu;
    float probability;
    FaultType fault_type_enum;
    std::bitset<64> fault_mask;   // D2: was bitset<32>; now full 64-bit
    int mask_width;               // D2: bytes the mask covers (1..8)
    StructuralFault structural_fault_enum;  // S1-5: P-D1 whole-word fault
    int skew_bytes;               // S1-5: byte_lane_skew rotation (1..7)
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
        statistics::Scalar numStructuralByteLaneSkew;  // S1-5: P-D1 rol
        statistics::Scalar numStructuralAllZero;       // S1-5: P-D1 empty slot
        statistics::Scalar numFwdSourceSub;            // S6-1: wrong-source forward
        statistics::Scalar numStaleLineReplay;         // S6-2: stale-line replay
        statistics::Scalar numPhaseOffset;             // S6-3: F6 phase offset
        CHAOSLSQFwdStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSLSQFwdStats> stats;
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_LSQ_FWD_HH__
