/*
 * CHAOSCov — single-run hardware coverage instrumentation for the
 * Harpocrates reproduction (harp plan Task 1.2; metrics per ISCA'24 §II-D).
 *
 * Two coverage families (definitions mirror the paper exactly):
 *   ACE lifetime (bit arrays: IRF, L1D, LSQ): ACE cycles / total ROI cycles
 *     summed over all bits, i.e. AVF. Upper bound of transient-fault
 *     detection capability.
 *   IBR (functional units): effective input bits delivered to the unit /
 *     theoretical max (full-width inputs at every ROI cycle). Correlates
 *     with (does not bound) permanent gate-level fault detection.
 *
 * ROI gating: m5ops workbegin/workend markers (inserted by tools/harp_wrap.py)
 * flip roi_active. Collection hooks short-circuit when !roi_active.
 * The pseudo_inst.cc side calls harp_cov_notify_work_begin/end() (weak
 * default no-op in CHAOSCov.cc; CHAOSCov registers itself there).
 *
 * This skeleton registers stats + detail dump; per-structure collectors
 * arrive in plan Tasks 2.x/3.x/4.1.
 */
#ifndef __CHAOS_COV_CHAOSCOV_HH__
#define __CHAOS_COV_CHAOSCOV_HH__

#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/statistics.hh"
#include "base/types.hh"

#include <cstdint>
#include <string>
#include <unordered_map>

namespace gem5
{

class CHAOSCovParams;
namespace o3 { class CPU; }
class BaseCache;
class CacheBlk;

// Global ROI notification hooks called from sim/pseudo_inst.cc.
// Defined in CHAOSCov.cc; when no CHAOSCov instance exists they are no-ops.
void harp_cov_notify_work_begin();
void harp_cov_notify_work_end();

// --- IRF ACE collector hooks (Task 2.1; called from regfile.hh/free_list.hh
// inline guarded call sites; no-ops unless CHAOSCov is mounted) ---
// Physical-register lifecycle events. Optimistic mode: a read at execute
// time extends the ACE interval of the value written into the slot.
void harp_cov_on_prf_write(int class_type, int idx);   // setReg int/float
void harp_cov_on_prf_read(int class_type, int idx);    // getReg int/float
void harp_cov_on_prf_alloc(int class_type, int idx);   // freeList getReg
void harp_cov_on_prf_free(int class_type, int idx);    // freeList addReg
bool harp_cov_prf_enabled();  // fast guard for inline hot paths

class CHAOSCov : public SimObject
{
  public:
    CHAOSCov(const CHAOSCovParams &p);
    ~CHAOSCov() override;
    void startup() override;
    // statistics::Group hook: finalize ledgers into stats right before any
    // stats dump. Covers every ROI mode (incl. roi=all/cycles where no
    // m5ops marker fires) without config-script cooperation.
    void preDumpStats() override;

    // ROI state (also read by collector hooks in later tasks)
    static bool roiActive() { return roi_active; }

    // Single-instance pointer (read by the global notify hooks below).
    static CHAOSCov *instance;

    // Target-cache identity for the L1D collector's owner filter.
    static const void *cacheTarget() { return instance ? instance->target_cache : nullptr; }

    // Notification from the global hooks (pseudo_inst workbegin/workend).
    void onWorkBegin();
    void onWorkEnd();

    // --- IRF collector event handlers (called by the hooks above) ---
    void irfOnWrite(int class_type, int idx);
    void irfOnRead(int class_type, int idx);
    void irfOnAlloc(int class_type, int idx);
    void irfOnFree(int class_type, int idx);
    void irfSampleOccupancy();   // per-ROI-cycle histogram sampling
    // Task 2.2 commit-confirmed read: called from Commit per committed
    // instruction per physical source register. Accumulates a second,
    // wrong-path-free ACE ledger (reads by squashed instructions never
    // commit, so they never enter this counter).
    void irfOnCommitRead(int class_type, int idx);

    // --- L1D ACE collector (Task 3.1) ---
    void cacheOnWrite(void *cache, void *blk);
    void cacheOnRead(void *cache, void *blk);
    void cacheOnEvict(void *cache, void *blk);

    // --- LSQ SQ-data ACE collector (Task 3.2) ---
    void sqOnWrite();
    void sqOnConsume();
    void sqOnFree();

    // Per-cycle poll from collectors (cycle-granular ROI bookkeeping).
    void tickROICycles() { if (roi_active) roi_cycles++; }

    uint64_t roiCycles() const { return roi_cycles; }

    // Finalize stats. Called from onWorkEnd (m5ops mode) and from the
    // config script after m5.simulate() returns (roi=all/cycles modes,
    // where no marker ever fires). Idempotent via max() guards.
    void finishStats();

  private:
    o3::CPU *cpu;
    enum class RoiMode { M5Ops, Cycles, All };
    RoiMode roi_mode;
    uint64_t roi_begin_cycle, roi_end_cycle;
    bool write_detail;

    static bool roi_active;         // set/cleared by hooks (or cycle mode)
    uint64_t roi_cycles = 0;

    OutputStream *detail_stream = nullptr;

    // --- IRF ACE collector state (Task 2.1, optimistic mode) ---
    // Per physical register (int and float spaces independently numbered):
    //   value_birth_cycle : cycle the current value was written (setReg),
    //                       or 0 = no live value since ROI start
    //   last_read_cycle   : last optimistic read (getReg at execute time);
    //                       ACE interval = [birth, last_read] (read-extended)
    //   open              : interval currently open (written, not yet free'd
    //                       or overwritten)
    // ACE accounting (paper Fig.3 semantics):
    //   write→read    : ACE  [write, read]
    //   read→read     : ACE  (extends to latest read)
    //   write→write   : un-ACE (overwritten unread → 0 contribution)
    //   read→free     : un-ACE (idle tail until free)
    //   alloc→write   : un-ACE (free-list residency excluded)
    // Only intervals fully inside the ROI count; an interval open at ROI end
    // contributes up to the last read (conservative close).
    struct PrfRegState
    {
        uint64_t birth = 0;
        uint64_t last_read = 0;
        bool has_value = false;   // written, not yet overwritten/freed
        bool ever_read = false;
        // Task 2.2 commit-confirmed mirrors (separate ledger; wrong-path
        // reads extend only the optimistic fields above).
        uint64_t last_commit_read = 0;
        bool ever_commit_read = false;
    };
    std::vector<PrfRegState> irf_state[3];  // [0]=int [1]=float [2]=vector
    uint64_t irf_ace_cycles[3] = {0, 0, 0}; // accumulated ACE cycles (optimistic)
    uint64_t irf_ace_commit_cycles[3] = {0, 0, 0}; // commit-confirmed ledger
    uint64_t irf_live_regs[3]  = {0, 0, 0}; // regs with open interval at ROI end
    // occupancy histogram for the advice engine: samples of
    // (#regs with has_value && ever_read) taken each ROI cycle, bucketed.
    static constexpr int OCC_BUCKETS = 33;  // 0..32+ live-value regs
    std::vector<uint64_t> irf_occ_hist;     // per-bucket cycle counts
    uint64_t irf_occ_samples = 0;

    // --- L1D ACE state (Task 3.1) ---
    // Block-granular interval ledger keyed by CacheBlk pointer (stable
    // for the lifetime of the tags store). The same Fig.3 semantics as
    // the IRF: fill/store opens an interval, demand read extends it,
    // evict or overwrite closes it (unread tail un-ACE).
    struct BlkState
    {
        uint64_t birth = 0;
        uint64_t last_read = 0;
        bool has_value = false;
        bool ever_read = false;
    };
    const void *target_cache = nullptr;    // filter: only this cache
    unsigned cache_num_blocks = 0;         // sizing for AVF denominator
    unsigned cache_block_size = 0;
    std::unordered_map<const void *, BlkState> cache_state;
    uint64_t cache_ace_cycles = 0;
    uint64_t cache_reads = 0, cache_writes = 0, cache_evicts = 0;

    // --- LSQ SQ-data ACE state (Task 3.2) ---
    // Interval ledger keyed by SQ slot index (0..SQEntries-1). The same
    // Fig.3 semantics: data-write opens, consume extends/closes, free
    // closes; a written-but-never-consumed entry (squashed before
    // writeback, no forward) is un-ACE.
    struct SqState
    {
        uint64_t birth = 0;
        uint64_t last_consume = 0;
        bool has_data = false;
        bool ever_consumed = false;
    };
    std::vector<SqState> sq_state;
    unsigned sq_entries = 0;
    uint64_t sq_ace_cycles = 0;
    uint64_t sq_writes = 0, sq_consumes = 0, sq_frees = 0;

  protected:
    struct HarpStats : public statistics::Group
    {
        HarpStats(statistics::Group *parent);
        // --- ROI bookkeeping ---
        statistics::Scalar roiCycles;
        statistics::Scalar roiBeginTick;
        statistics::Scalar roiEndTick;
        // --- IRF ACE (Task 2.1) ---
        statistics::Scalar irfIntAceCycles;
        statistics::Scalar irfFloatAceCycles;
        statistics::Scalar irfVecAceCycles;
        statistics::Scalar irfAvf;         // (int+float+vec ACE) / (bits*T_ROI)
        statistics::Scalar irfAvfInt;
        statistics::Scalar irfAvfFloat;
        statistics::Scalar irfAvfVec;
        // Task 2.2 commit-confirmed variants (wrong-path reads excluded)
        statistics::Scalar irfAvfCommit;
        statistics::Scalar irfAvfCommitInt;
        // --- L1D ACE (Task 3.1) ---
        statistics::Scalar l1dAceCycles;
        statistics::Scalar l1dReads;
        statistics::Scalar l1dWrites;
        statistics::Scalar l1dEvicts;
        statistics::Scalar l1dAvf;
        // --- LSQ SQ-data ACE (Task 3.2) ---
        statistics::Scalar sqAceCycles;
        statistics::Scalar sqWrites;
        statistics::Scalar sqConsumes;
        statistics::Scalar sqFrees;
        statistics::Scalar sqAvf;
    } harpStats;

    void irfFinish();   // close open intervals at ROI end / sim end
};

} // namespace gem5

#endif // __CHAOS_COV_CHAOSCOV_HH__
