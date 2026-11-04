#ifndef __CPU_O3_CHAOS_PHYS_REG_HH__
#define __CPU_O3_CHAOS_PHYS_REG_HH__

#include <cstdint>
#include <random>
#include <bitset>
#include <map>
#include <string>
#include <utility>
#include <vector>

#include "params/CHAOSPhysReg.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"
#include "cpu/base.hh"
#include "cpu/reg_class.hh"    // PhysRegIdPtr (FR03 event helpers)
#include "base/output.hh"
#include "cpu/o3/chaos_l0.hh"  // W2.5 L0 lifecycle interface state
#include "cpu/o3/CHAOSPhysReg/chaos_vec_stuck.hh"  // [FR03] L5 ledger
#include "cpu/o3/CHAOSPhysReg/chaos_vec_transient.hh"  // [FR01/FR02]

// o3::CPU (C++ class behind ArmO3CPU) is needed to reach regFile/renameMap.
// We forward-declare it here (full definition pulled into the .cc via
// cpu/o3/cpu.hh) to avoid dragging cpu.hh into the auto-generated params
// wrapper. CHAOSPhysReg only supports O3CPU; dynamic_cast fails at construct
// time otherwise.
namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class DynInst; } }

namespace gem5
{

class CHAOSPhysReg : public SimObject
{
  public:
    CHAOSPhysReg(const CHAOSPhysRegParams &p);
    ~CHAOSPhysReg();

    void startup() override;   // self-attach to CPU.chaosPhysReg

    /** [FR03] Called from DynInst::execute() after staticInst->execute().
     *  Re-asserts the permanent Vec stuck bits after every write to the
     *  target physical cell. Read-only for every other instruction/register. */
    void maybeReapplyStuck(o3::DynInst *inst);

    /** [FR03] L5 terminal: called from Commit::commitHead() at the existing
     *  FSU noteCommit anchor, AFTER the instruction really committed. Emits
     *  kind=commit only when this seqNum is a recorded consumer of the
     *  permanently stuck cell; never changes commit behaviour. */
    void noteCommit(ThreadID tid, o3::DynInst *inst);

    /** [FR03] L5 squash observation: called from ROB::doSquash() for every
     *  instruction that is really squashed. Emits kind=squash (never a
     *  commit) only for recorded consumers; a squash never clears the
     *  permanent defect. */
    void noteSquash(ThreadID tid, o3::DynInst *inst);

  private:
    uint64_t vec_stuck_writes = 0;   // re-applies actually performed
    uint64_t vec_stuck_activated = 0;  // writes whose correct bit differed

    // ------------------------------------------------------------------
    // [FR03] Permanent Vec physical-cell event state.
    //
    // One permanent fault_id spans the whole run; `generation` is only an
    // allocation/exposure identity. A generation change emits an explicit
    // generation_change event and restarts exposure_id at 1. Producer /
    // consumer edges from an older generation are never joined to the new
    // generation: the new chain roots at generation_change.
    //
    // Event volume is sampled (counts stay exact): at most
    // kVecExposureEventCap ordinary write exposures, all first-of-generation
    // and first-activated exposures, kVecActivatedEventCap activated
    // exposures, kVecGenerationEventCap generation changes and
    // kVecReadEventCap read/carrier observations. Totals are reported in the
    // run-end chain_end.
    // ------------------------------------------------------------------
    struct VecStuckEmission
    {
        bool installed = false;
        uint64_t fault_id = 0;
        uint64_t install_event = 0;         // L0 root
        uint64_t generation_root_event = 0;  // current generation chain root
        uint64_t last_event = 0;
        uint32_t install_generation = 0;
        uint32_t observed_generation = 0;
        uint64_t generation_changes = 0;
        uint64_t generation_changes_sampled = 0;
        uint64_t exposure_id = 0;            // per generation, 1-based
        uint64_t exposures_total = 0;
        uint64_t exposures_sampled = 0;
        uint64_t exposures_dropped = 0;
        uint64_t activated_total = 0;
        uint64_t activated_events = 0;
        uint64_t first_activated_sn = 0;
        uint64_t last_exposure_sn = 0;
        uint64_t reads_total = 0;
        uint64_t reads_reported = 0;
        uint64_t read_events = 0;
        uint64_t operand_read_events = 0;
        // [FR03] Read and write exposures are separate, exact counters:
        //   write_exposures_total = installation write + every re-apply
        //   read_exposures_total  = every consumer read of the target cell
        // `exposures_total` keeps the historical write-exposure meaning so
        // existing F5 accounting stays valid.
        uint64_t write_exposures_total = 0;
        uint64_t read_exposures_total = 0;
        // L5 / first-impact evidence.
        uint64_t install_tick = 0;
        uint64_t first_activated_tick = 0;
        uint64_t first_impact_sn = 0;
        uint64_t first_impact_tick = 0;
        uint64_t first_impact_latency = 0;
        uint64_t l5_witness_event = 0;
        uint64_t commit_events = 0;
        uint64_t squash_events = 0;
        uint64_t consumers_recorded = 0;
        // Most recent L1 carrier_state event id (parent of the next L2
        // operand_read); 0 after a generation change until a new carrier is
        // observed, so old-generation carriers never parent a new chain.
        uint64_t last_carrier_event = 0;
        bool first_activated_emitted = false;
        bool exit_flush_registered = false;
    };
    VecStuckEmission vec_emit;
    // [FR03] L5 commit/squash state machine (host-unit-tested pure model).
    // Consumers are only recorded from real operand reads of the target cell
    // after at least one activated exposure; a squash never becomes a commit.
    chaos_vec_stuck::L5Ledger l5;
    uint64_t next_fsu_fault_id = 1;

    // ------------------------------------------------------------------
    // [FR01/FR02] TRANSIENT Vec physical-cell bit-flip state.
    //
    // Unlike FR03 there is no permanent write-path mask here: the injector
    // performs ONE read-modify-write of the target cell and nothing is armed.
    // The next real write to the cell replaces the value, so the defect is
    // gone by construction. The state below is evidence only: install
    // identity (phys/generation/bit positions), consumer reads, the real
    // overwrite, and the L5 commit/squash witness of a consumer.
    // ------------------------------------------------------------------
    struct VecTransientEmission
    {
        bool installed = false;
        uint64_t fault_id = 0;
        uint64_t root_event = 0;      // L0 fault_applied
        uint64_t carrier_event = 0;   // L1 carrier_state
        uint64_t last_event = 0;      // parent for the next event
        uint64_t install_tick = 0;
        int phys_index = -1;
        int arch_index = -1;
        uint32_t install_generation = 0;
        int lane_width = 32;
        chaos_vec_transient::Selection sel;
        uint64_t install_lane_before = 0;
        uint64_t install_lane_after = 0;
        uint64_t last_lane_value = 0;  // most recent observed target lane
        uint64_t install_reads_baseline = 0;
        uint64_t read_events = 0;
        uint64_t reads_total = 0;
        uint64_t write_exposures_total = 1;  // the install write
        bool overwritten = false;
        uint64_t overwrite_event = 0;
        uint64_t overwrite_sn = 0;
        uint64_t overwrite_tick = 0;
        uint64_t first_read_sn = 0;
        uint64_t commit_events = 0;
        uint64_t squash_events = 0;
        uint64_t consumers_recorded = 0;
        uint64_t first_impact_sn = 0;
        uint64_t first_impact_tick = 0;
        uint64_t first_impact_latency = 0;
        uint64_t l5_witness_event = 0;
        bool exit_flush_registered = false;
        chaos_vec_stuck::L5Ledger l5;
    };
    VecTransientEmission vec_transient;
    // A geometry/mask request that cannot be honoured (e.g. FR02 asks for two
    // bits but the explicit mask has one, or the lane is too narrow) must
    // fail CLOSED: no injection, no consumed fault, no silent 1-bit fault.
    // The attack event is unscheduled so a bad manifest cannot spin forever.
    bool vec_transient_fatal = false;

    uint64_t emitVecModelProp(
        const char *model, const char *freq, const char *kind,
        uint64_t fault_id, uint64_t parent,
        std::vector<std::pair<std::string, std::string>> kv);
    void noteVecTransientInstalled(
        ThreadID tid, int phys_idx, int arch_idx, uint32_t generation,
        const chaos_vec_transient::Selection &sel,
        const uint8_t *before, const uint8_t *after);
    void observeVecTransient(o3::DynInst *inst);
    void noteVecTransientCommit(ThreadID tid, o3::DynInst *inst);
    void noteVecTransientSquash(ThreadID tid, o3::DynInst *inst);
    void finalizeVecTransient(const char *terminal);
    void registerTransientExitFlush();
    static std::string bitIndices(const chaos_vec_transient::Selection &s);
    static std::string vec128Hex(const uint8_t *v);

    static constexpr uint64_t kVecExposureEventCap = 2048;
    static constexpr uint64_t kVecActivatedEventCap = 256;
    static constexpr uint64_t kVecGenerationEventCap = 4096;
    static constexpr uint64_t kVecReadEventCap = 2048;
    static constexpr uint64_t kVecOperandReadCap = 2048;
    // emitFsuProp() parent convention: 0 = let notePropEvt auto-link to the
    // fault_id cursor; a non-zero value is an explicit parent_event_id.

    uint64_t emitFsuProp(
        const char *kind, uint64_t fault_id, uint64_t parent,
        std::vector<std::pair<std::string, std::string>> kv);
    void noteVecStuckInstalled(uint32_t generation, uint64_t correct_lane,
                               uint64_t stuck_lane, bool cell_allocated);
    void observeVecGeneration(uint32_t generation);
    void noteVecStuckCarrier(uint32_t generation, PhysRegIdPtr phys_reg);
    void emitVecTerminal();
    void registerVecExitFlush();
    static const char *vecRegClassName(int cls);
    // [FR03] Only classes that are actually allocated through the unified
    // free list are legal permanent-cell targets. Misc/predicate/element/
    // matrix/CC classes are excluded (reserved/special, non-allocatable).
    static bool isFreeListClass(RegClassType cls);
    enum class FaultType { BitFlip, StuckAtZero, StuckAtOne, Random };
    enum class Mode { Phys, ArchFrontend, ArchCommit };
    enum class RegClassSel { Integer, FloatingPoint, Vector, Both };
    static RegClassSel stringToRegClassSel(const std::string &s);

    struct PermanentFault {
        FaultType fault_type;
        uint64_t mask;
        bool update;
        // [FR03] The physical space the index belongs to. Int/float/vec are
        // independently numbered from 0; the legacy periodic re-apply only
        // touches IntRegClass (int/float/vec write-path masks are authoritative).
        RegClassType reg_class = InvalidRegClass;
    };

    o3::CPU *cpu;      // dynamic_cast<o3::CPU*> in the .cc
    Mode fi_mode;
    unsigned free_list_size_at_inject = 0;  // diagnostic: numFreeRegs at inject
    uint64_t reads_before_overwrite = 0;   // reads of the INJECTED VALUE (stops at overwrite)
    bool trace_overwritten = false;        // has the injected value been overwritten?
    uint64_t overwritten_at_cycle = 0;     // cycle at which the injected value was overwritten
    bool overwrite_recorded = false;       // have we recorded overwritten_at_cycle?
    int traced_phys_idx = -1;              // phys idx being traced, or -1
    ChaOSL0State l0;   // W2.5 L0 lifecycle state (chaos_l0.hh) — mirrors the
                       // container-side counters; final CHAOS_L0 line from
                       // an exit callback (l0Final)

    // target selection
    int target_phys_idx;     // phys fi_mode; -1 = random
    int target_arch_idx;     // arch_frontend / arch_commit modes
    RegClassSel reg_target_class;  // integer / floating_point / both
    // [FR03] phys mode only: when true, install ONLY on a cell that is
    // currently allocated (not in the free list), i.e. held by an in-flight
    // instruction. Default false keeps every existing campaign byte-identical.
    bool require_allocated;
    // [FR03] requireAllocated retry pacing: a free fixed target must not
    // produce a same-tick retry loop (which once wrote 294M skip lines).
    bool wait_for_allocation = false;
    uint64_t skip_free_count = 0;

    // Phase 2 item 1: NEON lane stratification. The vec path corrupts ONE
    // lane of vec_lane_width bits at lane vec_lane_offset (within the
    // target VecRegClass phys reg), instead of always word0 (low 64 bits).
    int vec_lane_width;   // lane width in bits (8/16/32/64), default 32
    int vec_lane_offset;  // which lane (0-indexed); -1 = random lane

    // fault model
    float probability;
    int num_bits_to_change;
    FaultType fault_type_enum;
    std::bitset<64> fault_mask;
    float bit_flip_prob, stuck_at_zero_prob, stuck_at_one_prob;

    // timing
    Cycles first_clock, last_clock;

    // campaign control
    uint64_t max_faults;
    uint64_t faults_injected_count;
    uint64_t rng_seed;    bool write_log;
    // §1.3/§2.1B F3 data-dependent trigger + semanticRole.
    uint64_t trigger_value_mask = 0;
    uint64_t trigger_value_pattern = 0;
    std::string semantic_role;

    EventFunctionWrapper attackEvent, periodicCheck;
    EventFunctionWrapper readTraceEvent;  // polls read_count after inject

    std::geometric_distribution<unsigned> inter_fault_cycles_dist;
    std::discrete_distribution<int> random_fault_distribution;
    std::mt19937 rng;
    std::random_device rd;

    // permanent faults (keyed by phys reg flatIdx for phys fi_mode, or arch idx
    // for arch modes). For stuck-at via write-path mask, this is used by the
    // periodic re-apply fallback; the preferred stuck mechanism is the
    // write-path mask hook in PhysRegFile::setReg (TODO).
    std::map<std::pair<ThreadID, int>, PermanentFault> permanent_faults;

    OutputStream *log_stream;

    // helpers
    uint64_t generateRandomMask(std::mt19937 &gen, int bits_to_change, int len);
    void processFault(ThreadID tid);
    void scheduleAttackEvent(Cycles delay);
    void unscheduleAttackEvent();
    void scheduleCheckPermanentFault(Cycles delay);
    void checkPermanent();
    void attackCheck();
    void readTraceCheck();          // poll read_count, reschedule until halt
    void l0Final();                 // W2.5: exit-callback CHAOS_L0 line
    const char* faultTypeToString(FaultType f);
    static FaultType stringToFaultType(const std::string &s);
    static Mode stringToMode(const std::string &s);

    struct CHAOSPhysRegStats : public statistics::Group
    {
        statistics::Scalar numFaultsInjected;
        statistics::Scalar numBitFlips;
        statistics::Scalar numStuckAtZero;
        statistics::Scalar numStuckAtOne;
        statistics::Scalar numPermanentFaults;
        CHAOSPhysRegStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSPhysRegStats> stats;
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_PHYS_REG_HH__
