#ifndef __CPU_O3_CHAOS_RENAME_MAP_HH__
#define __CPU_O3_CHAOS_RENAME_MAP_HH__

#include <random>
#include <string>
#include <vector>

#include "params/CHAOSRenameMap.hh"
#include "sim/sim_object.hh"
#include "base/output.hh"
#include "base/types.hh"
#include "cpu/base.hh"

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

  private:
    enum class Mode { MapBitflip, MapBitflip2, SwapToActive, F5Substitute,
                      F4FieldStuck, SpecLeak, F5RatStuck, StaleRead };
    static Mode stringToMode(const std::string &s);
    const char *modeToString(Mode m);

    BaseCPU *cpu;  // set from p.cpu; dynamic_cast<o3::CPU*> in startup()

    Mode fi_mode;
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

    bool inWindow();
    // f5_substitute: pick a currently-allocated (not-free) physReg of the same
    // class as `cur`, return its index or -1 if no valid candidate after K tries.
    int pickAllocatedPhysReg(int class_value, int cur_idx, int num_phys,
                             o3::CPU *o3cpu);

    // W4.2a D13 swap_to_active: one candidate = the int-class dest physReg of
    // an in-flight (ROB-resident) instruction, != the current mapping.
    struct RobCand { int phys_idx; int dist; uint64_t sn; };
    // Walk the ROB from head (getEntryAtDistance, the CHAOSROB.cc pattern)
    // and collect all such candidates. Returns the candidate count (0 = ROB
    // empty or no int dest != cur_idx -> honest skip, caller logs it).
    int collectRobActiveDests(int cur_idx, o3::CPU *o3cpu, ThreadID tid,
                              std::vector<RobCand> &cands);
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_RENAME_MAP_HH__
