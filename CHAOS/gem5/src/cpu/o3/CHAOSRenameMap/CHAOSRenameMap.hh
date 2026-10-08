#ifndef __CPU_O3_CHAOS_RENAME_MAP_HH__
#define __CPU_O3_CHAOS_RENAME_MAP_HH__

#include <random>
#include <set>
#include <string>
#include <vector>

#include "params/CHAOSRenameMap.hh"
#include "sim/sim_object.hh"
#include "sim/eventq.hh"          // U2: EventFunctionWrapper (RAT replay /
                                  // deferred freelist pop next-tick events)
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"
#include "cpu/reg_class.hh"      // RegClassType (W7.2 targetClass)

// o3::CPU (C++ class behind ArmO3CPU) is needed to reach renameMap/freeList/
// regFile. Forward-declare (full definition pulled into the .cc via cpu/o3/cpu.hh).
// CHAOSRenameMap only supports O3CPU; dynamic_cast fails at construct time
// otherwise — same pattern as CHAOSPhysReg.
namespace gem5 { namespace o3 { class CPU; } }

namespace gem5
{

// forward-decl of the rename map entry id (pointer type used by rename_map.hh)
namespace o3 { class UnifiedRenameMap; }
namespace o3 { class UnifiedFreeList; }
namespace o3 { class DynInst; }   // U2 R08-c/d arg type (bare o3 — a
                                     // re-opened 'namespace gem5' INSIDE
                                     // gem5 declares a NESTED gem5::gem5:
                                     // namespace-def lookup only searches the
                                     // innermost enclosing scope; empirically
                                     // hit, build log /tmp/u2-outer.log:1111)
struct RegId;
class PhysRegId;
using PhysRegIdPtr = PhysRegId *;

class CHAOSRenameMap : public SimObject
{
  public:
    CHAOSRenameMap(const CHAOSRenameMapParams &p);
    ~CHAOSRenameMap();

    // Self-attach at startup (CPU hierarchy constructed before rename map
    // is wired). Sets thread-0 frontRenameMap().chaosRenameMap = this.
    void startup() override;

    // Called from UnifiedRenameMap::setEntry BEFORE the real map write (the
    // injector mutates the by-ref phys_reg so setEntry stores the corrupted
    // mapping; only thread-0's FRONT rename map is attached — the hook fires
    // on the squash-rollback restore path Rename::doSquash, since
    // SimpleRenameMap::rename() writes directly). map_bitflip: point at a
    // different valid physReg = 1-bit remap; map_bitflip2 (W4.1 D12): flip
    // TWO distinct random bits of the physReg index; f5_substitute: point at
    // a currently-allocated physReg of the same class; f4_field_stuck: pin to
    // a wrong physReg every time this arch_reg is setEntry'd. `tid` is the
    // thread (0 for single-thread SE). `arch_reg` is the architectural reg
    // whose entry was just written; `phys_reg` is the value written (by ref —
    // the injector may mutate it so the CALLER's setEntry sees the corrupted
    // mapping). Returns true if an injection happened this call.
    bool maybeCorrupt(ThreadID tid, const RegId &arch_reg,
                      PhysRegIdPtr &phys_reg);

    // §2.3 spec_leak (method1 speculative-state leak, Phase 4.1): called from
    // Rename::doSquash BEFORE the history-buffer rollback undoes a mapping.
    // Return true = SUPPRESS this one rollback: skip both the
    // renameMap->setEntry(archReg, prevPhysReg) restore AND the
    // freeingInProgress push of newPhysReg. The wrong-path µop's destination
    // register stays mapped+architecturally visible — its (wrong-path) value
    // leaks into the post-squeeze correct path. Resource accounting stays
    // consistent: the leaked physReg is owned by the arch reg until the next
    // committer of that arch reg frees it (same lifetime as any mapping).
    bool maybeSuppressRollback(ThreadID tid, const RegId &arch_reg,
                               PhysRegIdPtr new_phys, PhysRegIdPtr prev_phys);

    // W4.3 D15 f5_rat_stuck (04-design-matrix R16, F5 permanent, write-path
    // mask): ONE int-class FRONT-map RAT entry + ONE physReg-index bit pinned
    // to a fixed polarity, chosen once at the first in-window eligible write
    // event ("运行开始（首个注入窗口到达时）随机选一个 RAT 表项的一个比特
    // 位"). From then on EVERY write to that entry stores the value with that
    // bit forced — the G2 PhysRegFile::setStuckTarget write-path-mask
    // semantics (regfile.hh:360), with the state held HERE because
    // SimpleRenameMap cannot build a masked PhysRegIdPtr (no regFile access).
    // Applications after arming are exposures of the ONE permanent fault,
    // NOT new faults: arming is the only faults_injected_count increment and
    // is NOT re-gated by max_faults/probability afterwards (F5 = permanent
    // from existence). `site` only names the calling write path in the log
    // ("rename_write" = SimpleRenameMap::rename normal write;
    // "setEntry_restore" = squash-rollback restore).
    bool maybeStuckWrite(ThreadID tid, const RegId &arch_reg,
                         PhysRegIdPtr &phys_reg, const char *site);

    // W4.3 D15 post-rename hook: called from UnifiedRenameMap::rename AFTER
    // SimpleRenameMap::rename performed the entry write (the normal rename
    // write path — it writes the map DIRECTLY and never goes through
    // UnifiedRenameMap::setEntry, so the pre-existing setEntry hook cannot
    // mask it). `entry_phys` is in/out: on entry = the just-written phys; on
    // a true return the caller must re-store entry_phys (the masked value)
    // via the RAW SimpleRenameMap::setEntry (no recursion into the setEntry
    // hook). `prev_phys` = the mapping the entry held before this write
    // (W4.4 D16 stale_read rolls the entry back to it). Returns false for
    // every other mode (zero regression: the rename path keeps its original
    // behavior byte-for-byte).
    bool maybeFaultRename(ThreadID tid, const RegId &arch_reg,
                          PhysRegIdPtr prev_phys, PhysRegIdPtr &entry_phys);

    // W4 final D14 swap_mispred_event (ooo 04-design-matrix R15,
    // RAT映射字段·换值·误预测事件触发): called by Rename around its
    // squash() handling — records whether the squash currently in flight was
    // caused by a BRANCH MISPREDICTION (commit.cc sets commitInfo.mispredictInst
    // only for mispredict squashes; traps/order-violations/squashAfter NULL
    // it). While the context is active, the doSquash restore writes
    // (UnifiedRenameMap::setEntry -> maybeCorrupt) are eligible for the
    // D14 swap. clearSquashSignal() MUST be called after squash() returns
    // (rename.cc wraps the call). Notify-only for every other mode.
    void notifySquashSignal(bool mispredict, ThreadID tid, InstSeqNum sn);
    void clearSquashSignal();

    // W4 final D23/D24 hb_bitflip / hb_bitflip2 (ooo 04-design-matrix
    // R24/R25, 重命名检查点·单/双比特翻转): gem5 has no RAT-checkpoint
    // structure — the recovery checkpoint IS the historyBuffer entry
    // RenameHistory{instSeqNum, archReg, newPhysReg, prevPhysReg}
    // (rename.hh:301; mechanism-verified N1). Called from
    // Rename::renameDestRegs at the checkpoint's CREATION (push_front site):
    // flips 1 bit (D23) / 2 distinct random bits (D24) of ONE randomly
    // chosen field's physReg index (newPhysReg or prevPhysReg, 50/50). The
    // instruction itself keeps its TRUE dest (inst->renameDestReg is fed
    // from the untouched rename_result) — only the checkpoint copy is
    // corrupted, so the fault stays DORMANT until the entry is consumed by
    // doSquash (mispred restore: setEntry(free) with the corrupted phys) or
    // removeFromHistory (commit release: addReg of the corrupted phys).
    // Out-of-range flip = honest skip (logged, never clamped). Arms a
    // one-shot consumption watch (see notifyHistoryConsumed).
    bool maybeCorruptHistory(ThreadID tid, InstSeqNum sn,
                             const RegId &arch_reg,
                             PhysRegIdPtr &new_phys, PhysRegIdPtr &prev_phys);

    // W4 final D23/D24 consumption watch: called from Rename::doSquash and
    // Rename::removeFromHistory for EVERY history entry they process. When
    // the armed watch's seqNum matches, logs the "squash/commit consumed the
    // WRONG phys" evidence line and disarms. READ-ONLY (no behavior change,
    // no fault counting) — the corruption happened at creation. W5.6
    // oldphys_stuck additionally consults the masked-sn set below (the
    // repeatable-defect multi-consumption evidence).
    void notifyHistoryConsumed(ThreadID tid, InstSeqNum sn,
                               const RegId &arch_reg,
                               PhysRegIdPtr new_phys, PhysRegIdPtr prev_phys,
                               const char *site);

    // ---- U2 (R08/FR09, ooo 03-design-matrix R8/R38 Rename 时序) ----
    // Four sub-modes, one SimObject (per plan: 复用 CHAOSRenameMap 载体,
    // target_class int=R08 / vec=FR09 via the W7.2 class axis):
    //
    // a 提前 (RenameTimingEarly) — RAT 更新延后一拍·tick 始回放: called
    // from UnifiedRenameMap::rename AFTER SimpleRenameMap::rename wrote
    // the entry (rollback-and-defer: on true the caller re-stores
    // prev_phys, the injector queues (arch,new) and its next-tick-start
    // event re-applies map[arch]=new BEFORE any rename lookup of the
    // new cycle). In the window the arch reg reads the OLD mapping.
    // Honesty note (plan Step-1): gem5's sub-updates are tick-atomic —
    // a pure "write a full beat EARLY" has no observable surface; the
    // two 1-beat skews differ by replay point (tick-start vs tick-end);
    // only the tick-start variant is wired as sub-mode a (the tick-end
    // variant and the RAT-延后/freelist-提前 alternates stay recorded,
    // unwired, in the plan honesty note).
    bool maybeDeferRatWrite(const RegId &arch_reg, PhysRegIdPtr prev_phys,
                            PhysRegIdPtr new_phys);
    //
    // b 延后 (RenameTimingLate) — free-list 弹出延后一拍: PRE-pop hook in
    // SimpleFreeList::getReg. On true the caller does NOT pop: the phys
    // reg stays at the freelist head for the rest of this cycle (同窗另
    // 一 rename 可能弹出同号 → 双重分配 = 静默 SDC 源, 03 原文口径);
    // the injector's next-tick-start event performs the deferred pop.
    bool maybeDelayFreePop(int class_value, PhysRegIdPtr free_reg);
    //
    // c 丢失 (RenameTimingDrop) — ROB 分配时序 at commit.cc getInsts
    // rob->insertInst (v25: ROB insertion lives in the Commit tick —
    // plan honesty note). Returns 0 normal / 2 skip-insert (丢失:
    // executes, never retires — dest phys leaks, commit count loses
    // one). Eligibility: the inst has >=1 dest reg in target_class.
    int maybeTimingAlloc(const o3::DynInst *inst, ThreadID tid);
    //
    // d 重复 (RenameTimingDup) — U2 round-2 revision: the double-ROB-
    // insert realization aborted at rob.cc:513 readHeadInst isInROB
    // (first retire clears the flag; the second node violates it —
    // r08-dup/fr09-dup rc=134 evidence), so dup moved to the RENAME
    // HISTORY-BOOKKEEPING surface (rename.cc push_front site): the
    // victim's RenameHistory entry is pushed TWICE. The commit-side
    // removeFromHistory walk consumes both same-sn entries in one
    // pass → prevPhysReg is freeList->addReg'd TWICE (freelist gains
    // a duplicate phys reg → two later renames pop the same reg →
    // phys aliasing = silent SDC source) and committedMaps counts +2
    // (双提交/计数翻倍 observably preserved). Eligibility: the dest
    // rename's new phys is in target_class and differs from prev.
    bool maybeDupRenameHistory(ThreadID tid, InstSeqNum inst_seq_num,
                               const RegId &arch,
                               PhysRegIdPtr new_phys,
                               PhysRegIdPtr prev_phys);

  private:
    enum class Mode { MapBitflip, MapBitflip2, SwapToActive, F5Substitute,
                      F4FieldStuck, SpecLeak, F5RatStuck, StaleRead,
                      SwapMispredEvent, HbBitflip, HbBitflip2,
                      // W5.6 (ooo 04-design-matrix D36-D39, Int Dispatch/
                      // ROB old-physical-register field): the old-phys
                      // value in gem5 lives in the rename historyBuffer's
                      // prevPhysReg (the W4 N1 finding), so the family is
                      // implemented here, at the SAME push_front site the
                      // hb_bitflip modes use — but targeting prevPhysReg
                      // exclusively (hb_bitflip picks new/prev 50/50).
                      OldphysBitflip, OldphysBitflip2, OldphysSwapActive,
                      OldphysStuck,
                      // ---- U2 (R08/FR09, ooo 03-design-matrix R8/R38
                      // Rename 时序; 04-matrix numbering does NOT have
                      // these — the 03 registry is authoritative) ----
                      RenameTimingEarly,   // R08-a/FR09-a 提前: RAT 更新
                                           // 延后一拍, tick 始回放
                      RenameTimingLate,    // R08-b/FR09-b 延后: free-list
                                           // 弹出延后一拍 (双重分配窗口)
                      RenameTimingDrop,    // R08-c/FR09-c 丢失: ROB 分配
                                           // 丢失 (insert skipped)
                      RenameTimingDup };   // R08-d/FR09-d 重复: ROB 双
                                           // insert (双提交/计数翻倍)
    static Mode stringToMode(const std::string &s);
    const char *modeToString(Mode m);

    BaseCPU *cpu;  // set from p.cpu; dynamic_cast<o3::CPU*> in startup()

    Mode fi_mode;

    // W7.2 (ooo 04-design-matrix D62-D71 merged rows, VecRegClass RAT
    // family): the register class whose FRONT-map entries the injector
    // targets. "int" = IntRegClass (X0-X30; XZR idx 31 and banked slots
    // >=32 excluded — the CHAOSReg discipline), "vec" = VecRegClass
    // (V0-V31, flattened indices 0-31; gem5-internal Special-8 +
    // Interleave-4 indices 32-43 excluded as the banked-slot analog;
    // AArch64 has NO zero vector register). Platform fact (W1.2, verified
    // on C3): AArch64 gem5 v25 renames scalar FP (D/S regs) through
    // VecRegClass — FloatRegClass is structurally present but inert — so
    // the north-star's scalar-FP rows D62-66 are MERGED into the vec
    // class (D62's own merge clause), not a separate "float" target.
    //
    // ATTRIBUTION DESIGN DECISION (documented): the rename hooks receive
    // only the RegId being written — no opClass — so at injection time a
    // vec-class entry cannot be attributed to a scalar-FP (D62-66) vs a
    // SIMD (D67-71) producer. Both row families share this ONE code path
    // by design; attribution is POST-HOC via the commit trace
    // (CHAOSCommitTrace opClass column) when the campaign needs the split.
    //
    // The W5.6 oldphys_* modes (D36-D39, Int Dispatch/ROB family) stay
    // int-only: targetClass=vec + oldphys_* warns at construction and the
    // injector stays inert (their own IntRegClass gate is unchanged).
    RegClassType target_class = IntRegClass;

    int target_arch_reg;       // -1 = random
    double probability;
    uint64_t first_clock, last_clock;
    uint64_t fault_mask;
    uint64_t max_faults;
    uint64_t faults_injected_count = 0;
    uint64_t rng_seed;
    bool write_log;

    // f4_field_stuck: pin a specific arch_reg's entry to a wrong physReg
    // permanently. Set on first injection of that arch_reg.
    bool f4_armed = false;
    int f4_arch_reg = -1;
    int f4_wrong_phys_idx = -1;

    // W4.3 D15 f5_rat_stuck state: armed ONCE at the first in-window eligible
    // write (the fault's creation), permanent until end of run. Every write
    // to f5s_arch_reg's FRONT-map entry is masked with the forced bit.
    bool f5s_armed = false;
    int f5s_arch_reg = -1;
    int f5s_bit = -1;
    int f5s_polarity = 0;      // 0 = stuck_at_zero (force 0), 1 = stuck_at_one
    uint64_t f5s_exposures = 0;  // write-path mask applications (persistence
                                 // evidence; NOT fault count)

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    // spec_leak sampling-bias fix (Phase 3.0 family): geometric(0.1) count
    // of eligible rollbacks to skip before the first suppressed one.
    uint64_t events_to_skip = 0;

    // ---- U2 (R08/FR09) timing-mode state ----
    // R08-a: pending deferred RAT writes + the next-tick-start replay
    // event (Default_Pri < CPU_Tick_Pri=50 -> fires BEFORE the CPU tick:
    // the recorded "任何 rename lookup 之前" replay point).
    // prev = the pre-write mapping: the replay is CONDITIONAL (only
    // lands if the entry still equals prev — an intervening newer write
    // of the same arch reg inside the window stands, the deferred write
    // is absorbed and logged honest_skip; otherwise a blind replay would
    // revert a newer mapping, a corruption stronger than the 1-beat
    // visibility window the model specifies).
    struct PendingRatWrite { RegId arch; PhysRegIdPtr phys;
                             PhysRegIdPtr prev; };
    std::vector<PendingRatWrite> pending_rat_writes;
    EventFunctionWrapper ratReplayEvent;
    // R08-b: deferred freelist pops (per class value) + the same
    // next-tick-start event shape.
    std::vector<int> pending_pops;
    EventFunctionWrapper freePopEvent;
    // cached dynamic_cast<o3::CPU*>(cpu) from startup() (the replay
    // handlers need it without re-casting inside the event).
    o3::CPU *o3cpu = nullptr;
    void ratReplay();
    void freePopReplay();

    // W4 final D14 swap_mispred_event squash context: set by
    // notifySquashSignal() for the duration of Rename::squash() (which runs
    // doSquash to completion in one call), cleared by clearSquashSignal().
    // sq_mispredict = commitInfo.mispredictInst != NULL (branch-mispred
    // squash); the D14 injection is eligible ONLY inside a mispredict
    // restore. sq_sn = doneSeqNum (the mispredicted branch's seqNum) for the
    // evidence line.
    bool sq_active = false;
    bool sq_mispredict = false;
    InstSeqNum sq_sn = 0;
    uint64_t sq_signals_logged = 0;

    // W4 final D23/D24 hb_bitflip(_2) consumption watch: armed at the
    // creation-time corruption; disarmed by the first
    // notifyHistoryConsumed() whose sn matches (the checkpoint is consumed
    // exactly once — erased by doSquash/removeFromHistory).
    bool hb_watch_armed = false;
    InstSeqNum hb_watch_sn = 0;
    int hb_watch_arch_idx = -1;
    int hb_watch_is_new_field = 0;   // 1 = newPhysReg flipped, 0 = prevPhysReg
    int hb_watch_orig_idx = -1;      // the TRUE phys idx before the flip
    int hb_watch_corrupt_idx = -1;   // the flipped (wrong) phys idx

    // W5.6 D39 oldphys_stuck (F5) state: ONE stuck-at bit in the
    // old-phys FIELD's storage cell — per the design row ("运行开始时
    // 随机选一个比特位置，永久固定为 0 或 1 ... 持久缺陷+多次 squash
    // 反复命中 ... 累积效应") the defect is NOT one entry (contrast
    // f5_rat_stuck's "随机选一个 RAT 表项") but the shared field cell:
    // EVERY int-class history push's prevPhysReg write is masked after
    // arming. ops_masked_sns tracks the entries whose stored value the
    // mask actually CHANGED (the observable corruptions) so the
    // consumption watch can log every squash/release that consumes a
    // masked old-phys — the "同一错误模式在多次 squash 中重复出现"
    // evidence.
    bool ops_armed = false;
    int ops_bit = -1;
    int ops_polarity = 0;            // 0 = stuck_at_zero, 1 = stuck_at_one
    uint64_t ops_exposures = 0;      // write-path mask applications
    uint64_t ops_masked_count = 0;   // writes whose value the mask changed
    std::set<InstSeqNum> ops_masked_sns;

    bool inWindow();

    // ---- W7.2 class helpers (targetClass; int paths byte-identical) ----
    // Number of arch regs the random-target draw may land on: int 31
    // (X0-X30), vec 32 (V0-V31, ArmISA::NumVecV8ArchRegs).
    int numArchTargetRegs() const;
    // Validity guard replacing the int-only "arch_idx > 30" XZR/banked
    // check: int -> idx <= 30; vec -> idx < 32 (NO zero reg in the vector
    // class; Special-8/Interleave-4 flattened indices 32-43 excluded).
    bool archIdxValid(int idx) const;
    const char *archPrefix() const;   // "X" / "V" (log arch names)
    const char *className() const;    // "int" / "vec" (log arch_reg=...)
    // "" for int (byte-identical legacy log lines) / ", class=vec" tag.
    const char *classTag() const;
    // Pool size / id-table accessor for target_class: numIntPhysRegs vs
    // numVecPhysRegs, intPhysRegId vs vecPhysRegId (regfile.hh:172-177).
    int numPhysForClass(o3::CPU *o3cpu) const;
    PhysRegIdPtr physRegIdForClass(o3::CPU *o3cpu, int idx) const;

    // f5_substitute: pick a currently-allocated (not-free) physReg of the same
    // class as `cur`, return its index or -1 if no valid candidate after K tries.
    int pickAllocatedPhysReg(int class_value, int cur_idx, int num_phys,
                             o3::CPU *o3cpu);

    // W4.2a D13 swap_to_active: one candidate = the dest physReg (of
    // `class_value`'s class) of an in-flight (ROB-resident) instruction,
    // != the current mapping. W7.2: class parameterized — the vec modes
    // collect VecRegClass dests (the "vec 活跃池" evidence pool).
    struct RobCand { int phys_idx; int dist; uint64_t sn; };
    // Walk the ROB from head (getEntryAtDistance, the CHAOSROB.cc pattern)
    // and collect all such candidates. Returns the candidate count (0 = ROB
    // empty or no class-matching dest != cur_idx -> honest skip, logged).
    int collectRobActiveDests(int class_value, int cur_idx, o3::CPU *o3cpu,
                              ThreadID tid, std::vector<RobCand> &cands);

    // W5.6 D36-D39 oldphys family impl (called from maybeCorruptHistory —
    // the same rename.cc push_front site as hb_bitflip, but the corrupted
    // field is ALWAYS prevPhysReg, the "ROB old-physical-register field"
    // of the design, realized as the rename-history checkpoint's old-phys
    // value). One-shot for bitflip/bitflip2/swap_active (targetArchReg
    // directed or random 0..30, the W4.4 flat-index discipline); F5
    // permanent write-path mask for stuck. Dormant until a squash/release
    // consumes the checkpoint (the hb_watch / ops_masked_sns evidence).
    bool maybeCorruptOldphys(ThreadID tid, InstSeqNum sn,
                             const RegId &arch_reg,
                             PhysRegIdPtr &new_phys,
                             PhysRegIdPtr &prev_phys);
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_RENAME_MAP_HH__
