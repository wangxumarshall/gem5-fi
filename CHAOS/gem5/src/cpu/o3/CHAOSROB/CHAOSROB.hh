#ifndef __CPU_O3_CHAOS_ROB_HH__
#define __CPU_O3_CHAOS_ROB_HH__

#include <deque>
#include <random>
#include <string>
#include <vector>

#include "params/CHAOSROB.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/o3/dyn_inst_ptr.hh"  // DynInstPtr
#include "cpu/reg_class.hh"        // RegClassType (W7.4 targetClass)

namespace gem5 { namespace o3 { class CPU; } }
namespace gem5 { namespace o3 { class ROB; } }

namespace gem5
{

class CHAOSROB : public SimObject
{
  public:
    CHAOSROB(const CHAOSROBParams &p);
    ~CHAOSROB();

    void startup() override;  // self-attach to ROB.chaosROB

    // Called from ROB::retireHead AFTER popping the head DynInst (before
    // cpu->removeFrontInst). For entry_bitflip: the entry at distance D from
    // head has a field bit flipped. For exc_suppress: the head's fault is
    // cleared (NoFault) so a pending SError/DUE is swallowed. For the W5
    // stuck modes: retire-time read-back of the armed entry's field (the
    // "该 ROB 项存活期间持续带着这个缺陷" persistence evidence).
    // Returns true if an injection happened this call.
    bool maybeCorrupt(ThreadID tid, o3::DynInstPtr &head_inst);

    // W5.1-W5.3 (ooo 04-design-matrix D25-D31, Int Dispatch/ROB): called from
    // ROB::insertInst — the ROB-entry WRITE path (the TC'23 site: the fault is
    // in the entry's PC / dest-register-id field as the entry is written into
    // the ROB, before the instruction completes). Injects into the entry
    // being written (the inserting inst): pc_bitflip/pc_bitflip2 flip 1/2
    // random bits of the pcState pc address; destid_bitflip/destid_bitflip2
    // flip 1/2 random bits of a random integer dest physReg index;
    // destid_swap_active replaces it with the dest physReg of another
    // ROB-resident in-flight instruction; pc_stuck/destid_stuck arm ONE
    // stuck-at bit (F5 write-path mask, the f5_rat_stuck precedent) applied
    // to the armed entry's field at its write. Returns true on injection.
    bool maybeCorruptEntry(ThreadID tid, const o3::DynInstPtr &inst);

    // W5.4 D34/D35 done_delay(_event) (ooo 04-design-matrix R35/R36, done位·
    // 延迟置位): called from Commit::markCompletedInsts for EACH fromIEW
    // completed inst, BEFORE its setCanCommit. Returning true makes the
    // caller SKIP that setCanCommit — fromIEW carries each instruction's
    // completion exactly once (the time-buffer wire only holds the current
    // cycle's completions), so the skip means the entry is NEVER marked
    // done: it occupies its ROB slot forever, the in-order commit head
    // blocks on it and the ROB fills (resource-exhaustion Timeout, the
    // free-list-leak family). done_delay_event additionally requires ROB
    // occupancy > 80% at the decision. Excludes the classes that self-heal
    // (non-speculative/barrier/store-conditional/atomic/strictly-ordered
    // loads re-arm and complete through fromIEW a second time via the
    // commitHead nonSpecSeqNum path). Only done_delay modes ever return
    // true — every other mode is a zero-regression no-op here.
    bool maybeDelayDoneBit(const o3::DynInstPtr &inst);

    // W5.4 D32/D33 done_early(_event) (ooo 04-design-matrix R33/R34, done位·
    // 提前置位): called ONCE per Commit::markCompletedInsts (per cycle).
    // Picks ONE ROB-resident entry whose done bit is still clear and whose
    // execution has NOT finished, and forces setCanCommit() + setExecuted()
    // on it — the paired setExecuted is REQUIRED to bypass the
    // commitHead assert (commit.cc:1128-1134: an un-executed head must be
    // non-speculative/barrier/... or commit panics). The committed entry's
    // result value is then whatever the physRegFile cell still holds from
    // its previous occupant (spike A) — silent-SDC potential, the design's
    // "预期 Int Dispatch/ROB 里 SDC 概率最高" cell. done_early_event
    // additionally requires ROB occupancy > 80%. v1 scoping: stores/
    // atomics/barriers/non-speculative/strictly-ordered loads and control
    // transfers are excluded (SQ double-commit and resolve-after-commit
    // squash-machinery hazards); plain ALU ops and plain loads remain —
    // exactly the stale-PRF-value population. Only done_early modes ever
    // inject — every other mode is a zero-regression no-op here.
    void maybeEarlyDoneBit();

  private:
    enum class Mode {
        EntryBitflip, ExcSuppress,
        PcBitflip, PcBitflip2, PcStuck,
        DestIdBitflip, DestIdBitflip2, DestIdSwapActive, DestIdStuck,
        // W5.4 (D32-D35): the done/completed (CanCommit) status bit.
        DoneEarly, DoneEarlyEvent, DoneDelay, DoneDelayEvent,
        // W5.6 D40 (R41): the whole ROB-entry record read stale at commit.
        RobStaleRead,
        // W5.6 D36-D39 oldphys_* mount through --rob_mode but live in
        // CHAOSRenameMap (rename historyBuffer prevPhysReg, the W4 N1
        // finding: gem5's old-phys lives in the rename checkpoint, not a
        // ROB-array field). CHAOSROB must stay INERT for them — unknown
        // modes must never silently fall back to entry_bitflip (which
        // toggles CanCommit) — hence the explicit inert mode.
        OldphysInert,
        // W5.8-W5.9 (D41-D46, ooo 04-design-matrix R42-R47): the ROB
        // head/tail POINTER family. gem5's ROB is a std::list with no
        // pointer registers — every mode is an HONEST APPROXIMATION
        // (approx= on every log line, the W4 head_bitflip precedent):
        //   head_ptr_*  = commit-side entry-selection misalignment (the
        //     entry at the flip offset from head contributes its record to
        //     the next commit — the skip/repeat-commit observable).
        //   tail_ptr_*  = allocation-side alias (the new entry's record
        //     lands on the in-use entry at the flip offset behind the tail
        //     — the "新分配的 ROB 项覆盖仍在用的项" clobber).
        HeadPtrBitflip, HeadPtrBitflip2, HeadPtrStuck,
        TailPtrBitflip, TailPtrBitflip2, TailPtrStuck
    };
    static Mode stringToMode(const std::string &s);
    const char *modeToString(Mode m);

    enum class Field { Result, Done, ExcStatus, DestPhys, Spec };
    static Field stringToField(const std::string &s);

    // W5 D30 destid_swap_active: one ROB-resident candidate dest.
    struct RobDestCand { int phys_idx; int dist; uint64_t sn; };

    BaseCPU *cpu;
    Mode fi_mode;
    Field field;
    int distance_from_head;
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t fault_mask;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;
    // W7.4: register-class scope of the dest-id family. IntRegClass =
    // the W5 D28-D31 scope (default); VecRegClass = the FP/SIMD twins
    // (scalar FP + FP SIMD + integer SIMD dests all rename onto
    // VecRegClass on AArch64 — S/D are the low bits of V; FloatRegClass
    // is never renamed).
    RegClassType target_reg_class = IntRegClass;

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();

    // W5 stuck (D27/D31) state: ONE armed ROB entry (identified by its
    // seqNum — unique per instruction) + ONE bit + polarity. The write-path
    // mask applies at the armed entry's insert (the single write of a
    // ROB-resident entry's PC/destId field — gem5 never rewrites these
    // fields post-insert, so persistence = value permanence, verified by
    // the retire-time read-back in maybeCorrupt).
    bool stuck_armed = false;
    bool stuck_readback_done = false;
    uint64_t stuck_sn = 0;
    int stuck_bit = -1;
    int stuck_polarity = 0;
    int stuck_dest_slot = -1;   // destid_stuck: which renamedDestIdx slot
    uint64_t stuck_exposures = 0;

    // W5.6 D40 rob_stale_read state: gem5's ROB is a std::list of DynInst
    // (no physical slot array), so "the slot's previous occupant" is
    // approximated by the most-recently RETIRED instruction (at full
    // occupancy the head departure frees exactly the slot the tail is
    // about to write). Every retireHead departure is captured into a
    // bounded ring (the DynInstPtr keeps the record alive/readable); at
    // the chosen insert the entry's record fields (pcState, flattened /
    // renamed dest ids, prev-dest ids) are overwritten with the previous
    // occupant's — the "slot write silently failed, old record retained"
    // realization, proven by the retire-time STALE_RECORD_COMMITTED line.
    std::deque<o3::DynInstPtr> stale_departed;
    uint64_t stale_read_new_sn = 0;    // the entry whose record was staled
    bool stale_read_armed = false;
    bool stale_read_committed_logged = false;
    Addr stale_read_true_pc = 0;       // the new inst's TRUE pc (pre-copy)
    Addr stale_read_stale_pc = 0;      // the old record's pc (post-copy)
    uint64_t stale_read_old_sn = 0;    // the previous occupant's seqNum

    // W5.8-W5.9 D43/D46 pointer-stuck state (F5, the W4 head_stuck
    // pattern): ONE armed bit + polarity of the ROB slot-index domain
    // (128 entries -> 7 bits); the armed offset = 1<<bit is applied at
    // EVERY subsequent insert (ungated exposures of the one permanent
    // fault — "同一种错位模式重复出现" / "分配冲突的持续性重复").
    bool ptr_stuck_armed = false;
    int ptr_stuck_bit = -1;
    int ptr_stuck_polarity = 0;
    int ptr_stuck_offset = 0;          // 1 << ptr_stuck_bit (fixed pattern)
    uint64_t ptr_stuck_exposures = 0;
    uint64_t ptr_stuck_noaction = 0;   // exposures with no live target

    // shared helpers
    // W7.4: dest slots of inst in the TARGET register class (IntRegClass
    // = the W5 D28-D31 dest-id scope; VecRegClass = the FP/SIMD twins).
    int collectDestSlots(const o3::DynInstPtr &inst,
                         std::vector<int> &slots);
    // W7.4 class helpers: dest-id index domain and PhysRegId factory of
    // the target class (intPhysRegId / vecPhysRegId, regfile.hh).
    int numTargetPhysRegs(o3::CPU *o3cpu);
    PhysRegIdPtr targetPhysRegId(o3::CPU *o3cpu, int idx);
    const char *targetClassName();
    int collectRobActiveDests(int cur_idx, uint64_t self_sn,
                              o3::CPU *o3cpu, ThreadID tid,
                              std::vector<RobDestCand> &cands);
    bool maybeStuckEntryWrite(ThreadID tid, const o3::DynInstPtr &inst);
    void checkStuckReadback(const o3::DynInstPtr &head_inst);

    // W5.4/W5.6 helpers
    // ROB occupancy > 80% (the D33/D35 event gate: countInsts(tid) vs
    // getMaxEntries(tid), integer 4/5 compare).
    bool robAbove80Pct(o3::CPU *o3cpu, ThreadID tid);
    // The classes excluded from done-bit corruption (see the two public
    // hooks above for why each family is excluded).
    bool doneBitExcluded(const o3::DynInstPtr &inst, bool early);
    // D40: the insert-site stale-record overwrite.
    bool maybeStaleReadEntry(ThreadID tid, const o3::DynInstPtr &inst);

    // W5.8-W5.9 (D41-D46) helpers: copy one entry's RECORD (pcState + the
    // first min(dst,src) dest slots' flattened/renamed/prev ids — the D40
    // field set, bounded by the DESTINATION's array sizes, no OOB) from
    // src onto dst. Returns the number of dest slots copied.
    int copyRobRecord(const o3::DynInstPtr &dst, const o3::DynInstPtr &src);
    // The head/tail pointer family dispatcher (rob_insert site).
    bool maybePtrCorrupt(ThreadID tid, const o3::DynInstPtr &inst);
    // D41/D42 head-side one-shot misalignment; D44/D45 tail-side one-shot
    // allocation alias. stuck=false for the one-shots.
    bool applyHeadPtrFlip(ThreadID tid, const o3::DynInstPtr &inst,
                          int offset, bool stuck, int b1, int b2);
    bool applyTailPtrFlip(ThreadID tid, const o3::DynInstPtr &inst,
                          int offset, bool stuck, int b1, int b2);
    // End-of-run evidence for the F5 stuck pointer modes (total exposure
    // counts, the CHAOSFreeList finalSummary pattern).
    void ptrStuckFinalSummary();
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_ROB_HH__
