#ifndef __CPU_O3_CHAOS_LSQ_FWD_HH__
#define __CPU_O3_CHAOS_LSQ_FWD_HH__

#include <random>
#include <bitset>
#include <memory>

#include "base/output.hh"
#include "sim/eventq.hh"
#include "cpu/o3/chaos_l0.hh"           // LSU W3 L0 funnel
#include "cpu/o3/chaos_lsu_trigger.hh"  // LSU W2 event-normalized tiers
#include "cpu/o3/CHAOSLSQFwd/da04_byte_enable.hh"  // LSU v3.2.4 DA04
#include "cpu/o3/CHAOSLSQFwd/fw05_rules.hh"        // LSU v3.2.7 FW05
#include "cpu/o3/CHAOSLSQFwd/fw02_rules.hh"        // LSU v3.2.12 FW02
#include "cpu/o3/CHAOSLSQFwd/sq01_rules.hh"        // LSU v3.2.12 SQ01
#include "cpu/o3/CHAOSLSQFwd/sq03_rules.hh"        // LSU v3.2.7 SQ03
#include "cpu/o3/CHAOSLSQFwd/sp05_rules.hh"        // LSU v3.2.9 SP05
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

    // FW05 (LSU v3.2.7, option A): strict single wrong-source forwarding.
    // The caller supplies the gem5-selected true source and one older SQ
    // candidate, with real addresses/sizes/seqs so FW05-ELIG-v1 can reject
    // partial coverage, data equality, non-older or same-instruction cases.
    // Returns true iff the load buffer was filled from the alternative.
    bool maybeSubstituteFW05(uint8_t *load_data, unsigned copy_size,
                             Addr vaddr, uint64_t load_seq, uint64_t load_pc,
                             uint64_t true_seq, Addr true_addr,
                             unsigned true_size, const uint8_t *true_data,
                             uint64_t alt_seq, Addr alt_addr,
                             unsigned alt_size, const uint8_t *alt_data,
                             uint64_t sq_idx, uint64_t sq_gen,
                             uint64_t lq_idx, uint64_t lq_gen,
                             uint64_t load_attempt);

    // FW02 (LSU v3.2 pilot, F6): at the full-coverage forwarding DECISION
    // point, return true exactly once for a real older-store/younger-load
    // pair. The caller skips the forwarding branch and falls through to the
    // normal memory access for that load. This is a conditional false miss,
    // not a data corruption of the forwarded buffer.
    bool maybeSuppressForwarding(uint64_t load_seq, uint64_t store_seq,
                                 Addr vaddr, unsigned size);

    // v3.2.1: ptag registered for the FW02 false-miss (0 = none).
    uint64_t lastFwdPtag() const { return last_fwd_ptag; }
    bool fw05Mode() const { return struct_mode == StructMode::Fw05OlderSrc; }

    // SQ03: one-shot premature _canWB for the selected real store. The
    // caller must also increment storesToWB.
    bool maybeSetCanWB(uint64_t store_seq, uint64_t sq_idx, uint64_t sq_gen);

    // SP05 (v3.2.9): select the Nth committed store, then complete it before
    // its cache write is sent. The caller must call the real completeStore()
    // so the storesToWB decrement stays paired.
    bool maybeSelectSP05(uint64_t store_seq, uint64_t sq_idx, uint64_t sq_gen,
                         uint32_t size, bool is_prefetch);
    bool maybeCompleteSP05(uint64_t store_seq, uint64_t sq_idx,
                           uint64_t sq_gen, bool request_sent);
    void sp05Watchdog();
    bool sp05Mode() const { return struct_mode == StructMode::Sp05Complete; }
    // Consume the pending SP05 trace flag: true exactly once, for the
    // premature-completion call itself (not for ordinary completions).
    bool consumeSP05Trace(uint64_t seq);
    uint64_t sp05Eligible() const { return eligible_count; }

    // SQ03 in-simulator watchdog: logs CHAOS_SQ03_WATCHDOG=EXPIRED and exits
    // the simulation with a non-zero code. The event fires at
    // sq03WatchdogCycles after construction.
    void sq03Watchdog();
    uint64_t sq03LastEligible() const { return eligible_count; }
    uint64_t injectorSeed() const { return rng_seed; }

    // SQ01 (LSU v3.2.3): after LSQUnit::write() has copied store data into the
    // SQ entry, flip byte0 bit3 once under the F0 trigger. Data-only: no SQ
    // state, no request, no pointer is changed.
    bool maybeCorruptStoreData(uint8_t *data, unsigned size, Addr vaddr,
                               uint64_t dyn_seq, uint64_t store_idx,
                               uint64_t generation);

    // DA04 (LSU v3.2.4): clear bit0 of a 4-byte store's byte-enable after the
    // mask has been built in LSQ::pushRequest. Store-only; address, size and
    // store data are untouched. Returns true iff the mask changed.
    bool maybeCorruptStoreByteEnable(std::vector<bool> &be, unsigned size,
                                     Addr vaddr, uint64_t dyn_seq,
                                     uint64_t sq_idx, uint64_t generation,
                                     const uint8_t *store_data);

    // §2.4 F6 phase_offset (Phase 4.7, method3 forward-path phase): called
    // at the forward WritebackEvent schedule site (lsq_unit.cc:~1596).
    // If the RNG fires, returns the DELAY in CPU cycles to apply to this
    // forward's writeback (0 = no injection — the caller schedules at
    // curTick() as usual). Only active in PhaseOffset mode.
    Cycles maybeDelayForward(Addr vaddr, unsigned size);

    // LSU W5 L03: violation-detection address corruption. Called from
    // checkViolations before the overlap comparison. Returns true if the
    // comparison address was corrupted (caller logs it). The corruption
    // changes ONLY the violation check, not the actual memory access.
    bool violationCorrupt(Addr& cmp_addr);

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
    //   phase_offset (F6, Phase 4.7 — DONE): delay this forward's
    //     WritebackEvent by phaseOffset CPU cycles (the REAL method3
    //     forward-path phase proxy, unlike IQ's wake_phase which the
    //     E3 boundary analysis showed captures scheduler phase, not
    //     forward-path phase).
    enum class StructMode { ByteFlip, ByteLaneSkew, AllZero, FwdSourceSub,
                            PhaseOffset, F6Fw02, Sq01Bit3, Da04BeBit0,
                            Fw05OlderSrc, Sq03CanWB, Sp05Complete };
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
    bool l03_mode = false;   // [LSU][SEM-B] W5 L03: violation-site only
    // Sampling-bias fix (same as CHAOSL1DForward, findings.md Phase 2.2):
    // number of eligible forwarding events to skip before the first
    // injection — geometric(p=0.1) from the seed, so maxFaults=1 lands on a
    // seed-dependent forwarding event instead of always the first eligible
    // one (which is the same dynamic store->load pair every rep on a
    // deterministic stream).
    // LSU W2/W5: event-normalized trigger + L0 funnel (same wiring pattern
    // as CHAOSAddrPath; lsuTier != off routes the injection decision through
    // the trigger and the funnel prints at exit).
    ChaOSLsuTrigger *lsuTrigger = nullptr;
    ChaOSL0Funnel l0_funnel;
    ChaOSL0State l0_item;

    uint64_t events_to_skip = 0;
    // v1.1 Phase 8.2 uniform sampling (chaos_event_sample.hh): FIXED skip
    // from the driver overrides the legacy geometric(0.1) draw.
    bool count_only = false;         // consume + count, never corrupt
    uint64_t eligible_count = 0;     // CHAOS_ELIGIBLE_COUNT=<n> at teardown

    // FW02 (LSU v3.2 F6 pilot): a real full-coverage older-store/younger-load
    // pair is the trigger. The first such pair fires once; subsequent pairs
    // are counted but not suppressed.
    bool f6_fired = false;
    uint64_t f6_observed = 0;
    uint64_t f6_load_seq = 0;
    uint64_t f6_store_seq = 0;
    uint64_t last_fwd_ptag = 0;
    uint64_t f6_event_ordinal = 0;
    uint64_t fw05_event_ordinal = 0;
    // SQ03 one-shot: independent of max_faults, so a duplicate call can
    // never apply a second premature canWB.
    bool sq03_fired = false;

    EventFunctionWrapper *sq03_watchdog_event = nullptr;

    // SP05 state (v3.2.9): entry-keyed target + independent one-shot.
    bool sp05_selected = false;
    bool sp05_fired = false;
    uint64_t sp05_target_seq = 0;
    uint64_t sp05_target_idx = 0;
    uint64_t sp05_target_gen = 0;
    uint64_t sp05_event_ordinal = 0;
    bool sp05_pending_trace = false;
    EventFunctionWrapper *sp05_watchdog_event = nullptr;

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
