/*
 * CHAOSCov — Harpocrates coverage analyzer, skeleton (Task 1.2).
 * See CHAOSCov.hh for the metric definitions and ROI contract.
 */
#include "CHAOSCov/CHAOSCov.hh"
#include "params/CHAOSCov.hh"
#include "cpu/o3/cpu.hh"
#include "mem/cache/base.hh"
#include "base/trace.hh"
#include "debug/CHAOSCov.hh"

#include <fstream>
#include <iomanip>

namespace gem5
{

// --- static ROI state shared with collector hooks (Tasks 2-4) ---
bool CHAOSCov::roi_active = false;
CHAOSCov *CHAOSCov::instance = nullptr;

// Hot-path guard for the inline hooks in cpu/o3/regfile.hh/free_list.hh.
bool harp_enabled = false;

// Global notification hooks (called from sim/pseudo_inst.cc workbegin/end).
// No instance mounted -> no-ops (zero overhead for non-harp runs).
void harp_cov_notify_work_begin() { if (CHAOSCov::instance) CHAOSCov::instance->onWorkBegin(); }
void harp_cov_notify_work_end()   { if (CHAOSCov::instance) CHAOSCov::instance->onWorkEnd(); }

// --- IRF ACE collector hooks (Task 2.1) — see CHAOSCov.hh for semantics ---
bool harp_cov_prf_enabled() { return CHAOSCov::instance != nullptr; }

void harp_cov_on_prf_write(int class_type, int idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->irfOnWrite(class_type, idx); }

void harp_cov_on_prf_read(int class_type, int idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->irfOnRead(class_type, idx); }

void harp_cov_on_prf_alloc(int class_type, int idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->irfOnAlloc(class_type, idx); }

void harp_cov_on_prf_free(int class_type, int idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->irfOnFree(class_type, idx); }

// Task 2.2: commit-confirmed read (per committed inst, per phys src reg).
void harp_cov_on_prf_commit_read(int class_type, int idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->irfOnCommitRead(class_type, idx); }

// --- IBR collector hooks (Task 4.1) ---
void harp_cov_on_fu_issue(int fu_class, uint64_t src_bits)
{
    if (!CHAOSCov::instance) return;
    CHAOSCov::instance->fuOnIssue(fu_class, src_bits);
}

// --- LSQ SQ-data ACE collector hooks (Task 3.2) ---
void harp_cov_on_sq_write()   { if (CHAOSCov::instance) CHAOSCov::instance->sqOnWrite(); }
void harp_cov_on_sq_consume() { if (CHAOSCov::instance) CHAOSCov::instance->sqOnConsume(); }
void harp_cov_on_sq_free()    { if (CHAOSCov::instance) CHAOSCov::instance->sqOnFree(); }

// --- L1D ACE collector hooks (Task 3.1) ---
// The cache pointer identifies which cache instance fired the event;
// CHAOSCov filters against its configured targetCache.
static inline bool harp_cache_owner(void *cache)
{ return CHAOSCov::instance && cache && CHAOSCov::cacheTarget() == cache; }

void harp_cov_on_cache_write(void *cache, void *blk)
{ if (harp_cache_owner(cache)) CHAOSCov::instance->cacheOnWrite(cache, blk); }

void harp_cov_on_cache_read(void *cache, void *blk)
{ if (harp_cache_owner(cache)) CHAOSCov::instance->cacheOnRead(cache, blk); }

void harp_cov_on_cache_evict(void *cache, void *blk)
{ if (harp_cache_owner(cache)) CHAOSCov::instance->cacheOnEvict(cache, blk); }

// Per-cycle tick from Commit::tick — drives the ROI cycle counter and the
// IRF occupancy sampling (advice-engine evidence).
void harp_cov_on_cycle()
{
    if (!CHAOSCov::instance) return;
    CHAOSCov::instance->tickROICycles();
    if (CHAOSCov::roiActive())
        CHAOSCov::instance->irfSampleOccupancy();
}

CHAOSCov::CHAOSCov(const CHAOSCovParams &p)
    : SimObject(p),
      cpu(dynamic_cast<o3::CPU *>(p.cpu)),
      roi_begin_cycle(p.roiBeginCycle),
      roi_end_cycle(p.roiEndCycle),
      write_detail(p.writeDetail),
      harpStats(this)
{
    if (!cpu)
        throw std::runtime_error(
            "CHAOSCov: cpu is not an O3CPU — O3-only (IRF/LSQ/IQ hooks)");
    if (p.roiMode == "m5ops")       roi_mode = RoiMode::M5Ops;
    else if (p.roiMode == "cycles") roi_mode = RoiMode::Cycles;
    else                            roi_mode = RoiMode::All;

    if (instance)
        warn("CHAOSCov: multiple instances mounted; the last one wins "
             "(ROI hooks are global)\n");
    instance = this;
    // NOTE: irf_state must be sized BEFORE harp_enabled goes true — the
    // regfile/free_list hooks fire during CPU init (before startup()),
    // and an empty vector would segfault on [idx] (measured).
    // Spaces: [0]=int (64b), [1]=float (legacy 32b-ARM FP; AArch64 FP
    // aliases into [2] vector), [2]=vector/NEON (128b — where AArch64
    // fadd/fmul d-registers actually live, per arch/arm/isa/operands.isa
    // FpDest = VectorElem).
    const unsigned n_int = cpu->physRegFile().numIntPhysRegs();
    const unsigned n_flt = cpu->physRegFile().numFloatPhysRegs();
    const unsigned n_vec = cpu->physRegFile().numVecPhysRegs();
    irf_state[0].assign(n_int, PrfRegState{});
    irf_state[1].assign(n_flt, PrfRegState{});
    irf_state[2].assign(n_vec, PrfRegState{});
    irf_occ_hist.assign(OCC_BUCKETS, 0);
    // Task 3.1: target cache + sizing for the AVF denominator.
    // BaseTags::numBlocks is protected and BaseCache params lack size in
    // C++ view, so the config passes cacheNumBlocks explicitly.
    if (p.targetCache) {
        target_cache = p.targetCache;
        cache_block_size = p.targetCache->getBlockSize();
        cache_num_blocks = p.cacheNumBlocks;
    }
    // Task 3.2: SQ sizing (passed from the config; LSQ::SQEntries is
    // private to the LSQ).
    sq_entries = p.sqEntries;
    sq_state.clear();
    // SDC-ED Task 2.1: IBR denominators from the CPU profile (defaults =
    // TaiShan v110 fu_pool values; the .py params carry the same defaults,
    // so behavior is unchanged unless a profile overrides them).
    {
        const auto &counts = p.ibrFuCounts;
        const auto &widths = p.ibrFuWidths;
        if (counts.size() != static_cast<size_t>(NUM_FU_CLASSES)
            || widths.size() != static_cast<size_t>(NUM_FU_CLASSES))
            throw std::runtime_error(
                "CHAOSCov: ibrFuCounts/ibrFuWidths must have exactly 4 "
                "entries [IntAdd, IntMul, FPAdd, FPMul]");
        for (int c = 0; c < NUM_FU_CLASSES; c++) {
            ibr_fu_count[c] = static_cast<unsigned>(counts[c]);
            ibr_full_width[c] = static_cast<unsigned>(widths[c]);
        }
    }
    harp_enabled = true;

    if (roi_mode == RoiMode::All)
        roi_active = true;
}

CHAOSCov::~CHAOSCov()
{
    if (instance == this) {
        instance = nullptr;
        harp_enabled = false;
    }
}

void
CHAOSCov::onWorkBegin()
{
    if (roi_mode != RoiMode::M5Ops)
        return;
    assert(!roi_active);
    roi_active = true;
    harpStats.roiBeginTick = curTick();
    DPRINTF(CHAOSCov, "ROI begin @ tick %llu\n", (unsigned long long)curTick());
}

void
CHAOSCov::onWorkEnd()
{
    if (roi_mode != RoiMode::M5Ops)
        return;
    // Marker pair seen; close the window. (Re-open supported: harp_wrap
    // emits exactly one pair, but keep it robust for multi-ROI workloads.)
    roi_active = false;
    harpStats.roiEndTick = curTick();
    finishStats();
    DPRINTF(CHAOSCov, "ROI end @ tick %llu (roi_cycles=%llu)\n",
            (unsigned long long)curTick(), (unsigned long long)roi_cycles);
}

// Finalize all coverage stats from the raw ledgers. Also the only writer
// of the detail dump. Called from onWorkEnd (m5ops) and from the config
// script post-simulate (roi=all/cycles); idempotent for the ledgers
// because the raw counters are monotone and the scalars simply take the
// final values.
void
CHAOSCov::finishStats()
{
    irfFinish();
    harpStats.roiCycles = roi_cycles;
    harpStats.irfIntAceCycles = irf_ace_cycles[0];
    harpStats.irfFloatAceCycles = irf_ace_cycles[1];
    harpStats.irfVecAceCycles = irf_ace_cycles[2];
    // AVF per the paper's definition: ACE cycles summed over all bits of
    // the structure / (total bits * exposure window). Width-weighted:
    // int/float 64b, vector 128b (NEON).
    const double w[3] = {64.0, 64.0, 128.0};
    double bits_total = 0, bits_ace = 0;
    for (int c = 0; c < 3; c++) {
        bits_total += (double)irf_state[c].size() * w[c] * roi_cycles;
        bits_ace += (double)irf_ace_cycles[c] * w[c];
    }
    if (roi_cycles > 0 && bits_total > 0) {
        harpStats.irfAvf = bits_ace / bits_total;
        harpStats.irfAvfInt =
            (double)irf_ace_cycles[0] * w[0]
            / ((double)irf_state[0].size() * w[0] * roi_cycles);
        harpStats.irfAvfFloat =
            irf_state[1].size()
                ? (double)irf_ace_cycles[1] * w[1]
                      / ((double)irf_state[1].size() * w[1] * roi_cycles)
                : 0.0;
        harpStats.irfAvfVec =
            irf_state[2].size()
                ? (double)irf_ace_cycles[2] * w[2]
                      / ((double)irf_state[2].size() * w[2] * roi_cycles)
                : 0.0;
        double bits_ace_c = 0;
        for (int c = 0; c < 3; c++)
            bits_ace_c += (double)irf_ace_commit_cycles[c] * w[c];
        harpStats.irfAvfCommit = bits_ace_c / bits_total;
        harpStats.irfAvfCommitInt =
            irf_state[0].size()
                ? (double)irf_ace_commit_cycles[0] * w[0]
                      / ((double)irf_state[0].size() * w[0] * roi_cycles)
                : 0.0;
    }
    // L1D ACE stats
    harpStats.l1dAceCycles = cache_ace_cycles;
    harpStats.l1dReads = cache_reads;
    harpStats.l1dWrites = cache_writes;
    harpStats.l1dEvicts = cache_evicts;
    if (roi_cycles > 0 && cache_num_blocks > 0)
        harpStats.l1dAvf =
            (double)cache_ace_cycles
            / ((double)cache_num_blocks * (double)roi_cycles);
    harpStats.sqAceCycles = sq_ace_cycles;
    harpStats.sqWrites = sq_writes;
    harpStats.sqConsumes = sq_consumes;
    harpStats.sqFrees = sq_frees;
    if (roi_cycles > 0 && sq_entries > 0)
        harpStats.sqAvf =
            (double)sq_ace_cycles / ((double)sq_entries * (double)roi_cycles);
    // IBR (paper: input bits / theoretical max at every ROI cycle).
    for (int c = 0; c < 4; c++) {
        harpStats.ibrInputBits[c] = ibr_input_bits[c];
        harpStats.ibrIssues[c] = ibr_issues[c];
    }
    const double denom[4] = {
        (double)ibr_full_width[0] * ibr_fu_count[0] * (double)roi_cycles,
        (double)ibr_full_width[1] * ibr_fu_count[1] * (double)roi_cycles,
        (double)ibr_full_width[2] * ibr_fu_count[2] * (double)roi_cycles,
        (double)ibr_full_width[3] * ibr_fu_count[3] * (double)roi_cycles};
    if (roi_cycles > 0) {
        harpStats.ibrIntAdd = denom[0] ? (double)ibr_input_bits[0] / denom[0] : 0;
        harpStats.ibrIntMul = denom[1] ? (double)ibr_input_bits[1] / denom[1] : 0;
        harpStats.ibrFpAdd  = denom[2] ? (double)ibr_input_bits[2] / denom[2] : 0;
        harpStats.ibrFpMul  = denom[3] ? (double)ibr_input_bits[3] / denom[3] : 0;
    }
    if (detail_stream && detail_stream->stream()) {
        auto &os = *(detail_stream->stream());
        os << "# finish roi_cycles " << roi_cycles << "\n";
        // IRF detail block (advice-engine evidence)
        os << "irf int_regs " << irf_state[0].size()
           << " float_regs " << irf_state[1].size()
           << " vec_regs " << irf_state[2].size() << "\n";
        os << "irf int_ace_cycles " << irf_ace_cycles[0]
           << " float_ace_cycles " << irf_ace_cycles[1]
           << " vec_ace_cycles " << irf_ace_cycles[2] << "\n";
        os << "irf int_ace_commit_cycles " << irf_ace_commit_cycles[0]
           << " float_ace_commit_cycles " << irf_ace_commit_cycles[1]
           << " vec_ace_commit_cycles " << irf_ace_commit_cycles[2] << "\n";
        os << "irf live_at_end int " << irf_live_regs[0]
           << " float " << irf_live_regs[1]
           << " vec " << irf_live_regs[2] << "\n";
        os << "irf occupancy_hist (bucket=live/8)";
        for (auto b : irf_occ_hist) os << " " << b;
        os << "\n";
        os << "l1d blocks " << cache_num_blocks
           << " block_size " << cache_block_size
           << " ace_cycles " << cache_ace_cycles
           << " reads " << cache_reads
           << " writes " << cache_writes
           << " evicts " << cache_evicts << "\n";
        os << "sq entries " << sq_entries
           << " ace_cycles " << sq_ace_cycles
           << " writes " << sq_writes
           << " consumes " << sq_consumes
           << " frees " << sq_frees << "\n";
        os << "ibr";
        for (int c = 0; c < 4; c++)
            os << " " << ibr_input_bits[c] << "/" << ibr_issues[c];
        os << "\n";
    }
}

// ---------------------------------------------------------------------------
// IRF ACE collector (Task 2.1, optimistic mode)
// ---------------------------------------------------------------------------
// Cycle-granularity: all events use cpu->curCycle() (== roi_cycles clock).
// The interval accounting is exactly the paper's Fig.3 semantics adapted to
// a rename-based PRF: a phys slot's value is ACE from write until its last
// read; idle time after the last read (until free/overwrite) is un-ACE.

void
CHAOSCov::irfOnWrite(int class_type, int idx)
{
    if (!roi_active) return;
    auto &st = irf_state[class_type][idx];
    const uint64_t now = roi_cycles;
    // Close the previous value's interval: if it was read at least once,
    // its ACE contribution [birth, last_read] has already been accumulated
    // incrementally at each read (see irfOnRead); if never read, it
    // contributes nothing (write→write overwrite = un-ACE).
    // Start the new value's interval.
    st.birth = now;
    st.last_read = now;
    st.has_value = true;
    st.ever_read = false;
    st.last_commit_read = now;
    st.ever_commit_read = false;
}

void
CHAOSCov::irfOnRead(int class_type, int idx)
{
    if (!roi_active) return;
    auto &st = irf_state[class_type][idx];
    if (!st.has_value) return;    // read of a slot with no ROI value (e.g.
                                  // value written before ROI): treat the
                                  // readable residency as ACE from ROI start
    const uint64_t now = roi_cycles;
    if (!st.ever_read) {
        // First read: accumulate [birth, now] (write→read interval).
        irf_ace_cycles[class_type] += now - st.birth;
        st.ever_read = true;
    } else {
        // read→read: extend to now.
        irf_ace_cycles[class_type] += now - st.last_read;
    }
    st.last_read = now;
}

void
CHAOSCov::irfOnCommitRead(int class_type, int idx)
{
    if (!roi_active) return;
    auto &st = irf_state[class_type][idx];
    if (!st.has_value) return;
    const uint64_t now = roi_cycles;
    if (!st.ever_commit_read) {
        irf_ace_commit_cycles[class_type] += now - st.birth;
        st.ever_commit_read = true;
    } else {
        irf_ace_commit_cycles[class_type] += now - st.last_commit_read;
    }
    st.last_commit_read = now;
}

void
CHAOSCov::irfOnAlloc(int class_type, int idx)
{
    // Allocation itself is un-ACE (free-list residency). Nothing to do:
    // the interval only starts at write. Reset stale state defensively.
    auto &st = irf_state[class_type][idx];
    st.has_value = false;
    st.ever_read = false;
}

void
CHAOSCov::irfOnFree(int class_type, int idx)
{
    // Freeing closes any open interval; unread tail (last_read..free) is
    // un-ACE and was never accumulated. has_value=false stops future reads.
    auto &st = irf_state[class_type][idx];
    st.has_value = false;
}

void
CHAOSCov::irfFinish()
{
    // ROI end: values still open with reads (read→ROI-end tail is un-ACE —
    // the paper's analysis stops at the last confirmed use). Nothing to
    // add; just count how many intervals were live for the detail dump.
    for (int c = 0; c < 3; c++) {
        irf_live_regs[c] = 0;
        for (auto &st : irf_state[c])
            if (st.has_value) irf_live_regs[c]++;
    }
}

void
CHAOSCov::irfSampleOccupancy()
{
    // Advice-engine evidence: histogram of live-value registers per cycle.
    unsigned live = 0;
    for (int c = 0; c < 3; c++)
        for (auto &st : irf_state[c])
            if (st.has_value) live++;
    unsigned bucket = std::min<unsigned>(live / 8, OCC_BUCKETS - 1);
    irf_occ_hist[bucket]++;
    irf_occ_samples++;
}

CHAOSCov::HarpStats::HarpStats(statistics::Group *parent)
    : statistics::Group(parent, "harp"),
      ADD_STAT(roiCycles, statistics::units::Cycle::get(),
               "Cycles inside the ROI window"),
      ADD_STAT(roiBeginTick, statistics::units::Tick::get(),
               "Tick of the first workbegin marker (m5ops ROI mode)"),
      ADD_STAT(roiEndTick, statistics::units::Tick::get(),
               "Tick of the workend marker (m5ops ROI mode)"),
      ADD_STAT(irfIntAceCycles, statistics::units::Cycle::get(),
               "IRF ACE cycles accumulated over int phys regs (optimistic)"),
      ADD_STAT(irfFloatAceCycles, statistics::units::Cycle::get(),
               "IRF ACE cycles accumulated over float phys regs (optimistic)"),
      ADD_STAT(irfVecAceCycles, statistics::units::Cycle::get(),
               "IRF ACE cycles accumulated over vector phys regs (optimistic) —"
               " AArch64 FP/SIMD regs live here"),
      ADD_STAT(irfAvf, statistics::units::Ratio::get(),
               "IRF AVF = (int+float ACE cycles) / ((int+float regs) * ROI "
               "cycles). Paper: ACE lifetime analysis (upper bound of "
               "transient-fault detection)"),
      ADD_STAT(irfAvfInt, statistics::units::Ratio::get(),
               "IRF AVF, int space"),
      ADD_STAT(irfAvfFloat, statistics::units::Ratio::get(),
               "IRF AVF, float space"),
      ADD_STAT(irfAvfVec, statistics::units::Ratio::get(),
               "IRF AVF, vector space (AArch64 FP/SIMD)"),
      ADD_STAT(irfAvfCommit, statistics::units::Ratio::get(),
               "IRF AVF, commit-confirmed reads only (wrong-path excluded)"),
      ADD_STAT(irfAvfCommitInt, statistics::units::Ratio::get(),
               "IRF AVF int space, commit-confirmed"),
      ADD_STAT(l1dAceCycles, statistics::units::Cycle::get(),
               "L1D ACE cycles accumulated over blocks (block-granular)"),
      ADD_STAT(l1dReads, statistics::units::Count::get(),
               "L1D demand reads observed by the collector"),
      ADD_STAT(l1dWrites, statistics::units::Count::get(),
               "L1D fills + store-data updates observed"),
      ADD_STAT(l1dEvicts, statistics::units::Count::get(),
               "L1D evictions observed"),
      ADD_STAT(l1dAvf, statistics::units::Ratio::get(),
               "L1D AVF = block ACE cycles / (numBlocks * ROI cycles). "
               "Paper: ACE lifetime analysis for caches"),
      ADD_STAT(sqAceCycles, statistics::units::Cycle::get(),
               "SQ data-field ACE cycles (aggregate interval ledger)"),
      ADD_STAT(sqWrites, statistics::units::Count::get(),
               "Store data writes into SQ entries"),
      ADD_STAT(sqConsumes, statistics::units::Count::get(),
               "SQ data consumptions (writebacks + forwards)"),
      ADD_STAT(sqFrees, statistics::units::Count::get(),
               "SQ entry frees (completions/squashes)"),
      ADD_STAT(sqAvf, statistics::units::Ratio::get(),
               "SQ AVF = ACE cycles / (SQEntries * ROI cycles). Paper: "
               "SQ-data ACE (Micro'26 adds the LSQ as a bit-array)"),
      ADD_STAT(ibrInputBits, statistics::units::Bit::get(),
               "IBR numerator: input bits delivered per FU class "
               "[0=IntAdd 1=IntMul 2=FPAdd 3=FPMul]"),
      ADD_STAT(ibrIssues, statistics::units::Count::get(),
               "Issues per FU class (instruction-mix evidence)"),
      ADD_STAT(ibrIntAdd, statistics::units::Ratio::get(),
               "IBR IntAdd = input bits / (128 * instances * ROI cycles)"),
      ADD_STAT(ibrIntMul, statistics::units::Ratio::get(),
               "IBR IntMul = input bits / (128 * instances * ROI cycles)"),
      ADD_STAT(ibrFpAdd, statistics::units::Ratio::get(),
               "IBR FPAdd = input bits / (256 * instances * ROI cycles)"),
      ADD_STAT(ibrFpMul, statistics::units::Ratio::get(),
               "IBR FPMul = input bits / (256 * instances * ROI cycles)")
{
    ibrInputBits.init(NUM_FU_CLASSES);
    ibrInputBits.subname(0, "IntAdd");
    ibrInputBits.subname(1, "IntMul");
    ibrInputBits.subname(2, "FPAdd");
    ibrInputBits.subname(3, "FPMul");
    ibrIssues.init(NUM_FU_CLASSES);
    ibrIssues.subname(0, "IntAdd");
    ibrIssues.subname(1, "IntMul");
    ibrIssues.subname(2, "FPAdd");
    ibrIssues.subname(3, "FPMul");
}

// ---------------------------------------------------------------------------
// IBR collector (Task 4.1)
// ---------------------------------------------------------------------------
void
CHAOSCov::fuOnIssue(int fu_class, uint64_t src_bits)
{
    if (!roi_active) return;
    if (fu_class < 0 || fu_class >= NUM_FU_CLASSES) return;
    ibr_input_bits[fu_class] += src_bits;
    ibr_issues[fu_class]++;
}

// ---------------------------------------------------------------------------
// LSQ SQ-data ACE collector (Task 3.2)
// ---------------------------------------------------------------------------
// Slot identity: the O3 storeQueue is a circular buffer; the data array is
// per-slot and stable, so we track the aggregate ledger with a simple
// open-interval count: each write opens an interval, consume extends all
// open intervals (conservative — exact per-slot tracking would need the
// slot index through the forwarding path, which the gem5 API doesn't
// expose cheaply; the aggregate approximates the paper's SQ-data AVF from
// above for the forward part and exactly for the writeback part).
//   NOTE (honest boundary): this is an aggregate approximation. Per-slot
//   exact tracking is deferred to Task 7.4 documentation.
struct HarpSqOpenInterval
{
    uint64_t birth;
    bool consumed;
};
static std::vector<HarpSqOpenInterval> harp_sq_open;

void
CHAOSCov::sqOnWrite()
{
    if (!roi_active) return;
    sq_writes++;
    harp_sq_open.push_back({roi_cycles, false});
}

void
CHAOSCov::sqOnConsume()
{
    if (!roi_active) return;
    // A consume event closes ONE open interval (the SQ drains roughly in
    // order). We close the oldest, accumulating [birth, now] if it was
    // never consumed before (first consume), else extending.
    if (!harp_sq_open.empty()) {
        auto &iv = harp_sq_open.front();
        sq_ace_cycles += roi_cycles - iv.birth;
        harp_sq_open.erase(harp_sq_open.begin());
    }
    sq_consumes++;
}

void
CHAOSCov::sqOnFree()
{
    if (!roi_active) return;
    sq_frees++;
    // Free without consume (squashed, never forwarded/written back):
    // un-ACE — drop the oldest open interval without accumulating.
    if (!harp_sq_open.empty())
        harp_sq_open.erase(harp_sq_open.begin());
}

// ---------------------------------------------------------------------------
// L1D ACE collector (Task 3.1, block-granular Fig.3 semantics)
// ---------------------------------------------------------------------------
void
CHAOSCov::cacheOnWrite(void *cache, void *blk)
{
    if (!roi_active) return;
    cache_writes++;
    auto &st = cache_state[blk];
    const uint64_t now = roi_cycles;
    // Overwrite closes the previous interval exactly as in the IRF: an
    // interval that was read has already been accumulated; an unread one
    // contributes nothing (write→write = un-ACE).
    st.birth = now;
    st.last_read = now;
    st.has_value = true;
    st.ever_read = false;
}

void
CHAOSCov::cacheOnRead(void *cache, void *blk)
{
    if (!roi_active) return;
    auto it = cache_state.find(blk);
    if (it == cache_state.end()) return;   // block never written in ROI
    auto &st = it->second;
    if (!st.has_value) return;
    const uint64_t now = roi_cycles;
    if (!st.ever_read) {
        cache_ace_cycles += now - st.birth;
        st.ever_read = true;
    } else {
        cache_ace_cycles += now - st.last_read;
    }
    st.last_read = now;
    cache_reads++;
}

void
CHAOSCov::cacheOnEvict(void *cache, void *blk)
{
    if (!roi_active) return;
    cache_evicts++;
    auto it = cache_state.find(blk);
    if (it != cache_state.end())
        it->second.has_value = false;   // unread tail un-ACE; state kept
}

void
CHAOSCov::preDumpStats()
{
    finishStats();
}

void
CHAOSCov::startup()
{
    if (write_detail) {
        detail_stream = simout.create("harp_cov_detail.log", false, true);
        if (!detail_stream || !detail_stream->stream())
            panic("CHAOSCov: could not open harp_cov_detail.log");
    }
    DPRINTF(CHAOSCov, "CHAOSCov started, roiMode=%d, intRegs=%zu fltRegs=%zu\n",
            (int)roi_mode, irf_state[0].size(), irf_state[1].size());
}

} // namespace gem5
