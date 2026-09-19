/*
 * CHAOSCov — Harpocrates coverage analyzer, skeleton (Task 1.2).
 * See CHAOSCov.hh for the metric definitions and ROI contract.
 */
#include "CHAOSCov/CHAOSCov.hh"
#include "params/CHAOSCov.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/dyn_inst.hh"
#include "mem/cache/base.hh"
#include "base/trace.hh"
#include "debug/CHAOSCov.hh"

#include <algorithm>
#include <cmath>
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

// SDC-ED Task 3.2: FP value-class lanes from the issue point.
void harp_cov_on_fu_issue_value(int fu_class, int n_lanes, const int *cls)
{
    if (!CHAOSCov::instance) return;
    CHAOSCov::instance->fuOnIssueValue(fu_class, n_lanes, cls);
}

// SDC-ED Task 4.1/4.2: dynamic-slice node from the commit point.
void harp_cov_on_slice_commit(const o3::DynInstPtr &inst)
{
    if (!CHAOSCov::instance) return;
    CHAOSCov::instance->sliceOnCommit(inst);
}

// --- LSQ SQ-data ACE collector hooks (Task 3.2; SDC-ED Task 3.1 adds
// the slot index — the legacy aggregate ledger inside the handlers is
// unchanged) ---
void harp_cov_on_sq_write(unsigned slot_idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->sqOnWrite(slot_idx); }
void harp_cov_on_sq_consume(unsigned slot_idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->sqOnConsume(slot_idx); }
void harp_cov_on_sq_free(unsigned slot_idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->sqOnFree(slot_idx); }

// --- SDC-ED Task 3.1: per-slot forward + load-use distance hooks ---
void harp_cov_on_sq_forward(unsigned slot_idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->sqOnForward(slot_idx); }
void harp_cov_on_load_wb(int class_type, int idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->loadOnWriteback(class_type, idx); }
void harp_cov_on_load_use(int class_type, int idx)
{ if (CHAOSCov::instance) CHAOSCov::instance->loadOnUse(class_type, idx); }

// --- L1D/L2 ACE collector hooks (Task 3.1; SDC-ED Task 2.2 multi-cache) ---
// The cache pointer identifies which cache instance fired the event;
// CHAOSCov dispatches to the ledger whose cache matches (owner filter:
// untracked caches — I$, other levels — are ignored).
static inline bool harp_cache_owner(void *cache)
{ return CHAOSCov::instance && cache && CHAOSCov::instance->ledgerFor(cache); }

void harp_cov_on_cache_write(void *cache, void *blk)
{ if (harp_cache_owner(cache)) CHAOSCov::instance->cacheOnWrite(cache, blk); }

void harp_cov_on_cache_read(void *cache, void *blk)
{ if (harp_cache_owner(cache)) CHAOSCov::instance->cacheOnRead(cache, blk); }

void harp_cov_on_cache_evict(void *cache, void *blk)
{ if (harp_cache_owner(cache)) CHAOSCov::instance->cacheOnEvict(cache, blk); }

// SDC-ED Task 3.3: tag-face event — a tag comparison was performed by this
// cache for a CPU-side access (fired from BaseCache::access right after
// tags->accessBlock, so exactly once per CPU-side access regardless of
// hit/miss). Counts tag-plane coverage; no ACE-interval effect.
void harp_cov_on_cache_tag_access(void *cache)
{ if (harp_cache_owner(cache)) CHAOSCov::instance->cacheOnTagAccess(cache); }

// Per-cycle tick from Commit::tick — drives the ROI cycle counter and the
// IRF occupancy sampling (advice-engine evidence). SDC-ED Task 3.4: also
// buckets the ROB occupancy band (in-flight / capacity, 8 bands of 12.5%).
void harp_cov_on_cycle(int rob_in_flight, int rob_max)
{
    if (!CHAOSCov::instance) return;
    CHAOSCov::instance->tickROICycles();
    if (CHAOSCov::roiActive())
        CHAOSCov::instance->irfSampleOccupancy();
    if (CHAOSCov::roiActive() && rob_max > 0) {
        unsigned band = (unsigned)((long long)rob_in_flight * 8 / rob_max);
        if (band > 7) band = 7;
        CHAOSCov::instance->robOccSample(band);
    }
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
    // SDC-ED Task 2.2: slot 0 = legacy targetCache (l1d* stats); the
    // extraTargetCaches list appends independent ledgers (l2c* stats).
    cache_ledgers.clear();
    if (p.targetCache) {
        target_cache = p.targetCache;
        cache_block_size = p.targetCache->getBlockSize();
        cache_num_blocks = p.cacheNumBlocks;
        CacheLedger led;
        led.cache = p.targetCache;
        led.block_size = cache_block_size;
        led.num_blocks = cache_num_blocks;
        cache_ledgers.push_back(led);
    }
    {
        const auto &extras = p.extraTargetCaches;
        const auto &extra_blocks = p.extraCacheNumBlocks;
        if (extras.size() != extra_blocks.size())
            throw std::runtime_error(
                "CHAOSCov: extraTargetCaches and extraCacheNumBlocks must "
                "have equal length");
        for (size_t i = 0; i < extras.size(); i++) {
            if (!extras[i])
                throw std::runtime_error(
                    "CHAOSCov: extraTargetCaches contains NULL");
            CacheLedger led;
            led.cache = extras[i];
            led.block_size = extras[i]->getBlockSize();
            led.num_blocks = static_cast<unsigned>(extra_blocks[i]);
            cache_ledgers.push_back(led);
        }
    }
    // Task 3.2: SQ sizing (passed from the config; LSQ::SQEntries is
    // private to the LSQ).
    sq_entries = p.sqEntries;
    sq_state.clear();
    sq_state.resize(sq_entries);
    // SDC-ED Task 3.1: load-use birth marks mirror the IRF spaces (the
    // load-use interval lives in the PRF; [0]=int [1]=float [2]=vector).
    for (int c = 0; c < 3; c++)
        lu_state[c].assign(irf_state[c].size(), 0);
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
    // SDC-ED Task 4.2: solve the dynamic slice, then close the SDC-ACE
    // ledgers by re-classifying the logged commit reads.
    solveSliceAndSdc();
    if (roi_cycles > 0 && bits_total > 0) {
        double bits_sdc = 0;
        for (int c = 0; c < 3; c++)
            bits_sdc += (double)irf_ace_sdc_cycles[c] * w[c];
        harpStats.irfAvfSdc = bits_sdc / bits_total;
        harpStats.irfAvfSdcInt =
            irf_state[0].size()
                ? (double)irf_ace_sdc_cycles[0] * w[0]
                      / ((double)irf_state[0].size() * w[0] * roi_cycles)
                : 0.0;
        // Gap baseline = the COMMIT-CONFIRMED ACE ledger (same read
        // stream the SDC replay rides — the optimistic ledger would
        // mix in wrong-path reads and can even be smaller than the
        // commit ledger, producing negative gaps; measured).
        double bits_ace_cc = 0;
        for (int c = 0; c < 3; c++)
            bits_ace_cc += (double)irf_ace_commit_cycles[c] * w[c];
        harpStats.sdcGap = bits_ace_cc
            ? (bits_ace_cc - bits_sdc) / bits_ace_cc : 0.0;
    }
    harpStats.sdcOnPathReads = sdc_on_path_reads;
    harpStats.sdcTotalReads = sdc_total_reads;
    // L1D ACE stats (ledger 0 = legacy targetCache)
    {
        uint64_t ace = 0, rd = 0, wr = 0, ev = 0;
        unsigned blocks = 0;
        if (!cache_ledgers.empty()) {
            ace = cache_ledgers[0].ace_cycles;
            rd = cache_ledgers[0].reads;
            wr = cache_ledgers[0].writes;
            ev = cache_ledgers[0].evicts;
            blocks = cache_ledgers[0].num_blocks;
        }
        harpStats.l1dAceCycles = ace;
        harpStats.l1dReads = rd;
        harpStats.l1dWrites = wr;
        harpStats.l1dEvicts = ev;
        if (roi_cycles > 0 && blocks > 0)
            harpStats.l1dAvf =
                (double)ace / ((double)blocks * (double)roi_cycles);
    }
    // L2C ACE stats (aggregate over extra ledgers; SDC-ED Task 2.2;
    // SDC-ED Task 3.3 adds the tag-face counter and ratio)
    {
        uint64_t ace = 0, rd = 0, wr = 0, ev = 0, trd = 0;
        double blocks_total = 0;
        for (size_t i = 1; i < cache_ledgers.size(); i++) {
            ace += cache_ledgers[i].ace_cycles;
            rd += cache_ledgers[i].reads;
            wr += cache_ledgers[i].writes;
            ev += cache_ledgers[i].evicts;
            trd += cache_ledgers[i].tag_reads;
            blocks_total += (double)cache_ledgers[i].num_blocks;
        }
        harpStats.l2cAceCycles = ace;
        harpStats.l2cReads = rd;
        harpStats.l2cWrites = wr;
        harpStats.l2cEvicts = ev;
        harpStats.l2cTagReads = trd;
        // tag-face ratio: tag comparisons per data-face event (reads+
        // writes). > 1 is expected — every access does one tag lookup,
        // while a data event only fires on fill/read-hit/writeback.
        // Honest boundary: coverage signal for the ECC-blind tag plane
        // (ρ_L2C tag 0.45 vs data SECDED 0.0), NOT an ACE interval.
        const uint64_t data_events = rd + wr;
        harpStats.l2cTagFaceRatio =
            data_events ? (double)trd / (double)data_events : 0.0;
        if (roi_cycles > 0 && blocks_total > 0)
            harpStats.l2cAvf =
                (double)ace / (blocks_total * (double)roi_cycles);
    }
    harpStats.sqAceCycles = sq_ace_cycles;
    harpStats.sqWrites = sq_writes;
    harpStats.sqConsumes = sq_consumes;
    harpStats.sqFrees = sq_frees;
    if (roi_cycles > 0 && sq_entries > 0)
        harpStats.sqAvf =
            (double)sq_ace_cycles / ((double)sq_entries * (double)roi_cycles);
    // SDC-ED Task 3.1: per-slot forward/wb face split + load-use histogram
    harpStats.sqForwards = sq_forwards;
    harpStats.sqForwardAceCycles = sq_fwd_ace_cycles;
    harpStats.sqWritebackAceCycles = sq_wb_ace_cycles;
    if (roi_cycles > 0 && sq_entries > 0)
        harpStats.sqForwardAvf =
            (double)sq_fwd_ace_cycles
            / ((double)sq_entries * (double)roi_cycles);
    for (int b = 0; b < LU_BUCKETS; b++)
        harpStats.loadUseDist[b] = lu_hist[b];
    // SDC-ED Task 3.4: rename distance + ROB occupancy bands
    for (int b = 0; b < RD_BUCKETS; b++)
        harpStats.renameDist[b] = rd_hist[b];
    for (int b = 0; b < 8; b++)
        harpStats.robOccBands[b] = rob_occ_hist[b];
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
    // SDC-ED Task 2.3: merge the per-collector stats into the 7-unit
    // coverage vector (mapping fixed in CHAOSCov.hh's covUnits comment).
    // Read back the scalar stats just finalized — the merge is derived,
    // never double-counted from raw ledgers, so it stays consistent with
    // the legacy stats by construction.
    {
        const double irf_avf = roi_cycles ? harpStats.irfAvf.value() : 0.0;
        const double iex = std::max(harpStats.ibrIntAdd.value(),
                                    harpStats.ibrIntMul.value());
        const double fsu = std::max(harpStats.ibrFpAdd.value(),
                                    harpStats.ibrFpMul.value());
        const double l2c = std::max(harpStats.l1dAvf.value(),
                                    harpStats.l2cAvf.value());
        harpStats.covUnits[0] = 0.0;   // IFU: Crash axis (ρ=0, Phase 16)
        harpStats.covUnits[1] = irf_avf;
        harpStats.covUnits[2] = iex;
        harpStats.covUnits[3] = roi_cycles ? harpStats.sqAvf.value() : 0.0;
        harpStats.covUnits[4] = fsu;
        harpStats.covUnits[5] = 0.0;   // MMU: SE userspace ceiling
        harpStats.covUnits[6] = l2c;
    }
    // SDC-ED Task 3.2: FP value-class histogram + entropy (merged over
    // the two FP FU classes; per-class rows in the detail dump).
    {
        uint64_t merged[NUM_VALUE_CLASSES] = {0, 0, 0, 0, 0};
        for (int fc = 0; fc < NUM_FU_CLASSES; fc++)
            for (int vc = 0; vc < NUM_VALUE_CLASSES; vc++) {
                harpStats.fpValueHist[fc * NUM_VALUE_CLASSES + vc] =
                    fp_value_hist[fc][vc];
                if (fc >= 2) merged[vc] += fp_value_hist[fc][vc];
            }
        uint64_t total = 0;
        for (int vc = 0; vc < NUM_VALUE_CLASSES; vc++) total += merged[vc];
        double entropy = 0.0;
        if (total > 0) {
            for (int vc = 0; vc < NUM_VALUE_CLASSES; vc++) {
                if (!merged[vc]) continue;
                const double p = (double)merged[vc] / (double)total;
                entropy -= p * std::log2(p);
            }
            entropy /= std::log2((double)NUM_VALUE_CLASSES);  // normalize
        }
        harpStats.fpValueEntropy = entropy;
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
        for (size_t i = 0; i < cache_ledgers.size(); i++) {
            const auto &led = cache_ledgers[i];
            os << (i == 0 ? "l1d" : "l2c") << " cache " << i
               << " blocks " << led.num_blocks
               << " block_size " << led.block_size
               << " ace_cycles " << led.ace_cycles
               << " reads " << led.reads
               << " writes " << led.writes
               << " evicts " << led.evicts
               << " tag_reads " << led.tag_reads << "\n";
        }
        os << "sq entries " << sq_entries
           << " ace_cycles " << sq_ace_cycles
           << " writes " << sq_writes
           << " consumes " << sq_consumes
           << " frees " << sq_frees << "\n";
        // SDC-ED Task 3.1 detail: forward/wb face split + load-use hist
        os << "sq_fwd forwards " << sq_forwards
           << " fwd_ace_cycles " << sq_fwd_ace_cycles
           << " wb_ace_cycles " << sq_wb_ace_cycles << "\n";
        os << "load_use samples " << lu_samples
           << " hist (buckets 0,1,2,4,...,32768,>32768)";
        for (int b = 0; b < LU_BUCKETS; b++)
            os << " " << lu_hist[b];
        os << "\n";
        // SDC-ED Task 3.4: OoO evidence — rename distance + ROB bands
        os << "rename_dist hist (buckets 0,1,2,4,...,32768,>32768)";
        for (int b = 0; b < RD_BUCKETS; b++)
            os << " " << rd_hist[b];
        os << "\n";
        os << "rob_occ bands (0-12.5%,...,87.5-100%)";
        for (int b = 0; b < 8; b++)
            os << " " << rob_occ_hist[b];
        os << "\n";
        // SDC-ED Task 4.2: slice + SDC-ACE evidence
        os << "sdc slice_nodes " << slice_nodes.size()
           << " events " << sdc_events.size()
           << " on_path_reads " << sdc_on_path_reads
           << " total_reads " << sdc_total_reads
           << " sdc_ace_cycles int " << irf_ace_sdc_cycles[0]
           << " float " << irf_ace_sdc_cycles[1]
           << " vec " << irf_ace_sdc_cycles[2] << "\n";
        os << "ibr";
        for (int c = 0; c < 4; c++)
            os << " " << ibr_input_bits[c] << "/" << ibr_issues[c];
        os << "\n";
        // SDC-ED Task 3.2: per-FU-class value-class rows (advice engine:
        // "generate subnormal/NaN-heavy operands" rules read this)
        static const char *const vc_names[NUM_VALUE_CLASSES] =
            {"normal", "subnormal", "NaN", "Inf", "zero"};
        for (int fc = 2; fc < 4; fc++) {
            os << "fp_values " << (fc == 2 ? "FPAdd" : "FPMul");
            for (int vc = 0; vc < NUM_VALUE_CLASSES; vc++)
                os << " " << vc_names[vc] << "=" << fp_value_hist[fc][vc];
            os << "\n";
        }
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
    // SDC-ED Task 3.1: any producer write invalidates a pending load-use
    // birth mark on this slot (the load value was overwritten before its
    // first committed consumption — dead interval, not counted). The
    // load's OWN writeback re-marks the slot right after (completeAcc:
    // setReg fires first, then harp_cov_on_load_wb — call order in
    // LSQUnit::writeback, measured).
    if (class_type >= 0 && class_type <= 2 &&
        (size_t)idx < lu_state[class_type].size())
        lu_state[class_type][idx] = 0;
    // SDC-ED Task 4.2: log the write for the SDC replay (interval
    // birth; execute-time, node unknown — the replay pairs it with the
    // next commit-read of the slot via interval arithmetic).
    if (sdc_events.size() < (4u << 20))
        sdc_events.push_back({true, (int8_t)class_type, idx, -1, now});
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
        // SDC-ED Task 3.4: rename-distance sample at interval close
        // (producer write → first consumer read, cycles).
        renameDistSample(now - st.birth);
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
    // SDC-ED Task 4.2: commit-confirmed read event for the SDC replay,
    // tagged with the reading instruction's slice node (sliceOnCommit
    // ran first in the same commit step — commit.cc call order).
    if (sdc_events.size() < (4u << 20) && !slice_nodes.empty())
        sdc_events.push_back({false, (int8_t)class_type, idx,
                              (int)slice_nodes.size() - 1, now});
}

// SDC-ED Task 4.1: record one committed instruction's dataflow node.
// Called FIRST in the commit-step harp block (before the commit-read
// hook — the read events tag themselves with this node's index).
// Class mapping mirrors the IRF spaces: int/float/vec → 0/1/2; other
// classes (cc/misc/pred/mat) are skipped — they never enter the IRF
// ledgers. Producer snapshot: slice_producer[cls][idx] holds the node
// index of the most recent EARLIER writer (updated as nodes are
// appended in commit order — so src_prod captures "who wrote the value
// this instruction reads" exactly). Buffer cap: 1M nodes (~20 MB) —
// beyond that the slice degrades to the first 1M committed insts
// (logged honestly in the detail dump).
void
CHAOSCov::sliceOnCommit(const o3::DynInstPtr &inst)
{
    if (!roi_active) return;
    if (slice_nodes.size() >= (1u << 20)) return;
    // Lazy init (sizes only known once the regfile is sized).
    if (slice_producer[0].empty()) {
        for (int c = 0; c < 3; c++)
            slice_producer[c].assign(irf_state[c].size(), -1);
    }
    SliceNode n;
    n.is_store = inst->isStore();
    for (size_t i = 0; i < inst->numDestRegs() && n.n_dst < SliceNode::MAX_REGS; i++) {
        const PhysRegIdPtr reg = inst->renamedDestIdx(i);
        const auto cls = reg->classValue();
        if (cls == IntRegClass) {
            n.dst_cls[n.n_dst] = 0; n.dst_idx[n.n_dst] = (int)reg->index();
        } else if (cls == FloatRegClass) {
            n.dst_cls[n.n_dst] = 1; n.dst_idx[n.n_dst] = (int)reg->index();
        } else if (cls == VecRegClass) {
            n.dst_cls[n.n_dst] = 2; n.dst_idx[n.n_dst] = (int)reg->index();
        } else continue;
        n.n_dst++;
    }
    for (size_t i = 0; i < inst->numSrcRegs() && n.n_src < SliceNode::MAX_REGS; i++) {
        const PhysRegIdPtr reg = inst->renamedSrcIdx(i);
        if (reg->is(InvalidRegClass)) continue;
        const auto cls = reg->classValue();
        int c;
        if (cls == IntRegClass) c = 0;
        else if (cls == FloatRegClass) c = 1;
        else if (cls == VecRegClass) c = 2;
        else continue;
        n.src_cls[n.n_src] = (int8_t)c;
        n.src_idx[n.n_src] = (int)reg->index();
        const int idx = (int)reg->index();
        n.src_prod[n.n_src] =
            (idx >= 0 && (size_t)idx < slice_producer[c].size())
                ? slice_producer[c][idx] : -1;
        n.n_src++;
    }
    const int my = (int)slice_nodes.size();
    // The node itself becomes the most recent writer of its dsts.
    for (int d = 0; d < n.n_dst; d++) {
        const int c = n.dst_cls[d], idx = n.dst_idx[d];
        if (idx >= 0 && (size_t)idx < slice_producer[c].size())
            slice_producer[c][idx] = my;
    }
    slice_nodes.push_back(std::move(n));
}

void
CHAOSCov::setReachManifest(const std::string &path)
{
    reach_manifest_path = path;
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

// SDC-ED Task 4.2: solve the dynamic slice and close the SDC-ACE
// ledgers. Algorithm:
//   1. Backward on-path sweep over slice_nodes (commit order == program
//      order): stores are sinks (their data+addr sources sit on the
//      path to the checkable output — the wrapper CRC-hashes all of
//      mem and hashes g_reg after the store-back). An on-path node
//      marks its RECORDED producers (src_prod[] was snapshotted in the
//      forward pass at sliceOnCommit time — "who wrote the value this
//      instruction reads"). Since src_prod[i] < i always, one
//      newest→oldest sweep reaches the transitive closure.
//   2. Replay sdc_events (chronological: execute-time writes with
//      node=-1 + commit-time reads tagged with the reading node).
//      Interval arithmetic mirrors irfOnWrite/irfOnCommitRead, but only
//      reads whose READING NODE is on-path count into irf_ace_sdc_cycles
//      — node-level classification (a slot's dead intervals stay out
//      even when the same slot's final value is stored back; stricter
//      and more faithful than any slot-level OR). Reads on the
//      commit-confirmed stream: wrong-path reads never commit, so
//      SDC-ACE ≤ commit-confirmed ACE ≤ optimistic ACE by construction.
void
CHAOSCov::solveSliceAndSdc()
{
    if (slice_nodes.empty()) return;
    // Idempotence: finishStats runs from both onWorkEnd and
    // preDumpStats (measured — the m5ops path fires onWorkEnd first,
    // then the stats dump calls it again). The optimistic ledgers are
    // naturally monotone; these SDC counters are RE-DERIVED each call,
    // so clear them here (double-count was measured as sdcGap=-1).
    irf_ace_sdc_cycles[0] = irf_ace_sdc_cycles[1] = irf_ace_sdc_cycles[2] = 0;
    sdc_on_path_reads = 0;
    sdc_total_reads = 0;
    // 1. Backward on-path sweep.
    for (int i = (int)slice_nodes.size() - 1; i >= 0; i--) {
        SliceNode &n = slice_nodes[i];
        if (n.is_store) n.on_path = true;
        if (n.on_path) {
            for (int s = 0; s < n.n_src; s++) {
                const int p = n.src_prod[s];
                if (p >= 0 && p < (int)slice_nodes.size())
                    slice_nodes[p].on_path = true;
            }
        }
    }
    // 2. Chronological replay with node-level on-path classification.
    //    Events: writes (node=-1) reset the interval machine for the
    //    slot; reads (node>=0) extend it iff the reading node is
    //    on-path. Stable sort by cycle keeps the write-before-read
    //    order inside a cycle (execute precedes commit within a tick;
    //    std::stable_sort preserves the append order for ties, and
    //    writes are appended during execute before the commit reads of
    //    the same cycle — measured pipeline order).
    {
        std::vector<size_t> order(sdc_events.size());
        for (size_t i = 0; i < order.size(); i++) order[i] = i;
        std::stable_sort(order.begin(), order.end(),
            [this](size_t a, size_t b) {
                return sdc_events[a].cycle < sdc_events[b].cycle;
            });
        struct SdcSlot
        {
            uint64_t birth = 0, last_read = 0;
            bool has_value = false, ever_read = false;
        };
        std::vector<SdcSlot> sdc_st[3];
        for (int c = 0; c < 3; c++) sdc_st[c].assign(irf_state[c].size(), {});
        for (size_t oi = 0; oi < order.size(); oi++) {
            const SdcEvent &ev = sdc_events[order[oi]];
            if (ev.cls < 0 || ev.cls > 2) continue;
            if ((size_t)ev.idx >= sdc_st[ev.cls].size()) continue;
            SdcSlot &st = sdc_st[ev.cls][ev.idx];
            if (ev.is_write) {
                st.birth = ev.cycle;
                st.last_read = ev.cycle;
                st.has_value = true;
                st.ever_read = false;
            } else {
                sdc_total_reads++;
                if (!st.has_value) continue;
                const bool on_path =
                    ev.node >= 0 && ev.node < (int)slice_nodes.size()
                    && slice_nodes[ev.node].on_path;
                if (on_path) {
                    if (!st.ever_read) {
                        irf_ace_sdc_cycles[ev.cls] += ev.cycle - st.birth;
                        st.ever_read = true;
                    } else {
                        irf_ace_sdc_cycles[ev.cls] += ev.cycle - st.last_read;
                    }
                    sdc_on_path_reads++;
                }
                st.last_read = ev.cycle;
            }
        }
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

// SDC-ED Task 3.4: bucket a rename distance into the power-of-two
// histogram (same scheme as the load-use distance).
void
CHAOSCov::renameDistSample(uint64_t dist)
{
    int b;
    if (dist == 0) b = 0;
    else if (dist > 32768) b = RD_BUCKETS - 1;
    else {
        b = 1;
        while ((1ULL << b) < dist) b++;
        // dist in (2^(b-1), 2^b] → bucket b, capped
        if (b >= RD_BUCKETS - 1) b = RD_BUCKETS - 2;
    }
    rd_hist[b]++;
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
      ADD_STAT(l2cAceCycles, statistics::units::Cycle::get(),
               "Extra-cache (L2) ACE cycles, aggregated over "
               "extraTargetCaches ledgers (SDC-ED L2C unit)"),
      ADD_STAT(l2cReads, statistics::units::Count::get(),
               "Extra-cache demand reads observed"),
      ADD_STAT(l2cWrites, statistics::units::Count::get(),
               "Extra-cache fills + store-data updates observed"),
      ADD_STAT(l2cEvicts, statistics::units::Count::get(),
               "Extra-cache evictions observed"),
      ADD_STAT(l2cAvf, statistics::units::Ratio::get(),
               "Extra-cache AVF = block ACE cycles / (total extra blocks "
               "* ROI cycles) (SDC-ED L2C unit)"),
      ADD_STAT(l2cTagReads, statistics::units::Count::get(),
               "Extra-cache tag comparisons (tag-plane coverage signal; "
               "NOT an ACE interval — the data-face ledger above stays the "
               "ACE account. ECC-blind tag plane: rho_L2C tag=0.45 vs "
               "data SECDED=0.0)"),
      ADD_STAT(l2cTagFaceRatio, statistics::units::Ratio::get(),
               "Extra-cache tag-face ratio = tagReads / (reads + writes). "
               "Coverage signal for the tag plane (SDC-ED L2C unit)"),
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
      ADD_STAT(sqForwards, statistics::units::Count::get(),
               "Store→load forwards observed (per-slot ledger; the load "
               "consumed the store data inside the SQ)"),
      ADD_STAT(sqForwardAceCycles, statistics::units::Cycle::get(),
               "SQ data-field ACE cycles attributable to forwarding "
               "consumption (per-slot exact ledger — supersedes the "
               "aggregate approximation for the forward face)"),
      ADD_STAT(sqWritebackAceCycles, statistics::units::Cycle::get(),
               "SQ data-field ACE cycles attributable to memory-writeback "
               "consumption (per-slot exact ledger)"),
      ADD_STAT(sqForwardAvf, statistics::units::Ratio::get(),
               "Forward-face SQ AVF = forward ACE cycles / (SQEntries * "
               "ROI cycles) (SDC-ED LSU unit, forward coverage)"),
      ADD_STAT(loadUseDist, statistics::units::Count::get(),
               "Load-use distance histogram: cycles between a load's data "
               "writeback into the PRF and its first commit-confirmed "
               "consumption. Buckets: [0]=0, [i]=2^(i-1)..2^i cycles, "
               "[16]=>32768 (SDC-ED LSU unit, load-use distance)"),
      ADD_STAT(renameDist, statistics::units::Count::get(),
               "Rename-distance histogram: cycles from a PRF value's "
               "producing write to its first read (the write→read ACE "
               "interval length). Buckets: [0]=0, [i]=2^(i-1)..2^i, "
               "[16]=>32768 (SDC-ED Task 3.4, OoO unit)"),
      ADD_STAT(robOccBands, statistics::units::Count::get(),
               "ROB occupancy-band histogram: per-ROI-cycle samples of "
               "numInstsInROB bucketed into 8 bands of capacity/8 "
               "(SDC-ED Task 3.4, OoO unit)"),
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
               "IBR FPMul = input bits / (256 * instances * ROI cycles)"),
      ADD_STAT(covUnits, statistics::units::Ratio::get(),
               "SDC-ED 7-unit coverage vector A_u [IFU OoO IEX LSU FSU MMU "
               "L2C]. IFU=0 (Crash axis, rho=0), MMU=0 (SE ceiling, FS arm "
               "TBD), OoO=irfAvf, IEX=max(ibrIntAdd,ibrIntMul), LSU=sqAvf, "
               "FSU=max(ibrFpAdd,ibrFpMul), L2C=max(l1dAvf,l2cAvf). "
               "Consumed by tools/ed_score.py (ED = Σ w·ρ·q·A_u)"),
      ADD_STAT(fpValueHist, statistics::units::Count::get(),
               "FP source-lane value-class histogram [FU class][class]: "
               "rows IntAdd/IntMul/FPAdd/FPMul (FP rows only), cols "
               "normal/subnormal/NaN/Inf/zero. SDC-ED Task 3.2"),
      ADD_STAT(fpValueEntropy, statistics::units::Ratio::get(),
               "Normalized Shannon entropy of the merged FP value-class "
               "distribution (0=single class, 1=uniform over 5 classes). "
               "FSU value-coverage axis the IBR cannot see"),
      ADD_STAT(irfAvfSdc, statistics::units::Ratio::get(),
               "SDC-ACE AVF: ACE cycles whose reads lie on the dynamic "
               "slice to a checkable output (committed-store sinks), / "
               "(bits * ROI cycles). SDC-ED Task 4.2"),
      ADD_STAT(irfAvfSdcInt, statistics::units::Ratio::get(),
               "SDC-ACE AVF, int space"),
      ADD_STAT(sdcGap, statistics::units::Ratio::get(),
               "SDC gap = (ACE - SDC-ACE) / ACE: the fraction of "
               "architecturally-consumed residency that never reaches a "
               "checkable output (sequence-design defect signal for the "
               "advice engine)"),
      ADD_STAT(sdcOnPathReads, statistics::units::Count::get(),
               "Optimistic IRF reads on the dynamic slice"),
      ADD_STAT(sdcTotalReads, statistics::units::Count::get(),
               "Total optimistic IRF reads logged")
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
    // SDC-ED Task 3.1: load-use distance buckets (0, 1, 2, 4, ..., >32768)
    loadUseDist.init(LU_BUCKETS);
    loadUseDist.subname(0, "c0");
    for (int b = 1; b < LU_BUCKETS - 1; b++) {
        loadUseDist.subname(b, "c" + std::to_string(1 << (b - 1))
                               + "-" + std::to_string(1 << b));
    }
    loadUseDist.subname(LU_BUCKETS - 1, "gt32768");
    // SDC-ED Task 3.4: rename-distance buckets (same scheme)
    renameDist.init(RD_BUCKETS);
    renameDist.subname(0, "c0");
    for (int b = 1; b < RD_BUCKETS - 1; b++) {
        renameDist.subname(b, "c" + std::to_string(1 << (b - 1))
                               + "-" + std::to_string(1 << b));
    }
    renameDist.subname(RD_BUCKETS - 1, "gt32768");
    robOccBands.init(8);
    for (int b = 0; b < 8; b++)
        robOccBands.subname(b, "b" + std::to_string(b) + "_" +
                               std::to_string(b * 100 / 8) + "-"
                               + std::to_string((b + 1) * 100 / 8) + "pct");
    // SDC-ED Task 2.3: 7-unit vector subnames (order fixed in CHAOSCov.hh)
    covUnits.init(NUM_ED_UNITS);
    covUnits.subname(0, "IFU");
    covUnits.subname(1, "OoO");
    covUnits.subname(2, "IEX");
    covUnits.subname(3, "LSU");
    covUnits.subname(4, "FSU");
    covUnits.subname(5, "MMU");
    covUnits.subname(6, "L2C");
    // SDC-ED Task 3.2: [fu_class][value_class] flattened 4x5 subnames
    fpValueHist.init(NUM_FU_CLASSES * NUM_VALUE_CLASSES);
    static const char *const fu_names[NUM_FU_CLASSES] =
        {"IntAdd", "IntMul", "FPAdd", "FPMul"};
    static const char *const vc_names[NUM_VALUE_CLASSES] =
        {"normal", "subnormal", "NaN", "Inf", "zero"};
    for (int fc = 0; fc < NUM_FU_CLASSES; fc++)
        for (int vc = 0; vc < NUM_VALUE_CLASSES; vc++)
            fpValueHist.subname(fc * NUM_VALUE_CLASSES + vc,
                                std::string(fu_names[fc]) + "."
                                + vc_names[vc]);
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

// SDC-ED Task 3.2: FP source-lane value classification. The caller
// already filtered to FP FU classes (2/3) and classified each 64-bit
// lane; this only buckets. Entropy is finalized in finishStats.
void
CHAOSCov::fuOnIssueValue(int fu_class, int n_lanes, const int *lane_class)
{
    if (!roi_active) return;
    if (fu_class < 0 || fu_class >= NUM_FU_CLASSES) return;
    for (int i = 0; i < n_lanes; i++) {
        const int c = lane_class[i];
        if (c < 0 || c >= NUM_VALUE_CLASSES) continue;
        fp_value_hist[fu_class][c]++;
        fp_lanes_sampled++;
    }
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
CHAOSCov::sqOnWrite(unsigned slot_idx)
{
    if (!roi_active) return;
    sq_writes++;
    harp_sq_open.push_back({roi_cycles, false});
    // SDC-ED Task 3.1 per-slot ledger: data entered this slot's data
    // field — birth of both the forward-face and wb-face intervals.
    if (slot_idx < sq_state.size()) {
        auto &st = sq_state[slot_idx];
        st.birth = roi_cycles;
        st.last_consume = roi_cycles;
        st.last_forward = roi_cycles;
        st.has_data = true;
        st.ever_consumed = false;
        st.ever_forwarded = false;
    }
}

void
CHAOSCov::sqOnConsume(unsigned slot_idx)
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
    // SDC-ED Task 3.1 per-slot wb ledger: the memory writeback consumed
    // this slot's data (writeback face of the SQ-data ACE).
    if (slot_idx < sq_state.size()) {
        auto &st = sq_state[slot_idx];
        if (st.has_data) {
            if (!st.ever_consumed) {
                sq_wb_ace_cycles += roi_cycles - st.birth;
                st.ever_consumed = true;
            } else {
                sq_wb_ace_cycles += roi_cycles - st.last_consume;
            }
            st.last_consume = roi_cycles;
        }
    }
}

void
CHAOSCov::sqOnFree(unsigned slot_idx)
{
    if (!roi_active) return;
    sq_frees++;
    // Free without consume (squashed, never forwarded/written back):
    // un-ACE — drop the oldest open interval without accumulating.
    if (!harp_sq_open.empty())
        harp_sq_open.erase(harp_sq_open.begin());
    // SDC-ED Task 3.1 per-slot ledger: slot released — close the value's
    // intervals. Un-consumed tails (neither forwarded nor written back
    // since the last event) are un-ACE and add nothing (already the case:
    // each face only ever accumulated up to its last event).
    if (slot_idx < sq_state.size())
        sq_state[slot_idx].has_data = false;
}

// ---------------------------------------------------------------------------
// SDC-ED Task 3.1: per-slot forward ledger + load-use distance
// ---------------------------------------------------------------------------
// The forwarding hook fires at the exact store→load forwarding hit in
// LSQUnit::read (FullAddrRangeCoverage branch), with the SQ slot id
// (absolute index mod capacity — the data-array position). This is the
// per-slot read-type consumption the Task 3.2 aggregate approximated:
//
//   forward-ACE  [store-data write, forwarding read]   — this ledger
//   wb-ACE       [store-data write, memory writeback]  — sqOnConsume
//
// Both ledgers are per-slot: a forwarded store that is later written back
// to memory contributes to BOTH (its data was consumed twice — by the
// forwarding load inside the SQ, and by the memory system at writeback),
// which the aggregate approximation could not express.

void
CHAOSCov::sqOnForward(unsigned slot_idx)
{
    if (!roi_active) return;
    if (slot_idx >= sq_state.size()) return;   // defensive: config mismatch
    auto &st = sq_state[slot_idx];
    const uint64_t now = roi_cycles;
    // Forward is a read of the value written at st.birth (or extends the
    // forward interval from the last forward). Only stores that wrote
    // actual data open a per-slot interval (write() fires sqOnWrite at the
    // same slot; sqOnWrite below is bookkeeping for the aggregate).
    if (!st.has_data) return;
    if (!st.ever_forwarded) {
        sq_fwd_ace_cycles += now - st.birth;
        st.ever_forwarded = true;
    } else {
        sq_fwd_ace_cycles += now - st.last_forward;
    }
    st.last_forward = now;
    sq_forwards++;
}

void
CHAOSCov::loadOnWriteback(int class_type, int idx)
{
    if (!roi_active) return;
    if (class_type < 0 || class_type > 2) return;
    if (idx < 0 || (size_t)idx >= lu_state[class_type].size()) return;
    // Birth of the load-use interval: load data entered the PRF this cycle.
    // Cycle 0 is reserved as "no mark" (roi_cycles is 0 before the first
    // ROI cycle; a mark set in the very first ROI cycle would read as
    // empty — accept that one-off imprecision rather than paying an extra
    // flag word per reg; the first ROI cycle is the m5ops marker tick).
    lu_state[class_type][idx] = roi_cycles ? roi_cycles : 1;
}

void
CHAOSCov::loadOnUse(int class_type, int idx)
{
    if (!roi_active) return;
    if (class_type < 0 || class_type > 2) return;
    if (idx < 0 || (size_t)idx >= lu_state[class_type].size()) return;
    const uint64_t birth = lu_state[class_type][idx];
    if (!birth) return;   // not fresh load data — nothing to close
    const uint64_t dist = roi_cycles - birth;
    lu_state[class_type][idx] = 0;   // interval closed
    lu_samples++;
    // Bucket: powers of two — b[i] = cycles in (2^(i-1), 2^i], b[0]=0,
    // b[16]=>32768.
    unsigned b = LU_BUCKETS - 1;
    for (unsigned i = 0; i < LU_BUCKETS - 1; i++) {
        if (dist <= (1ull << i)) { b = i; break; }
    }
    lu_hist[b]++;
}

// ---------------------------------------------------------------------------
// L1D/L2 ACE collector (Task 3.1; SDC-ED Task 2.2 multi-cache ledgers)
// ---------------------------------------------------------------------------
// Dispatch: find the ledger owning this cache instance (nullptr = the
// event came from an untracked cache; the hook already checked).
CacheLedger *
CHAOSCov::ledgerFor(void *cache)
{
    for (auto &led : cache_ledgers)
        if (led.cache == cache)
            return &led;
    return nullptr;
}

void
CHAOSCov::cacheOnWrite(void *cache, void *blk)
{
    if (!roi_active) return;
    CacheLedger *led = ledgerFor(cache);
    if (!led) return;
    led->writes++;
    auto &st = led->state[blk];
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
    CacheLedger *led = ledgerFor(cache);
    if (!led) return;
    auto it = led->state.find(blk);
    if (it == led->state.end()) return;   // block never written in ROI
    auto &st = it->second;
    if (!st.has_value) return;
    const uint64_t now = roi_cycles;
    if (!st.ever_read) {
        led->ace_cycles += now - st.birth;
        st.ever_read = true;
    } else {
        led->ace_cycles += now - st.last_read;
    }
    st.last_read = now;
    led->reads++;
}

void
CHAOSCov::cacheOnEvict(void *cache, void *blk)
{
    if (!roi_active) return;
    CacheLedger *led = ledgerFor(cache);
    if (!led) return;
    led->evicts++;
    auto it = led->state.find(blk);
    if (it != led->state.end())
        it->second.has_value = false;   // unread tail un-ACE; state kept
}

// SDC-ED Task 3.3: tag-face event handler. One call per CPU-side access's
// tag comparison (BaseCache::access after tags->accessBlock — fires for
// hits AND misses). Count only; deliberately no interval bookkeeping:
// reading a tag does not extend any data bit's ACE residency. This is the
// coverage-side counterpart of the L2 tag-face SDC line (39-47% vs
// data-face SECDED 0%): a workload touching many distinct tags exercises
// the unprotected tag plane, which SECDED on the data array does not cover.
void
CHAOSCov::cacheOnTagAccess(void *cache)
{
    if (!roi_active) return;
    CacheLedger *led = ledgerFor(cache);
    if (!led) return;
    led->tag_reads++;
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
