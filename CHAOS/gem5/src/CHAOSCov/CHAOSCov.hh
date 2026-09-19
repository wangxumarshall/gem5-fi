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

// --- SDC-ED Task 3.1: SQ per-slot forward + load-use distance hooks ---
// Called from cpu/o3/lsq_unit.cc (forwarding hit / load writeback) and
// cpu/o3/commit.cc (commit-confirmed use). No-ops unless mounted. The
// first three hooks gained a slot_idx parameter (per-slot ledger); their
// legacy aggregate accounting is unchanged.
void harp_cov_on_sq_write(unsigned slot_idx);    // store data → SQ slot
void harp_cov_on_sq_consume(unsigned slot_idx);  // SQ data → memory writeback
void harp_cov_on_sq_free(unsigned slot_idx);     // SQ slot released
void harp_cov_on_sq_forward(unsigned slot_idx);  // store→load forward hit
void harp_cov_on_load_wb(int class_type, int idx);  // load data → PRF write
void harp_cov_on_load_use(int class_type, int idx); // committed consumption

// --- Cache block-ACE ledger types (Task 3.1; SDC-ED Task 2.2 multi-cache) ---
// Block-granular interval state, keyed by CacheBlk pointer (stable for the
// lifetime of the tags store). Same Fig.3 semantics as the IRF: fill/store
// opens an interval, demand read extends it, evict/overwrite closes it
// (unread tail un-ACE).
struct HarpBlkState
{
    uint64_t birth = 0;
    uint64_t last_read = 0;
    bool has_value = false;
    bool ever_read = false;
};
// One ledger per tracked cache. Slot 0 = the legacy targetCache (L1D,
// reported via the l1d* stats, unchanged); slots 1.. = the
// extraTargetCaches list (L2 etc., reported via l2c* stats — the SDC-ED
// L2C-unit collector).
//
// SDC-ED Task 3.3 — data-face/tag-face dual ledger: the ACE interval
// state below stays DATA-FACE only (reads/fills of block data). The tag
// face is a separate counter (tag_reads): how many tag comparisons this
// cache performed. Honest boundary: a tag lookup is NOT an ACE interval
// — reading a tag does not prolong any data bit's required residency —
// so tag_reads is a coverage signal for the ECC-blind tag plane (the
// ρ_L2C(tag)=0.45 vs data-face-SECDED ρ=0 split), never mixed into
// ace_cycles.
struct CacheLedger
{
    const void *cache = nullptr;
    unsigned num_blocks = 0;           // AVF denominator (config-passed)
    unsigned block_size = 0;
    std::unordered_map<const void *, HarpBlkState> state;
    uint64_t ace_cycles = 0;
    uint64_t reads = 0, writes = 0, evicts = 0;
    // SDC-ED Task 3.3: tag-plane lookup counter (one per CPU-side access's
    // tag comparison, hit or miss). Coverage signal only — see above.
    uint64_t tag_reads = 0;
};

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
    // SDC-ED Task 2.2: multi-cache dispatch lives in ledgerFor(); this
    // accessor remains for the first (L1D) ledger.

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
    // SDC-ED Task 3.3: tag-face event — a tag comparison was performed for
    // a CPU-side access (hit or miss; blk may be nullptr on miss). Counts
    // into the ledger's tag_reads; no ACE-interval effect.
    void cacheOnTagAccess(void *cache);
    // SDC-ED Task 2.2: dispatch to the ledger owning this cache instance
    // (nullptr = untracked). Public: the file-level owner-filter hooks in
    // CHAOSCov.cc call it before invoking the handlers.
    CacheLedger *ledgerFor(void *cache);

    // --- LSQ SQ-data ACE collector (Task 3.2; SDC-ED Task 3.1 adds the
    // slot index — the legacy aggregate interval ledger inside these
    // handlers is unchanged, the per-slot forward/wb ledgers are new) ---
    void sqOnWrite(unsigned slot_idx);
    void sqOnConsume(unsigned slot_idx);
    void sqOnFree(unsigned slot_idx);
    // SDC-ED Task 3.1: per-slot forward + load-use-distance collectors.
    // sqOnForward(slot): a load consumed this SQ slot's data IN THE QUEUE
    //   (store→load forwarding) — read-type consumption, kept in a separate
    //   ledger from the writeback consumption (sqOnConsume) so the forward
    //   face and writeback face of SQ-data ACE can be reported apart.
    // loadOnWriteback(class, idx): a load result was written back to the
    //   PRF (birth of the load-use interval). loadOnUse(class, idx): first
    //   commit-confirmed consumption — closes the interval, feeding the
    //   load-use distance histogram.
    void sqOnForward(unsigned slot_idx);
    void loadOnWriteback(int class_type, int idx);
    void loadOnUse(int class_type, int idx);

    // --- IBR collector (Task 4.1) ---
    void fuOnIssue(int fu_class, uint64_t src_bits);
    // SDC-ED Task 3.2: FP value-class profile. Same issue point as
    // fuOnIssue, but the caller (inst_queue.cc, which can safely read the
    // PRF at issue — values are written at execute, wake happens at
    // writeback, so by issue time every source value is resident) also
    // classifies each FP source operand's 64-bit lanes per IEEE754:
    //   0=normal 1=subnormal 2=NaN 3=Inf 4=zero
    // Per-FU-class histogram + normalized Shannon entropy over the five
    // classes. Motivation: CHAOSFPU N=20 all-Masked showed FP software
    // masking is VALUE-dependent — structural coverage (IBR) alone can't
    // distinguish a sequence exercising only normal-normal adds from one
    // that also drives NaN/subnormal/Inf propagation paths.
    void fuOnIssueValue(int fu_class, int n_lanes, const int *lane_class);

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

    // --- L1D/L2 ACE state (Task 3.1; SDC-ED Task 2.2 multi-cache) ---
    // Per-cache ledgers (types defined above the class): slot 0 = legacy
    // targetCache (l1d* stats), slots 1.. = extraTargetCaches (l2c*).
    std::vector<CacheLedger> cache_ledgers;   // [0]=L1D, [1+]=L2/...
    // Legacy single-cache scalars (kept for the constructor's L1D sizing
    // bookkeeping; the live ledgers are cache_ledgers).
    const void *target_cache = nullptr;    // filter: only tracked caches
    unsigned cache_num_blocks = 0;         // sizing for AVF denominator
    unsigned cache_block_size = 0;

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
        // SDC-ED Task 3.1: forward-consumption mirror of the Task 3.2
        // aggregate event stream — the per-slot ledger that eliminates the
        // "close the oldest open interval" approximation for the
        // forwarding face. ever_forwarded marks that this value was read
        // inside the SQ (store→load forwarding), independently of the
        // writeback consumption.
        uint64_t last_forward = 0;
        bool ever_forwarded = false;
    };
    std::vector<SqState> sq_state;
    unsigned sq_entries = 0;
    uint64_t sq_ace_cycles = 0;
    uint64_t sq_writes = 0, sq_consumes = 0, sq_frees = 0;
    // SDC-ED Task 3.1 per-slot forward ledger: forwarding is a read-type
    // consumption of the SQ data (the load reads the store's data IN the
    // queue). ACE split:
    //   sq_fwd_ace_cycles  — intervals closed/extended by forwards
    //   sq_wb_ace_cycles   — intervals closed/extended by writebacks
    // (sq_ace_cycles above remains the legacy aggregate — unchanged stats.)
    uint64_t sq_fwd_ace_cycles = 0;
    uint64_t sq_wb_ace_cycles = 0;
    uint64_t sq_forwards = 0;
    // --- load-use distance state (SDC-ED Task 3.1) ---
    // Birth marks: phys reg slots whose current value was produced by a
    // LOAD writeback and not yet consumed by a committed instruction.
    // loadOnWriteback sets the birth cycle; the first commit-confirmed
    // read of the slot (loadOnUse) closes the interval and buckets
    // (cycle_now - birth). Any intervening producer write clears the mark
    // (the load value was overwritten — interval dead, not counted).
    // Mirrors the irf_state spaces [0]=int [1]=float [2]=vector.
    std::vector<uint64_t> lu_state[3];
    uint64_t lu_samples = 0, lu_dead = 0;
    // Histogram buckets: powers of two up to 2^16, then an open last
    // bucket (16 buckets total: 0,1,2,4,...,32768,>32768).
    static constexpr int LU_BUCKETS = 17;
    uint64_t lu_hist[LU_BUCKETS] = {0};

    // --- IBR state (Task 4.1; SDC-ED Task 2.1 parameterized) ---
    // Numerators per FU class (input bits actually delivered), plus issue
    // counts for the advice engine's instruction-mix evidence.
    static constexpr int NUM_FU_CLASSES = 4;  // IntAdd IntMul FPAdd FPMul
    // SDC-ED Task 2.3: unit-axis size for the covUnits merge vector.
    static constexpr int NUM_ED_UNITS = 7;    // IFU OoO IEX LSU FSU MMU L2C
    uint64_t ibr_input_bits[NUM_FU_CLASSES] = {0, 0, 0, 0};
    uint64_t ibr_issues[NUM_FU_CLASSES]     = {0, 0, 0, 0};
    // Denominator widths per FU class (paper: theoretical max input bits
    // per cycle). Parameterized from the CPU profile (SDC-ED Layer C:
    // configs/cpu-profiles/*.yaml → CHAOSCov.py → here). Defaults are the
    // TaiShan v110 implementation-calibre values (fu_pool.py): FU counts
    // 3/1/2/2, widths IntAdd/IntMul 2x64, FPAdd/FPMul 2x128 (NEON lanes).
    unsigned ibr_fu_count[NUM_FU_CLASSES]   = {3, 1, 2, 2};
    unsigned ibr_full_width[NUM_FU_CLASSES] = {128, 128, 256, 256};

    // --- FP value-class state (SDC-ED Task 3.2) ---
    // [fu_class][value_class] lane counts; only FP classes (2=FPAdd,
    // 3=FPMul) are ever touched. Entropy computed at finishStats.
    static constexpr int NUM_FU_CLASSES_ = 4;
    static constexpr int NUM_VALUE_CLASSES = 5;  // normal subnorm NaN Inf zero
    uint64_t fp_value_hist[NUM_FU_CLASSES][NUM_VALUE_CLASSES] = {};
    uint64_t fp_lanes_sampled = 0;

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
        // --- L2C ACE (SDC-ED Task 2.2: extra caches ledger) ---
        statistics::Scalar l2cAceCycles;
        statistics::Scalar l2cReads;
        statistics::Scalar l2cWrites;
        statistics::Scalar l2cEvicts;
        statistics::Scalar l2cAvf;
        // SDC-ED Task 3.3: data-face/tag-face dual ledger. tagReads counts
        // tag comparisons (tag-plane coverage — the ECC-blind face);
        // tagFaceRatio = tagReads / (reads+writes) normalizes against the
        // data-face event stream. Both are coverage signals, NOT ACE
        // intervals (see CacheLedger for the honest boundary).
        statistics::Scalar l2cTagReads;
        statistics::Scalar l2cTagFaceRatio;
        // --- LSQ SQ-data ACE (Task 3.2) ---
        statistics::Scalar sqAceCycles;
        statistics::Scalar sqWrites;
        statistics::Scalar sqConsumes;
        statistics::Scalar sqFrees;
        statistics::Scalar sqAvf;
        // SDC-ED Task 3.1: forward/writeback face split + load-use distance
        statistics::Scalar sqForwards;
        statistics::Scalar sqForwardAceCycles;
        statistics::Scalar sqWritebackAceCycles;
        statistics::Scalar sqForwardAvf;
        statistics::Vector loadUseDist;
        // --- IBR (Task 4.1) ---
        statistics::Vector ibrInputBits;
        statistics::Vector ibrIssues;
        statistics::Scalar ibrIntAdd;
        statistics::Scalar ibrIntMul;
        statistics::Scalar ibrFpAdd;
        statistics::Scalar ibrFpMul;
        // --- FP value-class profile (SDC-ED Task 3.2) ---
        // Per-FU-class 5-bin histogram of FP source-operand lanes
        // (normal/subnormal/NaN/Inf/zero) + the normalized Shannon
        // entropy over the merged distribution. Value-class coverage is
        // the FSU axis the IBR can't see (software masking is
        // value-dependent — CHAOSFPU all-Masked evidence).
        statistics::Vector fpValueHist;
        statistics::Scalar fpValueEntropy;
        // --- SDC-ED Task 2.3: 7-unit coverage vector ---
        // Per-unit activation coverage A_u, merged from the collectors
        // above for tools/ed_score.py (ED = Σ w_u·ρ_u·q_u·A_u). The unit
        // decomposition is Layer A (CPU-independent); which collector
        // feeds which unit is fixed here, the weights live in the CPU
        // profile (Layer B/C):
        //   [0] IFU  = 0 placeholder (ρ=0 SDC axis per Phase 16; the
        //              predictor-plane signal goes to the Crash axis —
        //              SDC-ED Phase 7/8 may add a BPU collector)
        //   [1] OoO  = irfAvf (width-weighted PRF ACE across the three
        //              register spaces)
        //   [2] IEX  = max(ibrIntAdd, ibrIntMul) — integer FU classes
        //   [3] LSU  = sqAvf (SQ-data ACE; L1D sits on the cache axis)
        //   [4] FSU  = max(ibrFpAdd, ibrFpMul) — FP FU classes
        //   [5] MMU  = 0 placeholder (SE userspace ceiling; FS arm TBD)
        //   [6] L2C  = max(l1dAvf, l2cAvf) — cache hierarchy: the most
        //              activated level's block-ACE AVF
        // Legacy scalar stats above are all kept (harp_eval.py compat).
        statistics::Vector covUnits;
    } harpStats;

    void irfFinish();   // close open intervals at ROI end / sim end
};

} // namespace gem5

#endif // __CHAOS_COV_CHAOSCOV_HH__
