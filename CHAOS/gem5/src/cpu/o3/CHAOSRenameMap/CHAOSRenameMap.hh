#ifndef __CPU_O3_CHAOS_RENAME_MAP_HH__
#define __CPU_O3_CHAOS_RENAME_MAP_HH__

#include <random>
#include <string>

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

    // Called from UnifiedRenameMap::setEntry AFTER the map write (the entry
    // now points at phys_reg). The injector may RE-MAP the entry (map_bitflip:
    // point at a different valid physReg = 1-bit remap; f5_substitute: point at
    // a currently-allocated physReg of the same class; f4_field_stuck: pin to
    // a wrong physReg every time this arch_reg is setEntry'd). `tid` is the
    // thread (0 for single-thread SE). `arch_reg` is the architectural reg
    // whose entry was just written; `phys_reg` is the value written (by ref —
    // the injector may mutate it so the CALLER's setEntry sees the corrupted
    // mapping). Returns true if an injection happened this call.
    bool maybeCorrupt(ThreadID tid, const RegId &arch_reg,
                      PhysRegIdPtr &phys_reg);

  private:
    enum class Mode { MapBitflip, F5Substitute, F4FieldStuck };
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

    std::mt19937 rng;
    std::random_device rd;
    OutputStream *log_stream = nullptr;

    bool inWindow();
    // f5_substitute: pick a currently-allocated (not-free) physReg of the same
    // class as `cur`, return its index or -1 if no valid candidate after K tries.
    int pickAllocatedPhysReg(int class_value, int cur_idx, int num_phys,
                             o3::CPU *o3cpu);
};

} // namespace gem5

#endif // __CPU_O3_CHAOS_RENAME_MAP_HH__
